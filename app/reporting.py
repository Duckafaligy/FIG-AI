"""Everything the dashboard needs that is a question rather than a row.

The tables already hold scans and findings. What an agency actually asks is
different: which of my forty sites moved this week, what is wrong across all
of them at once, and what should I do first. Those are aggregations, and they
live here rather than being assembled inline in the view functions.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Finding, Page, Scan, Site
from app.rules.scoring import LAYER_LABEL, LAYER_SUB, verdict

LAYERS = ("craft", "structure", "search", "answers")
LAYER_META = [(k, LAYER_LABEL[k], LAYER_SUB[k]) for k in LAYERS]

# How much a finding is worth fixing, per site it appears on. Weight alone
# ranks a single high-severity oddity above something mediocre on thirty
# sites, which is the wrong way round for someone deciding what to do today.
SEVERITY_EFFORT = {"high": 3.5, "medium": 2.0, "low": 1.0, "info": 0.5}


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def done_scans(site: Site) -> list[Scan]:
    """Completed reads, oldest first."""
    return sorted(
        [s for s in site.scans if s.status == "done" and s.score is not None],
        key=lambda s: s.finished_at or s.created_at,
    )


def site_history(site: Site, limit: int = 12) -> list[dict]:
    return [
        {"at": s.finished_at or s.created_at, "score": s.score,
         "scan_id": s.id, "pages": s.pages_crawled,
         "layers": {k: getattr(s, f"score_{k}") for k in LAYERS}}
        for s in done_scans(site)[-limit:]
    ]


def site_delta(site: Site) -> dict | None:
    """Movement since the previous completed read, and which findings changed.

    This is the thing that makes a second read worth running: not the score,
    but which specific problems went away and which turned up.
    """
    scans = done_scans(site)
    if len(scans) < 2:
        return None
    prev, cur = scans[-2], scans[-1]

    def keys(scan: Scan) -> dict[str, Finding]:
        out: dict[str, Finding] = {}
        for f in scan.findings:
            out.setdefault(f"{f.check}|{f.page_url or ''}", f)
        return out

    a, b = keys(prev), keys(cur)
    fixed = [a[k] for k in a.keys() - b.keys()]
    new = [b[k] for k in b.keys() - a.keys()]
    return {
        "from_score": prev.score,
        "to_score": cur.score,
        "change": (cur.score or 0) - (prev.score or 0),
        "since": _aware(prev.finished_at or prev.created_at),
        "fixed": sorted(fixed, key=lambda f: -f.weight),
        "new": sorted(new, key=lambda f: -f.weight),
        "layers": {
            k: (getattr(cur, f"score_{k}") or 0) - (getattr(prev, f"score_{k}") or 0)
            for k in LAYERS
        },
    }


def sparkline(points: list[int], w: int = 104, h: int = 26) -> str:
    """An inline SVG polyline. No chart library for six numbers."""
    if len(points) < 2:
        return ""
    lo, hi = min(points), max(points)
    span = max(hi - lo, 1)
    step = w / (len(points) - 1)
    coords = " ".join(
        f"{i * step:.1f},{h - 2 - ((p - lo) / span) * (h - 4):.1f}"
        for i, p in enumerate(points)
    )
    return coords


def estate(session: Session, account: Account) -> dict:
    """One pass over the account: every site, its latest read, and the
    aggregates that only make sense across all of them."""
    sites = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.is_active.is_(True))
    ).all()

    rows, scored = [], []
    layer_totals = {k: [] for k in LAYERS}
    # check -> {sites, occurrences, worst severity, layer, an example fix}
    across: dict[str, dict] = defaultdict(
        lambda: {"sites": set(), "count": 0, "severity": "info",
                 "layer": "", "fix": "", "why": "", "example": ""})
    pending = 0

    for site in sites:
        latest = site.latest_scan()
        if any(s.status in ("queued", "running") for s in site.scans):
            pending += 1

        hist = site_history(site)
        points = [h["score"] for h in hist]
        delta = None
        if len(points) >= 2:
            delta = points[-1] - points[-2]

        row = {
            "site": site,
            "id": site.id,
            "hostname": site.hostname,
            "client": site.client_name,
            "monitor": site.monitor,
            "verified": site.is_verified,
            "score": latest.score if latest else None,
            "verdict": verdict(latest.score) if latest and latest.score is not None else None,
            "pages": latest.pages_crawled if latest else 0,
            "at": _aware(latest.finished_at) if latest else None,
            "layers": {k: getattr(latest, f"score_{k}") for k in LAYERS} if latest else None,
            "findings": len(latest.findings) if latest else 0,
            "delta": delta,
            "spark": sparkline(points),
            "history": points,
            "top": None,
            "busy": any(s.status in ("queued", "running") for s in site.scans),
        }

        if latest:
            scored.append(latest.score)
            for k in LAYERS:
                v = getattr(latest, f"score_{k}")
                if v is not None:
                    layer_totals[k].append(v)

            seen: set[str] = set()
            for f in sorted(latest.findings, key=lambda f: -f.weight):
                if row["top"] is None:
                    row["top"] = f
                if f.check in seen:
                    continue
                seen.add(f.check)
                a = across[f.check]
                a["sites"].add(site.hostname)
                a["count"] += 1
                a["layer"] = f.layer
                if SEVERITY_EFFORT.get(f.severity, 0) > SEVERITY_EFFORT.get(a["severity"], 0):
                    a["severity"] = f.severity
                if not a["fix"]:
                    a["fix"], a["why"], a["example"] = f.fix or "", f.why or "", site.hostname

        rows.append(row)

    rows.sort(key=lambda r: (r["score"] is None, r["score"] if r["score"] is not None else 999))

    common = []
    for check, a in across.items():
        n = len(a["sites"])
        common.append({
            "check": check,
            "label": check.replace("_", " "),
            "sites": n,
            "layer": a["layer"],
            "layer_label": LAYER_LABEL.get(a["layer"], a["layer"]),
            "severity": a["severity"],
            "fix": a["fix"],
            "why": a["why"],
            "example": a["example"],
            # what it is worth doing: how bad, times how widespread
            "impact": round(SEVERITY_EFFORT.get(a["severity"], 1) * n, 1),
        })
    common.sort(key=lambda c: -c["impact"])

    buckets = {"clean": 0, "check": 0, "fix": 0, "none": 0}
    for r in rows:
        buckets[r["verdict"] or "none"] += 1

    layer_avg = {
        k: round(sum(v) / len(v)) if v else None for k, v in layer_totals.items()
    }
    weakest = None
    have = {k: v for k, v in layer_avg.items() if v is not None}
    if have:
        weakest = min(have, key=have.get)

    return {
        "rows": rows,
        "sites": len(rows),
        "scanned": len(scored),
        "pending": pending,
        "average": round(sum(scored) / len(scored)) if scored else None,
        "buckets": buckets,
        "layer_avg": layer_avg,
        "layer_meta": LAYER_META,
        "weakest": weakest,
        "weakest_label": LAYER_LABEL.get(weakest, "") if weakest else "",
        "common": common,
        "movers": sorted(
            [r for r in rows if r["delta"] is not None and r["delta"] != 0],
            key=lambda r: -abs(r["delta"]),
        )[:6],
    }


def findings_across(session: Session, account: Account, check: str | None = None) -> dict:
    """Every finding on the account, grouped by check.

    This is the working view: an agency does not fix one site at a time, it
    fixes one *problem* across every site that has it.
    """
    sites = {s.id: s for s in session.scalars(
        select(Site).where(Site.account_id == account.id, Site.is_active.is_(True))
    ).all()}
    latest_ids = {}
    for s in sites.values():
        sc = s.latest_scan()
        if sc:
            latest_ids[sc.id] = s

    if not latest_ids:
        return {"groups": [], "total": 0, "selected": None}

    q = select(Finding).where(Finding.scan_id.in_(list(latest_ids)))
    if check:
        q = q.where(Finding.check == check)
    findings = session.scalars(q).all()

    groups: dict[str, dict] = {}
    for f in findings:
        site = latest_ids.get(f.scan_id)
        if site is None:
            continue
        g = groups.setdefault(f.check, {
            "check": f.check, "label": f.check.replace("_", " "),
            "layer": f.layer, "layer_label": LAYER_LABEL.get(f.layer, f.layer),
            "severity": f.severity, "why": f.why, "fix": f.fix,
            "instances": [],
        })
        if SEVERITY_EFFORT.get(f.severity, 0) > SEVERITY_EFFORT.get(g["severity"], 0):
            g["severity"] = f.severity
        g["instances"].append({
            "site_id": site.id, "hostname": site.hostname,
            "client": site.client_name, "summary": f.summary,
            "page": f.page_url, "evidence": f.evidence or [],
        })

    out = list(groups.values())
    for g in out:
        g["site_count"] = len({i["hostname"] for i in g["instances"]})
        g["impact"] = round(SEVERITY_EFFORT.get(g["severity"], 1) * g["site_count"], 1)
    out.sort(key=lambda g: -g["impact"])
    return {"groups": out, "total": len(findings), "selected": check}


def page_rows(session: Session, scan: Scan) -> list[Page]:
    return session.scalars(
        select(Page).where(Page.scan_id == scan.id).order_by(Page.path)
    ).all()


# --- layer-specific views ----------------------------------------------

# Which checks belong to which working view. A person fixing search problems
# is doing different work from a person making a site quotable, so the two
# get their own screens rather than one undifferentiated list.
LAYER_CHECKS = {
    "search": ("missing_title", "title_length", "missing_meta_description",
               "meta_description_length", "missing_canonical", "missing_lang",
               "missing_alt", "few_internal_links"),
    "answers": ("no_structured_data", "thin_structured_data",
                "no_answerable_questions", "low_specificity"),
    "structure": ("section_order", "missing_h1", "multiple_h1",
                  "heading_skips", "thin_page"),
    "craft": ("component_uniformity", "numbered_eyebrows", "generic_copy",
              "default_color_palette", "flat_typography", "overused_icons"),
}

# What a clean result on each check actually means, said as a positive. The
# report is more useful when it also says what is already working -- a page of
# nothing but problems tells you nothing about what to protect.
GOOD_NEWS = {
    "missing_title": "Every page has a title",
    "missing_meta_description": "Every page has a meta description",
    "missing_canonical": "Canonicals are set",
    "missing_lang": "Language is declared",
    "missing_alt": "Images carry alt text",
    "few_internal_links": "Pages link onward",
    "no_structured_data": "Structured data is present",
    "no_answerable_questions": "Pages carry answerable questions",
    "low_specificity": "Copy carries concrete specifics",
    "section_order": "Sections run in an order that makes its case first",
    "missing_h1": "Every page has an h1",
    "multiple_h1": "One h1 per page",
    "heading_skips": "Heading levels step down cleanly",
    "thin_page": "No thin pages",
    "component_uniformity": "Cards are not all identical",
    "generic_copy": "No filler marketing phrasing",
    "default_color_palette": "The palette is not a framework default",
    "flat_typography": "The type scale has real hierarchy",
    "overused_icons": "Icons are not the usual four",
    "numbered_eyebrows": "No numbered section labels",
}


def layer_view(session: Session, account: Account, layer: str) -> dict:
    """One layer across the whole estate: the score, what is failing, and --
    the half usually missing from tools like this -- what is already clean."""
    e = estate(session, account)
    checks = set(LAYER_CHECKS.get(layer, ()))

    failing, sites_hit = [], set()
    for c in e["common"]:
        if c["check"] in checks:
            failing.append(c)
            sites_hit.add(c["check"])

    passing = [
        {"check": c, "label": GOOD_NEWS.get(c, c.replace("_", " "))}
        for c in sorted(checks) if c not in sites_hit
    ]

    scores = [r["layers"][layer] for r in e["rows"]
              if r["layers"] and r["layers"][layer] is not None]
    best = sorted(
        [r for r in e["rows"] if r["layers"] and r["layers"][layer] is not None],
        key=lambda r: -r["layers"][layer])

    return {
        "layer": layer,
        "label": LAYER_LABEL.get(layer, layer),
        "sub": LAYER_SUB.get(layer, ""),
        "average": round(sum(scores) / len(scores)) if scores else None,
        "sites": len(scores),
        "failing": failing,
        "passing": passing,
        "worst": list(reversed(best))[:8],
        "best": best[:5],
        "clean_sites": sum(1 for s in scores if s >= 80),
    }


def analytics(session: Session, account: Account) -> dict:
    """Movement over time, and coverage. Answers "is this getting better".

    A single read is a snapshot and says nothing about direction; this only
    becomes useful on the second read of a site, and says so when it cannot
    tell you anything yet.
    """
    sites = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.is_active.is_(True))
    ).all()

    tracked, improving, declining, flat = [], 0, 0, 0
    total_reads = 0
    first_scores, latest_scores = [], []
    layer_first = {k: [] for k in LAYERS}
    layer_now = {k: [] for k in LAYERS}

    for site in sites:
        hist = site_history(site, limit=50)
        total_reads += len(hist)
        if not hist:
            continue
        latest_scores.append(hist[-1]["score"])
        for k in LAYERS:
            if hist[-1]["layers"][k] is not None:
                layer_now[k].append(hist[-1]["layers"][k])
        if len(hist) < 2:
            continue
        first_scores.append(hist[0]["score"])
        for k in LAYERS:
            if hist[0]["layers"][k] is not None:
                layer_first[k].append(hist[0]["layers"][k])
        change = hist[-1]["score"] - hist[0]["score"]
        if change > 0:
            improving += 1
        elif change < 0:
            declining += 1
        else:
            flat += 1
        tracked.append({
            "id": site.id, "hostname": site.hostname, "client": site.client_name,
            "reads": len(hist), "from": hist[0]["score"], "to": hist[-1]["score"],
            "change": change, "spark": sparkline([h["score"] for h in hist]),
            "first_at": _aware(hist[0]["at"]), "last_at": _aware(hist[-1]["at"]),
        })

    tracked.sort(key=lambda t: -abs(t["change"]))

    def avg(xs):
        return round(sum(xs) / len(xs)) if xs else None

    # Estate average over time: bucket every read by day and average it, so a
    # single chart can show whether the whole account is moving.
    by_day: dict[str, list[int]] = defaultdict(list)
    for site in sites:
        for h in site_history(site, limit=50):
            at = _aware(h["at"])
            if at:
                by_day[at.strftime("%Y-%m-%d")].append(h["score"])
    series = [
        {"at": datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc),
         "score": round(sum(v) / len(v)), "pages": len(v)}
        for day, v in sorted(by_day.items())
    ]

    return {
        "estate_series": series,
        "sites": len(sites),
        "with_history": len(tracked),
        "total_reads": total_reads,
        "improving": improving, "declining": declining, "flat": flat,
        "avg_now": avg(latest_scores),
        "avg_then": avg(first_scores),
        "layer_now": {k: avg(v) for k, v in layer_now.items()},
        "layer_then": {k: avg(v) for k, v in layer_first.items()},
        "tracked": tracked,
        "layer_meta": LAYER_META,
    }


def audits(session: Session, account: Account, limit: int = 80) -> dict:
    """Every read ever run on this account, newest first."""
    sites = {s.id: s for s in session.scalars(
        select(Site).where(Site.account_id == account.id)).all()}
    if not sites:
        return {"rows": [], "counts": {}, "total": 0}

    scans = session.scalars(
        select(Scan).where(Scan.site_id.in_(list(sites)))
        .order_by(Scan.created_at.desc()).limit(limit)
    ).all()

    counts = {"done": 0, "failed": 0, "queued": 0, "running": 0}
    rows = []
    for sc in scans:
        counts[sc.status] = counts.get(sc.status, 0) + 1
        site = sites.get(sc.site_id)
        rows.append({
            "scan": sc, "site_id": sc.site_id,
            "hostname": site.hostname if site else "—",
            "client": site.client_name if site else None,
            "status": sc.status, "trigger": sc.trigger,
            "pages": sc.pages_crawled, "score": sc.score,
            "verdict": verdict(sc.score) if sc.score is not None else None,
            "took": sc.duration_s(), "at": _aware(sc.created_at), "error": sc.error,
        })
    return {"rows": rows, "counts": counts, "total": len(scans)}


def chart(points: list[dict], w: int = 720, h: int = 200,
          pad_l: int = 34, pad_b: int = 26, pad_t: int = 12) -> dict | None:
    """Geometry for a score-over-time line chart.

    Returned as plain numbers so the template draws inline SVG. A chart
    library for a dozen points would be a bigger dependency than the whole
    charting problem.
    """
    if len(points) < 2:
        return None

    scores = [p["score"] for p in points]
    lo = max(0, min(scores) - 8)
    hi = min(100, max(scores) + 8)
    if hi - lo < 20:                       # keep a flat line from looking dramatic
        mid = (hi + lo) / 2
        lo, hi = max(0, mid - 10), min(100, mid + 10)
    span = max(hi - lo, 1)

    inner_w = w - pad_l - 10
    inner_h = h - pad_t - pad_b
    step = inner_w / (len(points) - 1)

    xy = []
    for i, p in enumerate(points):
        x = pad_l + i * step
        y = pad_t + (1 - (p["score"] - lo) / span) * inner_h
        at = _aware(p["at"])
        xy.append({
            "x": round(x, 1), "y": round(y, 1), "score": p["score"],
            "label": at.strftime("%d %b") if at else "",
            "when": at.strftime("%d %b %Y, %H:%M") if at else "",
            "pages": p.get("pages"),
        })

    line = " ".join(f'{p["x"]},{p["y"]}' for p in xy)
    area = (f'M{xy[0]["x"]},{h - pad_b} ' +
            " ".join(f'L{p["x"]},{p["y"]}' for p in xy) +
            f' L{xy[-1]["x"]},{h - pad_b} Z')

    ticks = []
    for frac in (0, 0.5, 1):
        value = round(lo + span * (1 - frac))
        ticks.append({"y": round(pad_t + frac * inner_h, 1), "value": value})

    return {
        "w": w, "h": h, "line": line, "area": area, "points": xy,
        "ticks": ticks, "baseline": h - pad_b, "pad_l": pad_l,
        "lo": round(lo), "hi": round(hi),
    }
