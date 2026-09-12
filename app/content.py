"""The content queue: briefs in, scored drafts out, publish through the CMS.

The audit finds two kinds of problem. Most are a field that is wrong — a
missing title, no canonical, no schema — and `publishing.py` queues those as a
one-line change. The rest are a page that does not exist: nothing on the site
answers a question a buyer actually asks, or a page is 90 words of preamble
with no specifics in it. You cannot fix that with a field edit. You fix it by
writing something.

So this module turns those findings into briefs, moves each brief through
queued -> in progress -> review -> scheduled -> published, and scores the
draft on the way past.

Two things it deliberately does not do:

  * It does not write the prose. `draft()` refuses unless a writer is
    configured, and there is no writer today. CLAUDE.md puts every LLM call in
    `ai_explain.py`; a generation step is a different call with a different
    cost shape and it needs deciding on purpose, not slipping in behind a
    button.
  * It does not invent keyword data. Search volume and difficulty come from a
    keyword source, and until one is connected those columns are empty rather
    than plausible.

Scoring is rules, not judgement — same reason as everywhere else in this
codebase. Nine checks, weighted, on the draft that exists.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, ContentPost, Finding, Page, Scan, Site

STATES = ("queued", "in_progress", "review", "scheduled", "published")

STATE_LABEL = {
    "queued": "Queued",
    "in_progress": "In Progress",
    "review": "Review",
    "scheduled": "Scheduled",
    "published": "Published",
}

# Pill colour per state. `warn` is amber, `good` green, `info` blue.
STATE_TONE = {
    "queued": "",
    "in_progress": "warn",
    "review": "info",
    "scheduled": "violet",
    "published": "good",
}

CATEGORIES = [
    ("blog", "Blog post"),
    ("glossary", "Glossary entry"),
    ("guide", "Guide"),
    ("faq", "FAQ"),
    ("case", "Case study"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# --- scoring -------------------------------------------------------------
#
# A post's SEO score is nine deterministic checks on the draft. Weighted so
# that the things which actually decide whether a page can rank or be quoted
# (enough substance, the keyword where it counts, specifics a model can lift)
# outweigh the hygiene items.

_WORD = re.compile(r"[A-Za-z0-9'’\-]+")
_SPECIFIC = re.compile(r"\b\d[\d,.]*\s?(?:%|percent|years?|days?|hours?|mins?|"
                       r"minutes?|weeks?|months?|kg|lb|mi|km|sites?|clients?)\b|"
                       r"[$£€]\s?\d", re.I)

# How long a piece of each kind has to be to be worth publishing. A glossary
# entry padded to a thousand words is the exact thing this product flags, so
# the bar is not the same for every category.
TARGET_WORDS = {"glossary": 250, "faq": 300, "case": 550, "blog": 700, "guide": 700}

CHECK_WEIGHTS = [
    ("substance", 18, "Long enough for its category"),
    ("keyword_title", 14, "Target keyword in the title"),
    ("keyword_open", 10, "Keyword in the first paragraph"),
    ("structure", 12, "Three or more subheadings"),
    ("specifics", 14, "Numbers, names or figures a model can quote"),
    ("question", 10, "Answers a question in the words people ask it"),
    ("meta", 8, "An opening paragraph a description can be lifted from"),
    ("internal", 8, "Two or more links to your own pages"),
    ("not_stuffed", 6, "The phrase is not repeated every other paragraph"),
]


def score_post(post: ContentPost) -> dict:
    """Score a draft. Returns the score plus which checks it failed.

    A brief with no body scores nothing rather than scoring badly — there is
    no draft to judge yet, and a red 12 next to an unstarted item is just
    noise.
    """
    body = (post.body or "").strip()
    if not body:
        return {"score": None, "passed": [], "failed": [], "words": 0}

    words = _WORD.findall(body)
    n = len(words)
    lower = body.lower()
    kw = (post.target_keyword or "").strip().lower()
    head = " ".join(words[:80]).lower()

    heads = len(re.findall(r"^\s{0,3}#{2,3}\s+\S", body, re.M))
    heads += len(re.findall(r"<h[23][\s>]", body, re.I))

    # Stuffing is a phrase turning up again and again, not a long-tail
    # question asked twice in nine hundred words. Once per 120 words, with a
    # floor of two so a short piece can still name its subject.
    kw_hits = lower.count(kw) if kw else 0
    allowed = max(2, n / 120)

    # The meta description gets lifted from the opening paragraph when nobody
    # writes one, so that paragraph has to be able to stand alone: long enough
    # to fill a search result, short enough not to be a wall of text.
    # Headings come out; the blank lines stay, because they are what marks
    # one paragraph off from the next.
    prose = "\n".join("" if (ln.lstrip().startswith("#")
                             or re.match(r"^\s*<h[1-6]", ln, re.I)) else ln
                      for ln in body.splitlines())
    opening = next((blk.strip() for blk in re.split(r"\n\s*\n", prose)
                    if blk.strip()), "")

    results = {
        "substance": n >= TARGET_WORDS.get(post.category, 700),
        "keyword_title": bool(kw) and kw in (post.title or "").lower(),
        "keyword_open": bool(kw) and kw in head,
        "structure": heads >= 3,
        "specifics": len(_SPECIFIC.findall(body)) >= 3,
        "question": bool(re.search(r"(?:^|\n)\s*#{0,3}\s*(?:what|why|how|when|"
                                   r"which|does|do|is|are|can)\b[^\n]*\?", body, re.I)),
        "meta": 110 <= len(opening) <= 320,
        "internal": len(re.findall(r'href="/|\]\(/', body)) >= 2,
        "not_stuffed": kw_hits <= allowed,
    }
    earned = sum(w for key, w, _label in CHECK_WEIGHTS if results[key])
    total = sum(w for _k, w, _l in CHECK_WEIGHTS)
    return {
        "score": round(earned / total * 100),
        "words": n,
        "passed": [label for key, _w, label in CHECK_WEIGHTS if results[key]],
        "failed": [label for key, _w, label in CHECK_WEIGHTS if not results[key]],
    }


def rescore(post: ContentPost) -> ContentPost:
    r = score_post(post)
    post.seo_score = r["score"]
    post.word_count = r["words"]
    return post


# --- briefs from findings ------------------------------------------------
#
# Which findings are answered by a page rather than by a field edit.

BRIEF_FROM = {
    "no_answerable_questions": (
        "faq", "high",
        "Answer “{q}” on a page of its own",
        "Nothing on {host} answers this in the words people ask it. A model "
        "asked this question has to guess, or cite somebody else."),
    "low_specificity": (
        "case", "high",
        "One piece with real figures behind {who}",
        "The copy claims outcomes with no number anywhere near them. A single "
        "page with real figures gives every other page something to point at."),
    "thin_page": (
        "guide", "medium",
        "Turn {where} on {host} into a page worth reading",
        "{words} words is not enough for this page to rank or be quoted. It "
        "needs the detail a buyer is actually looking for."),
    "no_structured_data": (
        "glossary", "low",
        "A glossary entry {who} can get quoted for",
        "Short, factual, marked up. Glossary pages are the cheapest kind to get "
        "cited for and {host} has none."),
}

# Which brief is worth writing first when a site has several gaps. An
# unanswered question beats a thin page, because the page at least exists.
BRIEF_ORDER = ("no_answerable_questions", "low_specificity",
               "thin_page", "no_structured_data")

_Q = re.compile(r"[“\"']([^”\"']{8,120}\?)[”\"']")


def propose(session: Session, site: Site, *, limit: int = 6) -> list[ContentPost]:
    """Turn this site's latest findings into briefs. Idempotent by title."""
    latest = session.scalars(
        select(Scan).where(Scan.site_id == site.id, Scan.status == "done")
        .order_by(Scan.finished_at.desc()).limit(1)).first()
    if latest is None:
        return []

    have = set(session.scalars(
        select(ContentPost.title).where(ContentPost.site_id == site.id)).all())

    findings = session.scalars(
        select(Finding).where(Finding.scan_id == latest.id)).all()

    candidates = sorted(
        (f for f in findings if f.check in BRIEF_FROM),
        key=lambda f: (BRIEF_ORDER.index(f.check), -(f.weight or 0)))

    made: list[ContentPost] = []
    seen_checks: set[str] = set()
    for f in candidates:
        if len(made) >= limit:
            break
        if f.check in seen_checks:      # one brief per gap, not one per page
            continue
        spec = BRIEF_FROM[f.check]
        category, priority, title_t, detail_t = spec

        host = site.hostname
        path = (f.page_url or "/").replace(f"https://{host}", "") or "/"
        where = "the homepage" if path == "/" else path
        hay = " ".join([f.summary or "", f.why or "", f.fix or ""]
                       + [str(x) for x in (f.evidence or [])])
        m = _Q.search(hay)
        q = m.group(1) if m else None
        if f.check == "no_answerable_questions" and not q:
            q = f"What does {_name(site)} actually do?"
        wm = re.search(r"(\d+)\s*words?", hay)

        fields = {"q": q, "path": path, "where": where, "host": host,
                  "who": _name(site),
                  "words": (wm.group(1) if wm else "Too few")}
        title = title_t.format(**fields)
        brief = detail_t.format(**fields)
        if title in have:
            continue
        have.add(title)
        seen_checks.add(f.check)

        post = ContentPost(
            site_id=site.id,
            title=title,
            category=category,
            priority=priority,
            state="queued",
            target_keyword=_keyword_for(session, f, site, q),
            brief=brief,
            body=None,
            word_count=0,
        )
        post.slug = _slug(title)
        session.add(post)
        made.append(post)

    session.commit()
    return made


