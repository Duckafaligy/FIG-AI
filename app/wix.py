"""Wix CMS adapter.

Deliberately title-only, not a smaller copy of WordPress/Shopify's scope by
accident: Wix's blog posts store body content as `richContent`, a
structured JSON node tree (paragraph/heading/text nodes with their own
`type` and nesting), not an HTML string -- app/html_headings.py's
promote/demote transforms operate on HTML and cannot be reused here without
real, separately-verified knowledge of that JSON schema, which this file
does not claim. `title` is confirmed as a separate, simple top-level string
field on the draft post object, safe to touch without going near
`richContent` at all -- see CLAUDE.md for the exact docs pages checked.

Different auth shape too: app/oauth.py's Wix connect step only ever stores
`instance_id` (Wix's external-install-flow model has no code-exchange step
to hand back a ready-to-use token -- see that module). This adapter mints
its own short-lived access token via the client-credentials grant on every
call, using the app's own client_id/client_secret plus the stored
instance_id.

**Blocked on a real permission today, not just an unverified endpoint**:
writing a post needs the `SCOPE.DC-BLOG.MANAGE-BLOG` permission on the Wix
app; only `SCOPE.DC-BLOG.READ-BLOGS` ("Read Blog") was granted when the app
was set up (see CLAUDE.md). Every call this module makes will 401/403 until
that permission is added on the app's Permissions page and the site owner
reconnects to grant it. The code is written and fake-network tested against
Wix's own documented shapes regardless, same as every other adapter here --
it just hasn't been run for real yet, for a permissions reason rather than
an "unbuilt" one.
"""
from __future__ import annotations

from urllib.parse import quote, urlparse

import httpx

PLATFORM = "wix"
TIMEOUT = 15.0
TOKEN_URL = "https://www.wixapis.com/oauth2/token"
API_BASE = "https://www.wixapis.com"

TITLE_CHECKS = {"missing_title", "title_length"}
NOT_EXPOSED_HERE = {
    "missing_meta_description", "meta_description_length", "missing_canonical",
    "missing_lang", "no_structured_data", "thin_structured_data",
    "heading_skips", "missing_alt", "missing_h1", "multiple_h1",
}


def _mint_access_token(client_id: str, client_secret: str, instance_id: str) -> tuple[str | None, str | None]:
    try:
        resp = httpx.post(TOKEN_URL, timeout=TIMEOUT, json={
            "grant_type": "client_credentials", "client_id": client_id,
            "client_secret": client_secret, "instance_id": instance_id,
        })
    except httpx.HTTPError as exc:
        return None, f"could not reach Wix: {exc}"
    if resp.status_code != 200:
        return None, f"Wix rejected the token request: HTTP {resp.status_code}: {resp.text[:200]}"
    token = resp.json().get("access_token", "")
    if not token:
        return None, "Wix returned no access_token"
    return token, None


def _slug_of(page_url: str) -> str:
    path = urlparse(page_url).path.strip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def apply_change(instance_id: str, client_id: str, client_secret: str, *,
                 check: str, page_url: str, after: str | None) -> tuple[bool, str, str | None]:
    """Writes one change to the live Wix site. Returns
    (ok, message, applied_value), matching every other adapter's shape."""
    if not instance_id:
        return False, "no Wix instance id was recorded for this connection", None
    if check in NOT_EXPOSED_HERE:
        return (False,
                "This isn't wired up for Wix yet -- richContent's JSON body structure and "
                "Wix's SEO fields haven't been verified against a real site. See app/wix.py.", None)
    if check not in TITLE_CHECKS:
        return False, f"no Wix handling exists for the '{check}' check yet", None
    if not after:
        return False, "no new title has been drafted for this change yet", None

    token, error = _mint_access_token(client_id, client_secret, instance_id)
    if error:
        return False, error, None

    slug = _slug_of(page_url)
    if not slug:
        return False, f"couldn't derive a slug from {page_url!r}", None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = httpx.get(f"{API_BASE}/v3/posts/slugs/{quote(slug, safe='')}",
                         headers=headers, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return False, f"could not reach Wix: {exc}", None
    if resp.status_code != 200:
        return False, f"couldn't find a Wix post matching {page_url} (HTTP {resp.status_code})", None
    post_id = (resp.json().get("post") or {}).get("id", "")
    if not post_id:
        return False, f"couldn't find a Wix post matching {page_url}", None

    try:
        update_resp = httpx.patch(f"{API_BASE}/blog/v3/draft-posts/{post_id}",
                                  headers=headers, timeout=TIMEOUT,
                                  json={"draftPost": {"id": post_id, "title": after}})
    except httpx.HTTPError as exc:
        return False, f"could not reach Wix: {exc}", None
    if update_resp.status_code not in (200, 202):
        return (False, f"Wix rejected the title update: HTTP {update_resp.status_code}: "
                       f"{update_resp.text[:200]}", None)
    return True, "title updated", after
