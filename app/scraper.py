"""Fetches pages and reduces them to structural signal for rules/checks.py.

Costs $0 to run — no LLM calls here (see the architecture note in CLAUDE.md).
`parse_html` is kept separate from the network code so tests can feed it
hand-written HTML with no network access.

Network rules, all enforced in `_http_get`, the one function that makes a
request to a scanned site:

  * every URL -- each redirect hop, every sitemap -- passes
    `validation.check_url` first, so the crawler cannot be pointed or
    redirected at a private address;
  * redirects are followed by hand (at most MAX_REDIRECTS) so that each hop is
    checked, and robots.txt is consulted before every hop of a page fetch;
  * bodies are streamed and capped at MAX_RESPONSE_BYTES;
  * one request per host at a time, spaced by CRAWL_DELAY.

`crawl` fills an optional `CrawlReport` with what happened at each step --
which scheme answered, what robots.txt said, what the sitemap listed, and
every page read or skipped and why. The pipeline stores it on the scan.
"""
from __future__ import annotations

import gzip
import io
import re
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from app import config
from app.config import CRAWL_DELAY, MAX_PAGES_PER_SCAN, REQUEST_TIMEOUT, USER_AGENT
from app.robots import Robots
from app.validation import ValidationError, check_url, pinned

HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
ICON_TOKEN_PATTERN = re.compile(r"(?:icon|lucide|feather|heroicon)[-_]?([a-z0-9-]+)", re.IGNORECASE)
HEADING_TAG_PATTERN = re.compile(r"^h[1-6]$")
TEXT_NODE_TAGS = ("p", "span", "div")
MAX_TEXT_NODE_LENGTH = 400
PRICE_RE = re.compile(r"[$£€]\s?\d|\b\d+\s?(?:/|per )\s?(?:mo|month|year|yr|seat|user)\b", re.I)
SKIP_EXT = (".pdf", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
            ".mp4", ".mp3", ".css", ".js", ".ico", ".xml", ".json", ".woff", ".woff2")

REDIRECT_CODES = (301, 302, 303, 307, 308)
ROBOTS_TTL = 3600.0          # re-read a site's robots.txt at most hourly
MAX_REPORTED_PAGES = 200     # keep one scan's trace a sensible size
_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
}


class ScrapeError(Exception):
    """A URL that could not or should not be read. `code` says which:
    robots, http_status, not_html, too_large, network, redirect_loop,
    bad_redirect, or one of the validation codes when a URL was blocked."""

    def __init__(self, message: str, code: str = "error") -> None:
        super().__init__(message)
        self.code = code


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


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str
    text: str
    bytes: int
    ms: int
    redirects: list[str] = field(default_factory=list)
    body: bytes = b""            # raw, for parsers that must see the declared encoding


@dataclass
class RobotsInfo:
    url: str
    status: int | None = None
    outcome: str = ""            # parsed | allow_all | disallow_all
    rules: list[str] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    ms: int = 0
    error: str = ""


@dataclass
class CrawlReport:
    """What `crawl` did, step by step. Plain, JSON-safe data."""

    base_url: str = ""
    base_attempts: list[dict] = field(default_factory=list)
    resolve_ms: int = 0
    robots: dict = field(default_factory=dict)
    sitemaps: list[dict] = field(default_factory=list)
    sitemap_urls: int = 0
    same_site_urls: int = 0
    discovery_ms: int = 0
    pages: list[dict] = field(default_factory=list)
    fetch_ms: int = 0
    stopped: str = ""


def _ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


# --- network ------------------------------------------------------------

_polite_lock = threading.Lock()
_last_hit: dict[str, float] = {}


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _be_polite(url: str) -> None:
    """One request per host at a time, spaced by CRAWL_DELAY. This is the
    difference between a crawler and a nuisance. Locked, because two worker
    threads can be reading the same host."""
    host = urlparse(url).netloc.lower()
    while True:
        with _polite_lock:
            now = time.monotonic()
            last = _last_hit.get(host)
            wait = 0.0 if last is None else CRAWL_DELAY - (now - last)
            if wait <= 0:
                _last_hit[host] = now
                return
        time.sleep(wait)


_CHARSET = re.compile(r"charset=[\"']?([\w.:-]+)", re.I)


def _decode(body: bytes, content_type: str) -> str:
    match = _CHARSET.search(content_type or "")
    if match:
        try:
            return body.decode(match.group(1), errors="replace")
        except LookupError:
            pass
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("cp1252", errors="replace")


