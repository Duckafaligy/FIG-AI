"""Webflow CMS adapter.

A genuinely different capability shape from WordPress/Shopify, not a
smaller or larger copy of the same one -- each field name below was checked
against developers.webflow.com's live docs before writing any code:

- Static Pages (`PUT /v2/pages/{id}`) expose `title` AND a real `seo.title`/
  `seo.description` pair as native, versioned API fields. Meta description
  fixes are refused everywhere else in this codebase (WordPress: rendered
  by a theme/SEO plugin with no stable field; Shopify: exists only as an
  unverified metafield convention) -- Webflow is the first platform here
  where this is a genuine, checked capability, not a guess.
- Pages expose **no body-content field at all**. Webflow pages are built
  visually in the Designer; there is nothing here shaped like WordPress's
  `content.raw` or Shopify's `Page.body` to regex a heading out of. Heading-
  structure fixes (missing_h1, multiple_h1) are refused for Pages -- not a
  gap to close later, a real ceiling of what this API exposes.
- CMS Collection Items (`PATCH /v2/collections/{id}/items`) are Webflow's
  blog-post equivalent. `fieldData.name` is a reserved field on every
  Collection Item regardless of the collection's custom schema, so a title
  fix works there too. A collection's rich-text body field is NOT reserved
  -- its key is whatever the site owner named it when they built the
  collection, which this adapter has no way to discover yet, so heading-
  structure fixes refuse there too, honestly, rather than guess a key.

A page_url is resolved to either a Page or a Collection Item by trying
Pages first (by slug), then every Collection's Items (also by slug) --
Webflow's Data API has no "look up by front-end URL" endpoint either, same
gap WordPress and Shopify both have.
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx

PLATFORM = "webflow"
TIMEOUT = 15.0
API_BASE = "https://api.webflow.com/v2"

TITLE_CHECKS = {"missing_title", "title_length"}
META_CHECKS = {"missing_meta_description", "meta_description_length"}
# Heading-structure fixes are NOT here: see module docstring for why neither
# Pages nor Collection Items can take them yet.
NOT_EXPOSED_HERE = {
    "missing_canonical", "missing_lang", "no_structured_data",
    "thin_structured_data", "heading_skips", "missing_alt",
    "missing_h1", "multiple_h1",
}


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


def _slug_of(page_url: str) -> str:
    path = urlparse(page_url).path.strip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def _find_page(site_id: str, headers: dict, slug: str) -> dict | None:
    try:
        resp = httpx.get(f"{API_BASE}/sites/{site_id}/pages", headers=headers, timeout=TIMEOUT)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    for page in resp.json().get("pages", []):
        if page.get("slug") == slug:
            return page
    return None


def _find_collection_item(site_id: str, headers: dict, slug: str) -> tuple[str, dict] | tuple[None, None]:
    try:
        coll_resp = httpx.get(f"{API_BASE}/sites/{site_id}/collections", headers=headers, timeout=TIMEOUT)
    except httpx.HTTPError:
        return None, None
    if coll_resp.status_code != 200:
        return None, None
    for collection in coll_resp.json().get("collections", []):
        collection_id = collection.get("id")
        try:
            items_resp = httpx.get(f"{API_BASE}/collections/{collection_id}/items",
                                   headers=headers, timeout=TIMEOUT)
        except httpx.HTTPError:
            continue
        if items_resp.status_code != 200:
            continue
        for item in items_resp.json().get("items", []):
            if (item.get("fieldData") or {}).get("slug") == slug:
                return collection_id, item
    return None, None


def apply_change(site_id: str, access_token: str, *,
                 check: str, page_url: str, after: str | None) -> tuple[bool, str, str | None]:
    """Writes one change to the live Webflow site. Returns
    (ok, message, applied_value), matching every other adapter's shape."""
    if not site_id:
        return (False, "no Webflow site was identified when this was connected -- "
                       "reconnect under Settings to fix this", None)
    if check in NOT_EXPOSED_HERE:
        return (False,
                "This isn't exposed by Webflow's API for this kind of content -- see "
                "app/webflow.py for exactly what is and isn't, and why.", None)

    headers = _auth_headers(access_token)
    slug = _slug_of(page_url)
    if not slug:
        return False, f"couldn't derive a slug from {page_url!r}", None

    page = _find_page(site_id, headers, slug)
    if page is not None:
        return _apply_to_page(headers, page["id"], check, after)

    collection_id, item = _find_collection_item(site_id, headers, slug)
    if item is not None:
        return _apply_to_item(headers, collection_id, item, check, after)

    return (False, f"couldn't find a Webflow page or collection item matching "
                   f"{page_url} on this site (checked Pages and every Collection)", None)


def _apply_to_page(headers: dict, page_id: str, check: str,
                   after: str | None) -> tuple[bool, str, str | None]:
    if not after:
        return False, "no new text has been drafted for this change yet", None
    if check in TITLE_CHECKS:
        body = {"title": after}
        applied = after
        label = "title"
    else:  # META_CHECKS
        body = {"seo": {"description": after}}
        applied = after
        label = "meta description"
    try:
        resp = httpx.put(f"{API_BASE}/pages/{page_id}", headers=headers, json=body, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return False, f"could not reach Webflow: {exc}", None
    if resp.status_code not in (200, 202):
        return False, f"Webflow rejected the {label} update: HTTP {resp.status_code}: {resp.text[:200]}", None
    return True, f"{label} updated", applied


def _apply_to_item(headers: dict, collection_id: str, item: dict, check: str,
                   after: str | None) -> tuple[bool, str, str | None]:
    if check not in TITLE_CHECKS:
        # META_CHECKS has no equivalent on a Collection Item -- SEO fields
        # are a Page-only concept in this API.
        return False, "meta description isn't exposed on a Collection Item, only on a Page", None
    if not after:
        return False, "no new title has been drafted for this change yet", None
    item_id = item.get("id")
    try:
        resp = httpx.patch(f"{API_BASE}/collections/{collection_id}/items",
                           headers=headers, timeout=TIMEOUT,
                           json={"items": [{"id": item_id, "fieldData": {"name": after}}]})
    except httpx.HTTPError as exc:
        return False, f"could not reach Webflow: {exc}", None
    if resp.status_code not in (200, 202):
        return False, f"Webflow rejected the title update: HTTP {resp.status_code}: {resp.text[:200]}", None
    return True, "title updated", after