def _name(site: Site) -> str:
    """What to call this site in a sentence. A partner's client name wins."""
    return site.client_name or site.label or site.hostname


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:70].rstrip("-")


def _keyword_for(session: Session, f: Finding, site: Site, q: str | None) -> str | None:
    """The phrase the piece is aimed at.

    Not a keyword *suggestion* — there is no volume data to suggest from. It is
    the question as asked, or the page's own title, which is a defensible
    starting point and honest about where it came from. When neither exists it
    stays empty and the queue asks you for it.
    """
    if q:
        return re.sub(r"[?“”\"']", "", q).strip().lower()[:70] or None
    if f.page_url:
        page = session.scalars(
            select(Page).where(Page.url == f.page_url,
                               Page.scan_id == f.scan_id).limit(1)).first()
        if page is not None and page.title:
            # Drop the brand half of "Services | Meridian Roofing".
            head = re.split(r"\s[|–—-]\s", page.title)[0].strip()
            if len(head) >= 6:
                return head.lower()[:70]
    return None


# --- state transitions ---------------------------------------------------


class Refused(Exception):
    """A transition that cannot happen, with a reason worth showing."""


def _owned(session: Session, account: Account, post_id: str) -> ContentPost:
    post = session.get(ContentPost, post_id)
    if post is None:
        raise Refused("That post no longer exists.")
    site = session.get(Site, post.site_id)
    if site is None or site.account_id != account.id:
        raise Refused("That post belongs to another account.")
    return post