def _http_get(url: str, *, robots: bool, max_bytes: int | None = None) -> FetchResult:
    """The only function in FIG that makes an HTTP request to a scanned site.
    Returns any final status; callers decide what counts as success."""
    cap = max_bytes or config.MAX_RESPONSE_BYTES
    started = time.monotonic()
    current = url
    hops: list[str] = []

    for _ in range(config.MAX_REDIRECTS + 1):
        try:
            resolution = check_url(current)
        except ValidationError as exc:
            raise ScrapeError(f"blocked {current}: {exc.message}", code=exc.code) from None
        if robots and not robots_allowed(current):
            raise ScrapeError(f"robots.txt disallows {current}", code="robots")

        _be_polite(current)
        try:
            # Pinned to the address check_url just validated -- otherwise
            # `requests` would resolve the hostname again right here, and an
            # answer that changed between the check above and this connect
            # (DNS rebinding) would bypass every check this module does.
            with pinned(resolution.hostname, resolution.addresses[0]):
                resp = requests.get(current, headers=_HEADERS, timeout=REQUEST_TIMEOUT,
                                    allow_redirects=False, stream=True)
        except requests.RequestException as exc:
            raise ScrapeError(f"could not fetch {current}: {exc}", code="network") from None

        try:
            if resp.status_code in REDIRECT_CODES:
                location = resp.headers.get("location", "").strip()
                if not location:
                    raise ScrapeError(f"{current} redirected without a Location header",
                                      code="bad_redirect")
                current = urljoin(current, location)
                hops.append(current)
                continue

            raw = bytearray()
            for chunk in resp.iter_content(64 * 1024):
                raw.extend(chunk)
                if len(raw) > cap:
                    raise ScrapeError(f"{current} is larger than {cap:,} bytes", code="too_large")
            ctype = resp.headers.get("content-type", "")
            data = bytes(raw)
            return FetchResult(url=url, final_url=current, status=resp.status_code,
                               content_type=ctype, text=_decode(data, ctype),
                               bytes=len(data), ms=_ms(started), redirects=hops, body=data)
        except requests.RequestException as exc:
            raise ScrapeError(f"could not read {current}: {exc}", code="network") from None
        finally:
            resp.close()

    raise ScrapeError(f"{url} redirected more than {config.MAX_REDIRECTS} times",
                      code="redirect_loop")


# --- robots.txt ---------------------------------------------------------

_robots_lock = threading.Lock()
_robots_cache: dict[str, tuple[float, Robots, RobotsInfo]] = {}


def _robots(url: str) -> tuple[Robots, RobotsInfo]:
    """This origin's robots.txt, read the RFC 9309 way (app/robots.py says why
    not urllib.robotparser), cached for an hour."""
    origin = _origin(url)
    now = time.monotonic()
    with _robots_lock:
        hit = _robots_cache.get(origin)
        if hit and now - hit[0] < ROBOTS_TTL:
            return hit[1], hit[2]

    robots_url = f"{origin}/robots.txt"
    info = RobotsInfo(url=robots_url)
    started = time.monotonic()
    try:
        res = _http_get(robots_url, robots=False, max_bytes=512 * 1024)
    except ScrapeError as exc:
        # An unreachable robots.txt is not itself a disallow.
        rules = Robots(allow_all=True)
        info.outcome, info.error = "allow_all", str(exc)
    else:
        info.status = res.status
        if res.status in (401, 403) or res.status >= 500:
            # RFC 9309: a locked or broken robots.txt means assume everything
            # is disallowed.
            rules = Robots(disallow_all=True)
            info.outcome = "disallow_all"
        elif res.status >= 400:
            rules = Robots(allow_all=True)
            info.outcome = "allow_all"
        else:
            rules = Robots.parse(res.text)
            info.outcome = "parsed"
            info.rules = rules.describe(USER_AGENT)
            info.sitemaps = list(rules.sitemaps)
    info.ms = _ms(started)

    with _robots_lock:
        _robots_cache[origin] = (now, rules, info)
    return rules, info


def robots_allowed(url: str) -> bool:
    rules, _info = _robots(url)
    return rules.allowed(USER_AGENT, url)


# --- pages --------------------------------------------------------------


def fetch_page(url: str) -> FetchResult:
    """A page for the rules engine: robots-checked, validated, 2xx, HTML."""
    res = _http_get(url, robots=True)
    if not 200 <= res.status < 300:
        raise ScrapeError(f"{res.final_url} returned HTTP {res.status}", code="http_status")
    if res.content_type and "html" not in res.content_type.lower():
        raise ScrapeError(f"{res.final_url} is {res.content_type}, not HTML", code="not_html")
    return res


def scrape(url: str) -> PageSignal:
    _base, res = _resolve_base(url)
    signal = parse_html(res.final_url, res.text)
    signal.status_code = res.status
    return signal


