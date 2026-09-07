"""Exercises the deterministic rules engine against hand-written fake HTML —
no network access and no ANTHROPIC_API_KEY needed. Run with:

    python test_local.py

The craft checks are the taste layer: a hand-made page should stay quiet on
those. The structure/search/answers checks are hygiene, and a bare fixture
legitimately fails them — so those are asserted separately rather than
expecting silence across the board.
"""
from app.rules.checks import run_all_checks
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


if __name__ == "__main__":
    test_generic_html_triggers_expected_flags()
    test_handcrafted_html_stays_quiet_on_craft()
    test_hygiene_layers_fire_when_head_is_bare()
    test_section_roles_and_order()
    print("\nAll local rule-engine tests passed.")