ALLOWED = {
    ("queued", "in_progress"),
    ("in_progress", "review"),
    ("review", "scheduled"),
    ("review", "in_progress"),
    ("scheduled", "published"),
    ("scheduled", "review"),
}


def move(session: Session, account: Account, post_id: str, to: str,
         *, when: datetime | None = None) -> ContentPost:
    post = _owned(session, account, post_id)
    if to not in STATES:
        raise Refused(f"{to} is not a state.")
    if (post.state, to) not in ALLOWED:
        raise Refused(f"A post cannot go from {STATE_LABEL[post.state]} "
                      f"to {STATE_LABEL[to]}.")
    if to == "review" and not (post.body or "").strip():
        raise Refused("There is no draft to review yet.")
    if to == "scheduled":
        post.scheduled_for = when or (_now() + timedelta(days=2))
    if to == "published":
        raise Refused(
            "Publishing a post needs a connected CMS. Connect one in "
            "Settings → Integrations and this becomes a one-click push.")
    post.state = to
    rescore(post)
    session.commit()
    return post


def draft(session: Session, account: Account, post_id: str) -> ContentPost:
    """Write the draft. Not built, and refuses rather than pretending.

    CLAUDE.md: every LLM call lives in `ai_explain.py`, which receives small
    already-flagged data and never the page. Drafting a 900-word post is a
    different call with a different cost per run, and adding it changes the
    unit economics the whole architecture is built around. That is a decision
    to take deliberately.
    """
    _owned(session, account, post_id)
    raise Refused(
        "FIG does not write the copy yet. The brief, the target phrase and the "
        "scoring are here; the drafting step is not built. Paste a draft in and "
        "it gets scored and queued like any other change.")


