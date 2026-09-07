"""Fetches pages and reduces them to structural signal for rules/checks.py.

Costs $0 to run — no LLM calls here (see the architecture note in CLAUDE.md).
`parse_html` is kept separate from `scrape` so tests can feed it hand-written
HTML with no network access; `scrape` and `crawl` are the only functions that
touch the network.

`crawl` is what makes an estate scan possible: sitemap first, internal links
as a fallback, one request per host at a time with a delay between them.
"""
from __future__ import annotations

import re
import time
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from app.config import CRAWL_DELAY, MAX_PAGES_PER_SCAN, REQUEST_TIMEOUT, USER_AGENT

HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
ICON_TOKEN_PATTERN = re.compile(r"(?:icon|lucide|feather|heroicon)[-_]?([a-z0-9-]+)", re.IGNORECASE)
HEADING_TAG_PATTERN = re.compile(r"^h[1-6]$")
TEXT_NODE_TAGS = ("p", "span", "div")
MAX_TEXT_NODE_LENGTH = 400
PRICE_RE = re.compile(r"[$£€]\s?\d|\b\d+\s?(?:/|per )\s?(?:mo|month|year|yr|seat|user)\b", re.I)
SKIP_EXT = (".pdf", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".mp4", ".mp3", ".css", ".js", ".ico", ".xml", ".json", ".woff", ".woff2")


class ScrapeError(Exception):
    """Raised when a URL can't or shouldn't be scraped (network failure,
    non-2xx response, or robots.txt disallow)."""


@dataclass
class ElementSignal:
    tag: str
    classes: list[str]


@dataclass
class SectionSignal:
    """One top-level block of a page, in document order. `role` is assigned by
    rules/sections.py — the scraper only reports what is there."""

    index: int
    tag: str
    heading: str = ""
    heading_level: int = 0
    word_count: int = 0
    link_count: int = 0
    button_count: int = 0
    image_count: int = 0
    list_items: int = 0
    has_price: bool = False
    has_form: bool = False
    text: str = ""
    classes: list[str] = field(default_factory=list)
    element_id: str = ""


@dataclass
class PageSignal:
    url: str
    title: str
    headings: list[str]
    heading_tags: list[str]
    paragraphs: list[str]
    elements: list[ElementSignal]
    hex_colors: list[str]
    icon_tokens: list[str]
    # Added for the structure / search / answers layers. All default so
    # parse_html stays a drop-in for anything built against the old shape.
    sections: list[SectionSignal] = field(default_factory=list)
    meta_description: str = ""
    canonical: str = ""
    lang: str = ""
    jsonld_types: list[str] = field(default_factory=list)
    images_total: int = 0
    images_missing_alt: int = 0
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    word_count: int = 0
    h1_count: int = 0
    status_code: int | None = None
    has_faq_block: bool = False
    numbers_in_copy: int = 0
    proper_nouns: int = 0


# --- network ------------------------------------------------------------

_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _robots(url: str):
    origin = _origin(url)
    if origin not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{origin}/robots.txt")
        try:
            rp.read()
        except Exception:
            # No reachable/parseable robots.txt is not itself a disallow.
            rp = None
        _robots_cache[origin] = rp
    return _robots_cache[origin]


def _robots_allowed(url: str) -> bool:
    rp = _robots(url)
    if rp is None:
        return True
    try:
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def _be_polite(url: str) -> None:
    """One request per host at a time, spaced by CRAWL_DELAY. This is the
    difference between a crawler and a nuisance."""
    host = urlparse(url).netloc
    last = _last_hit.get(host)
    if last is not None:
        wait = CRAWL_DELAY - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
    _last_hit[host] = time.monotonic()


def fetch(url: str) -> tuple[str, int]:
    if not _robots_allowed(url):
        raise ScrapeError(f"robots.txt disallows fetching {url}")
    _be_polite(url)
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=REQUEST_TIMEOUT, allow_redirects=True)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f"could not fetch {url}: {exc}") from exc
    ctype = r.headers.get("content-type", "")
    if "html" not in ctype and ctype:
        raise ScrapeError(f"{url} is {ctype or 'not HTML'}")
    return r.text, r.status_code


def scrape(url: str) -> PageSignal:
    url = resolve_base(url)
    html, code = fetch(url)
    signal = parse_html(url, html)
    signal.status_code = code
    return signal


# --- discovery ----------------------------------------------------------


def _normalise(url: str) -> str:
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme, p.netloc.lower(), path, "", "", ""))


