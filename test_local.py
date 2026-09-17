"""Exercises the deterministic rules engine against hand-written fake HTML —
no network access and no ANTHROPIC_API_KEY needed. Run with:

    python test_local.py

The craft checks are the taste layer: a hand-made page should stay quiet on
those. The structure/search/answers checks are hygiene, and a bare fixture
legitimately fails them — so those are asserted separately rather than
expecting silence across the board.
"""
from app.rules.checks import CHECKLIST, checklist, run_all_checks
from app.rules.sections import roles_for
from app.scraper import parse_html

GENERIC_HTML = """
<html>
<head><title>Launch Your Startup</title></head>
<body>
  <section>
    <span>01</span>
    <h3>Elevate your workflow</h3>
    <p>Streamline your process and unlock your potential with our all-in-one solution.</p>
  </section>
  <section>
    <span>02</span>
    <h3>Seamlessly integrate</h3>
    <p>Get started in minutes and supercharge your team.</p>
  </section>
  <section>
    <span>03</span>
    <h3>Built for speed and scale</h3>
    <p>Take it to the next level.</p>
  </section>
  <div class="rounded-2xl shadow-lg">Card A</div>
  <div class="rounded-2xl shadow-lg">Card B</div>
  <div class="rounded-2xl shadow-lg">Card C</div>
  <div class="rounded-2xl shadow-lg">Card D</div>
  <svg data-lucide="sparkles"></svg>
  <svg data-lucide="arrow-right"></svg>
  <svg data-lucide="zap"></svg>
  <style>
    .btn { color: #4F46E5; }
    .cta { background: #8B5CF6; }
  </style>
</body>
</html>
"""

HANDCRAFTED_HTML = """
<html lang="en">
<head>
  <title>Maria Chen -- Ceramics</title>
  <meta name="description" content="Maria Chen throws wheel-formed stoneware in a shed
  behind her house in Asheville, and sells it on Saturdays at the Haywood Street market.">
  <link rel="canonical" href="https://maria-chen.test/">
  <script type="application/ld+json">{"@type":"Person","name":"Maria Chen"}</script>
</head>
<body>
  <h1>Maria Chen</h1>
  <p>I throw pots in a shed behind my house in Asheville.</p>
  <h2>Recent work</h2>
  <div class="piece">A wide bowl, glazed in three passes.</div>
  <h2>Where to find me</h2>
  <p>Saturdays at the Haywood Street market.</p>
</body>
</html>
"""

# Pricing above the section that justifies it — the inversion the product
# leads with.
BAD_ORDER_HTML = """
<html lang="en"><head><title>Northwind</title></head>
<body>
  <section id="hero"><h1>Northwind</h1><p>Scheduling for clinics.</p>
    <a class="btn" href="#">Start free</a></section>
  <section id="pricing"><h2>Pricing</h2>
    <p>Solo $19 per month. Clinic $49 per month. Group $120 per month.</p></section>
  <section id="features"><h2>Features</h2>
    <ul><li>Online booking</li><li>Reminders</li><li>Waitlists</li>
        <li>Reports</li><li>Payments</li><li>Records</li></ul></section>
  <footer><a href="/a">A</a><a href="/b">B</a><a href="/c">C</a>
    <a href="/d">D</a><a href="/e">E</a><a href="/f">F</a></footer>
</body></html>
"""


def _triggered(flags):
    return {flag.check for flag in flags}


def _by_layer(flags, layer):
    return {f.check for f in flags if f.layer == layer}


def test_generic_html_triggers_expected_flags():
    signal = parse_html("https://example-startup.test/", GENERIC_HTML)
    triggered = _triggered(run_all_checks(signal))

    expected = {
        "component_uniformity",
        "numbered_eyebrows",
        "generic_copy",
        "default_color_palette",
        "overused_icons",
    }
    missing = expected - triggered
    assert not missing, f"expected flags did not fire: {missing} (got {triggered})"
    print(f"[PASS] generic HTML triggered: {sorted(triggered)}")


def test_handcrafted_html_stays_quiet_on_craft():
    signal = parse_html("https://maria-chen.test/", HANDCRAFTED_HTML)
    flags = run_all_checks(signal)
    craft = _by_layer(flags, "craft")
    assert not craft, f"hand-crafted HTML should not trigger craft flags, got: {craft}"
    print("[PASS] hand-crafted HTML triggered no craft flags")


def test_hygiene_layers_fire_when_head_is_bare():
    signal = parse_html("https://example-startup.test/", GENERIC_HTML)
    flags = run_all_checks(signal)
    search = _by_layer(flags, "search")
    answers = _by_layer(flags, "answers")
    assert "missing_meta_description" in search, search
    assert "no_structured_data" in answers, answers
    print(f"[PASS] search={sorted(search)} answers={sorted(answers)}")


def test_section_roles_and_order():
    signal = parse_html("https://northwind.test/", BAD_ORDER_HTML)
    roles = roles_for(signal)
    assert "pricing" in roles and "features" in roles, roles
    assert roles.index("pricing") < roles.index("features"), roles

    flags = run_all_checks(signal)
    order = [f for f in flags if f.check == "section_order"]
    assert order, f"section_order did not fire on an inverted page (roles: {roles})"
    assert any("justifies it" in f.summary for f in order), [f.summary for f in order]
    print(f"[PASS] section order: {' -> '.join(roles)}")
    print(f"       {order[0].summary}")