def add(session: Session, account: Account, *, site_id: str, title: str,
        category: str = "blog", priority: str = "medium",
        keyword: str = "", body: str = "") -> ContentPost:
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise Refused("Pick one of your own sites.")
    title = title.strip()
    if not title:
        raise Refused("A post needs a title.")
    post = ContentPost(
        site_id=site.id, title=title, slug=_slug(title),
        category=category if category in dict(CATEGORIES) else "blog",
        priority=priority if priority in ("high", "medium", "low") else "medium",
        target_keyword=(keyword.strip().lower() or None),
        body=(body.strip() or None), state="queued")
    rescore(post)
    session.add(post)
    session.commit()
    return post


# --- the page ------------------------------------------------------------


def ring(score: int | None, *, size: int = 42, stroke: int = 4) -> dict:
    """Geometry for a circular gauge. Same stroke-dash trick as the donut."""
    r = (size - stroke) / 2
    circ = 2 * 3.14159265 * r
    pct = 0 if score is None else max(0, min(100, score))
    tone = "none" if score is None else (
        "good" if pct >= 80 else ("warn" if pct >= 60 else "bad"))
    return {"size": size, "r": round(r, 2), "c": size / 2, "stroke": stroke,
            "dash": round(circ * pct / 100, 2), "gap": round(circ, 2),
            "score": score, "tone": tone}


def _trend(now: int, before: int) -> float | None:
    if not before:
        return None
    return round((now - before) / before * 100, 1)


