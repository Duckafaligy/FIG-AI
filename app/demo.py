"""Filler metrics for the demo estate.

`app/seed.py` builds an invented agency with invented client sites so the
dashboard can be looked at with data in it. The audit half of that is real —
findings come from running fixture pages through the actual rules engine. But
traffic, impressions, keyword positions and AI citations come from Search
Console, Google Analytics and the model-visibility crawl, none of which are
connected. Those panels were rendering as em dashes, which is correct for a
real empty workspace and useless for looking at the design.

So: this module supplies those numbers, and **only for the demo account**. Any
other workspace still gets `None` and still says what it needs. One flag, one
module, easy to delete when the real integrations land.

Everything is derived from a hash of the site id, so a given site always shows
the same figures — reload the page and nothing jumps around, which is what
makes it usable as a demo rather than a slot machine.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from app import config


def is_demo(account) -> bool:
    return bool(account) and account.slug == config.DEMO_ACCOUNT_SLUG


def _seed(*parts: str) -> int:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16)


def _rand(seed: int, lo: float, hi: float) -> float:
    """A stable value in [lo, hi] from an integer seed."""
    return lo + (seed % 10_000) / 10_000 * (hi - lo)


def scaled(key: str, base: int, spread: float = 0.55) -> int:
    """A stable number around `base`, within +/- spread."""
    s = _seed(key)
    return int(base * _rand(s, 1 - spread, 1 + spread))


def pct(key: str, lo: int = 20, hi: int = 95) -> int:
    return int(_rand(_seed(key), lo, hi))


def delta(key: str, lo: float = -8, hi: float = 34) -> float:
    return round(_rand(_seed(key, "d"), lo, hi), 1)


def curve(key: str, days: int, base: int, *, growth: float = 0.55,
          wobble: float = 0.1) -> list[int]:
    """A rising series with believable noise — no two days identical, no
    sawtooth. Used for every trend chart in the demo."""
    out: list[int] = []
    for i in range(days):
        t = i / max(1, days - 1)
        trend = 1 + growth * t
        n = _rand(_seed(key, i), 1 - wobble, 1 + wobble)
        out.append(max(0, int(base * trend * n)))
    return out


def day_labels(days: int) -> list[str]:
    """Date labels ending today, in the designs' `Apr 26` shape."""
    end = datetime.now(timezone.utc)
    out = []
    for i in range(days - 1, -1, -1):
        d = end - timedelta(days=i)
        out.append(f"{d.strftime('%b')} {d.day}")
    return out


# --- the figures each page needs ----------------------------------------


def site_traffic(site_id: str) -> int:
    return scaled(f"traffic:{site_id}", 4200, 0.6)


def site_impressions(site_id: str) -> int:
    return scaled(f"impr:{site_id}", 42_700, 0.6)


def estate_traffic(site_ids: list[str]) -> int:
    return sum(site_traffic(s) for s in site_ids)


def estate_impressions(site_ids: list[str]) -> int:
    return sum(site_impressions(s) for s in site_ids)


def keywords_top10(site_id: str) -> int:
    return scaled(f"kw10:{site_id}", 312, 0.5)


def queries(site_ids: list[str]) -> int:
    return sum(scaled(f"q:{s}", 1248 // max(1, len(site_ids)), 0.4)
               for s in site_ids) or 1248


ENGINES = [
    ("Google Search", "#3B82F6", 78),
    ("AI Search (ChatGPT)", "#7C5CFC", 56),
    ("Perplexity", "#14B8A6", 48),
    ("Claude", "#F59E0B", 42),
    ("Bing Copilot", "#EC4899", 38),
]

GA_PANEL = [
    ("2m 14s", "Avg. engagement time", 24.0),
    ("42%", "Bounce rate", -8.0),
    ("312", "Blog conversions", 28.0),
    ("18%", "Returning readers", 6.0),
]

TOP_QUERIES = [
    ("on-page seo", 1, 1400), ("seo checklist", 3, 880),
    ("local seo guide", 2, 720), ("backlinks strategy", 4, 580),
    ("free seo tools", 3, 420),
]

CLUSTERS = [
    ("page seo", 48, "#5457E5"), ("ecommerce", 72, "#7C5CFC"),
    ("local seo", 64, "#12B76A"), ("content marketing", 52, "#F59E0B"),
    ("technical seo", 44, "#EC4899"), ("other", 32, "#C7CDDA"),
]

PROMPT_CLUSTERS = [
    ("Product Recommendations", 68), ("How-to Guides", 54),
    ("Benefits & Science", 46), ("Comparisons", 38),
    ("Routines", 33), ("Price & Purchasing", 28),
]

CITATION_TYPES = [
    ("Blog Posts", 118, "#5457E5"), ("Product Pages", 81, "#7C5CFC"),
    ("Guides & Tutorials", 56, "#12B76A"), ("About/Company", 31, "#F59E0B"),
    ("Other", 26, "#C7CDDA"),
]

CHANNELS = [("In-app notifications", 98), ("Email notifications", 96),
            ("Slack (Workspace)", 92), ("Browser push", 89),
            ("SMS (Critical only)", 100)]

WORK_AREAS = [("Blog Content", 482), ("Product Pages", 308), ("Site SEO", 246),
              ("Collections", 186), ("Navigation", 92)]
