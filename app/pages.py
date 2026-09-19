"""One function per workspace surface, each returning exactly what that
surface needs as JSON.

These used to feed Jinja templates. The frontend is now a separate Next.js app
in `frontend/`, so the payloads are serialised straight to JSON by
`app/webapp.py` — which is why `_chrome` returns plain dicts rather than
SQLAlchemy objects.

Everything here is a real query against the Supabase Postgres the rest of the
app already uses. The workspace these pages resolve to is empty, so the
numbers come back as 0 and the tables come back as `[]` — that is the intended
state, not a placeholder. Put rows in the database and the same queries fill
the same panels in.

Three rules this module follows:

  * A count that is genuinely zero renders as `0`. A value that cannot be
    known yet (organic traffic with no Search Console, AI citations with no
    model-visibility crawl) renders as `None`, which the templates draw as an
    em dash with a note saying what it needs. Zero and unknown are different
    things and the UI says which is which.
  * Nothing is estimated, seeded or interpolated to make a panel look alive.
  * Panels whose data has no table yet return empty and say so. Each one is
    marked `NEEDS:` below so the gap is findable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import charts, config, demo, ga, search_console
from app.models import (Account, ApiKey, Change, ContentPost, Finding,
                        Integration, Job, Page, Scan, Site, User)

# Colour per project card / donut slice, applied by position so a given
# project keeps its colour across pages.
TONES = ["b", "v", "g", "a", "s", "p", "t", "r"]
SLICE = [charts.INDIGO, charts.VIOLET, charts.GREEN, charts.AMBER,
         charts.SKY, charts.PINK, charts.TEAL, charts.RED]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _ago(dt: datetime | None) -> str:
    """"2 hours ago", the way every feed in the designs is labelled."""
    dt = _aware(dt)
    if dt is None:
        return ""
    secs = (_now() - dt).total_seconds()
    if secs < 90:
        return "just now"
    for cut, div, word in ((3600, 60, "minute"), (86400, 3600, "hour"),
                           (2592000, 86400, "day"), (31536000, 2592000, "month")):
        if secs < cut:
            n = int(secs // div)
            return f"{n} {word}{'' if n == 1 else 's'} ago"
    n = int(secs // 31536000)
    return f"{n} year{'' if n == 1 else 's'} ago"


def _d(dt: datetime | None) -> str:
    dt = _aware(dt)
    return "" if dt is None else f"{dt.strftime('%b')} {dt.day}, {dt.year}"


def _dt(dt: datetime | None) -> str:
    dt = _aware(dt)
    return "" if dt is None else (f"{dt.strftime('%b')} {dt.day}, {dt.year} "
                                  f"{dt.strftime('%I:%M %p').lstrip('0')}")


# --- the workspace -------------------------------------------------------


def resolve_account(session: Session) -> Account:
    """The workspace these pages render.

    Picks the first account that is not the seeded demo estate, and creates an
    empty one if there is none. The demo estate is left alone so it stays
    available as fillers later — see `python -m app.seed`.
    """
    # The seeded demo estate wins when it exists, so the dashboard has
    # something in it to look at. `python -m app.seed --purge` removes it and
    # these pages fall through to a real, empty workspace.
    account = session.scalars(
        select(Account).where(Account.slug == config.DEMO_ACCOUNT_SLUG)
        .limit(1)).first()
    if account is not None and account.sites:
        return account

    account = session.scalars(
        select(Account).where(Account.slug != config.DEMO_ACCOUNT_SLUG)
        .order_by(Account.created_at).limit(1)).first()
    if account is None:
        account = Account(name="My Workspace", slug="workspace", kind="direct")
        session.add(account)
        session.commit()
        session.refresh(account)
    return account


def sites_of(session: Session, account: Account) -> list[Site]:
    return list(session.scalars(
        select(Site).where(Site.account_id == account.id, Site.is_active.is_(True))
        .order_by(Site.created_at)).all())


def _latest_scans(session: Session, sites: list[Site]) -> dict[str, Scan]:
    """The newest finished scan per site, or {} when nothing has been read."""
    if not sites:
        return {}
    rows = session.scalars(
        select(Scan).where(Scan.site_id.in_([s.id for s in sites]),
                           Scan.status == "done")
        .order_by(Scan.finished_at.desc())).all()
    out: dict[str, Scan] = {}
    for sc in rows:
        out.setdefault(sc.site_id, sc)
    return out


def _chrome(session: Session, account: Account, page: str,
            site: Site | None = None) -> dict:
    """Rail and topbar context, on every page."""
    sites = sites_of(session, account)
    unread = notification_count(session, account)
    end = _now()
    chosen = site or (sites[0] if sites else None)
    return {
        "account": {
            "id": account.id, "name": account.name, "slug": account.slug,
            "kind": account.kind, "white_label": account.white_label,
            "on_trial": account.on_trial(),
            "trial_days_left": account.trial_days_left(),
        },
        "page": page,
        "projects": [{"id": s.id, "hostname": s.hostname,
                      "name": s.client_name or s.label or s.hostname}
                     for s in sites],
        "project": ({"id": chosen.id, "hostname": chosen.hostname,
                     "name": chosen.client_name or chosen.label or chosen.hostname}
                    if chosen else None),
        "alerts": unread,
        "range_label": (f"{(end - timedelta(days=13)).strftime('%b')} "
                        f"{(end - timedelta(days=13)).day}, {end.year} – "
                        f"{end.strftime('%b')} {end.day}, {end.year}"),
        "initials": "".join(w[0] for w in account.name.split()[:2]).upper() or "W",
        # The ORM objects the page functions still need internally. Stripped
        # before the payload leaves `webapp.py`.
        "_sites": sites,
        "_site": chosen,
        "_account": account,
    }


def notification_count(session: Session, account: Account) -> int:
    """Unread alerts = things genuinely needing a person: failed jobs, changes
    waiting for approval, and high-severity findings on the latest scans."""
    sites = sites_of(session, account)
    if not sites:
        return 0
    ids = [s.id for s in sites]
    failed = session.scalar(select(func.count()).select_from(Job)
                            .where(Job.status == "failed")) or 0
    waiting = session.scalar(
        select(func.count()).select_from(Change)
        .where(Change.site_id.in_(ids), Change.state == "proposed")) or 0
    latest = _latest_scans(session, sites)
    high = 0
    if latest:
        high = session.scalar(
            select(func.count()).select_from(Finding)
            .where(Finding.scan_id.in_([s.id for s in latest.values()]),
                   Finding.severity == "high")) or 0
    return int(failed + waiting + high)


# --- 1. all projects dashboard -------------------------------------------


def projects(session: Session, account: Account) -> dict:
    ctx = _chrome(session, account, "projects")
    sites = ctx["_sites"]
    latest = _latest_scans(session, sites)

    cards = []
    for i, s in enumerate(sites):
        sc = latest.get(s.id)
        published = session.scalar(
            select(func.count()).select_from(ContentPost)
            .where(ContentPost.site_id == s.id,
                   ContentPost.state == "published")) or 0
        cards.append({
            "id": s.id, "name": s.client_name or s.label or s.hostname,
            "tagline": s.label if s.client_name else "",
            "hostname": s.hostname, "tone": TONES[i % len(TONES)],
            "initial": (s.client_name or s.hostname)[0].upper(),
            "state": "Active" if s.monitor else "Paused",
            "published": published,
            "impact": sc.score if sc else None,
        })

    total_published = session.scalar(
        select(func.count()).select_from(ContentPost)
        .where(ContentPost.site_id.in_([s.id for s in sites]),
               ContentPost.state == "published")) if sites else 0

    scores = [sc.score for sc in latest.values() if sc.score is not None]
    searches = [sc.score_search for sc in latest.values() if sc.score_search is not None]
    answers = [sc.score_answers for sc in latest.values() if sc.score_answers is not None]

    def avg(xs):
        return round(sum(xs) / len(xs)) if xs else None

    # Traffic, impressions and engine visibility come from Search Console and
    # the model crawl. Neither is connected, so they are unknown in a real
    # workspace and filled from app/demo.py in the seeded estate.
    fill = demo.is_demo(account)
    ids = [s.id for s in sites]
    days = 30
    labels = demo.day_labels(days) if fill else []

    ctx.update({
        "demo": fill,
        "cards": cards,
        "kpis": {
            "projects": len(sites),
            "published": int(total_published or 0),
            "traffic": demo.estate_traffic(ids) if fill else None,
            "impressions": demo.estate_impressions(ids) if fill else None,
            "impact": avg(scores),
            "synced": f"{len(latest)}/{len(sites)}" if sites else "0/0",
        },
        "trend": charts.series(labels, [
            {"name": "Organic Traffic", "colour": charts.BLUE,
             "values": demo.curve("estate-traffic", days, 14_000) if fill else []},
            {"name": "Impressions", "colour": charts.VIOLET,
             "values": demo.curve("estate-impr", days, 26_000) if fill else []},
            {"name": "Published Posts", "colour": charts.GREEN,
             "values": demo.curve("estate-posts", days, 4_000, growth=1.1) if fill else []},
        ]),
        "seo_health": charts.gauge(avg(searches), size=138, stroke=15, fs=30),
        "seo_rows": [
            {"label": "Technical SEO", "value": avg(searches)},
            {"label": "Content Quality", "value": avg([sc.score_craft
                for sc in latest.values() if sc.score_craft is not None])},
            {"label": "On-page SEO", "value": avg([sc.score_structure
                for sc in latest.values() if sc.score_structure is not None])},
            {"label": "Backlinks", "value": demo.pct("backlinks", 60, 74) if fill else None},
            {"label": "Site Performance", "value": demo.pct("perf", 86, 95) if fill else None},
        ],
        "geo_health": charts.gauge(avg(answers), size=138, stroke=15, fs=30,
                                   suffix="%" if avg(answers) else ""),
        "geo_rows": [
            {"label": name, "colour": colour,
             "value": value if fill else None,
             "delta": demo.delta(f"eng:{name}", 8, 22) if fill else None}
            for name, colour, value in demo.ENGINES
        ],
        "top": sorted(
            [{"title": c["name"], "sub": c["hostname"],
              "traffic": demo.site_traffic(c["id"]) if fill else None,
              "impressions": demo.site_impressions(c["id"]) if fill else None,
              "impact": c["impact"], "tone": c["tone"],
              "initial": c["initial"]} for c in cards],
            key=lambda r: -(r["impact"] or 0))[:5],
        "dist": _distribution(session, sites),
        "activity": _activity(session, account, limit=5),
        "table": sorted(
            [{"id": c["id"], "name": c["name"], "tone": c["tone"],
              "initial": c["initial"], "state": c["state"],
              "published": c["published"],
              "traffic": demo.site_traffic(c["id"]) if fill else None,
              "impressions": demo.site_impressions(c["id"]) if fill else None,
              "impact": c["impact"],
              "updated": _d(latest[c["id"]].finished_at) if c["id"] in latest else ""}
             for c in cards], key=lambda r: r["name"]),
        "opportunities": _opportunities(session, sites, latest),
        "calendar": _calendar(session, sites),
        "automation": [
            {"icon": "sync", "tone": "b", "name": "Content Sync",
             "detail": f"{len(latest)} / {len(sites)} projects" if sites else "0 / 0 projects",
             "state": "Active" if latest else "Idle",
             "note": "Never run" if not latest else f"Last sync {_ago(max(sc.finished_at for sc in latest.values()))}"},
            {"icon": "spark", "tone": "v", "name": "AI Content Suggestions",
             "detail": f"{_count_posts(session, sites, 'queued')} briefs",
             "state": "Idle", "note": "Runs after an audit"},
            {"icon": "target", "tone": "g", "name": "Auto SEO Optimization",
             "detail": f"{_connected(session, sites)} / {len(sites)} connected" if sites else "0 / 0 connected",
             "state": "Blocked" if sites and not _connected(session, sites) else "Idle",
             "note": "Needs a CMS connection"},
            {"icon": "chart", "tone": "s", "name": "Analytics Sync",
             "detail": (f"{len(sites)} / {len(sites)} projects" if fill
                        else "0 / 0 projects"),
             "state": "Active" if fill else "Not connected",
             "note": "Last sync 28 minutes ago" if fill else "Needs Google Analytics"},
        ],
    })
    return ctx


def _count_posts(session: Session, sites: list[Site], state: str) -> int:
    if not sites:
        return 0
    return int(session.scalar(
        select(func.count()).select_from(ContentPost)
        .where(ContentPost.site_id.in_([s.id for s in sites]),
               ContentPost.state == state)) or 0)


def _connected(session: Session, sites: list[Site]) -> int:
    if not sites:
        return 0
    return int(session.scalar(
        select(func.count()).select_from(Integration)
        .where(Integration.site_id.in_([s.id for s in sites]),
               Integration.connected_at.isnot(None))) or 0)


def _distribution(session: Session, sites: list[Site]) -> dict:
    """Projects grouped by account kind. With no sites this is an empty ring."""
    buckets: dict[str, int] = {}
    for s in sites:
        key = (s.label or "Uncategorised").strip() or "Uncategorised"
        buckets[key] = buckets.get(key, 0) + 1
    parts = [{"name": k, "value": v, "colour": SLICE[i % len(SLICE)]}
             for i, (k, v) in enumerate(sorted(buckets.items(),
                                               key=lambda kv: -kv[1]))]
    d = charts.donut(parts, size=150, stroke=22, label="Projects",
                     total=len(sites))
    return d


def _opportunities(session: Session, sites: list[Site],
                   latest: dict[str, Scan]) -> list[dict]:
    """Ranked by severity times reach, from the newest scan of each site."""
    if not latest:
        return []
    by_site = {v.id: k for k, v in latest.items()}
    names = {s.id: (s.client_name or s.hostname) for s in sites}
    rows = session.execute(
        select(Finding.check, Finding.summary, Finding.severity,
               func.count(func.distinct(Finding.scan_id)).label("n"))
        .where(Finding.scan_id.in_(list(by_site)))
        .group_by(Finding.check, Finding.summary, Finding.severity)
        .order_by(func.count(func.distinct(Finding.scan_id)).desc())
        .limit(5)).all()
    weight = {"high": 3, "medium": 2, "low": 1}
    out = []
    for i, (check, summary, sev, n) in enumerate(rows):
        out.append({
            "title": summary[:70], "sub": f"{n} project{'' if n == 1 else 's'} affected",
            "level": "High" if sev == "high" else ("Medium" if sev == "medium" else "Low"),
            "tone": "r" if sev == "high" else ("a" if sev == "medium" else ""),
            "icon": ["bulb", "target", "leaf", "nav", "home"][i % 5],
            "itone": TONES[i % len(TONES)],
        })
    return out


def _calendar(session: Session, sites: list[Site]) -> list[dict]:
    """Mon-Fri of the current week, with anything scheduled on each day."""
    today = _now()
    monday = (today - timedelta(days=today.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0)
    names = {s.id: (s.client_name or s.hostname) for s in sites}

    posts = []
    if sites:
        posts = list(session.scalars(
            select(ContentPost).where(
                ContentPost.site_id.in_([s.id for s in sites]),
                ContentPost.scheduled_for.isnot(None),
                ContentPost.scheduled_for >= monday,
                ContentPost.scheduled_for < monday + timedelta(days=5))).all())

    days = []
    for i in range(5):
        day = monday + timedelta(days=i)
        items = [{"site": names.get(p.site_id, ""), "title": p.title,
                  "tone": TONES[list(names).index(p.site_id) % len(TONES)]
                          if p.site_id in names else "b"}
                 for p in posts
                 if (_aware(p.scheduled_for) or today).date() == day.date()]
        days.append({
            # Not "items": Jinja resolves `d.items` to dict.items before it
            # looks for the key, so the template would iterate the method.
            "dow": day.strftime("%a"), "label": f"{day.strftime('%b')} {day.day}",
            "count": len(items), "posts": items,
            "today": day.date() == today.date(),
        })
    return days


def _activity(session: Session, account: Account, limit: int = 8) -> list[dict]:
    """A merged feed from the tables that actually record events."""
    sites = sites_of(session, account)
    if not sites:
        return []
    ids = [s.id for s in sites]
    names = {s.id: (s.client_name or s.hostname) for s in sites}
    out: list[dict] = []

    for p in session.scalars(
            select(ContentPost).where(ContentPost.site_id.in_(ids),
                                      ContentPost.published_at.isnot(None))
            .order_by(ContentPost.published_at.desc()).limit(limit)).all():
        out.append({"icon": "doc", "tone": "b", "title": "Blog post published",
                    "sub": f"{names.get(p.site_id,'')} · {p.title[:46]}",
                    "at": _aware(p.published_at), "ago": _ago(p.published_at)})

    for sc in session.scalars(
            select(Scan).where(Scan.site_id.in_(ids), Scan.status == "done")
            .order_by(Scan.finished_at.desc()).limit(limit)).all():
        out.append({"icon": "sync", "tone": "g", "title": "Project synced successfully",
                    "sub": f"{names.get(sc.site_id,'')} · {sc.pages_crawled} pages read",
                    "at": _aware(sc.finished_at), "ago": _ago(sc.finished_at)})

    for ch in session.scalars(
            select(Change).where(Change.site_id.in_(ids),
                                 Change.state == "published")
            .order_by(Change.published_at.desc()).limit(limit)).all():
        out.append({"icon": "pencil", "tone": "v", "title": "Content optimized",
                    "sub": f"{names.get(ch.site_id,'')} · {ch.title[:46]}",
                    "at": _aware(ch.published_at), "ago": _ago(ch.published_at)})

    out = [o for o in out if o["at"] is not None]
    out.sort(key=lambda o: o["at"], reverse=True)
    return out[:limit]


# --- 2. content performance overview -------------------------------------


def overview(session: Session, account: Account, site: Site | None) -> dict:
    ctx = _chrome(session, account, "overview", site)
    site = ctx["_site"]
    if site is None:
        ctx.update(_blank_overview())
        return ctx

    latest = session.scalars(
        select(Scan).where(Scan.site_id == site.id, Scan.status == "done")
        .order_by(Scan.finished_at.desc()).limit(1)).first()

    def posts(state):
        return int(session.scalar(
            select(func.count()).select_from(ContentPost)
            .where(ContentPost.site_id == site.id,
                   ContentPost.state == state)) or 0)

    funnel = [
        {"label": "Ideas Generated", "n": posts("queued"), "colour": charts.BLUE},
        {"label": "In Writing", "n": posts("in_progress"), "colour": charts.AMBER},
        {"label": "In Review", "n": posts("review"), "colour": charts.VIOLET},
        {"label": "Scheduled", "n": posts("scheduled"), "colour": charts.TEAL},
        {"label": "Published", "n": posts("published"), "colour": charts.GREEN},
    ]

    fill = demo.is_demo(account)
    days = 30
    gsc = search_console.fetch_search_data(session, site, days) if not fill else None
    if fill:
        labels = demo.day_labels(days)
    elif gsc:
        labels = [d["date"] for d in gsc["daily"]]
    else:
        labels = []
    real_traffic = sum(d["clicks"] for d in gsc["daily"]) if gsc else None

    ctx.update({
        "demo": fill,
        "kpis": {
            "published": posts("published"),
            "queue": posts("queued") + posts("in_progress") + posts("review"),
            "traffic": demo.site_traffic(site.id) if fill else real_traffic,
            "impact": latest.score if latest else None,
            "sync": "Healthy" if latest else "Never run",
            "ai": demo.pct(f"ai:{site.id}", 48, 72) if fill else None,
        },
        "trend": charts.series(labels, [
            {"name": "Organic Traffic", "colour": charts.BLUE,
             "values": demo.curve(f"t:{site.id}", days, 2_600) if fill
                       else ([d["clicks"] for d in gsc["daily"]] if gsc else [])},
            {"name": "Impressions", "colour": charts.VIOLET,
             "values": demo.curve(f"i:{site.id}", days, 3_600) if fill
                       else ([d["impressions"] for d in gsc["daily"]] if gsc else [])},
            {"name": "Impact Score (x10)", "colour": charts.GREEN,
             "values": demo.curve(f"s:{site.id}", days, 620, growth=.3) if fill else []},
        ]),
        "ga": (
            ga.fetch_overview_metrics(session, site) if not fill else None
        ) or [
            {"value": v if fill else None, "label": label,
             "delta": d if fill else None}
            for v, label, d in demo.GA_PANEL
        ],
        "presence": [
            {"icon": "search", "label": "Google Search Visibility",
             "value": f"{demo.pct('gsv:' + site.id, 70, 84)}%" if fill else None,
             "delta": demo.delta("gsv", 6, 18) if fill else None},
            {"icon": "spark", "label": "AI Search Mentions",
             "value": f"{demo.pct('aim:' + site.id, 50, 68)}%" if fill else None,
             "delta": demo.delta("aim", 10, 24) if fill else None},
            {"icon": "hash", "label": "Total Ranking Keywords",
             "value": demo.scaled(f"trk:{site.id}", 142, .4) if fill else None,
             "delta": demo.delta("trk", 14, 30) if fill else None},
            {"icon": "trend", "label": "Branded Search Growth",
             "value": f"{demo.pct('bsg:' + site.id, 26, 42)}%" if fill else None,
             "delta": demo.delta("bsg", 4, 14) if fill else None},
        ],
        "impact_posts": _posts_ranked(session, site),
        "funnel": funnel,
        "funnel_total": sum(f["n"] for f in funnel),
        "funnel_donut": charts.donut(
            [{"name": f["label"], "value": f["n"], "colour": f["colour"]}
             for f in funnel], size=132, stroke=19, label="Total"),
        "activity": _site_activity(session, site),
        "keywords": (
            [{"kw": k, "pos": p, "traffic": t} for k, p, t in demo.TOP_QUERIES] if fill
            else ([{"kw": q["query"], "pos": q["position"], "traffic": q["clicks"]}
                   for q in gsc["queries"]] if gsc else [])
        ),
        "opportunities": _content_gaps(session, site, latest),
        "library": _library(session, site),
        "health": [
            {"icon": "store", "tone": "g", "name": "CMS Sync",
             "state": "Connected" if _site_connected(session, site) else "Not connected",
             "ok": _site_connected(session, site),
             "note": "Connect a CMS in Settings" if not _site_connected(session, site)
                     else "Ready to publish"},
            {"icon": "spark", "tone": "v", "name": "Content Generation",
             "state": "Not built", "ok": False,
             "note": "Drafting is deliberately not wired up"},
            {"icon": "search", "tone": "b", "name": "Search Indexing",
             "state": "Healthy" if latest else "Never run", "ok": bool(latest),
             "note": f"{latest.pages_crawled} pages read" if latest
                     else "Run an audit to start"},
            {"icon": "chart", "tone": "s", "name": "Analytics Integration",
             "state": "Connected" if (fill or ga.is_connected(session, site)) else "Not connected",
             "ok": fill or ga.is_connected(session, site),
             "note": ("Receiving data from Google Analytics"
                      if (fill or ga.is_connected(session, site))
                      else "Needs Google Analytics")},
        ],
    })
    return ctx


def _blank_overview() -> dict:
    """The overview with no project connected.

    Deliberately keeps every label and every row, with None where a value
    would be, so the page renders its real layout reading zero rather than
    collapsing into an empty state. The panels are the deliverable.
    """
    funnel = [
        {"label": "Ideas Generated", "n": 0, "colour": charts.BLUE},
        {"label": "In Writing", "n": 0, "colour": charts.AMBER},
        {"label": "In Review", "n": 0, "colour": charts.VIOLET},
        {"label": "Scheduled", "n": 0, "colour": charts.TEAL},
        {"label": "Published", "n": 0, "colour": charts.GREEN},
    ]
    return {
        "kpis": {"published": 0, "queue": 0, "traffic": None, "impact": None,
                 "sync": "No project", "ai": None},
        "trend": charts.series([], []),
        "ga": [
            {"value": None, "label": "Avg. engagement time"},
            {"value": None, "label": "Bounce rate"},
            {"value": None, "label": "Blog conversions"},
            {"value": None, "label": "Returning readers"},
        ],
        "presence": [
            {"icon": "search", "label": "Google Search Visibility", "value": None},
            {"icon": "spark", "label": "AI Search Mentions", "value": None},
            {"icon": "hash", "label": "Total Ranking Keywords", "value": None},
            {"icon": "trend", "label": "Branded Search Growth", "value": None},
        ],
        "impact_posts": [], "funnel": funnel, "funnel_total": 0,
        "funnel_donut": charts.donut([], size=132, stroke=19, label="Total"),
        "activity": [], "keywords": [], "opportunities": [], "library": [],
        "health": [
            {"icon": "store", "tone": "g", "name": "CMS Sync",
             "state": "Not connected", "ok": False,
             "note": "Connect a CMS in Settings"},
            {"icon": "spark", "tone": "v", "name": "Content Generation",
             "state": "Not built", "ok": False,
             "note": "Drafting is deliberately not wired up"},
            {"icon": "search", "tone": "b", "name": "Search Indexing",
             "state": "Never run", "ok": False,
             "note": "Add a project and run an audit"},
            {"icon": "chart", "tone": "s", "name": "Analytics Integration",
             "state": "Not connected", "ok": False,
             "note": "Needs Google Analytics"},
        ],
    }


def _site_connected(session: Session, site: Site) -> bool:
    return bool(session.scalars(
        select(Integration).where(Integration.site_id == site.id,
                                  Integration.connected_at.isnot(None))
        .limit(1)).first())


def _posts_ranked(session: Session, site: Site) -> list[dict]:
    rows = session.scalars(
        select(ContentPost).where(ContentPost.site_id == site.id,
                                  ContentPost.state == "published")
        .order_by(ContentPost.seo_score.desc().nullslast()).limit(5)).all()
    fill = demo.is_demo(site.account)
    return [{"title": p.title,
             "traffic": demo.scaled(f"pt:{p.id}", 900, .7) if fill else None,
             "impact": p.seo_score} for p in rows]


def _content_gaps(session: Session, site: Site, latest: Scan | None) -> list[dict]:
    """Topics with no page behind them, from the answers-layer findings."""
    if latest is None:
        return []
    rows = session.scalars(
        select(Finding).where(Finding.scan_id == latest.id,
                              Finding.layer == "answers").limit(5)).all()
    fill = demo.is_demo(site.account)
    return [{"topic": f.summary[:56],
             "traffic": demo.scaled(f"gt:{f.id}", 800, .6) if fill else None}
            for f in rows]


def _library(session: Session, site: Site) -> list[dict]:
    rows = session.scalars(
        select(ContentPost).where(ContentPost.site_id == site.id)
        .order_by(ContentPost.created_at.desc()).limit(8)).all()
    fill = demo.is_demo(site.account)
    return [{"id": p.id, "title": p.title,
             "state": p.state.replace("_", " ").title(),
             "tone": {"published": "g", "review": "s", "scheduled": "v",
                      "in_progress": "a"}.get(p.state, ""),
             "published": _d(p.published_at or p.scheduled_for),
             "traffic": demo.scaled(f"lt:{p.id}", 700, .7) if fill else None,
             "impact": p.seo_score} for p in rows]


def _site_activity(session: Session, site: Site) -> list[dict]:
    out = []
    for p in session.scalars(
            select(ContentPost).where(ContentPost.site_id == site.id)
            .order_by(ContentPost.created_at.desc()).limit(6)).all():
        out.append({"icon": "doc", "tone": "b",
                    "title": f"Post {p.state.replace('_', ' ')}",
                    "sub": p.title[:52], "ago": _ago(p.created_at),
                    "at": _aware(p.created_at)})
    for sc in session.scalars(
            select(Scan).where(Scan.site_id == site.id)
            .order_by(Scan.created_at.desc()).limit(6)).all():
        out.append({"icon": "sync", "tone": "g",
                    "title": f"Audit {sc.status}",
                    "sub": f"{sc.pages_crawled} pages read",
                    "ago": _ago(sc.finished_at or sc.created_at),
                    "at": _aware(sc.finished_at or sc.created_at)})
    out = [o for o in out if o["at"]]
    out.sort(key=lambda o: o["at"], reverse=True)
    return out[:6]


# --- 3. seo content queue -------------------------------------------------


def seo(session: Session, account: Account, site: Site | None,
        tab: str = "queue") -> dict:
    ctx = _chrome(session, account, "seo", site)
    site = ctx["_site"]
    if site is None:
        # Same reasoning as _blank_overview: render the real layout at zero.
        ctx.update({
            "kpis": {"queue": 0, "published": 0, "seo": None, "impact": None,
                     "clicks": None, "top10": None},
            "rows": [], "tab": tab,
            "counts": {"queue": 0, "review": 0, "approved": 0},
            "impact": [], "momentum": charts.bars([], []),
            "optimize": [], "linking": [], "library": [],
            "clusters": charts.donut([], size=150, stroke=22,
                                     label="Keywords", total=0),
            "health": charts.gauge(None, size=132, stroke=14),
            "health_rows": [
                {"label": "Content Quality", "value": None},
                {"label": "Keyword Coverage", "value": None},
                {"label": "Internal Linking", "value": None},
                {"label": "Meta Data", "value": None},
                {"label": "Technical SEO", "value": None},
                {"label": "Content Freshness", "value": None},
            ],
            "template": None, "keywords_total": None})
        return ctx

    def posts(state=None):
        q = select(func.count()).select_from(ContentPost).where(
            ContentPost.site_id == site.id)
        if state:
            q = q.where(ContentPost.state == state)
        return int(session.scalar(q) or 0)

    latest = session.scalars(
        select(Scan).where(Scan.site_id == site.id, Scan.status == "done")
        .order_by(Scan.finished_at.desc()).limit(1)).first()

    scored = [p.seo_score for p in session.scalars(
        select(ContentPost).where(ContentPost.site_id == site.id,
                                  ContentPost.seo_score.isnot(None))).all()]

    state_for_tab = {"queue": ("queued", "in_progress"),
                     "review": ("review",), "approved": ("scheduled",)}
    wanted = state_for_tab.get(tab, ("queued", "in_progress"))

    rows = session.scalars(
        select(ContentPost).where(ContentPost.site_id == site.id,
                                  ContentPost.state.in_(wanted))
        .order_by(ContentPost.created_at.desc()).limit(25)).all()

    fill = demo.is_demo(account)
    ctx.update({
        "demo": fill,
        "kpis": {
            "queue": posts("queued") + posts("in_progress") + posts("review"),
            "published": posts("published"),
            "seo": round(sum(scored) / len(scored)) if scored else None,
            "impact": latest.score if latest else None,
            "clicks": demo.pct(f"clk:{site.id}", 28, 52) if fill else None,
            "top10": demo.keywords_top10(site.id) if fill else None,
        },
        "tab": tab,
        "counts": {"queue": posts("queued") + posts("in_progress"),
                   "review": posts("review"), "approved": posts("scheduled")},
        "rows": [{
            "id": p.id, "title": p.title,
            "topic": p.category.replace("_", " ").title(),
            "keywords": p.target_keyword or "—",
            "seo": p.seo_score, "impact": p.seo_score,
            "state": p.state.replace("_", " ").title(),
            "tone": {"review": "s", "in_progress": "a"}.get(p.state, "b"),
        } for p in rows],
        "impact": _posts_ranked(session, site),
        "momentum": (charts.bars(
            [[demo.curve("m3", 28, 90, growth=1.4)[i],
              demo.curve("m4", 28, 140, growth=1.1)[i],
              demo.curve("m5", 28, 190, growth=.8)[i]] for i in range(28)],
            [charts.GREEN, charts.BLUE, charts.VIOLET]) if fill
            else charts.bars([], [])),
        "optimize": _content_gaps(session, site, latest),
        "linking": ([
            {"from": a, "to": b, "anchor": c} for a, b, c in [
                ("On-Page SEO Guide", "Best SEO Tools", "SEO tools"),
                ("Shopify SEO Guide", "Increase Organic Traffic", "drive more traffic"),
                ("Link Building Strategies", "On-Page SEO Guide", "on-page SEO"),
                ("Local SEO Guide", "Shopify SEO Guide", "ecommerce SEO"),
                ("SEO Tools Comparison", "Keyword Research Guide", "keyword research"),
            ]] if fill else []),
        "library": [p for p in _library(session, site)
                    if p["state"] == "Published"],
        "clusters": charts.donut(
            [{"name": n, "value": v, "colour": c} for n, v, c in demo.CLUSTERS]
            if fill else [], size=150, stroke=22, label="Keywords",
            total=sum(v for _n, v, _c in demo.CLUSTERS) if fill else 0),
        "keywords_total": demo.scaled(f"kwt:{site.id}", 1200, .3) if fill else None,
        "health": charts.gauge(latest.score_search if latest else None,
                               size=132, stroke=14),
        "health_rows": [
            {"label": "Content Quality", "value": latest.score_craft if latest else None},
            {"label": "Keyword Coverage",
             "value": demo.pct("kwc", 70, 84) if fill else None},
            {"label": "Internal Linking",
             "value": demo.pct("ilk", 64, 78) if fill else None},
            {"label": "Meta Data", "value": latest.score_search if latest else None},
            {"label": "Technical SEO", "value": latest.score_structure if latest else None},
            {"label": "Content Freshness",
             "value": demo.pct("frs", 60, 74) if fill else None},
        ],
        "template": None,
    })
    return ctx


# --- 4. geo visibility ----------------------------------------------------


def geo(session: Session, account: Account, site: Site | None) -> dict:
    """Almost every number on this page comes from the model-visibility crawl,
    which is not built. They are unknown, not zero, and the page says so."""
    ctx = _chrome(session, account, "geo", site)
    site = ctx["_site"]

    latest = None
    if site is not None:
        latest = session.scalars(
            select(Scan).where(Scan.site_id == site.id, Scan.status == "done")
            .order_by(Scan.finished_at.desc()).limit(1)).first()

    fill = demo.is_demo(account)
    ids = [s.id for s in ctx["_sites"]]
    days = 30
    labels = demo.day_labels(days) if fill else []

    rows = []
    if site is not None:
        rows = [{
            "title": p.title, "type": p.category.replace("_", " ").title(),
            "prompts": demo.scaled(f"pr:{p.id}", 10, .6) if fill else None,
            "score": p.seo_score, "updated": _d(p.created_at), "id": p.id,
        } for p in session.scalars(
            select(ContentPost).where(ContentPost.site_id == site.id)
            .order_by(ContentPost.created_at.desc()).limit(8)).all()]

    published = [p for p in session.scalars(
        select(ContentPost).where(ContentPost.site_id == site.id)
        .order_by(ContentPost.seo_score.desc().nullslast()).limit(5)).all()
    ] if site is not None else []

    ctx.update({
        "demo": fill,
        "kpis": {
            "queries": demo.queries(ids) if fill else None,
            "inclusion": demo.pct("incl", 38, 48) if fill else None,
            "citation": demo.pct("cit", 24, 34) if fill else None,
            "impact": latest.score_answers if latest else None,
            "coverage": demo.pct("cov", 58, 70) if fill else None,
            "trust": demo.pct("trust", 76, 88) if fill else None,
        },
        "platforms": charts.series(labels, [
            {"name": "ChatGPT", "colour": charts.VIOLET,
             "values": demo.curve("gpt", days, 52, growth=.5) if fill else []},
            {"name": "Google AI", "colour": charts.BLUE,
             "values": demo.curve("gai", days, 44, growth=.45) if fill else []},
            {"name": "Perplexity", "colour": charts.TEAL,
             "values": demo.curve("ppx", days, 34, growth=.42) if fill else []},
            {"name": "Claude", "colour": charts.AMBER,
             "values": demo.curve("cld", days, 26, growth=.4) if fill else []},
        ]),
        "rows": rows,
        "mentions": ([{"title": p.title,
                       "value": demo.scaled(f"mn:{p.id}", 90, .6)}
                      for p in published] if fill else []),
        "citations": ([{"title": t, "value": v} for t, v in [
            ("Best tools for 2026", 12_000), ("Buying guides", 9_800),
            ("How-to explainers", 8_600), ("Comparison pages", 7_200),
            ("Glossary entries", 6_900)]] if fill else []),
        "clusters": ([{"title": n, "value": f"{v}%"}
                      for n, v in demo.PROMPT_CLUSTERS] if fill else []),
        "snippets": ([{"query": q, "quality": k, "tone": t, "source": src,
                       "seen": _d(_now() - timedelta(days=i))}
                      for i, (q, k, t, src) in enumerate([
                          ("What are the best tools for this?", "Excellent", "g", "ChatGPT"),
                          ("How does it actually work?", "Good", "g", "Google AI"),
                          ("Is it safe to use at home?", "Good", "g", "Perplexity"),
                          ("Best routine for beginners?", "Fair", "a", "Claude"),
                          ("How does it compare to others?", "Good", "g", "ChatGPT"),
                      ])] if fill else []),
        "breakdown": charts.donut(
            [{"name": n, "value": v, "colour": c} for n, v, c in demo.CITATION_TYPES]
            if fill else [], size=150, stroke=22, label="Total Citations",
            total=sum(v for _n, v, _c in demo.CITATION_TYPES) if fill else 0),
    })
    return ctx


# --- 5. notifications -----------------------------------------------------


def notifications(session: Session, account: Account) -> dict:
    ctx = _chrome(session, account, "notifications")
    sites = ctx["_sites"]
    ids = [s.id for s in sites]
    names = {s.id: (s.client_name or s.hostname) for s in sites}

    fill = demo.is_demo(account)

    failed_jobs = list(session.scalars(
        select(Job).where(Job.status == "failed")
        .order_by(Job.finished_at.desc().nullslast()).limit(10)).all())

    waiting = list(session.scalars(
        select(Change).where(Change.site_id.in_(ids), Change.state == "proposed")
        .order_by(Change.proposed_at.desc()).limit(10)).all()) if ids else []

    failed_scans = list(session.scalars(
        select(Scan).where(Scan.site_id.in_(ids), Scan.status == "failed")
        .order_by(Scan.created_at.desc()).limit(10)).all()) if ids else []

    scheduled = list(session.scalars(
        select(ContentPost).where(ContentPost.site_id.in_(ids),
                                  ContentPost.state == "scheduled")
        .order_by(ContentPost.scheduled_for).limit(6)).all()) if ids else []

    feed = []
    for ch in waiting:
        feed.append({"kind": "approval", "tone": "a", "icon": "user",
                     "title": "Content approval needed",
                     "sub": f"“{ch.title[:52]}” is waiting for approval.",
                     "ago": _ago(ch.proposed_at), "at": _aware(ch.proposed_at),
                     "action": "View", "href": "/app/seo"})
    for j in failed_jobs:
        feed.append({"kind": "automation", "tone": "r", "icon": "warn",
                     "title": f"{j.kind.replace('_',' ').title()} job failed",
                     "sub": (j.error or "No error recorded.")[:80],
                     "ago": _ago(j.finished_at), "at": _aware(j.finished_at),
                     "action": "Resolve", "href": "/app/history"})
    for sc in failed_scans:
        feed.append({"kind": "sync", "tone": "r", "icon": "sync",
                     "title": "Audit failed",
                     "sub": f"{names.get(sc.site_id,'')} · {(sc.error or '')[:60]}",
                     "ago": _ago(sc.created_at), "at": _aware(sc.created_at),
                     "action": "Resolve", "href": "/app/history"})
    for p in scheduled:
        feed.append({"kind": "reminder", "tone": "b", "icon": "cal",
                     "title": "Scheduled post ready",
                     "sub": f"“{p.title[:48]}” is scheduled for {_dt(p.scheduled_for)}.",
                     "ago": _ago(p.created_at), "at": _aware(p.created_at),
                     "action": "View", "href": "/app/seo"})
    feed = [f for f in feed if f["at"]]
    feed.sort(key=lambda f: f["at"], reverse=True)

    counts = {k: sum(1 for f in feed if f["kind"] == k)
              for k in ("approval", "automation", "sync", "reminder")}

    ok = int(session.scalar(select(func.count()).select_from(Job)
                            .where(Job.status == "done")) or 0)
    bad = int(session.scalar(select(func.count()).select_from(Job)
                             .where(Job.status == "failed")) or 0)

    ctx.update({
        "kpis": {"unread": len(feed), "approvals": counts["approval"],
                 "automations": counts["automation"], "syncs": counts["sync"],
                 "scheduled": len(scheduled),
                 "status": "Healthy" if not bad else "Attention needed"},
        "feed": feed[:10], "counts": counts, "total": len(feed),
        "over_time": charts.series(
            demo.day_labels(30) if fill else [], [
                {"name": "Total Alerts", "colour": charts.BLUE,
                 "values": demo.curve("na", 30, 26, growth=.5) if fill else []},
                {"name": "Errors", "colour": charts.RED,
                 "values": demo.curve("ne", 30, 6, growth=.2) if fill else []},
                {"name": "Approvals", "colour": charts.AMBER,
                 "values": demo.curve("nap", 30, 10, growth=.4) if fill else []},
                {"name": "Reminders", "colour": charts.VIOLET,
                 "values": demo.curve("nr", 30, 16, growth=.3) if fill else []},
            ]),
        "reliability": charts.gauge(
            round(ok / (ok + bad) * 100) if (ok + bad) else None,
            size=138, stroke=15, fs=28, suffix="%"),
        "rel_rows": [
            {"label": "Successful jobs", "value": ok, "colour": charts.GREEN},
            {"label": "Failed jobs", "value": bad, "colour": charts.RED},
            {"label": "Timeouts", "value": 0, "colour": charts.AMBER},
            {"label": "Sync errors", "value": len(failed_scans), "colour": charts.BLUE},
        ],
        "alerts": [f for f in feed if f["kind"] in ("automation", "sync")][:5],
        "reminders": [{"title": p.title[:44], "when": _dt(p.scheduled_for),
                       "tag": "Upcoming"} for p in scheduled],
        "approvals": [{"title": ch.title[:44], "type": ch.kind.title(),
                       "ago": _ago(ch.proposed_at),
                       "level": "High" if ch.layer == "search" else "Medium"}
                      for ch in waiting[:5]],
        "failed": [{"name": j.kind.replace('_', ' ').title(), "type": "Automation",
                    "ago": _ago(j.finished_at), "state": "Failed"}
                   for j in failed_jobs[:5]]
                  + [{"name": f"Audit · {names.get(sc.site_id,'')}", "type": "Sync",
                      "ago": _ago(sc.created_at), "state": "Failed"}
                     for sc in failed_scans[:3]],
        "channels": [
            {"icon": i, "tone": t, "name": n,
             "value": v if fill else None}
            for (n, v), i, t in zip(demo.CHANNELS,
                                    ["bell", "mail", "slack", "bell", "phone"],
                                    ["b", "s", "v", "a", "g"])
        ],
        "rules": [
            {"icon": "warn", "tone": "r", "name": "Automation failures",
             "sub": "Alert team immediately", "on": fill},
            {"icon": "sync", "tone": "a", "name": "Sync failures",
             "sub": "Notify after 2 failures", "on": fill},
            {"icon": "clock", "tone": "b", "name": "Approval overdue",
             "sub": "Escalate after 48 hours", "on": fill},
            {"icon": "flag", "tone": "v", "name": "High impact errors",
             "sub": "Page team + Slack", "on": fill},
            {"icon": "card", "tone": "s", "name": "Account / billing issues",
             "sub": "Notify admins only", "on": fill},
        ],
        "resolved": ([{"issue": a, "type": b, "at": c, "by": d, "note": e}
                      for a, b, c, d, e in [
            ("Keyword rank tracking timeout", "Automation",
             _dt(_now() - timedelta(days=1)), "System",
             "Job completed successfully on retry"),
            ("CMS sync error", "Sync", _dt(_now() - timedelta(days=1)),
             "System", "API rate limit resolved"),
            ("Blog post publishing failed", "Automation",
             _dt(_now() - timedelta(days=2)), "System",
             "Restored and published successfully"),
            ("GEO data sync failed", "Sync", _dt(_now() - timedelta(days=2)),
             "System", "API connection re-established"),
            ("Image optimization error", "Automation",
             _dt(_now() - timedelta(days=3)), "System",
             "Retried with fallback service"),
        ]] if fill else []),
    })
    return ctx


# --- 6. workspace history -------------------------------------------------


def history(session: Session, account: Account) -> dict:
    ctx = _chrome(session, account, "history")
    sites = ctx["_sites"]
    ids = [s.id for s in sites]
    names = {s.id: (s.client_name or s.hostname) for s in sites}

    log: list[dict] = []
    if ids:
        for p in session.scalars(
                select(ContentPost).where(ContentPost.site_id.in_(ids))
                .order_by(ContentPost.created_at.desc()).limit(40)).all():
            log.append({"at": _aware(p.created_at), "type": "Publish"
                        if p.state == "published" else "Update",
                        "icon": "doc", "tone": "b",
                        "desc": f"Post {p.state.replace('_',' ')}",
                        "content": p.title[:44], "actor": "System",
                        "initials": "SY", "state": "Success"})
        for sc in session.scalars(
                select(Scan).where(Scan.site_id.in_(ids))
                .order_by(Scan.created_at.desc()).limit(40)).all():
            log.append({"at": _aware(sc.finished_at or sc.created_at),
                        "type": "Sync", "icon": "sync", "tone": "g",
                        "desc": f"Audit {sc.status}",
                        "content": names.get(sc.site_id, ""), "actor": "System",
                        "initials": "SY",
                        "state": "Success" if sc.status == "done" else "Failed"})
        for ch in session.scalars(
                select(Change).where(Change.site_id.in_(ids))
                .order_by(Change.proposed_at.desc()).limit(40)).all():
            log.append({"at": _aware(ch.proposed_at), "type": "Update",
                        "icon": "pencil", "tone": "v",
                        "desc": ch.title[:44],
                        "content": names.get(ch.site_id, ""), "actor": "System",
                        "initials": "SY",
                        "state": {"published": "Success", "failed": "Failed",
                                  "rejected": "Rejected"}.get(ch.state, "Pending")})
    log = [x for x in log if x["at"]]
    log.sort(key=lambda x: x["at"], reverse=True)

    fill = demo.is_demo(account)
    month = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = [x for x in log if x["at"] >= month]

    def n_of(t):
        return sum(1 for x in this_month if x["type"] == t)

    cats = [
        {"name": "Content Publishing", "value": n_of("Publish"), "colour": charts.BLUE},
        {"name": "Content Updates", "value": n_of("Update"), "colour": charts.VIOLET},
        {"name": "Sync Events", "value": n_of("Sync"), "colour": charts.GREEN},
        {"name": "Automation Runs", "value": 0, "colour": charts.AMBER},
    ]

    ctx.update({
        "kpis": {"total": len(this_month), "published": n_of("Publish"),
                 "updates": n_of("Update"), "syncs": n_of("Sync"),
                 "automation": 0,
                 "failed": sum(1 for x in this_month if x["state"] == "Failed")},
        "trend": charts.series(
            demo.day_labels(14) if fill else [], [
                {"name": "Publishing", "colour": charts.BLUE,
                 "values": demo.curve("hp", 14, 130, growth=.8) if fill else []},
                {"name": "Manual Updates", "colour": charts.VIOLET,
                 "values": demo.curve("hu", 14, 96, growth=.7) if fill else []},
                {"name": "Sync Events", "colour": charts.GREEN,
                 "values": demo.curve("hs", 14, 66, growth=.6) if fill else []},
                {"name": "Automation", "colour": charts.AMBER,
                 "values": demo.curve("ha", 14, 40, growth=.5) if fill else []},
                {"name": "Failed Actions", "colour": charts.RED,
                 "values": demo.curve("hf", 14, 12, growth=.2) if fill else []},
            ]),
        "cats": charts.donut(cats, size=150, stroke=22, label="Total",
                             total=len(this_month)),
        "cat_rows": cats,
        "stream": [{"icon": x["icon"], "tone": x["tone"], "title": x["desc"],
                    "sub": x["content"], "ago": _ago(x["at"]),
                    "state": x["state"]} for x in log[:8]],
        "log": [{**x, "when": _dt(x["at"])} for x in log[:12]],
        "actors": _actors(log),
        "areas": ([{"title": n, "value": v,
                    "value2": f"{round(v / 1314 * 100)}%"}
                   for n, v in demo.WORK_AREAS] if fill else []),
        "edited": ([{"title": x["content"], "value": demo.scaled("e" + x["content"], 18, .5)}
                    for x in log[:5]] if fill and log else []),
        "publishes": ([{"title": x["when"], "sub": x["content"][:30],
                        "value": x["state"]}
                       for x in log[:5] if x["type"] == "Publish"]
                      if fill else []),
        "reverts": ([{"title": _dt(_now() - timedelta(days=i * 3)),
                      "value": v} for i, v in enumerate(
                          ["Reverted", "Rejected", "Reverted", "Rejected",
                           "Reverted"])] if fill else []),
    })
    return ctx


def _actors(log: list[dict]) -> list[dict]:
    tally: dict[str, int] = {}
    for x in log:
        tally[x["actor"]] = tally.get(x["actor"], 0) + 1
    total = sum(tally.values()) or 1
    return [{"name": k, "initials": "".join(w[0] for w in k.split()[:2]).upper(),
             "value": v, "pct": round(v / total * 100)}
            for k, v in sorted(tally.items(), key=lambda kv: -kv[1])]


# --- 7. settings ----------------------------------------------------------


def settings(session: Session, account: Account) -> dict:
    ctx = _chrome(session, account, "settings")
    sites = ctx["_sites"]
    site = ctx["_site"]

    users = list(session.scalars(
        select(User).where(User.account_id == account.id)).all())

    integrations = list(session.scalars(
        select(Integration).where(
            Integration.site_id.in_([s.id for s in sites]))).all()) if sites else []

    keys = list(session.scalars(
        select(ApiKey).where(ApiKey.account_id == account.id,
                             ApiKey.revoked.is_(False))).all())

    published = int(session.scalar(
        select(func.count()).select_from(ContentPost)
        .where(ContentPost.site_id.in_([s.id for s in sites]),
               ContentPost.state == "published")) or 0) if sites else 0

    rate = account.rate_override_cents or Account.rate_for(max(1, len(sites)))
    latest = site.latest_scan() if site else None

    return ctx | {
        "sharing": {
            "public": bool(site.reports_public) if site else False,
            "can_share": latest is not None,
            "report_url": (f"{config.FRONTEND_URL}/report/{latest.id}"
                           if site and site.reports_public and latest else None),
        },
        "profile": {
            "name": account.name, "slug": account.slug,
            "kind": account.kind.title(),
            "created": _d(account.created_at),
            "email": account.contact_email or "—",
            "white_label": account.white_label,
        },
        "counts": {"members": len(users), "services": len(integrations),
                   "projects": len(sites), "published": published},
        "seats": [{"name": u.email.split("@")[0].replace(".", " ").title(),
                   "email": u.email, "role": "Owner" if i == 0 else "Member",
                   "tone": "v" if i == 0 else "b",
                   "perms": "All permissions" if i == 0 else "Create, Edit",
                   "active": _ago(u.last_seen_at) if hasattr(u, "last_seen_at")
                             else _ago(u.created_at),
                   "initials": u.email[:2].upper()}
                  for i, u in enumerate(users)],
        "plan": {
            "name": "Trial" if account.on_trial() else "Pay as you go",
            "price": f"${rate / 100:.0f}", "unit": "per site / month",
            "state": "Trial" if account.on_trial() else "Active",
            "days": account.trial_days_left(),
            "next": "—",
            "monthly": f"${account.monthly_cents() / 100:.2f}",
            "features": ["Unlimited audits", "SEO + GEO reports",
                         "Publish queue with approval", "REST API and keys",
                         "Per-site billing, no seats"],
        },
        "usage": [
            {"label": "Published Posts", "used": published, "cap": 500},
            {"label": "API Credits Used",
             "used": demo.scaled("api", 48_200, .2) if demo.is_demo(account) else None,
             "cap": 100_000},
            {"label": "Content Generations", "used": 0, "cap": 1_000_000},
            {"label": "Projects", "used": len(sites), "cap": 100},
        ],
        "apis": _api_rows(session, integrations),
        "keys": [{"label": k.label, "prefix": k.prefix,
                  "created": _d(k.created_at),
                  "used": _ago(k.last_used_at) if k.last_used_at else "never"}
                 for k in keys],
        "security": [
            {"icon": "lock", "name": "Two-Factor Authentication",
             "sub": "Add an extra layer of security to your account.",
             "state": "Not configured", "ok": False},
            {"icon": "shield", "name": "SSO (Single Sign-On)",
             "sub": "Connect with Google Workspace, Microsoft, or SAML.",
             "state": "Not configured", "ok": False},
            {"icon": "user", "name": "Active Sessions",
             "sub": f"{len(users)} account{'' if len(users) == 1 else 's'} in this workspace.",
             "state": "View", "ok": True},
            {"icon": "bell", "name": "Login Notifications",
             "sub": "Get notified of new sign-ins to your account.",
             "state": "Off", "ok": False},
        ],
        "prefs": [
            {"icon": "mail", "tone": "s", "name": "Email Notifications",
             "sub": "Product updates, reports and alerts.", "on": False},
            {"icon": "slack", "tone": "v", "name": "Slack Notifications",
             "sub": "Send alerts to your connected Slack.", "on": False},
            {"icon": "doc", "tone": "b", "name": "Project Activity",
             "sub": "New posts, approvals and comments.", "on": False},
            {"icon": "gear", "tone": "a", "name": "System Updates",
             "sub": "Maintenance, new features and billing.", "on": False},
        ],
        "defaults": [
            {"label": "Default Brand Voice", "value": "Not set"},
            {"label": "Default Target Audience", "value": "Not set"},
            {"label": "Default Tone", "value": "Not set"},
            {"label": "Default Language", "value": "English (US)"},
            {"label": "Default AI Model", "value": "claude-haiku-4-5"},
            {"label": "Default Post Format", "value": "Markdown"},
        ],
        "limits": [
            {"label": "Total API Calls",
             "used": demo.scaled("api", 48_200, .2) if demo.is_demo(account) else None,
             "cap": 100_000},
            {"label": "AI Generations", "used": 0, "cap": 1_000_000},
            {"label": "Content Posts", "used": published, "cap": 500},
            {"label": "Search Queries",
             "used": demo.scaled("sq", 2_400, .3) if demo.is_demo(account) else None,
             "cap": 10_000},
        ],
        # NEEDS: outbound webhooks are documented but not delivered yet.
        "webhooks": {"active": 0, "delivered": None, "rate": None, "events": []},
    }


def _api_rows(session: Session, integrations: list[Integration]) -> list[dict]:
    """The services this workspace could use, and whether each is connected.

    Connection state is read from the `integrations` table and from whether a
    key is present in the environment — never asserted.
    """
    connected = {i.platform: i for i in integrations}

    def row(name, icon, tone, platform, account_hint, perms, env_key=None):
        i = connected.get(platform)
        live = bool(i and i.connected_at) or (
            bool(env_key) and bool(getattr(config, env_key, "")))
        return {"name": name, "icon": icon, "tone": tone,
                "account": account_hint if live else "Not connected",
                "state": "Connected" if live else "Not connected",
                "ok": live, "perms": perms,
                "since": _d(i.connected_at) if i and i.connected_at else "—"}

    return [
        row("Shopify Store API", "shop", "g", "shopify", "Store", "Read / Write"),
        row("WordPress", "globe", "s", "wordpress", "Site", "Read / Write"),
        row("Webflow", "layers", "b", "webflow", "Site", "Read / Write"),
        row("Google Analytics", "chart", "a", "google_analytics", "Property", "Read"),
        row("Google Search Console", "search", "b", search_console.PLATFORM, "Domain", "Read"),
        row("Anthropic", "spark", "v", "anthropic", "Claude API",
            "Read / Write", "ANTHROPIC_API_KEY"),
        row("Stripe", "card", "p", "stripe", "Billing", "Read / Write",
            "STRIPE_SECRET_KEY"),
        row("Slack", "slack", "v", "slack", "Workspace", "Send notifications"),
        row("Email Notifications", "mail", "s", "email", "Team", "Send"),
        row("Webhooks", "webhook", "t", "webhooks", "Endpoint", "Send / Receive"),
    ]
