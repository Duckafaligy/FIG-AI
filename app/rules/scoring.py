"""Turns a list of Flags into the four layer scores the report shows.

Deterministic and explainable on purpose: every point lost maps to a finding
you can point at. A score that cannot be traced back to a specific line on a
specific page is not worth showing anyone.
"""
from __future__ import annotations

from collections import defaultdict

from app.rules.checks import Flag

LAYERS = ("craft", "structure", "search", "answers")

LAYER_LABEL = {
    "craft": "Craft",
    "structure": "Structure",
    "search": "Search",
    "answers": "Answers",
}

LAYER_SUB = {
    "craft": "how it reads",
    "structure": "what sits where",
    "search": "what a crawler reaches",
    "answers": "what a model can quote",
}

# How much one point of finding weight costs that layer. Craft is scored more
# forgivingly than Search: a stock palette is a taste call, a missing title is
# not.
LAYER_COST = {"craft": 5.0, "structure": 7.0, "search": 6.0, "answers": 8.0}

# The headline is not a flat average. A site can be immaculate to read and
# still be invisible, and the report should say so.
LAYER_WEIGHT = {"craft": 0.30, "structure": 0.25, "search": 0.25, "answers": 0.20}


def _clamp(v: float) -> int:
    return int(max(0, min(100, round(v))))


def layer_scores(flags: list[Flag], pages: int = 1) -> dict[str, int]:
    """Per-layer 0-100.

    Findings are counted once per (check, layer) rather than once per page, so
    a 40-page estate scan does not score worse than a 3-page one for the same
    site-wide mistake. Repeats still cost something, at a decreasing rate.
    """
    grouped: dict[str, dict[str, list[Flag]]] = defaultdict(lambda: defaultdict(list))
    for f in flags:
        grouped[f.layer][f.check].append(f)

    out: dict[str, int] = {}
    for layer in LAYERS:
        penalty = 0.0
        for _check, group in grouped.get(layer, {}).items():
            first = group[0]
            penalty += first.weight * LAYER_COST[layer]
            # Each repeat of the same check on another page adds a fraction.
            extras = len(group) - 1
            if extras:
                share = min(extras / max(pages, 1), 1.0)
                penalty += first.weight * LAYER_COST[layer] * 0.6 * share
        out[layer] = _clamp(100 - penalty)
    return out


def overall(scores: dict[str, int]) -> int:
    return _clamp(sum(scores[l] * LAYER_WEIGHT[l] for l in LAYERS))


def verdict(score: int) -> str:
    """Three words, deliberately. The report says Clean / Check / Fix and never
    says a page 'is' anything."""
    if score >= 80:
        return "clean"
    if score >= 55:
        return "check"
    return "fix"


def summarise(flags: list[Flag], pages: int = 1) -> dict:
    scores = layer_scores(flags, pages)
    return {
        "layers": scores,
        "overall": overall(scores),
        "verdict": verdict(overall(scores)),
        "counts": {
            layer: sum(1 for f in flags if f.layer == layer) for layer in LAYERS
        },
    }