def _same_host(a: str, b: str) -> bool:
    ha, hb = urlparse(a).netloc.lower(), urlparse(b).netloc.lower()
    return ha.removeprefix("www.") == hb.removeprefix("www.")


def sitemap_urls(base_url: str, limit: int = 500) -> list[str]:
    """robots.txt Sitemap: directives first, then the conventional path.
    Nested sitemap indexes are followed one level, which covers almost every
    real site without turning into an unbounded walk."""
    origin = _origin(base_url)
    candidates: list[str] = []

    rp = _robots(base_url)
    if rp is not None:
        try:
            candidates.extend(rp.site_maps() or [])
        except Exception:
            pass
    candidates.append(f"{origin}/sitemap.xml")
    candidates.append(f"{origin}/sitemap_index.xml")

    found: list[str] = []
    seen_maps: set[str] = set()

    def read_map(map_url: str, depth: int = 0) -> None:
        if map_url in seen_maps or depth > 1 or len(found) >= limit:
            return
        seen_maps.add(map_url)
        try:
            _be_polite(map_url)
            r = requests.get(map_url, headers={"User-Agent": USER_AGENT},
                             timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                return
            soup = BeautifulSoup(r.text, "xml")
        except Exception:
            return
        for sm in soup.find_all("sitemap"):
            loc = sm.find("loc")
            if loc and loc.text:
                read_map(loc.text.strip(), depth + 1)
        for u in soup.find_all("url"):
            loc = u.find("loc")
            if loc and loc.text and len(found) < limit:
                found.append(loc.text.strip())

    for c in candidates:
        read_map(c)
        if found:
            break
    return found


def resolve_base(host: str) -> str:
    """https first, http as a fallback. Plenty of small business sites — the
    ones this tool is most often pointed at — are still http-only, and a scan
    that refuses them is not much use to the agency that inherited them."""
    if "://" in host:
        return host
    for scheme in ("https", "http"):
        url = f"{scheme}://{host}"
        try:
            fetch(url)
            return url
        except ScrapeError:
            continue
    return f"https://{host}"


def crawl(base_url: str, max_pages: int = MAX_PAGES_PER_SCAN) -> list[PageSignal]:
    """Read up to max_pages of one site. Sitemap if there is one, breadth-first
    over internal links if not. Failures on individual pages are skipped rather
    than aborting the scan — a 404 on one page is a finding, not an outage."""
    base_url = resolve_base(base_url)

    queue: list[str] = [base_url]
    for u in sitemap_urls(base_url):
        if _same_host(u, base_url) and not u.lower().endswith(SKIP_EXT):
            queue.append(u)

    seen: set[str] = set()
    out: list[PageSignal] = []
    i = 0

    while i < len(queue) and len(out) < max_pages:
        url = queue[i]
        i += 1
        key = _normalise(url)
        if key in seen:
            continue
        seen.add(key)
        try:
            html, code = fetch(url)
        except ScrapeError:
            continue
        sig = parse_html(url, html)
        sig.status_code = code
        out.append(sig)

        # Only widen the frontier when the sitemap did not already supply
        # enough to work with.
        if len(queue) < max_pages * 2:
            for link in sig.internal_links:
                if len(queue) >= max_pages * 2:
                    break
                if _same_host(link, base_url) and not link.lower().endswith(SKIP_EXT):
                    if _normalise(link) not in seen:
                        queue.append(link)

    return out


# --- extraction ---------------------------------------------------------

_BLOCK_PARENTS = ("main", "body")
_SECTION_TAGS = {"section", "header", "footer", "article", "aside", "nav", "div"}


def _section_blocks(soup: BeautifulSoup):
    """Top-level blocks in document order.

    Prefers real landmarks. Falls back to the direct children of <main> or
    <body> so that div-soup pages — which are most of the pages this tool
    exists for — still produce an ordered list of sections.
    """
    root = soup.find("main") or soup.body or soup
    landmarks = [c for c in root.find_all(["section", "header", "footer"], recursive=False)]
    if len(landmarks) >= 3:
        return landmarks

    deep = soup.find_all(["section", "header", "footer"])
    if len(deep) >= 3:
        # Keep only outermost ones so nested sections do not double-count.
        outer = [s for s in deep if not s.find_parent(["section", "article"])]
        if len(outer) >= 3:
            return outer
        return deep

    kids = [c for c in root.find_all(recursive=False) if c.name in _SECTION_TAGS]
    return kids or deep


def _describe_section(idx: int, el) -> SectionSignal:
    heading, level = "", 0
    h = el.find(HEADING_TAG_PATTERN)
    if h:
        heading = h.get_text(" ", strip=True)
        level = int(h.name[1])
    text = el.get_text(" ", strip=True)
    return SectionSignal(
        index=idx,
        tag=el.name,
        heading=heading,
        heading_level=level,
        word_count=len(text.split()),
        link_count=len(el.find_all("a")),
        button_count=len(el.find_all("button")) + len(
            el.find_all("a", class_=re.compile(r"btn|button|cta", re.I))),
        image_count=len(el.find_all("img")) + len(el.find_all("svg")),
        list_items=len(el.find_all("li")),
        has_price=bool(PRICE_RE.search(text)),
        has_form=bool(el.find("form") or el.find("input")),
        text=text[:600],
        classes=el.get("class") or [],
        element_id=el.get("id") or "",
    )


def parse_html(url: str, html: str) -> PageSignal:
    """Pure extraction step — no network access. Safe to call directly in tests."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""

    # Captured unconditionally (unlike `elements` below, which only tracks
    # elements carrying a class attribute) so pages using plain semantic HTML
    # without utility classes still register their heading hierarchy.
    headings: list[str] = []
    heading_tags: list[str] = []
    for h in soup.find_all(HEADING_TAG_PATTERN):
        text = h.get_text(strip=True)
        if text:
            headings.append(text)
            heading_tags.append(h.name)

    paragraphs = [
        text
        for p in soup.find_all(TEXT_NODE_TAGS)
        if (text := p.get_text(strip=True)) and len(text) < MAX_TEXT_NODE_LENGTH
    ]

    elements: list[ElementSignal] = []
    icon_tokens: list[str] = []
    for tag in soup.find_all(True):
        classes = tag.get("class") or []
        if not classes:
            continue
        elements.append(ElementSignal(tag=tag.name, classes=classes))
        for cls in classes:
            match = ICON_TOKEN_PATTERN.search(cls)
            if match:
                icon_tokens.append(match.group(1).lower())

    for svg in soup.find_all("svg"):
        for attr in ("aria-label", "data-icon", "data-lucide"):
            value = svg.get(attr)
            if value:
                icon_tokens.append(value.lower())

    # Scanning the raw markup (rather than walking inline style="" attributes
    # and <style> blocks separately) picks up both in one pass.
    hex_colors = HEX_COLOR_PATTERN.findall(html)

    # --- head / structured data ---
    md = soup.find("meta", attrs={"name": "description"})
    meta_description = (md.get("content") or "").strip() if md else ""
    can = soup.find("link", attrs={"rel": lambda v: v and "canonical" in (
        v if isinstance(v, list) else [v])})
    canonical = (can.get("href") or "").strip() if can else ""
    lang = (soup.html.get("lang") or "").strip() if soup.html else ""

    jsonld_types: list[str] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        for m in re.finditer(r'"@type"\s*:\s*"([^"]+)"', raw):
            jsonld_types.append(m.group(1))

    # --- media / links ---
    imgs = soup.find_all("img")
    images_missing_alt = sum(
        1 for i in imgs
        if i.get("alt") is None or (i.get("alt").strip() == "" and not i.get("aria-hidden"))
    )

    internal: list[str] = []
    external: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(url, href)
        if not absolute.startswith("http"):
            continue
        (internal if _same_host(absolute, url) else external).append(absolute)

    body_text = soup.body.get_text(" ", strip=True) if soup.body else soup.get_text(" ", strip=True)
    words = body_text.split()

    sections = [_describe_section(i, el) for i, el in enumerate(_section_blocks(soup))]

    faq_block = any(t.lower() in ("faqpage", "question") for t in jsonld_types) or any(
        s.heading.lower().startswith(("faq", "frequently asked", "common questions"))
        for s in sections if s.heading
    )

    return PageSignal(
        url=url,
        title=title,
        headings=headings,
        heading_tags=heading_tags,
        paragraphs=paragraphs,
        elements=elements,
        hex_colors=hex_colors,
        icon_tokens=icon_tokens,
        sections=sections,
        meta_description=meta_description,
        canonical=canonical,
        lang=lang,
        jsonld_types=jsonld_types,
        images_total=len(imgs),
        images_missing_alt=images_missing_alt,
        internal_links=internal,
        external_links=external,
        word_count=len(words),
        h1_count=sum(1 for t in heading_tags if t == "h1"),
        has_faq_block=faq_block,
        # Specificity signals: a page a model can quote tends to carry actual
        # numbers and actual names.
        numbers_in_copy=len(re.findall(r"\b\d[\d,.]*\b", body_text)),
        proper_nouns=len(re.findall(r"\b[A-Z][a-z]{2,}\b", body_text)),
    )