STATS_WITH_DOLLARS_HTML = """
<html>
<head><title>Northwind results</title></head>
<body>
  <header><h1>Northwind</h1></header>
  <section>
    <h2>Results that speak for themselves</h2>
    <ul>
      <li>Grew revenue from $50k to $120k in one year</li>
      <li>Cut support costs by $8k per quarter</li>
      <li>500+ teams onboarded</li>
    </ul>
    <a class="button" href="/case-studies">Read the case studies</a>
  </section>
  <section>
    <h2>What you get</h2>
    <p>Everything you need to run a modern support desk.</p>
  </section>
  <footer><p>Northwind Inc.</p></footer>
</body>
</html>
"""

BARE_LEGAL_PAGE_HTML = """
<html>
<head><title>Privacy Policy</title></head>
<body>
  <h1>Privacy Policy</h1>
  <p>We collect only what is needed to run this service, and nothing more
  than that. This policy explains what we collect, why, and how long we
  keep it before it is deleted from every system that holds a copy.</p>
  <h2>What we collect</h2>
  <p>Account email, hashed passwords, and the pages a signed-in user visits
  inside the product. We do not sell any of it to a third party, ever.</p>
</body>
</html>
"""


def test_a_stats_section_quoting_dollar_figures_is_not_read_as_pricing():
    """A results/stats section that happens to quote money in prose (a case
    study, a savings figure) is not a pricing table. Section role keywords
    on the heading now outrank the weak has-price-and-a-list heuristic."""
    signal = parse_html("https://northwind.test/", STATS_WITH_DOLLARS_HTML)
    roles = roles_for(signal)
    assert "pricing" not in roles, roles
    assert "stats" in roles, roles
    print(f"[PASS] stats section with dollar figures classified as: {roles}")


def test_bare_body_text_with_no_section_wrapper_is_still_attributed():
    """A legal/policy page with no <section>/<div>/<article> wrapper at all
    (bare <h1>/<p> directly under <body>) used to produce zero sections,
    silently dropping all of its text from every section-based check."""
    signal = parse_html("https://northwind.test/privacy", BARE_LEGAL_PAGE_HTML)
    assert signal.sections, "expected at least one section, got none"
    total_words = sum(s.word_count for s in signal.sections)
    assert total_words > 20, f"expected real body text attributed, got {total_words} words"
    print(f"[PASS] bare legal page attributed {total_words} words across "
          f"{len(signal.sections)} section(s)")


BLOG_CARD_HEADING_BLEED_HTML = """
<html>
<head><title>Northwind blog</title></head>
<body>
  <header><h1>Northwind blog</h1></header>
  <section class="post-grid">
    <article>
      <h2>Claude's API Pricing Beats ChatGPT Plus</h2>
      <p>A look at how usage-based pricing changes the calculus for teams.</p>
    </article>
    <article>
      <h2>Shipping Faster With Small Teams</h2>
      <p>Notes from three months of weekly releases.</p>
    </article>
    <article>
      <h2>Why We Rewrote Our Onboarding Flow</h2>
      <p>The old flow lost a third of signups before day two.</p>
    </article>
  </section>
  <footer><p>Northwind Inc.</p></footer>
</body>
</html>
"""


def test_a_card_grids_first_article_title_does_not_relabel_the_whole_section():
    """A blog/card-listing section is described by whichever heading
    `_describe_section` finds first inside it -- the first card's own
    title, not a real section label. A sentence-length title that happens
    to contain a role keyword ("...Pricing Beats...") used to relabel the
    entire grid as that role. Found on real launchvault.ca content pages."""
    signal = parse_html("https://northwind.test/blog", BLOG_CARD_HEADING_BLEED_HTML)
    roles = roles_for(signal)
    assert "pricing" not in roles, roles
    print(f"[PASS] card grid with a pricing-sounding article title classified as: {roles}")


def test_checklist_ids_are_unique_and_cover_observed_flags():
    """CHECKLIST is hand-maintained (see rules/checks.py), so the one thing
    worth guarding automatically is that it does not drift into duplicate or
    missing ids as checks change. Cross-checked against every id the fixtures
    above are already known to trigger."""
    seen: dict[str, str] = {}
    for entry in CHECKLIST:
        for check_id in entry["ids"]:
            assert check_id not in seen, f"'{check_id}' declared in two checklist entries"
            seen[check_id] = entry["title"]
    all_ids = set(seen)

    observed: set[str] = set()
    for html in (GENERIC_HTML, HANDCRAFTED_HTML, BAD_ORDER_HTML):
        signal = parse_html("https://checklist-coverage.test/", html)
        observed |= {f.check for f in run_all_checks(signal)}
    missing = observed - all_ids
    assert not missing, f"checks fire that CHECKLIST does not describe: {missing}"

    assert checklist() == CHECKLIST
    print(f"[PASS] checklist describes {len(all_ids)} check ids, "
          f"{len(observed)} observed in fixtures")


if __name__ == "__main__":
    test_generic_html_triggers_expected_flags()
    test_handcrafted_html_stays_quiet_on_craft()
    test_hygiene_layers_fire_when_head_is_bare()
    test_section_roles_and_order()
    test_a_stats_section_quoting_dollar_figures_is_not_read_as_pricing()
    test_bare_body_text_with_no_section_wrapper_is_still_attributed()
    test_a_card_grids_first_article_title_does_not_relabel_the_whole_section()
    test_checklist_ids_are_unique_and_cover_observed_flags()
    print("\nAll local rule-engine tests passed.")