# --- discovery ----------------------------------------------------------


def _normalise(url: str) -> str:
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme, p.netloc.lower(), path, "", "", ""))


def _same_host(a: str, b: str) -> bool:
    ha, hb = urlparse(a).netloc.lower(), urlparse(b).netloc.lower()
    return ha.removeprefix("www.") == hb.removeprefix("www.")


def _skip(url: str) -> bool:
    return urlparse(url).path.lower().endswith(SKIP_EXT)


def _sitemap_locs(body: bytes) -> tuple[list[str], list[str]]:
    """(child sitemaps, page URLs) from a sitemap or a sitemap index.

    The standard library's parser rather than BeautifulSoup's "xml" mode,
    which needs lxml: where lxml was missing, every sitemap failed to parse,
    the error was swallowed, and scans quietly fell back to following links.
    Parsing bytes also honours the encoding the file declares. Expat never
    fetches external entities, the bundled version refuses entity-expansion
    bombs, and the body is already size-capped. Gzipped sitemaps are unpacked
    first, up to the same cap.
    """
    if body[:2] == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=io.BytesIO(body)) as packed:
            body = packed.read(config.MAX_RESPONSE_BYTES + 1)
        if len(body) > config.MAX_RESPONSE_BYTES:
            raise ValueError(f"unpacked sitemap is larger than {config.MAX_RESPONSE_BYTES:,} bytes")
    root = ET.fromstring(body.lstrip(b" \t\r\n"))

    def local(tag) -> str:
        return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""

    children: list[str] = []
    urls: list[str] = []
    for element in root.iter():
        kind = local(element.tag)
        if kind not in ("sitemap", "url"):
            continue
        loc = next((c.text.strip() for c in element if local(c.tag) == "loc" and c.text), "")
        if loc:
            (children if kind == "sitemap" else urls).append(loc)
    return children, urls


def sitemap_urls(base_url: str, limit: int = 500, report: CrawlReport | None = None) -> list[str]:
    """robots.txt Sitemap: directives first, then the conventional paths.
    Nested sitemap indexes are followed one level, which covers almost every
    real site without turning into an unbounded walk."""
    origin = _origin(base_url)
    _parser, robots = _robots(base_url)
    candidates = list(robots.sitemaps) + [f"{origin}/sitemap.xml", f"{origin}/sitemap_index.xml"]

    found: list[str] = []
    seen_maps: set[str] = set()

    def note(entry: dict) -> None:
        if report is not None:
            report.sitemaps.append(entry)

    def read_map(map_url: str, depth: int = 0) -> None:
        if map_url in seen_maps or depth > 1 or len(found) >= limit:
            return
        seen_maps.add(map_url)
        entry: dict = {"url": map_url, "depth": depth}
        try:
            res = _http_get(map_url, robots=False)
        except ScrapeError as exc:
            note({**entry, "outcome": exc.code, "error": str(exc)})
            return
        entry.update(status=res.status, ms=res.ms)
        if res.status != 200:
            note({**entry, "outcome": "http_status"})
            return
        try:
            children, urls = _sitemap_locs(res.body)
        except (ET.ParseError, OSError, EOFError, ValueError) as exc:
            note({**entry, "outcome": "unparseable", "error": str(exc)})
            return
        note({**entry, "outcome": "ok", "child_sitemaps": len(children), "urls": len(urls)})
        for child in children:
            read_map(child, depth + 1)
        for u in urls:
            if len(found) >= limit:
                break
            found.append(u)

    for candidate in candidates:
        read_map(candidate)
        if found:
            break
    return found


def _resolve_base(host_or_url: str, report: CrawlReport | None = None) -> tuple[str, FetchResult]:
    """https first, http as a fallback. Plenty of small business sites — the
    ones this tool is most often pointed at — are still http-only, and a scan
    that refuses them is not much use to the agency that inherited them.

    Returns the origin that answered and its homepage, so the crawl does not
    fetch the homepage twice."""
    if "://" in host_or_url:
        candidates = [host_or_url]
    else:
        candidates = [f"https://{host_or_url}/", f"http://{host_or_url}/"]

    errors: list[ScrapeError] = []
    for url in candidates:
        try:
            res = fetch_page(url)
        except ScrapeError as exc:
            errors.append(exc)
            if report is not None:
                report.base_attempts.append({"url": url, "outcome": exc.code, "error": str(exc)})
            continue
        if report is not None:
            report.base_attempts.append({
                "url": url, "outcome": "ok", "status": res.status, "ms": res.ms,
                "final_url": res.final_url, "redirects": res.redirects,
            })
        return _origin(res.final_url), res

    raise ScrapeError("could not read the homepage: " + "; ".join(str(e) for e in errors),
                      code=errors[-1].code)


