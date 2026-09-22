"""Backend tests that need no network, no database and no API key.

    python test_backend.py

Covers the validation system (the syntax half, and the DNS half through an
injected resolver), the crawler's network rules against a fake network
(redirect hops re-validated, robots.txt honoured on every hop, bodies capped,
a whole crawl end to end), the grouping that decides what the AI step is
sent, the AI step's usage accounting against a fake client, and the
WordPress adapter (app/wordpress.py) against a fake WordPress REST API --
the same fake-network pattern as the crawler tests, for the same reason:
this environment's Docker couldn't run a real WordPress instance to test
against (a broken data-root config, not a code issue), so the adapter's
actual HTTP request/response handling is exercised here instead of trusted
on read-through.
"""
from __future__ import annotations

import os

# Must happen before any `from app import ...` below: sentry_sdk.init() runs
# at app/main.py's *import* time, once, and reads this value right then --
# patching config.SENTRY_DSN afterward cannot undo an init() that already
# ran. Without this, the startup-check tests further down (which deliberately
# log real ERROR-level messages) would have those messages captured and sent
# to the real Sentry project, using whatever real DSN is sitting in .env.
# Found by running these tests once and watching two real events land there.
os.environ["SENTRY_DSN"] = ""

import gzip
import json
import re
import sys
import traceback
import types
from contextlib import contextmanager
from pathlib import Path

import requests as real_requests

from app import ai_explain, pages, scraper, search_console, validation, wordpress
from app.pipeline import explanation_payload, group_flags
from app.rules.checks import Flag
from app.validation import ValidationError, check_url, normalise_target, validate_target

ROOT = Path(__file__).resolve().parent

PUBLIC = "93.184.216.34"
DNS = {
    "launchvault.ca": [PUBLIC],
    "shop.testsite.com": [PUBLIC],
    "sneaky.testsite.com": ["10.0.0.5"],
    "mixed.testsite.com": [PUBLIC, "127.0.0.1"],
    "mapped.testsite.com": ["::ffff:127.0.0.1"],
    "cgnat.testsite.com": ["100.64.0.1"],
    "metadata.testsite.com": ["169.254.169.254"],
}


def fake_resolver(host: str) -> list[str]:
    if host in DNS:
        return list(DNS[host])
    raise OSError(f"getaddrinfo failed for {host}")


def expect_code(code: str, fn, *args) -> ValidationError:
    try:
        fn(*args)
    except ValidationError as exc:
        assert exc.code == code, f"{args!r}: expected {code}, got {exc.code} ({exc.message})"
        return exc
    raise AssertionError(f"{args!r}: expected ValidationError {code}, nothing was raised")


# --- validation: syntax --------------------------------------------------


def test_normalises_what_people_actually_type():
    t = normalise_target("https://LaunchVault.ca:443/pricing?utm=x#top")
    assert t.hostname == "launchvault.ca", t
    notes = " | ".join(t.notes)
    assert "scheme" in notes and "port" in notes and "path" in notes, notes
    assert normalise_target("Launchvault.ca").hostname == "launchvault.ca"
    assert normalise_target("Launchvault.ca.").hostname == "launchvault.ca"
    assert normalise_target("bücher.de").hostname == "xn--bcher-kva.de"


def test_rejects_unsafe_and_malformed_targets():
    cases = {
        "": "empty",
        "   ": "empty",
        "127.0.0.1": "ip_literal",
        "169.254.169.254": "ip_literal",
        "http://[::1]/": "ip_literal",
        "http://user@10.0.0.1/": "ip_literal",
        "http://10.0.0.1:8080/admin": "has_port",
        "2130706433": "bad_hostname",            # 127.0.0.1 written as a number
        "0x7f.0.0.1": "bad_hostname",
        "localhost": "reserved_name",
        "printer.internal": "reserved_name",
        "nas.local": "reserved_name",
        "router.home.arpa": "reserved_name",
        "ftp://launchvault.ca": "bad_scheme",
        "javascript://x": "bad_scheme",
        "http://launchvault.ca:8080/": "has_port",
        "not a host": "bad_hostname",
        "exa_mple.com": "bad_hostname",
        "-bad.com": "bad_hostname",
        ("a" * 64) + ".com": "bad_hostname",
        "launchvault": "bad_hostname",
    }
    for value, code in cases.items():
        expect_code(code, normalise_target, value)


# --- validation: network -------------------------------------------------


def test_dns_half_refuses_anything_not_public():
    target, resolution = validate_target("Launchvault.ca", fake_resolver)
    assert target.hostname == "launchvault.ca" and resolution.addresses == [PUBLIC]
    for host in ("sneaky.testsite.com", "mixed.testsite.com", "mapped.testsite.com",
                 "cgnat.testsite.com", "metadata.testsite.com"):
        expect_code("non_public_address", validate_target, host, fake_resolver)
    expect_code("dns_failed", validate_target, "nowhere.testsite.com", fake_resolver)
    expect_code("dns_failed", validate_target, "silent.testsite.com", lambda _h: [])