def view(session: Session, account: Account, *, tab: str = "all",
         category: str = "") -> dict:
    """Everything the SEO page renders."""
    sites = session.scalars(
        select(Site).where(Site.account_id == account.id)).all()
    by_id = {s.id: s for s in sites}
    if not by_id:
        return {"empty": True, "rows": [], "tabs": [], "kpis": []}

    posts = session.scalars(
        select(ContentPost).where(ContentPost.site_id.in_(list(by_id)))
        .order_by(ContentPost.created_at.desc())).all()

    counts = {k: 0 for k in STATES}
    for p in posts:
        counts[p.state] = counts.get(p.state, 0) + 1

    # --- the five cards
    month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    published_month = [p for p in posts if p.state == "published"
                       and (_aware(p.published_at) or _now()) >= month_start]
    yesterday = _now() - timedelta(days=1)
    queued_new = [p for p in posts if p.state in ("queued", "in_progress", "review")
                  and (_aware(p.created_at) or _now()) >= yesterday]

    scored = [p.seo_score for p in posts if p.seo_score is not None]
    avg = round(sum(scored) / len(scored)) if scored else None

    in_queue = counts["queued"] + counts["in_progress"] + counts["review"] + counts["scheduled"]

    kpis = [
        {"label": "Posts in Queue", "value": str(in_queue), "icon": "doc",
         "sub": (f"+{len(queued_new)} since yesterday" if queued_new
                 else "nothing new since yesterday"),
         "delta": None, "source": "fig"},
        {"label": "Published (This Month)", "value": str(len(published_month)),
         "icon": "check", "sub": "pushed to a connected CMS",
         "delta": None, "source": "fig"},
        {"label": "Avg. SEO Score", "value": ("—" if avg is None else str(avg)),
         "icon": "gauge",
         "sub": (f"across {len(scored)} scored draft{'' if len(scored) == 1 else 's'}"
                 if scored else "no drafts scored yet"),
         "delta": None, "source": "fig"},
        {"label": "Organic Traffic", "value": "—", "icon": "users",
         "sub": "needs Search Console", "delta": None, "source": "console"},
        {"label": "Impressions", "value": "—", "icon": "eye",
         "sub": "needs Search Console", "delta": None, "source": "console"},
    ]

    # --- rows
    rows_src = posts
    if tab != "all":
        rows_src = [p for p in rows_src if p.state == tab]
    if category:
        rows_src = [p for p in rows_src if p.category == category]

    # What needs a person first, not the pipeline order. A draft in Review is
    # blocking somebody; twenty-one untouched briefs are not.
    ROW_ORDER = ("review", "in_progress", "scheduled", "queued", "published")
    order = {"high": 0, "medium": 1, "low": 2}
    rows_src = sorted(rows_src, key=lambda p: (
        ROW_ORDER.index(p.state) if p.state in ROW_ORDER else 9,
        order.get(p.priority, 3),
        -(p.seo_score or 0)))

    rows = []
    for p in rows_src:
        site = by_id[p.site_id]
        sch = _aware(p.scheduled_for) or _aware(p.published_at)
        rows.append({
            "id": p.id,
            "title": p.title,
            "category": dict(CATEGORIES).get(p.category, p.category),
            "words": p.word_count or 0,
            "state": p.state,
            "state_label": STATE_LABEL.get(p.state, p.state),
            "tone": STATE_TONE.get(p.state, ""),
            "ring": ring(p.seo_score),
            "keyword": p.target_keyword or "—",
            "volume": p.search_volume,
            "kd": p.keyword_difficulty,
            "priority": p.priority,
            "date": sch.strftime("%b ") + str(sch.day) + sch.strftime(", %Y") if sch else None,
            "time": sch.strftime("%I:%M %p").lstrip("0") if sch else None,
            "hostname": site.hostname,
            "site_id": site.id,
            "next": _next_action(p.state),
        })

    # --- bottom three
    live = [p for p in posts if p.state == "published"]
    top_posts = [{
        "title": p.title, "hostname": by_id[p.site_id].hostname,
        "clicks": p.clicks, "score": p.seo_score,
    } for p in sorted(live, key=lambda p: (-(p.clicks or 0),
                                           -(p.seo_score or 0)))[:5]]

    kw_rows = {}
    for p in posts:
        if not p.target_keyword:
            continue
        r = kw_rows.setdefault(p.target_keyword, {"keyword": p.target_keyword,
                                                  "posts": 0, "clicks": None,
                                                  "volume": p.search_volume})
        r["posts"] += 1
        if p.clicks:
            r["clicks"] = (r["clicks"] or 0) + p.clicks
    top_keywords = sorted(kw_rows.values(),
                          key=lambda r: (-(r["clicks"] or 0), -r["posts"]))[:5]

    # --- health: the real search-layer score, and a truthful subline
    latest_scans = [s.latest_scan() for s in sites]
    health_scores = [sc.score_search for sc in latest_scans
                     if sc is not None and sc.score_search is not None]
    health = round(sum(health_scores) / len(health_scores)) if health_scores else None
    clean = sum(1 for s in health_scores if s >= 80)

    return {
        "empty": False,
        "kpis": kpis,
        "counts": counts,
        "tabs": [("all", "All", len(posts))] + [
            (k, STATE_LABEL[k], counts.get(k, 0)) for k in STATES],
        "tab": tab,
        "categories": CATEGORIES,
        "category": category,
        "rows": rows,
        "total": len(posts),
        "top_posts": top_posts,
        "top_keywords": top_keywords,
        "keyword_source": False,   # no keyword provider is wired up
        "health": {
            "ring": ring(health, size=150, stroke=13),
            "score": health,
            "label": _band(health),
            "clean": clean,
            "sites": len(health_scores),
        },
        "sites": [{"id": s.id, "hostname": s.hostname} for s in sites],
    }


def _next_action(state: str) -> dict | None:
    return {
        "queued": {"to": "in_progress", "label": "Start"},
        "in_progress": {"to": "review", "label": "Review"},
        "review": {"to": "scheduled", "label": "Schedule"},
        "scheduled": {"to": "published", "label": "Publish"},
    }.get(state)


def _band(score: int | None) -> str:
    if score is None:
        return "Not audited"
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Fair"
    return "Needs work"
