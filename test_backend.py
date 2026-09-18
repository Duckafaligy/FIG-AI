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

import gzip
import json
import sys
import traceback
import types
from contextlib import contextmanager

import requests as real_requests

from app import ai_explain, scraper, validation, wordpress
from app.pipeline import explanation_payload, group_flags
from app.rules.checks import Flag
from app.validation import ValidationError, check_url, normalise_target, validate_target

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
    assert check_url("https://shop.testsite.com/a?b=c", fake_resolver) == "shop.testsite.com"
    expect_code("ip_literal", check_url, "http://169.254.169.254/latest/meta-data/", fake_resolver)
    expect_code("bad_scheme", check_url, "file:///etc/passwd", fake_resolver)
    expect_code("has_port", check_url, "https://shop.testsite.com:6379/", fake_resolver)
    expect_code("non_public_address", check_url, "https://sneaky.testsite.com/", fake_resolver)


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