def test_every_request_url_goes_through_the_gate():
    resolution = check_url("https://shop.testsite.com/a?b=c", fake_resolver)
    assert resolution.hostname == "shop.testsite.com" and resolution.addresses == [PUBLIC]
    expect_code("ip_literal", check_url, "http://169.254.169.254/latest/meta-data/", fake_resolver)
    expect_code("bad_scheme", check_url, "file:///etc/passwd", fake_resolver)
    expect_code("has_port", check_url, "https://shop.testsite.com:6379/", fake_resolver)
    expect_code("non_public_address", check_url, "https://sneaky.testsite.com/", fake_resolver)


def test_pinning_closes_the_rebinding_gap():
    """The actual TOCTOU this whole module exists to close: an answer that
    changes between the check and the connection. Proven here without any
    real network access -- `pinned()` patches socket.getaddrinfo itself, so
    calling it directly is enough to prove the connection would have used
    the checked address, not a fresh (possibly rebound) lookup."""
    import socket

    # Unpinned: the real resolver would run. We don't call it (no network in
    # this test file), we only prove nothing is pinned yet.
    assert not getattr(validation._pin_local, "map", None)

    with validation.pinned("rebind.testsite.com", PUBLIC):
        infos = socket.getaddrinfo("rebind.testsite.com", 443)
        assert infos == [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (PUBLIC, 443))]
        # A different, unrelated hostname pinned on the same thread must not
        # bleed into this one -- each pin is keyed by its own hostname.
        with validation.pinned("other.testsite.com", "203.0.113.9"):
            assert socket.getaddrinfo("rebind.testsite.com", 443)[0][4] == (PUBLIC, 443)
            assert socket.getaddrinfo("other.testsite.com", 80)[0][4] == ("203.0.113.9", 80)
        # Restored, not left dangling, once the inner block exits.
        assert "other.testsite.com" not in validation._pin_local.map

    # And once the outer block exits, nothing is pinned at all -- a lookup
    # for a real hostname now falls through to the real resolver again.
    assert "rebind.testsite.com" not in getattr(validation._pin_local, "map", {})


# --- the crawler, against a fake network ---------------------------------


