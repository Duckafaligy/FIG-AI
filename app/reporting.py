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
