"""Shopify CMS adapter.

Unlike WordPress, the connection point here is OAuth (app/oauth.py), which
already proves the access token is real at connect time -- there is no
separate test_connection() the way Application Passwords need one, since a
successful token exchange already is that proof.

Shopify's REST Admin API is deprecated (all endpoints, since October 2024)
and new custom apps are expected onto the GraphQL Admin API instead -- this
adapter is GraphQL-only from the start, not a REST implementation ported
later. Every field name below (Page.body, Article.body, the pageUpdate/
articleUpdate mutations and their userErrors) was checked against
shopify.dev's live docs, the same rigor as every other adapter in this
codebase -- see PLATFORMS.md for the exact pages checked.

Scope matches app/wordpress.py's exactly, on purpose, not because Shopify's
API can't do more: a Page/Article's title and body content are native,
stable GraphQL fields on any store, so title fixes and the two heading-
structure fixes (missing_h1, multiple_h1 -- pure structural transforms) are
real. Shopify *does* have a native way to set a page's SEO title/description
(the `global.title_tag` / `global.description_tag` metafields the admin UI's
"Edit website SEO" section writes to) but that hasn't been verified against
a real store the way the fields below have -- refuses honestly rather than
guess at an undocumented-here shape, same reasoning as WordPress's meta
description refusal.
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.html_headings import demote_extra_h1s, promote_first_heading

PLATFORM = "shopify"
TIMEOUT = 15.0
API_VERSION = "2026-07"

STRUCTURAL_CHECKS = {"missing_h1", "multiple_h1"}
TITLE_CHECKS = {"missing_title", "title_length"}
NOT_EXPOSED_HERE = {
    "missing_meta_description", "meta_description_length",
    "missing_canonical", "missing_lang", "no_structured_data",
    "thin_structured_data", "heading_skips", "missing_alt",
}


def _graphql_url(shop_domain: str) -> str:
    return f"https://{shop_domain}/admin/api/{API_VERSION}/graphql.json"


def _query(shop_domain: str, access_token: str, query: str,
          variables: dict | None = None) -> tuple[dict | None, str | None]:
    """One GraphQL request. Returns (data, error) -- exactly one is set.
    Both request-level errors (auth, syntax -- top-level `errors`) and
    mutation-level `userErrors` are surfaced as the error string; callers
    don't need to know which kind they got."""
    try:
        resp = httpx.post(_graphql_url(shop_domain), timeout=TIMEOUT,
                          headers={"X-Shopify-Access-Token": access_token,
                                   "Content-Type": "application/json"},
                          json={"query": query, "variables": variables or {}})
    except httpx.HTTPError as exc:
        return None, f"could not reach {shop_domain}: {exc}"
    if resp.status_code != 200:
        return None, f"Shopify returned HTTP {resp.status_code}: {resp.text[:300]}"
    try:
        body = resp.json()
    except ValueError:
        return None, f"{shop_domain} did not return a GraphQL response"
    if body.get("errors"):
        return None, f"Shopify rejected the request: {body['errors']}"
    return body.get("data"), None


def _handle_of(page_url: str) -> str:
    path = urlparse(page_url).path.strip("/")
    return path.rsplit("/", 1)[-1] if path else ""


_FIND_QUERY = """
query FindByHandle($handle: String!) {
  pages(first: 1, query: $handle) { edges { node { id title body } } }
  articles(first: 1, query: $handle) { edges { node { id title body } } }
}
"""


def _find_content(shop_domain: str, access_token: str,
                  page_url: str) -> tuple[str, dict, str] | tuple[None, None, str]:
    """(kind, node, gid) for whichever of Pages/Articles matches this URL's
    last path segment, or (None, None, error). No "look up by front-end URL"
    field exists here either (same gap WordPress's REST API has) -- resolved
    the same way, by handle."""
    handle = _handle_of(page_url)
    if not handle:
        return None, None, f"couldn't derive a handle from {page_url!r}"
    data, error = _query(shop_domain, access_token, _FIND_QUERY,
                         {"handle": f"handle:{handle}"})
    if error:
        return None, None, error
    for kind in ("pages", "articles"):
        edges = (data or {}).get(kind, {}).get("edges", [])
        if edges:
            node = edges[0]["node"]
            return kind[:-1], node, node["id"]
    return None, None, (f"couldn't find a Shopify page or article matching {page_url} "
                        f"on {shop_domain} (checked Pages and Articles by handle)")


_UPDATE_MUTATION = {
    "page": """
        mutation UpdatePage($id: ID!, $page: PageUpdateInput!) {
          pageUpdate(id: $id, page: $page) {
            page { id title body }
            userErrors { field message }
          }
        }
    """,
    "article": """
        mutation UpdateArticle($id: ID!, $article: ArticleUpdateInput!) {
          articleUpdate(id: $id, article: $article) {
            article { id title body }
            userErrors { field message }
          }
        }
    """,
}


def _update(shop_domain: str, access_token: str, kind: str, gid: str,
           fields: dict) -> tuple[bool, str]:
    mutation_name = f"{kind}Update"
    data, error = _query(shop_domain, access_token, _UPDATE_MUTATION[kind],
                         {"id": gid, kind: fields})
    if error:
        return False, error
    result = (data or {}).get(mutation_name) or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        return False, f"Shopify rejected the update: {user_errors}"
    return True, "updated"


def apply_change(shop_domain: str, access_token: str, *,
                 check: str, page_url: str, after: str | None) -> tuple[bool, str, str | None]:
    """Writes one change to the live Shopify store. Returns
    (ok, message, applied_value), matching app/wordpress.py's shape."""
    if check in NOT_EXPOSED_HERE:
        return (False,
                "This isn't wired up for Shopify yet -- title and heading-structure fixes "
                "are, but this needs a shape (SEO metafields, alt text on a specific image) "
                "that hasn't been verified against a real store. See app/shopify.py.", None)

    kind, node, gid = _find_content(shop_domain, access_token, page_url)
    if kind is None:
        return False, gid, None  # gid holds the error message in this branch

    if check in TITLE_CHECKS:
        if not after:
            return False, "no new title has been drafted for this change yet", None
        ok, message = _update(shop_domain, access_token, kind, gid, {"title": after})
        return (ok, "title updated" if ok else message, after if ok else None)

    if check in STRUCTURAL_CHECKS:
        body = node.get("body") or ""
        if check == "missing_h1":
            fixed, changed = promote_first_heading(body, from_level=2, to_level=1)
        else:  # multiple_h1
            fixed, changed = demote_extra_h1s(body)
        if not changed:
            return False, ("no heading matching this finding was found in the current "
                          "content (it may have already been fixed on the site)"), None
        ok, message = _update(shop_domain, access_token, kind, gid, {"body": fixed})
        return (ok, "heading structure fixed" if ok else message, fixed if ok else None)

    return False, f"no Shopify handling exists for the '{check}' check yet", None