class FakeResponse:
    def __init__(self, status: int = 200, body: bytes = b"", headers: dict | None = None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def iter_content(self, size: int):
        for i in range(0, len(self._body), size):
            yield self._body[i:i + size]

    def close(self) -> None:
        pass


class FakeNetwork:
    """Canned responses by URL, and a record of everything requested."""

    def __init__(self, routes: dict[str, FakeResponse]):
        self.routes = routes
        self.requested: list[str] = []

    def get(self, url: str, **_kwargs) -> FakeResponse:
        self.requested.append(url)
        return self.routes.get(url, FakeResponse(404, b"gone", {"content-type": "text/html"}))


HTML = {"content-type": "text/html; charset=utf-8"}
TEXT = {"content-type": "text/plain"}


@contextmanager
def fake_network(routes: dict[str, FakeResponse]):
    net = FakeNetwork(routes)
    saved = (scraper.requests, validation.system_resolver, scraper.CRAWL_DELAY)
    scraper.requests = types.SimpleNamespace(get=net.get,
                                             RequestException=real_requests.RequestException)
    validation.system_resolver = fake_resolver
    scraper.CRAWL_DELAY = 0
    validation.clear_cache()
    scraper._robots_cache.clear()
    scraper._last_hit.clear()
    try:
        yield net
    finally:
        scraper.requests, validation.system_resolver, scraper.CRAWL_DELAY = saved
        validation.clear_cache()
        scraper._robots_cache.clear()


def expect_scrape(code: str, fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except scraper.ScrapeError as exc:
        assert exc.code == code, f"expected {code}, got {exc.code}: {exc}"
        return
    raise AssertionError(f"expected ScrapeError {code}")


def test_a_redirect_to_a_private_address_is_never_followed():
    routes = {
        "https://shop.testsite.com/robots.txt": FakeResponse(404, b"", TEXT),
        "https://shop.testsite.com/go": FakeResponse(302, b"", {"location": "http://sneaky.testsite.com/admin"}),
    }
    with fake_network(routes) as net:
        expect_scrape("non_public_address", scraper.fetch_page, "https://shop.testsite.com/go")
        assert not any("sneaky" in u for u in net.requested), net.requested


def test_robots_txt_is_honoured_on_every_hop():
    routes = {
        "https://shop.testsite.com/robots.txt": FakeResponse(200, b"User-agent: *\nDisallow: /login\n", TEXT),
        "https://shop.testsite.com/account": FakeResponse(302, b"", {"location": "/login"}),
    }
    with fake_network(routes) as net:
        expect_scrape("robots", scraper.fetch_page, "https://shop.testsite.com/login")
        expect_scrape("robots", scraper.fetch_page, "https://shop.testsite.com/account")
        assert "https://shop.testsite.com/login" not in net.requested, net.requested


def test_a_broken_robots_txt_means_disallow_everything():
    routes = {"https://shop.testsite.com/robots.txt": FakeResponse(503, b"down", TEXT)}
    with fake_network(routes) as net:
        expect_scrape("robots", scraper.fetch_page, "https://shop.testsite.com/")
        assert net.requested == ["https://shop.testsite.com/robots.txt"], net.requested


def test_bodies_are_capped_and_redirect_loops_stop():
    routes = {
        "https://shop.testsite.com/robots.txt": FakeResponse(404, b"", TEXT),
        "https://shop.testsite.com/big": FakeResponse(200, b"x" * 5000, HTML),
        "https://shop.testsite.com/loop": FakeResponse(302, b"", {"location": "/loop"}),
        "https://shop.testsite.com/file": FakeResponse(200, b"%PDF", {"content-type": "application/pdf"}),
    }
    with fake_network(routes):
        expect_scrape("too_large", scraper._http_get, "https://shop.testsite.com/big",
                      robots=False, max_bytes=1000)
        expect_scrape("redirect_loop", scraper.fetch_page, "https://shop.testsite.com/loop")
        expect_scrape("not_html", scraper.fetch_page, "https://shop.testsite.com/file")


def test_a_whole_crawl_reads_what_it_may_and_reports_what_it_skipped():
    home = (b'<html><head><title>Shop</title></head><body>'
            b'<a href="/about">About</a><a href="/login">Log in</a>'
            b'<a href="/report.pdf">PDF</a><a href="https://elsewhere.com/">Elsewhere</a>'
            b'</body></html>')
    page = b"<html><head><title>Page</title></head><body><h1>Page</h1></body></html>"
    sitemap = (b'<?xml version="1.0" encoding="UTF-8"?>'
               b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               b'<url><loc>https://shop.testsite.com/pricing</loc></url></urlset>')
    routes = {
        "https://shop.testsite.com/robots.txt": FakeResponse(
            200, b"User-agent: *\nDisallow: /login\nSitemap: https://shop.testsite.com/sitemap.xml\n", TEXT),
        "https://shop.testsite.com/": FakeResponse(200, home, HTML),
        "https://shop.testsite.com/sitemap.xml": FakeResponse(200, sitemap, {"content-type": "application/xml"}),
        "https://shop.testsite.com/pricing": FakeResponse(200, page, HTML),
        "https://shop.testsite.com/about": FakeResponse(200, page, HTML),
    }
    report = scraper.CrawlReport()
    with fake_network(routes) as net:
        signals = scraper.crawl("shop.testsite.com", max_pages=10, report=report)

    read = sorted(s.url for s in signals)
    assert read == ["https://shop.testsite.com/", "https://shop.testsite.com/about",
                    "https://shop.testsite.com/pricing"], read
    outcomes = {p["url"]: p["outcome"] for p in report.pages}
    assert outcomes["https://shop.testsite.com/login"] == "robots", outcomes
    assert report.robots["outcome"] == "parsed" and "Disallow: /login" in report.robots["rules"]
    assert report.same_site_urls == 1 and report.base_url == "https://shop.testsite.com"
    for never in ("https://shop.testsite.com/login", "https://shop.testsite.com/report.pdf",
                  "https://elsewhere.com/"):
        assert never not in net.requested, (never, net.requested)
    assert net.requested.count("https://shop.testsite.com/") == 1, "homepage fetched twice"


def test_sitemaps_parse_with_no_optional_parser_including_indexes_and_gzip():
    index = (b'<?xml version="1.0" encoding="UTF-8"?>'
             b'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             b'<sitemap><loc> https://shop.testsite.com/pages.xml </loc></sitemap></sitemapindex>')
    children, urls = scraper._sitemap_locs(index)
    assert children == ["https://shop.testsite.com/pages.xml"] and urls == [], (children, urls)

    latin1 = (b'<?xml version="1.0" encoding="ISO-8859-1"?>'
              b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              b'<url><loc>https://shop.testsite.com/caf\xe9</loc></url></urlset>')
    children, urls = scraper._sitemap_locs(gzip.compress(b"\n  " + latin1))
    assert children == [] and urls == ["https://shop.testsite.com/caf\u00e9"], urls


# --- what the AI step is sent --------------------------------------------


def test_the_ai_step_gets_one_item_per_distinct_finding():
    flags = [
        Flag(check="missing_canonical", summary="No canonical on /", layer="search",
             severity="low", page_url="https://s.com/", evidence=["no <link rel=canonical>"]),
        Flag(check="missing_canonical", summary="No canonical on /about", layer="search",
             severity="medium", page_url="https://s.com/about"),
        Flag(check="generic_copy", summary="Filler phrases", layer="craft",
             severity="medium", page_url="https://s.com/", evidence=["Elevate your workflow"]),
    ]
    groups = group_flags(flags)
    assert [len(g) for g in groups] == [2, 1]
    item = explanation_payload(groups[0])
    assert item["layer"] == "search" and item["check"] == "missing_canonical"
    assert item["occurrences"] == 2 and item["pages_affected"] == 2
    assert item["severity"] == "medium", "the worst severity in the group should be sent"
    assert item["example_pages"] == ["/", "/about"]
    assert set(item) == {"layer", "check", "severity", "summary", "occurrences",
                         "pages_affected", "example_pages", "evidence"}


class _Message:
    def __init__(self, text: str, stop: str = "end_turn"):
        self.content = [types.SimpleNamespace(type="text", text=text)]
        self.stop_reason = stop
        self.usage = types.SimpleNamespace(input_tokens=100, output_tokens=50)
        self.model = "claude-haiku-4-5-20251001"
        self._request_id = "req_test"


def test_ai_usage_is_counted_even_when_a_batch_is_unusable():
    six = json.dumps([{"why": f"w{i}", "fix": f"f{i}"} for i in range(6)])
    replies = [_Message(six), _Message("[]", stop="refusal"), _Message("not json at all")]
    fake = types.SimpleNamespace(messages=types.SimpleNamespace(create=lambda **_kw: replies.pop(0)))
    saved = ai_explain._client
    ai_explain._client = fake
    try:
        written, usage = ai_explain.explain_flags([{"layer": "search", "check": "x"}] * 13)
    finally:
        ai_explain._client = saved

    assert len(written) == 13
    assert all(w.get("why") for w in written[:6]) and all(w == {} for w in written[6:])
    assert usage.calls == 3 and usage.failed_batches == 2, usage
    assert usage.input_tokens == 300 and usage.output_tokens == 150
    assert usage.resolved_model == "claude-haiku-4-5-20251001"
    assert usage.cost_usd > 0 and len(usage.request_ids) == 3
    assert any("declined" in e for e in usage.errors), usage.errors


def test_trace_details_can_reuse_the_stage_field_names():
    # robots.txt's detail carries its own status and ms; that used to crash run_scan.
    from app.pipeline import Trace
    trace = Trace()
    trace.record('robots', 'ok', 5, status=200, ms=12, url='https://s.com/robots.txt')
    trace.add('rules', 'ok', 0.0, stage='not a clash', status='also fine')
    stages = trace.as_json()['stages']
    assert stages[0]['status'] == 'ok' and stages[0]['ms'] == 5
    assert stages[0]['detail'] == {'status': 200, 'ms': 12, 'url': 'https://s.com/robots.txt'}
    assert stages[1]['stage'] == 'rules' and stages[1]['detail']['stage'] == 'not a clash'


def test_robots_follows_rfc_9309_on_the_file_that_exposed_the_bug():
    # launchvault.ca's robots.txt shape, from Test #1. urllib.robotparser ended the
    # group at the blank line and let `Allow: /` win; RFC 9309 does neither.
    from app.robots import Robots
    lines = ["User-agent: *", "Allow: /", "Allow: /features", "Allow: /pricing", "",
             "Disallow: /dashboard", "Disallow: /login", "Disallow: /signup", "Disallow: /api/",
             "", "Sitemap: https://launchvault.ca/sitemap.xml"]
    robots = Robots.parse(chr(10).join(lines))
    ua = "FIGBot/0.2 (+https://fig.tools/bot)"
    verdicts = {p: robots.allowed(ua, "https://launchvault.ca" + p) for p in
                ("/", "/features", "/login", "/signup", "/login/help", "/dashboard",
                 "/api/v1/x", "/robots.txt")}
    assert verdicts == {"/": True, "/features": True, "/login": False, "/signup": False,
                        "/login/help": False, "/dashboard": False, "/api/v1/x": False,
                        "/robots.txt": True}, verdicts
    assert robots.sitemaps == ["https://launchvault.ca/sitemap.xml"]
    assert "Disallow: /login" in robots.describe(ua)


def test_robots_groups_wildcards_and_ties():
    from app.robots import Robots
    text = chr(10).join([
        "# a comment", "User-agent: googlebot", "Disallow: /", "",
        "User-agent: FIGBot", "User-agent: otherbot", "Disallow: /private",
        "Allow: /private/public", "Disallow: /*.pdf$", "Allow: /tie", "Disallow: /tie", "",
        "User-agent: *", "Disallow: /everyone-else",
    ])
    robots = Robots.parse(text)
    fig = "FIGBot/0.2"
    ok = lambda p: robots.allowed(fig, "https://s.com" + p)   # noqa: E731
    assert ok("/") and ok("/everyone-else"), "a group naming the crawler replaces the * group"
    assert not ok("/private/x") and ok("/private/public/y"), "longest match wins"
    assert not ok("/files/report.pdf") and ok("/files/report.pdf?v=2"), "$ anchors the end"
    assert ok("/tie"), "Allow wins a tie"
    assert robots.allowed("SomeOtherBot/1.0", "https://s.com/everyone-else") is False
    assert Robots(disallow_all=True).allowed(fig, "https://s.com/") is False
    assert Robots(allow_all=True).allowed(fig, "https://s.com/anything") is True


def test_empty_blocks_are_not_sections_and_question_headings_count_as_a_faq():
    from app.rules.checks import run_all_checks
    legal = ("<html><head><title>Terms</title></head><body>"
             "<header><nav><a href='/'>Home</a></nav></header>"
             "<section><h1>Acceptable Use</h1><p>" + "words " * 40 + "</p></section>"
             "<footer><p>Product links and legal links here</p></footer>"
             "<section class=''></section>"
             "</body></html>")
    signal = scraper.parse_html("https://s.com/acceptable-use", legal)
    assert [s.tag for s in signal.sections] == ["header", "section", "footer"], signal.sections
    assert [s.index for s in signal.sections] == [0, 1, 2]
    assert "section_order" not in {f.check for f in run_all_checks(signal)}

    home = ("<html><head><title>Home</title></head><body>"
            "<section id='faq'><h2>Questions, answered</h2>"
            "<h3>What is it?</h3><p>A thing.</p><h3>Who is it for?</h3><p>People.</p></section>"
            # Long enough (250+ words) that check_faq would fire without the fix.
            "<section><h2>About</h2><p>" + "detail " * 260 + "</p></section>"
            "</body></html>")
    signal = scraper.parse_html("https://s.com/", home)
    assert signal.has_faq_block
    assert "no_answerable_questions" not in {f.check for f in run_all_checks(signal)}


# --- the WordPress adapter, against a fake WordPress REST API ------------


class FakeWPResponse:
    def __init__(self, status: int = 200, body=None, text: str = ""):
        self.status_code = status
        self._body = body
        self.text = text or (json.dumps(body) if body is not None else "")

    def json(self):
        if self._body is None:
            raise ValueError("no json body")
        return self._body


class FakeWordPress:
    """Canned responses keyed by (method, path); records every call made so
    a test can assert a refusal never touched the network at all."""

    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []
        self.reject_auth = False
        self.me = {"name": "Jamie Editor", "capabilities": {"edit_posts": True}}
        self.posts_by_slug: dict[str, dict] = {}
        self.updates: dict[int, dict] = {}

    def _path(self, url: str) -> str:
        return url.split("/wp-json/", 1)[-1]

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(("GET", self._path(url), params))
        if self.reject_auth:
            return FakeWPResponse(401, text="unauthorized")
        path = self._path(url)
        if path == "wp/v2/users/me":
            return FakeWPResponse(200, self.me)
        if path == "wp/v2/posts":
            slug = (params or {}).get("slug")
            post = self.posts_by_slug.get(slug)
            return FakeWPResponse(200, [post] if post else [])
        if path == "wp/v2/pages":
            return FakeWPResponse(200, [])
        return FakeWPResponse(404, text="not found")

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append(("POST", self._path(url), json))
        if self.reject_auth:
            return FakeWPResponse(401, text="unauthorized")
        post_id = int(self._path(url).rsplit("/", 1)[-1])
        self.updates[post_id] = json
        return FakeWPResponse(200, {"id": post_id, **(json or {})})


@contextmanager
def fake_wordpress():
    wp = FakeWordPress()
    saved = wordpress.httpx
    wordpress.httpx = types.SimpleNamespace(get=wp.get, post=wp.post, HTTPError=real_requests.RequestException)
    try:
        yield wp
    finally:
        wordpress.httpx = saved


def test_wordpress_connection_check_is_a_real_call_not_a_format_check():
    with fake_wordpress() as wp:
        ok, detail = wordpress.test_connection("https://shop.example.com", "jamie", "abcd 1234")
        assert ok and "Jamie Editor" in detail, detail
        assert wp.calls == [("GET", "wp/v2/users/me", None)]

    with fake_wordpress() as wp:
        wp.reject_auth = True
        ok, detail = wordpress.test_connection("https://shop.example.com", "jamie", "wrong")
        assert not ok and "rejected" in detail, detail


def test_wordpress_title_fix_writes_the_drafted_title():
    with fake_wordpress() as wp:
        wp.posts_by_slug["old-title"] = {"id": 42, "content": {"raw": "<p>hi</p>"}}
        ok, message, applied = wordpress.apply_change(
            "https://shop.example.com", "jamie", "abcd1234",
            check="title_length", page_url="https://shop.example.com/blog/old-title",
            after="A properly short title")
        assert ok, message
        assert applied == "A properly short title"
        assert wp.updates[42] == {"title": "A properly short title"}


def test_wordpress_title_fix_refuses_without_drafted_text():
    with fake_wordpress() as wp:
        wp.posts_by_slug["old-title"] = {"id": 42, "content": {"raw": "<p>hi</p>"}}
        ok, message, applied = wordpress.apply_change(
            "https://shop.example.com", "jamie", "abcd1234",
            check="missing_title", page_url="https://shop.example.com/old-title", after=None)
        assert not ok and applied is None
        assert "42" not in " ".join(str(c) for c in wp.calls if c[0] == "POST"), \
            "should never have tried to write without a drafted title"


def test_settings_integration_names_match_the_frontends_static_list():
    """The workspace API's connection state is looked up by the frontend as
    `live.apis.find(a => a.name === service.name)` -- a string comparison
    between two files that don't import each other, so nothing but a test
    catches a drift. This already happened for real once (Search Console
    said "Search Console" on one side, "Google Search Console" on the
    other, and simply never matched) and is checked here for every service
    that has a real Connect button wired in Settings: connecting would have
    kept showing "Not connected" forever, no matter how it actually went."""
    frontend_src = (ROOT / "frontend" / "app" / "app" / "settings" / "page.tsx").read_text(encoding="utf-8")
    start = frontend_src.index("const services: Service[] = [")
    end = frontend_src.index("];", start)
    frontend_names = set(re.findall(r'name:\s*"([^"]+)"', frontend_src[start:end]))

    backend_names = {row["name"] for row in pages._api_rows(None, [])}

    wired_in_frontend = {"Google Analytics", "Google Search Console", "WordPress", "Shopify",
                        "Webflow", "Wix"}
    missing_from_frontend = wired_in_frontend - frontend_names
    assert not missing_from_frontend, \
        f"expected a static row for {missing_from_frontend} in settings/page.tsx"
    missing_from_backend = wired_in_frontend - backend_names
    assert not missing_from_backend, \
        f"_api_rows() has no matching row for {missing_from_backend} -- Connect would never show as connected"


def test_wordpress_promotes_the_first_h2_to_h1():
    html, changed = wordpress._promote_first_heading(
        "<p>intro</p><h2 class=\"a\">Section</h2><p>more</p>", from_level=2, to_level=1)
    assert changed
    assert html == "<p>intro</p><h1 class=\"a\">Section</h1><p>more</p>"

    html, changed = wordpress._promote_first_heading("<p>no headings here</p>", from_level=2, to_level=1)
    assert not changed and html == "<p>no headings here</p>"


def test_wordpress_demotes_every_h1_after_the_first():
    html, changed = wordpress._demote_extra_h1s(
        "<h1>Real title</h1><p>x</p><h1 id=\"b\">Duplicate</h1><p>y</p><h1>Another</h1>")
    assert changed
    assert html.count("<h1") == 1 and html.count("<h2") == 2
    assert "<h1>Real title</h1>" in html
    assert "<h2 id=\"b\">Duplicate</h2>" in html


def test_wordpress_heading_fix_round_trips_through_the_fake_api():
    with fake_wordpress() as wp:
        wp.posts_by_slug["guide"] = {"id": 7, "content": {"raw": "<h2>Only heading</h2>"}}
        ok, message, applied = wordpress.apply_change(
            "https://shop.example.com", "jamie", "abcd1234",
            check="missing_h1", page_url="https://shop.example.com/guide", after=None)
        assert ok, message
        assert applied == "<h1>Only heading</h1>"
        assert wp.updates[7] == {"content": "<h1>Only heading</h1>"}


def test_wordpress_refuses_finding_types_its_rest_api_cannot_reach():
    with fake_wordpress() as wp:
        for check in wordpress.NOT_EXPOSED_BY_CORE:
            ok, message, applied = wordpress.apply_change(
                "https://shop.example.com", "jamie", "abcd1234",
                check=check, page_url="https://shop.example.com/any-page", after="ignored")
            assert not ok and applied is None, (check, message)
        assert wp.calls == [], f"a refusal should never touch the network: {wp.calls}"


def test_wordpress_refuses_alt_text_with_nothing_drafted():
    with fake_wordpress() as wp:
        wp.posts_by_slug["guide"] = {"id": 7, "content": {"raw": "<img>"}}
        ok, message, applied = wordpress.apply_change(
            "https://shop.example.com", "jamie", "abcd1234",
            check="missing_alt", page_url="https://shop.example.com/guide", after=None)
        assert not ok and applied is None


def test_wordpress_refuses_when_no_matching_post_is_found():
    with fake_wordpress() as wp:
        ok, message, applied = wordpress.apply_change(
            "https://shop.example.com", "jamie", "abcd1234",
            check="missing_title", page_url="https://shop.example.com/nowhere", after="New title")
        assert not ok and "couldn't find" in message


# --- Search Console's pure response-shaping and site-matching ------------


def test_search_console_shapes_daily_rows_sorted_by_date():
    rows = [
        {"keys": ["2026-09-03"], "clicks": 12.0, "impressions": 340.0},
        {"keys": ["2026-09-01"], "clicks": 8.0, "impressions": 210.0},
        {"keys": ["2026-09-02"], "clicks": 0, "impressions": 90.0},
    ]
    daily = search_console._shape_daily(rows)
    assert [d["date"] for d in daily] == ["2026-09-01", "2026-09-02", "2026-09-03"]
    assert daily[0] == {"date": "2026-09-01", "clicks": 8, "impressions": 210}


def test_search_console_shapes_queries_sorted_by_clicks_descending():
    rows = [
        {"keys": ["small brand"], "clicks": 3.0, "impressions": 40.0, "position": 8.2},
        {"keys": ["big keyword"], "clicks": 55.0, "impressions": 900.0, "position": 3.14159},
        {"keys": ["zero clicks"], "clicks": 0, "impressions": 12.0, "position": 40.0},
    ]
    queries = search_console._shape_queries(rows)
    assert [q["query"] for q in queries] == ["big keyword", "small brand", "zero clicks"]
    assert queries[0]["position"] == 3.1, "position rounds to one decimal"


def test_search_console_picks_the_matching_verified_property():
    urls = ["https://otherbrand.com/", "sc-domain:launchvault.ca", "https://third.com/"]
    assert search_console._pick_site_url(urls, "launchvault.ca") == "sc-domain:launchvault.ca"
    assert search_console._pick_site_url(urls, "www.launchvault.ca") == "sc-domain:launchvault.ca"

    urls2 = ["https://launchvault.ca/", "https://other.com/"]
    assert search_console._pick_site_url(urls2, "launchvault.ca") == "https://launchvault.ca/"

    # No exact match: falls back to the first verified property (no picker UI yet).
    urls3 = ["https://first-seen.com/", "https://second.com/"]
    assert search_console._pick_site_url(urls3, "launchvault.ca") == "https://first-seen.com/"

    assert search_console._pick_site_url([], "launchvault.ca") is None


def _run_lifespan_and_capture_logs(*, https=True, **config_overrides):
    """Drives app.main.lifespan() with everything that touches a real DB,
    the job queue or the scheduler mocked out, and returns every record the
    "fig" logger emitted. Isolated enough to run with no network, no DB.

    `_https` is computed once at import time from PUBLIC_URL, not
    re-evaluated per request, so it has to be patched directly rather than
    through a config override -- this test suite's own PUBLIC_URL is the
    local default, so without this every "production" case here would
    silently take the "local dev, no check needed" branch instead."""
    import asyncio
    import logging
    from contextlib import ExitStack
    from unittest.mock import patch

    from app import config as app_config, main as app_main

    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    async def run():
        with ExitStack() as stack:
            stack.enter_context(patch.object(app_main, "init_db"))
            stack.enter_context(patch.object(app_main, "start_workers"))
            stack.enter_context(patch.object(app_main, "stop_workers"))
            stack.enter_context(patch.object(app_main.scheduler, "start"))
            stack.enter_context(patch.object(app_main.scheduler, "stop"))
            stack.enter_context(patch.object(app_main, "_https", https))
            for key, value in config_overrides.items():
                stack.enter_context(patch.object(app_config, key, value))
            handler = Capture()
            logging.getLogger("fig").addHandler(handler)
            try:
                async with app_main.lifespan(object()):
                    pass
            finally:
                logging.getLogger("fig").removeHandler(handler)
    asyncio.run(run())
    return [r.getMessage() for r in records]


def test_oauth_redirect_uri_still_localhost_in_production_is_logged_as_an_error():
    """Exactly the bug that shipped once already: SHOPIFY_CLIENT_ID/SECRET
    were live on Render (so SHOPIFY_OAUTH_ENABLED read True and /health
    looked fine) but SHOPIFY_OAUTH_REDIRECT_URI was never set alongside
    them, so the redirect Shopify actually received was still the localhost
    default -- a real connection attempt would have been rejected outright.
    This is the startup check that catches it for any of the three OAuth
    platforms, the next time it happens."""
    messages = _run_lifespan_and_capture_logs(
        GOOGLE_OAUTH_ENABLED=False,
        SHOPIFY_OAUTH_ENABLED=True,
        SHOPIFY_OAUTH_REDIRECT_URI="http://localhost:8000/oauth/shopify/callback",
        WEBFLOW_OAUTH_ENABLED=False,
    )
    hit = [m for m in messages if "SHOPIFY_OAUTH_REDIRECT_URI" in m]
    assert hit, f"expected an error naming SHOPIFY_OAUTH_REDIRECT_URI, got: {messages}"


def test_wix_redirect_uri_still_localhost_in_production_is_also_caught():
    """Wix's postInstallationUrl isn't allowlisted the way the other three's
    redirect_uri is, but it's still a real HTTPS route the backend has to
    serve once deployed -- the same class of mistake is just as possible."""
    messages = _run_lifespan_and_capture_logs(
        GOOGLE_OAUTH_ENABLED=False,
        SHOPIFY_OAUTH_ENABLED=False,
        WEBFLOW_OAUTH_ENABLED=False,
        WIX_OAUTH_ENABLED=True,
        WIX_OAUTH_REDIRECT_URI="http://localhost:8000/oauth/wix/callback",
    )
    hit = [m for m in messages if "WIX_OAUTH_REDIRECT_URI" in m]
    assert hit, f"expected an error naming WIX_OAUTH_REDIRECT_URI, got: {messages}"


def test_a_correctly_set_redirect_uri_logs_nothing():
    """The check must not cry wolf on a genuinely correct deployment."""
    messages = _run_lifespan_and_capture_logs(
        GOOGLE_OAUTH_ENABLED=True,
        GOOGLE_OAUTH_REDIRECT_URI="https://fig-ai-backend.onrender.com/oauth/google/callback",
        SHOPIFY_OAUTH_ENABLED=True,
        SHOPIFY_OAUTH_REDIRECT_URI="https://fig-ai-backend.onrender.com/oauth/shopify/callback",
        WEBFLOW_OAUTH_ENABLED=True,
        WEBFLOW_OAUTH_REDIRECT_URI="https://fig-ai-backend.onrender.com/oauth/webflow/callback",
        WIX_OAUTH_ENABLED=True,
        WIX_OAUTH_REDIRECT_URI="https://fig-ai-backend.onrender.com/oauth/wix/callback",
    )
    assert not [m for m in messages if "OAUTH_REDIRECT_URI" in m], messages


def test_a_disabled_platform_is_not_checked_at_all():
    """An unconfigured platform's URI is still the localhost default --
    that's expected and must not be flagged."""
    messages = _run_lifespan_and_capture_logs(
        GOOGLE_OAUTH_ENABLED=False,
        SHOPIFY_OAUTH_ENABLED=False,
        WEBFLOW_OAUTH_ENABLED=False,
        WIX_OAUTH_ENABLED=False,
    )
    assert not [m for m in messages if "OAUTH_REDIRECT_URI" in m], messages


def test_a_localhost_redirect_uri_is_correct_in_local_dev_and_not_flagged():
    """The same localhost URI that's an error in production is exactly
    right when the backend itself is running locally (PUBLIC_URL is http)."""
    messages = _run_lifespan_and_capture_logs(
        https=False,
        SHOPIFY_OAUTH_ENABLED=True,
        SHOPIFY_OAUTH_REDIRECT_URI="http://localhost:8000/oauth/shopify/callback",
    )
    assert not [m for m in messages if "OAUTH_REDIRECT_URI" in m], messages


def test_sentry_excludes_the_deliberate_501_from_error_reporting():
    """app/content.py:draft() deliberately returns 501 for a feature that
    isn't built yet (CLAUDE.md: "FIG does not write the copy yet"). Sentry's
    FastAPI/Starlette integrations report every 5xx as an issue by default,
    which turned that expected, permanent refusal into a Sentry issue every
    time anything -- including the real end-to-end test script's own check
    that it still correctly refuses -- hit it (this really happened: issue
    FIG-AI-BACKEND-2). A real 500/502/503 must still be reported."""
    import importlib
    from unittest.mock import MagicMock, patch

    from app import config as app_config, main as app_main

    fake_init = MagicMock()
    try:
        with patch.object(app_config, "SENTRY_DSN", "https://fake@fake.ingest.sentry.io/1"), \
             patch("sentry_sdk.init", fake_init):
            importlib.reload(app_main)
        assert fake_init.called, "sentry_sdk.init() should run when SENTRY_DSN is set"
        integrations = fake_init.call_args.kwargs["integrations"]
        assert len(integrations) == 2
        for integ in integrations:
            codes = integ.failed_request_status_codes
            assert 501 not in codes, "the deliberate 'not built yet' refusal must not be reported"
            assert 500 in codes and 503 in codes, "real server errors must still be reported"
    finally:
        importlib.reload(app_main)  # restore real state: SENTRY_DSN="" again


TESTS = [fn for name, fn in list(globals().items()) if name.startswith("test_") and callable(fn)]

if __name__ == "__main__":
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception:                          # noqa: BLE001
            failed += 1
            print(f"[FAIL] {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} backend tests passed.")
    sys.exit(1 if failed else 0)
