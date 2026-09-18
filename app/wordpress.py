"""WordPress CMS adapter.

WordPress has no OAuth of its own for a self-hosted site -- the connection
point is Application Passwords (core since WP 5.6): a user generates one
under wp-admin -> Users -> Profile -> Application Passwords and gives FIG
the site URL, their username, and that password. Everything after is HTTP
Basic Auth against the site's own REST API
(https://developer.wordpress.org/rest-api/) -- no app registration, no
redirect URI, unlike the OAuth platforms in app/oauth.py.

Scope, on purpose, matches what WordPress core's REST API actually exposes
rather than what a plugin might: a post's title and body content are native
REST fields on any install, so title fixes and the two heading-structure
fixes (missing_h1, multiple_h1 -- pure structural transforms, no new prose
needed) are real. A meta description, canonical link, or <head> lang
attribute is normally rendered by the active theme or an SEO plugin
(Yoast, RankMath, ...) and none of those expose a stable, plugin-independent
REST field for it -- guessing at a plugin's private meta key is exactly the
kind of "pretend it works" this product exists to avoid, so those refuse
out loud instead of writing something that silently does nothing. Alt text
is a native field too, but needs a real description of the image, which
this module does not invent -- it requires Change.after to already carry
one and refuses otherwise.
"""
from __future__ import annotations

import base64
import re
from urllib.parse import urlparse

import httpx

PLATFORM = "wordpress"
TIMEOUT = 15.0

# check -> what it means for this adapter. Kept separate from
# app/publishing.py's MECHANICAL dict (which is about layer/severity
# bookkeeping) because this is specifically "can WordPress's own REST API
# do this on any install," not "is the fix mechanical in general."
STRUCTURAL_CHECKS = {"missing_h1", "multiple_h1"}
TITLE_CHECKS = {"missing_title", "title_length"}
NEEDS_DRAFTED_TEXT = {"missing_alt"}
NOT_EXPOSED_BY_CORE = {
    "missing_meta_description", "meta_description_length",
    "missing_canonical", "missing_lang", "no_structured_data",
    "thin_structured_data", "heading_skips",
}


def _auth_headers(username: str, app_password: str) -> dict:
    token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_connection(site_url: str, username: str, app_password: str) -> tuple[bool, str]:
    """A real call, not a format check -- the only way to know an
    Application Password actually works is to ask the site."""
    base = site_url.rstrip("/")
    headers = _auth_headers(username, app_password)
    try:
        resp = httpx.get(f"{base}/wp-json/wp/v2/users/me", headers=headers, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return False, f"could not reach {base}: {exc}"
    if resp.status_code == 401:
        return False, "WordPress rejected that username / application password"
    if resp.status_code == 404:
        return False, f"no WordPress REST API found at {base} (is this a WordPress site?)"
    if resp.status_code != 200:
        return False, f"WordPress returned HTTP {resp.status_code}: {resp.text[:200]}"
    try:
        who = resp.json()
    except ValueError:
        return False, f"{base} did not return a WordPress REST API response"
    name = who.get("name") or username
    caps = who.get("capabilities") or {}
    if caps and not caps.get("edit_posts"):
        return True, f"connected as {name}, but this user cannot edit posts -- publishing will fail"
    return True, f"connected as {name}"


def _slug_of(page_url: str) -> str:
    path = urlparse(page_url).path.strip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def _find_post(base: str, headers: dict, page_url: str) -> tuple[str, dict] | tuple[None, None]:
    """WordPress' REST API has no "look up by front-end URL" endpoint, so
    this resolves it the way a human would: ?slug= on the last path
    segment, checking posts then pages."""
    slug = _slug_of(page_url)
    if not slug:
        return None, None
    for kind in ("posts", "pages"):
        try:
            resp = httpx.get(f"{base}/wp-json/wp/v2/{kind}", params={"slug": slug},
                             headers=headers, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            return None, {"error": f"could not reach {base}: {exc}"}
        if resp.status_code == 200 and resp.json():
            return kind, resp.json()[0]
    return None, None


def _promote_first_heading(html: str, from_level: int, to_level: int) -> tuple[str, bool]:
    """Structural only: retags the first <hN> found, keeping its attributes
    and inner content exactly as they are. No new text is written."""
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


def _demote_extra_h1s(html: str) -> tuple[str, bool]:
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


def apply_change(site_url: str, username: str, app_password: str, *,
                 check: str, page_url: str, after: str | None) -> tuple[bool, str, str | None]:
    """Writes one change to the live WordPress site. Returns
    (ok, message, applied_value) -- applied_value is what actually got
    written, for the Change row's own record."""
    if check in NOT_EXPOSED_BY_CORE:
        return (False,
                "WordPress's core REST API doesn't expose this -- it's rendered by your "
                "theme or SEO plugin, which each do this differently (or not at all) and "
                "none of them expose a stable, plugin-independent field for it. Fix it in "
                "your SEO plugin's own editor for this page.", None)

    base = site_url.rstrip("/")
    headers = _auth_headers(username, app_password)
    kind, post = _find_post(base, headers, page_url)
    if kind is None and post is not None:
        return False, post["error"], None
    if post is None:
        return False, f"couldn't find a post or page matching {page_url} on {base}", None

    post_id = post["id"]

    if check in TITLE_CHECKS:
        if not after:
            return False, "no new title has been drafted for this change yet", None
        try:
            resp = httpx.post(f"{base}/wp-json/wp/v2/{kind}/{post_id}",
                              headers=headers, json={"title": after}, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            return False, f"could not reach {base}: {exc}", None
        if resp.status_code != 200:
            return False, f"WordPress rejected the title update: HTTP {resp.status_code}", None
        return True, "title updated", after

    if check in STRUCTURAL_CHECKS:
        content = (post.get("content") or {}).get("raw") or (post.get("content") or {}).get("rendered") or ""
        if check == "missing_h1":
            fixed, changed = _promote_first_heading(content, from_level=2, to_level=1)
        else:  # multiple_h1
            fixed, changed = _demote_extra_h1s(content)
        if not changed:
            return False, "no heading matching this finding was found in the current content "\
                          "(it may have already been fixed on the site)", None
        try:
            resp = httpx.post(f"{base}/wp-json/wp/v2/{kind}/{post_id}",
                              headers=headers, json={"content": fixed}, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            return False, f"could not reach {base}: {exc}", None
        if resp.status_code != 200:
            return False, f"WordPress rejected the content update: HTTP {resp.status_code}", None
        return True, "heading structure fixed", fixed

    if check in NEEDS_DRAFTED_TEXT:
        if not after:
            return False, "no alt text has been drafted for this image yet -- FIG doesn't "\
                          "invent image descriptions, someone has to write one first", None
        # missing_alt's page_url in this codebase points at the page, not
        # the specific attachment -- there's no per-image id to target yet
        # (a real gap, not a stub): refuse rather than guess which image.
        return False, "alt text fixes need a specific image id to target, which isn't "\
                      "tracked yet -- see app/wordpress.py", None

    return False, f"no WordPress handling exists for the '{check}' check yet", None
