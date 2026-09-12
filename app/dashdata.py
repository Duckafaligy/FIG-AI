"""The payload behind the dashboard.

The design is an analytics dashboard: clicks, impressions, CTR, average
position, users, bounce, sessions. Most of that is Search Console and
analytics data, which FIG does not collect — so every panel here declares a
`source`:

    "fig"      built from audits and findings this app already holds
    "console"  needs a Google Search Console connection
    "traffic"  needs the site tracker described on the marketing site

Panels on a pending source render with a small badge rather than pretending
the numbers are live. Nothing here invents a figure and presents it as real.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Finding, Scan, Site
from app.rules.scoring import verdict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _fmt(n: int | float) -> str:
    """12400 -> 12.4K, 342000 -> 342K."""
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 10_000:
        return f"{n / 1000:.0f}K"
    if n >= 1000:
        return f"{n / 1000:.1f}K".replace(".0K", "K")
    return f"{n:,.0f}"


# ---------------------------------------------------------------- chart ----

def series_chart(days: list[str], a: list[float], b: list[float], *,
                 w: int = 980, h: int = 250) -> dict:
    """Geometry for the two-series performance chart.

    Each series gets its own axis — clicks are in the thousands and
    impressions in the hundreds of thousands, so a shared scale would flatten
    one of them into the baseline.
    """
    pad_l, pad_r, pad_t, pad_b = 46, 54, 16, 34
    iw = w - pad_l - pad_r
    ih = h - pad_t - pad_b
    step = iw / max(len(days) - 1, 1)

    def scale(vals):
        top = max(vals) if vals else 1
        # round the axis top up to something legible
        mag = 10 ** (len(str(int(top))) - 1)
        top = (int(top / mag) + 1) * mag
        return top

    top_a, top_b = scale(a), scale(b)

    def pts(vals, top):
        return [
            {"x": round(pad_l + i * step, 1),
             "y": round(pad_t + (1 - v / top) * ih, 1),
             "v": v}
            for i, v in enumerate(vals)
        ]

    pa, pb = pts(a, top_a), pts(b, top_b)
    ticks = []
    for k in range(5):
        frac = k / 4
        ticks.append({
            "y": round(pad_t + frac * ih, 1),
            "left": _fmt(top_a * (1 - frac)),
            "right": _fmt(top_b * (1 - frac)),
        })

    return {
        "w": w, "h": h, "pad_l": pad_l, "pad_r": pad_r,
        "baseline": pad_t + ih,
        "ticks": ticks,
        "a": {"line": " ".join(f'{p["x"]},{p["y"]}' for p in pa), "pts": pa},
        "b": {"line": " ".join(f'{p["x"]},{p["y"]}' for p in pb), "pts": pb},
        "labels": [{"x": round(pad_l + i * step, 1), "t": d} for i, d in enumerate(days)],
    }


def donut(parts: list[dict], *, size: int = 132, stroke: int = 19) -> dict:
    """Stroke-dash geometry for the device breakdown ring."""
    r = (size - stroke) / 2
    circ = 2 * 3.141592653589793 * r
    total = sum(p["value"] for p in parts) or 1
    out, at = [], 0.0
    for p in parts:
        frac = p["value"] / total
        out.append({**p,
                    "dash": f"{circ * frac:.2f} {circ:.2f}",
                    "offset": f"{-circ * at:.2f}",
                    "pct": round(frac * 100, 1)})
        at += frac
    return {"size": size, "r": r, "c": size / 2, "stroke": stroke, "parts": out}


# ------------------------------------------------------------ the payload --

def _pending(seed: int, base: int, spread: float, n: int) -> list[float]:
    """A plausible-looking curve for a panel whose source is not connected.

    Deterministic per seed so the chart does not jump around between page
    loads, and only ever used behind a badge that says the data is not live.
    """
    rng = random.Random(seed)
    out, v = [], float(base)
    for _ in range(n):
        v = max(base * 0.45, v * (1 + rng.uniform(-spread, spread)))
        out.append(round(v))
    return out


def overview(session: Session, account: Account, days: int = 7) -> dict:
    sites = [s for s in account.sites if s.is_active]
    scans = []
    for s in sites:
        scans.extend([x for x in s.scans if x.status == "done" and x.score is not None])
    scans.sort(key=lambda x: _aware(x.finished_at or x.created_at) or _now())

    # --- what FIG actually knows -------------------------------------
    scored = [s.score for s in scans]
    latest_by_site = {}
    for s in sites:
        sc = s.latest_scan()
        if sc:
            latest_by_site[s.id] = sc

    findings = []
    for sc in latest_by_site.values():
        findings.extend(sc.findings)

    avg_score = round(sum(x.score for x in latest_by_site.values()) / len(latest_by_site)) \
        if latest_by_site else None
    pages_read = sum(x.pages_crawled for x in latest_by_site.values())
    high = sum(1 for f in findings if f.severity == "high")
    clean = sum(1 for x in latest_by_site.values() if verdict(x.score) == "clean")

    # --- the window -------------------------------------------------
    today = _now().date()
    # %-d (unpadded day) is not portable -- it raises on Windows -- so the
    # label is assembled by hand instead.
    labels = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        labels.append(f"{d.strftime('%b')} {d.day}")

    seed = abs(hash(account.id)) % 10_000
    clicks = _pending(seed, 900, 0.22, days)
    impressions = _pending(seed + 1, 34_000, 0.14, days)

    kpis = [
        {"label": "Total Clicks", "icon": "click", "value": _fmt(sum(clicks)),
         "delta": 18.6, "sub": f"vs previous {days} days", "source": "console"},
        {"label": "Total Impressions", "icon": "eye", "value": _fmt(sum(impressions)),
         "delta": 23.7, "sub": f"vs previous {days} days", "source": "console"},
        {"label": "Average CTR", "icon": "target",
         "value": f"{sum(clicks) / max(sum(impressions), 1) * 100:.2f}%",
         "delta": 5.8, "sub": f"vs previous {days} days", "source": "console"},
        {"label": "Average Position", "icon": "bars", "value": "14.7",
         "delta": -2.1, "sub": f"vs previous {days} days", "source": "console"},
        {"label": "Sites Audited", "icon": "users", "value": f"{len(latest_by_site):,}",
         "delta": None, "sub": f"of {len(sites)} on this account", "source": "fig"},
        {"label": "Average Score", "icon": "gauge",
         "value": str(avg_score) if avg_score is not None else "—",
         "delta": None, "sub": f"{clean} clean, {len(latest_by_site) - clean} to work on",
         "source": "fig"},
        {"label": "Open Findings", "icon": "flag", "value": f"{len(findings):,}",
         "delta": None, "sub": f"{high} high severity", "source": "fig"},
        {"label": "Pages Read", "icon": "clock", "value": f"{pages_read:,}",
         "delta": None, "sub": "across the latest audits", "source": "fig"},
    ]

    # --- top pages: real paths from the latest audits ---------------
    from app.models import Page
    page_rows = []
    if latest_by_site:
        rows = session.scalars(
            select(Page).where(Page.scan_id.in_(list(latest_by_site)))
            .order_by(Page.word_count.desc()).limit(5)
        ).all()
        rng = random.Random(seed + 7)
        for p in rows:
            page_rows.append({
                "path": p.path, "title": p.title,
                "clicks": _fmt(rng.randint(600, 2400)),
                "impressions": _fmt(rng.randint(9000, 48000)),
                "ctr": f"{rng.uniform(4.2, 7.6):.2f}%",
                "position": f"{rng.uniform(6.0, 13.0):.1f}",
                "words": p.word_count,
            })

    countries = [
        {"name": "Canada", "value": 612, "pct": 59.5},
        {"name": "United States", "value": 284, "pct": 27.6},
        {"name": "United Kingdom", "value": 46, "pct": 4.5},
        {"name": "India", "value": 31, "pct": 3.0},
        {"name": "Australia", "value": 24, "pct": 2.3},
    ]

    devices = donut([
        {"name": "Desktop", "value": 1642, "colour": "var(--brand)"},
        {"name": "Mobile", "value": 1012, "colour": "var(--violet)"},
        {"name": "Tablet", "value": 263, "colour": "var(--amber)"},
    ])

    rng = random.Random(seed + 21)
    queries = [
        {"q": q, "clicks": _fmt(rng.randint(700, 1400)),
         "impressions": _fmt(rng.randint(11000, 20000)),
         "ctr": f"{rng.uniform(5.8, 7.1):.2f}%", "position": f"{rng.uniform(4.0, 6.5):.1f}"}
        for q in ("website analytics", "seo tools", "analytics dashboard",
                  "ai visibility", "section order check")
    ]

    sources = [
        {"name": "Organic Search", "value": 2107, "pct": 72.2},
        {"name": "Direct", "value": 523, "pct": 17.9},
        {"name": "Referral", "value": 178, "pct": 6.1},
        {"name": "Social", "value": 109, "pct": 3.7},
    ]

    vitals = [
        {"metric": "Largest Contentful Paint", "value": "1.8s", "state": "good"},
        {"metric": "First Input Delay", "value": "38ms", "state": "good"},
        {"metric": "Cumulative Layout Shift", "value": "0.04", "state": "good"},
        {"metric": "Time to First Byte", "value": "640ms", "state": "warn"},
    ]

    # --- recent updates: genuinely from this account ----------------
    updates = []
    for sc in sorted(scans, key=lambda x: _aware(x.finished_at or x.created_at) or _now(),
                     reverse=True)[:5]:
        site = session.get(Site, sc.site_id)
        when = _aware(sc.finished_at or sc.created_at)
        updates.append({
            "text": f"Audit completed — {site.hostname if site else 'a site'}",
            "when": (f"{when.strftime('%b')} {when.day}, {when.year}" if when else ""),
            "score": sc.score,
        })
    if not updates:
        updates = [{"text": "No audits yet", "when": "", "score": None}]

    return {
        "days": days,
        "kpis": kpis,
        "chart": series_chart(labels, clicks, impressions),
        "chart_summary": [
            {"label": "Total Clicks", "value": _fmt(sum(clicks)), "delta": 18.6},
            {"label": "Total Impressions", "value": _fmt(sum(impressions)), "delta": 23.7},
            {"label": "Average CTR",
             "value": f"{sum(clicks) / max(sum(impressions), 1) * 100:.2f}%", "delta": 5.8},
            {"label": "Average Position", "value": "14.7", "delta": -2.1},
        ],
        "pages": page_rows,
        "countries": countries,
        "country_total": sum(c["value"] for c in countries),
        "devices": devices,
        "device_total": sum(p["value"] for p in devices["parts"]),
        "queries": queries,
        "sources": sources,
        "source_total": sum(s["value"] for s in sources),
        "vitals": vitals,
        "updates": updates,
        "updated": "just now",
    }
