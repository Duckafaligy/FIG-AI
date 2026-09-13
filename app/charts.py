"""Chart geometry. Pure functions, no library, no client-side rendering.

Every chart in the designs is a line chart, a donut, or a ring gauge, and all
three are a handful of arithmetic away from an inline SVG. Doing it here means
the page is complete in the first response with no layout shift, and there is
no chart bundle to ship.

Each builder returns the geometry only — the template does the drawing. When
there is no data the builders return an empty `lines`/`parts` list, which the
macro renders as an explicit "no data yet" panel rather than an empty box or,
worse, a plausible-looking invented curve.
"""
from __future__ import annotations

import itertools
from math import pi

# One palette, used in this order, so the same series is the same colour on
# every page it appears on.
BLUE = "#3B82F6"
VIOLET = "#7C5CFC"
GREEN = "#12B76A"
AMBER = "#F59E0B"
RED = "#EF4444"
INDIGO = "#5457E5"
SKY = "#3B82F6"
PINK = "#EC4899"
TEAL = "#14B8A6"
GREY = "#C7CDDA"

_uid = itertools.count(1)


def _nice(top: float) -> tuple[float, int]:
    """A round axis maximum and a sensible tick count for it."""
    if top <= 0:
        return 10.0, 5
    mag = 10 ** (len(str(int(top))) - 1)
    for step in (1, 2, 2.5, 5, 10):
        if top <= mag * step:
            return mag * step, 5
    return mag * 10, 5


def _fmt(v: float) -> str:
    if v >= 1_000_000:
        s = f"{v / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if v >= 1000:
        s = f"{v / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{s}K"
    return f"{v:.0f}"


def series(labels: list[str], sets: list[dict], *, w: int = 780, h: int = 300,
           pad_l: int = 46, pad_r: int = 12, pad_t: int = 14,
           pad_b: int = 28, area: bool = True) -> dict:
    """A multi-series line chart.

    `sets` is [{"name":…, "colour":…, "values":[…]}]. Series with no values, or
    all-zero values, still produce no geometry: an axis drawn against invented
    numbers is worse than an honest blank.
    """
    out = {"w": w, "h": h, "pad_l": pad_l, "uid": next(_uid),
           "ticks": [], "xlabels": [], "lines": [], "max": 0}

    usable = [s for s in sets if s.get("values")]
    if not labels or not usable or not any(any(s["values"]) for s in usable):
        return out

    top = max(max(s["values"]) for s in usable)
    axis_top, n_ticks = _nice(top)
    out["max"] = axis_top

    plot_h = h - pad_t - pad_b
    plot_w = w - pad_l - pad_r

    for i in range(n_ticks + 1):
        frac = i / n_ticks
        out["ticks"].append({
            "y": round(pad_t + plot_h * (1 - frac), 1),
            "label": _fmt(axis_top * frac),
        })

    n = len(labels)
    step = plot_w / max(1, n - 1) if n > 1 else 0

    def x_at(idx: int) -> float:
        return round(pad_l + (step * idx if n > 1 else plot_w / 2), 1)

    def y_at(v: float) -> float:
        return round(pad_t + plot_h * (1 - (v / axis_top if axis_top else 0)), 1)

    # Label every nth x so they never collide.
    every = max(1, round(n / 8))
    for idx, label in enumerate(labels):
        if idx % every == 0 or idx == n - 1:
            out["xlabels"].append({"x": x_at(idx), "label": label})

    for s in usable:
        pts = [{"x": x_at(i), "y": y_at(v), "v": v}
               for i, v in enumerate(s["values"][:n])]
        path = "M" + " L".join(f"{p['x']} {p['y']}" for p in pts)
        line = {"name": s["name"], "colour": s.get("colour", BLUE),
                "points": pts, "path": path, "area": ""}
        if area and s is usable[0] and len(pts) > 1:
            base = pad_t + plot_h
            line["area"] = (f"{path} L{pts[-1]['x']} {base} "
                            f"L{pts[0]['x']} {base} Z")
        out["lines"].append(line)

    return out


def donut(parts: list[dict], *, size: int = 150, stroke: int = 22,
          label: str = "Total", total: int | None = None) -> dict:
    """A segmented ring. `parts` is [{"name","value","colour"}].

    Segments are laid out with dash-offset rather than arc paths, which keeps
    the maths to one subtraction per segment.
    """
    r = (size - stroke) / 2
    circ = 2 * pi * r
    values = [max(0, p.get("value") or 0) for p in parts]
    grand = sum(values)

    out = {"size": size, "stroke": stroke, "c": size / 2, "r": round(r, 2),
           "circ": round(circ, 2), "parts": [],
           "total": total if total is not None else grand,
           "label": label, "empty": grand == 0}
    if grand == 0:
        return out

    run = 0.0
    for p, v in zip(parts, values):
        frac = v / grand
        out["parts"].append({
            "name": p["name"], "value": v, "colour": p.get("colour", GREY),
            "pct": round(frac * 100),
            "dash": round(circ * frac, 2),
            "offset": round(-circ * run, 2),
        })
        run += frac
    return out


def gauge(value: int | float | None, *, size: int = 130, stroke: int = 13,
          suffix: str = "", fs: int = 30, tone: str = "") -> dict:
    """A single-value ring. Tone follows the band unless one is forced."""
    r = (size - stroke) / 2
    circ = 2 * pi * r
    pct = 0 if value is None else max(0, min(100, float(value)))
    if not tone:
        tone = "n" if value is None else (
            "g" if pct >= 80 else ("a" if pct >= 60 else "r"))
    return {"size": size, "stroke": stroke, "c": size / 2, "r": round(r, 2),
            "circ": round(circ, 2), "dash": round(circ * pct / 100, 2),
            "value": value, "suffix": suffix, "tone": tone, "fs": fs}


def bars(groups: list[list[float]], colours: list[str], *,
         height: int = 170) -> dict:
    """Stacked columns, sized as percentages so the CSS can draw them."""
    if not groups or not any(sum(g) for g in groups):
        return {"cols": [], "empty": True, "height": height}
    top = max(sum(g) for g in groups)
    cols = []
    for g in groups:
        cols.append([{"pct": round(v / top * 100, 2), "colour": c}
                     for v, c in zip(g, colours) if v > 0])
    return {"cols": cols, "empty": False, "height": height, "max": top}
