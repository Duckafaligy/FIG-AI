"""GitHub repo adapter, for a self-hosted / Git-deployed site with no CMS
API at all -- a plain static export, or a site built with any static-site
generator and deployed from a Git repo (Cloudflare Pages, Netlify, Vercel,
GitHub Pages all commonly work this way, which is how this got prioritized:
launchvault.ca, FIG's own reference site, is exactly this shape).

No CMS here means no structured "get post by slug" the way WordPress/
Shopify/Webflow all have -- a git repo of source files has no such API, and
guessing at a framework's file layout (Next.js vs Hugo vs Astro vs plain
HTML export all differ) isn't something this locates reliably. The strategy
instead: **re-read the live page right now** (app.scraper.scrape(), the
same pure fetch-and-parse everything else here already trusts), take the
exact current text a check's evidence is about, and search the connected
repo for a file containing that literal text via GitHub's code search API.
Exactly one match required -- zero or several both refuse rather than guess
which file is really the source.

This is why scope here is narrower than WordPress/Shopify, not the same:
`missing_title` / `missing_h1` / `missing_meta_description` have nothing to
search for (the whole point is nothing is there), so they refuse -- not a
gap to close, a real ceiling of what text-search-based location can do.
`title_length` / `meta_description_length` / `multiple_h1` all have real
current text to anchor on and are real fixes here.

**Writes go through a Pull Request, never a direct commit to the default
branch** -- deliberately different from every other adapter in this
codebase, which write straight to the live CMS once a change is approved.
A PR is itself a review gate a site owner controls (merge, request changes,
close), which fits a source-controlled site better than a silent commit
would, and costs nothing extra to do since GitHub's API shape makes a PR
almost as cheap as a commit.

GitHub's OAuth App model only ever grants `repo` scope across every
repository the connecting account can reach, not one repo specifically
(see app/config.py's GITHUB_* block for why this isn't a GitHub App
instead) -- `repo` here is which one this Integration is actually meant to
touch, supplied at connect time and never assumed from anything broader.
"""
from __future__ import annotations

import base64
import secrets
from urllib.parse import quote

import httpx

from app.html_headings import demote_extra_h1s
from app.scraper import scrape

PLATFORM = "github"
TIMEOUT = 20.0
API_BASE = "https://api.github.com"

TITLE_CHECKS = {"title_length"}
META_CHECKS = {"meta_description_length"}
STRUCTURAL_CHECKS = {"multiple_h1"}
NOT_EXPOSED_HERE = {
    "missing_title", "missing_meta_description", "missing_h1",
    "missing_canonical", "missing_lang", "no_structured_data",
    "thin_structured_data", "heading_skips", "missing_alt",
}


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def _current_anchor(check: str, fresh) -> str:
    """The exact text to search the repo for, read from a fresh scrape --
    never from a Finding's possibly-stale, possibly-truncated evidence."""
    if check in TITLE_CHECKS:
        return fresh.title or ""
    if check in META_CHECKS:
        return fresh.meta_description or ""
    if check in STRUCTURAL_CHECKS:
        h1_texts = [h for h, tag in zip(fresh.headings, fresh.heading_tags) if tag == "h1"]
        # The second h1 is the first one demote_extra_h1s() would actually
        # change -- the first h1 is kept as-is, by design.
        return h1_texts[1] if len(h1_texts) > 1 else ""
    return ""