def resolve_base(host: str) -> str:
    return _resolve_base(host)[0]


def _note_page(report: CrawlReport, entry: dict) -> None:
    if len(report.pages) < MAX_REPORTED_PAGES:
        report.pages.append(entry)


def crawl(base_url: str, max_pages: int = MAX_PAGES_PER_SCAN,
          report: CrawlReport | None = None) -> list[PageSignal]:
    """Read up to max_pages of one site. Sitemap if there is one, breadth-first
    over internal links if not. Failures on individual pages are skipped rather
    than aborting the scan — a 404 on one page is a finding, not an outage.

    Raises ScrapeError only when the homepage itself cannot be read."""
    report = report if report is not None else CrawlReport()

    started = time.monotonic()
    try:
        base, homepage = _resolve_base(base_url, report)
    finally:
        report.resolve_ms = _ms(started)
    report.base_url = base

    _parser, robots = _robots(base)
    report.robots = asdict(robots)

    started = time.monotonic()
    listed = sitemap_urls(base, report=report)
    same_site = [u for u in listed if _same_host(u, base) and not _skip(u)]
    queue: list[str] = [homepage.final_url, *same_site]
    report.sitemap_urls = len(listed)
    report.same_site_urls = len(same_site)
    report.discovery_ms = _ms(started)

    started = time.monotonic()
    seen: set[str] = set()
    out: list[PageSignal] = []
    homepage_pending = True
    i = 0

    while i < len(queue) and len(out) < max_pages:
        url = queue[i]
        i += 1
        key = _normalise(url)
        if key in seen:
            continue
        seen.add(key)

        if homepage_pending:
            res, homepage_pending = homepage, False
        else:
            try:
                res = fetch_page(url)
            except ScrapeError as exc:
                _note_page(report, {"url": url, "outcome": exc.code, "error": str(exc)})
                continue

        # A redirect can land on a page that has already been read.
        final_key = _normalise(res.final_url)
        if final_key != key:
            if final_key in seen:
                _note_page(report, {"url": url, "outcome": "duplicate",
                                    "final_url": res.final_url})
                continue
            seen.add(final_key)

        sig = parse_html(res.final_url, res.text)
        sig.status_code = res.status
        out.append(sig)
        entry = {"url": url, "outcome": "ok", "status": res.status,
                 "bytes": res.bytes, "ms": res.ms}
        if res.final_url != url:
            entry["final_url"] = res.final_url
        _note_page(report, entry)

        # Only widen the frontier when the sitemap did not already supply
        # enough to work with.
        if len(queue) < max_pages * 2:
            for link in sig.internal_links:
                if len(queue) >= max_pages * 2:
                    break
                if _same_host(link, base) and not _skip(link) and _normalise(link) not in seen:
                    queue.append(link)

    report.fetch_ms = _ms(started)
    report.stopped = ("page limit reached" if len(out) >= max_pages
                      else "no more pages to read")
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
    if kids or deep:
        return kids or deep

    # Bare semantic HTML: body text sitting directly under <main>/<body> with
    # no wrapping <section>, <div>, or <article> at all -- common on
    # legal/policy pages (found on launchvault.ca's). Every branch above
    # returns nothing for this shape, which means none of that page's text
    # gets attributed to any section at all. Treat the whole root as one
    # unstructured content block instead of silently dropping it.
    return [root] if root.get_text(strip=True) else []


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

    # An empty block -- no words, images, buttons, forms or list items -- is a
    # mount point for a toast, a modal or a cookie banner, not a section. Left
    # in, it reads as "content below the footer": seven legal pages on
    # launchvault.ca were flagged high for one empty trailing <section> (Test #1).
    sections = [block for block in
                (_describe_section(i, el) for i, el in enumerate(_section_blocks(soup)))
                if block.word_count or block.image_count or block.button_count
                or block.has_form or block.list_items]
    for position, block in enumerate(sections):
        block.index = position

    # A Q&A block is FAQPage markup, a section named or labelled as an FAQ, or
    # at least two headings that are themselves questions. launchvault.ca's
    # homepage answers nine questions under "Questions, answered" in
    # <section id="faq"> and was still flagged as having none (Test #1).
    question_headings = sum(1 for h in headings if h.rstrip().endswith("?"))
    faq_block = (
        any(t.lower() in ("faqpage", "question") for t in jsonld_types)
        or any(s.heading.lower().startswith(("faq", "frequently asked", "common questions"))
               for s in sections if s.heading)
        or any("faq" in (s.element_id + " " + " ".join(s.classes)).lower() for s in sections)
        or question_headings >= 2
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
