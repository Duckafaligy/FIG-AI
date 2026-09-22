"""Pure HTML heading transforms shared by every CMS write adapter.

Structural only, on purpose: retags an existing heading or demotes existing
ones, never invents new text. Originally lived in app/wordpress.py; pulled
out once app/shopify.py needed the exact same two transforms against the
exact same two findings (missing_h1, multiple_h1) -- the fix has nothing to
do with WordPress, it is a generic "this HTML fragment has a heading
problem" transform any adapter can reuse.
"""
from __future__ import annotations

import re


def promote_first_heading(html: str, from_level: int, to_level: int) -> tuple[str, bool]:
    """Retags the first <hN> found, keeping its attributes and inner content
    exactly as they are. No new text is written."""
    pattern = re.compile(rf"<h{from_level}(\s[^>]*)?>", re.IGNORECASE)
    close_pattern = re.compile(rf"</h{from_level}>", re.IGNORECASE)
    match = pattern.search(html)
    if not match:
        return html, False
    opened = html[:match.start()] + f"<h{to_level}{match.group(1) or ''}>" + html[match.end():]
    close_match = close_pattern.search(opened, match.start())
    if not close_match:
        return html, False
    fixed = opened[:close_match.start()] + f"</h{to_level}>" + opened[close_match.end():]
    return fixed, True


def demote_extra_h1s(html: str) -> tuple[str, bool]:
    """Keeps the first <h1> as-is, demotes every subsequent one to <h2>."""
    parts = re.split(r"(<h1(?:\s[^>]*)?>.*?</h1>)", html, flags=re.IGNORECASE | re.DOTALL)
    seen_first = False
    changed = False
    out = []
    for part in parts:
        if re.match(r"<h1", part, re.IGNORECASE):
            if seen_first:
                part = re.sub(r"^<h1(\s[^>]*)?>", lambda m: f"<h2{m.group(1) or ''}>", part, flags=re.IGNORECASE)
                part = re.sub(r"</h1>$", "</h2>", part, flags=re.IGNORECASE)
                changed = True
            else:
                seen_first = True
        out.append(part)
    return "".join(out), changed