def _search_code(repo: str, access_token: str, text: str) -> tuple[str | None, str | None]:
    """(path, error) -- exactly one match required. GitHub's code search is
    a search index, not grep: it can miss an exact literal match or return
    more than one plausible file, and either case must refuse rather than
    pick one, since a wrong guess here means editing the wrong file.

    Quote characters are stripped from the *query* only (a title or
    description containing one would otherwise break GitHub's `"..."`
    phrase syntax) -- the later exact-match-and-replace step still uses
    the real, unmodified anchor text, so a quote in the original is never
    lost from the actual edit."""
    query = f'"{text.replace(chr(34), "")}" repo:{repo}'
    try:
        resp = httpx.get(f"{API_BASE}/search/code", headers=_headers(access_token),
                         params={"q": query}, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return None, f"could not reach GitHub: {exc}"
    if resp.status_code != 200:
        return None, f"GitHub search rejected the request: HTTP {resp.status_code}: {resp.text[:200]}"
    items = resp.json().get("items", [])
    if not items:
        return None, ("couldn't find any file in the repo containing the current text -- it may "
                      "be generated at build time rather than literal source")
    paths = sorted({i["path"] for i in items})
    if len(paths) > 1:
        return None, f"found the current text in {len(paths)} different files ({', '.join(paths[:5])}) -- too ambiguous to edit automatically"
    return items[0]["path"], None


def _get_repo_and_file(repo: str, access_token: str,
                       path: str) -> tuple[str, str, str] | tuple[None, None, None]:
    """(content, sha, default_branch), or (None, None, None) with the error
    logged by the caller via the returned message pattern below."""
    try:
        repo_resp = httpx.get(f"{API_BASE}/repos/{repo}", headers=_headers(access_token), timeout=TIMEOUT)
    except httpx.HTTPError:
        return None, None, None
    if repo_resp.status_code != 200:
        return None, None, None
    default_branch = repo_resp.json().get("default_branch", "main")

    try:
        file_resp = httpx.get(f"{API_BASE}/repos/{repo}/contents/{quote(path)}",
                              headers=_headers(access_token), params={"ref": default_branch},
                              timeout=TIMEOUT)
    except httpx.HTTPError:
        return None, None, None
    if file_resp.status_code != 200:
        return None, None, None
    body = file_resp.json()
    try:
        content = base64.b64decode(body["content"]).decode("utf-8")
    except (KeyError, ValueError, UnicodeDecodeError):
        return None, None, None
    return content, body["sha"], default_branch


def _open_pr(repo: str, access_token: str, *, default_branch: str, path: str, new_content: str,
            sha: str, title: str, body_text: str) -> tuple[bool, str]:
    """(ok, message) -- message is the PR url on success, an error otherwise."""
    branch = f"fig-fix-{secrets.token_hex(4)}"
    try:
        ref_resp = httpx.get(f"{API_BASE}/repos/{repo}/git/ref/heads/{default_branch}",
                             headers=_headers(access_token), timeout=TIMEOUT)
        if ref_resp.status_code != 200:
            return False, f"couldn't read {default_branch}'s current commit: HTTP {ref_resp.status_code}"
        base_sha = ref_resp.json()["object"]["sha"]

        create_ref = httpx.post(f"{API_BASE}/repos/{repo}/git/refs", headers=_headers(access_token),
                                json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=TIMEOUT)
        if create_ref.status_code not in (200, 201):
            return False, f"couldn't create a branch: HTTP {create_ref.status_code}: {create_ref.text[:200]}"

        update = httpx.put(f"{API_BASE}/repos/{repo}/contents/{quote(path)}",
                           headers=_headers(access_token),
                           json={"message": title,
                                 "content": base64.b64encode(new_content.encode("utf-8")).decode(),
                                 "sha": sha, "branch": branch}, timeout=TIMEOUT)
        if update.status_code not in (200, 201):
            return False, f"couldn't commit the fix: HTTP {update.status_code}: {update.text[:200]}"

        pr = httpx.post(f"{API_BASE}/repos/{repo}/pulls", headers=_headers(access_token),
                        json={"title": title, "head": branch, "base": default_branch,
                              "body": body_text}, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return False, f"could not reach GitHub: {exc}"
    if pr.status_code not in (200, 201):
        return False, f"couldn't open a pull request: HTTP {pr.status_code}: {pr.text[:200]}"
    return True, pr.json()["html_url"]


def apply_change(repo: str, access_token: str, *,
                 check: str, page_url: str, after: str | None) -> tuple[bool, str, str | None]:
    """Opens a Pull Request with one change. Returns
    (ok, message, applied_value) like every other adapter -- `message` is
    the PR's URL on success, not "published", since nothing here writes to
    the live site directly."""
    if not repo:
        return False, "no GitHub repo is connected for this site", None
    if check in NOT_EXPOSED_HERE:
        return (False,
                "This can't be located reliably in a repo -- nothing exists yet for FIG to "
                "search for (the fix would be adding something, not replacing something "
                "findable). See app/github_repo.py.", None)
    if check not in (TITLE_CHECKS | META_CHECKS | STRUCTURAL_CHECKS):
        return False, f"no GitHub handling exists for the '{check}' check yet", None
    if check in (TITLE_CHECKS | META_CHECKS) and not after:
        return False, "no new text has been drafted for this change yet", None

    try:
        fresh = scrape(page_url)
    except Exception as exc:
        return False, f"couldn't re-read the live page to find the current text: {exc}", None

    anchor = _current_anchor(check, fresh)
    if not anchor:
        return (False, "the live page no longer has the text this fix was based on -- it may "
                       "already be fixed, or the page changed since the scan", None)

    path, error = _search_code(repo, access_token, anchor)
    if path is None:
        return False, error, None

    content, sha, default_branch = _get_repo_and_file(repo, access_token, path)
    if content is None:
        return False, f"found {path} but couldn't fetch its content from GitHub", None

    if check in STRUCTURAL_CHECKS:
        new_content, changed = demote_extra_h1s(content)
        if not changed:
            return (False, f"no heading matching this finding was found in {path}'s current "
                          "content (it may already be fixed, or use a non-HTML heading "
                          "syntax like Markdown that this doesn't parse)", None)
    else:
        if anchor not in content:
            return (False, f"the text this fix was based on wasn't found verbatim in {path} -- "
                          "it may be assembled at build time rather than literal source", None)
        new_content = content.replace(anchor, after, 1)

    title = f"FIG: fix {check.replace('_', ' ')} on {page_url}"
    body_text = (f"Automated fix proposed by FIG for `{check}` on {page_url}.\n\n"
                f"This is a proposal, not a live change -- review and merge it like any "
                f"other pull request.")
    ok, result = _open_pr(repo, access_token, default_branch=default_branch, path=path,
                          new_content=new_content, sha=sha, title=title, body_text=body_text)
    if not ok:
        return False, result, None
    # applied_value matches every other adapter's convention: the drafted
    # replacement text itself for a title/meta fix, but the whole
    # transformed content for a structural fix -- there's no separate
    # "the new text" for a heading demotion the way there is for a title.
    applied_value = new_content if check in STRUCTURAL_CHECKS else after
    return True, f"opened a pull request for review: {result}", applied_value
