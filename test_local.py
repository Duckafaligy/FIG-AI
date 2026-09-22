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
from app.scraper import parse_html, _strip_suspense_fallbacks

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


STREAMED_LOADING_HTML = """
<html><head><title>Northwind</title></head>
<body>
<!--$?--><template id="B:0"></template><div class="route-feedback" role="status"><span aria-hidden="true"></span><h2>Loading your page</h2><p>Getting everything ready…</p></div><!--/$-->
<script>requestAnimationFrame(function(){$RT=performance.now()});</script>
<div hidden id="S:0">
  <h1>Northwind</h1>
  <p>Scheduling software for small clinics, built by a team of two people
  who got tired of the front desk double-booking the same afternoon slot.</p>
  <h2>Pricing</h2>
  <p>Nineteen dollars a month for a solo provider, forty-nine for a clinic
  with more than one person on the schedule at the same time.</p>
</div>
</body></html>
"""


def test_a_react_streaming_loading_fallback_is_not_read_as_page_content():
    """React/Next's streaming SSR flushes a route's loading.tsx fallback
    wrapped in <!--$?-->...<!--/$--> markers, with the real content placed
    separately in a hidden container a client script swaps in once JS runs.
    A plain HTTP fetch -- this scraper, same as any crawler or answer engine
    that doesn't execute JavaScript -- used to read the fallback as if it
    were the page, putting a phantom "Loading your page" <h2> and its
    "Getting everything ready…" paragraph on every single route of FIG's own
    site (found while tuning these checks against FIG's own pages)."""
    signal = parse_html("https://northwind.test/", STREAMED_LOADING_HTML)
    assert "Loading your page" not in signal.headings, signal.headings
    assert "Getting everything ready…" not in signal.paragraphs, signal.paragraphs
    assert signal.headings == ["Northwind", "Pricing"], signal.headings
    assert signal.word_count > 25, f"expected the real hidden content to still be read, got {signal.word_count} words"
    print(f"[PASS] streaming fallback stripped, real content kept: "
          f"{signal.headings}, {signal.word_count} words")


def test_strip_suspense_fallbacks_leaves_ordinary_html_and_unterminated_markers_alone():
    """Guards the helper directly: nested boundaries collapse to one removal,
    two separate boundaries both go, and a truncated/malformed document (no
    matching close) is returned untouched rather than risking real content."""
    nested = "X<!--$?--><!--$?-->inner<!--/$--><!--/$-->Y"
    assert _strip_suspense_fallbacks(nested) == "XY", _strip_suspense_fallbacks(nested)

    two_pairs = "A<!--$?-->f1<!--/$-->B<!--$?-->f2<!--/$-->C"
    assert _strip_suspense_fallbacks(two_pairs) == "ABC", _strip_suspense_fallbacks(two_pairs)

    unterminated = "A<!--$?-->never closes"
    assert _strip_suspense_fallbacks(unterminated) == unterminated

    plain = "<html><body>hello</body></html>"
    assert _strip_suspense_fallbacks(plain) == plain
    print("[PASS] suspense-fallback stripping: nested, sequential, unterminated and plain HTML")


LONG_POLICY_HTML = """
<html>
<head><title>Terms of Service</title></head>
<body>
  <h1>Terms of Service</h1>
  <h2>Who this agreement is with</h2>
  <p>These terms are an agreement between you and the company that runs this
  service. By creating an account or otherwise using the service, you agree
  to them. If you do not agree, you should not use the service at all, and
  should tell us so we can close any account you may have opened already.
  This section also explains who counts as an authorized user of an account
  opened on behalf of an organization rather than an individual person.</p>
  <h2>What the service does</h2>
  <p>The service reads the public pages of a website you point it at and
  reports back a set of patterns it found there, along with a plain
  explanation of why each pattern was flagged and a specific suggestion for
  how you might change it if you choose to make that change yourself. It
  does not write new copy for you, and it does not publish anything to your
  site without you reviewing and approving the specific change first.</p>
  <h2>Paying for the service</h2>
  <p>New accounts start with a free trial that does not require a card.
  Once the trial ends, continuing to use the paid parts of the service
  requires an active subscription, billed monthly in advance to whatever
  payment method you provide when you decide to subscribe for real. Prices
  are shown before you pay, and you can cancel the subscription at any time
  from your account settings without needing to contact anyone by email.</p>
  <h2>Ending your use of the service</h2>
  <p>You may stop using the service and cancel your subscription at any
  time, and we may suspend or end an account that breaks these terms,
  after making a reasonable effort to tell you why and give you a chance
  to fix it first wherever doing so is practical for everyone involved. An
  account that is ended this way keeps no special claim to a refund beyond
  whatever the separate refund policy already promises to every customer.</p>
  <h2>Which law applies</h2>
  <p>This agreement is governed by the law of the place stated in the
  full published terms, without regard to that place's conflict-of-laws
  rules, and any dispute is heard in the courts of that same place unless
  a mandatory consumer-protection law where you live says otherwise applies.
  Nothing here limits a right that the law in your own country will not
  allow a company to sign away, whatever this document otherwise says.</p>
</body>
</html>
"""

THIN_FLAT_SECTIONS_HTML = """
<html><head><title>Product</title></head><body>
<h1>Product</h1>
<h2>Fast</h2><p>It loads quickly every time you open it.</p>
<h2>Secure</h2><p>Your data stays protected, always and everywhere.</p>
<h2>Simple</h2><p>Anyone on the team can pick it up fast.</p>
<h2>Flexible</h2><p>Works however your team already operates today.</p>
</body></html>
"""


def test_flat_typography_spares_a_real_document_but_still_catches_a_thin_template():
    """A single-topic reference document -- one h1, a flat run of h2 clauses,
    each carrying a real paragraph -- reads as one h1 + mostly-h2 the same way
    a templated row of thin cards does, but it isn't the same pattern: there
    is real, substantial, differentiated content under every heading. FIG's
    own privacy and terms pages were tripping this before the words-per-
    heading exemption. A page that is genuinely just short, near-identical
    blurbs under a repeated heading level -- no real content, nothing to
    differentiate -- still has to fire, or the check is pointless."""
    document = parse_html("https://example.test/terms", LONG_POLICY_HTML)
    assert "flat_typography" not in _triggered(run_all_checks(document)), \
        "a real long-form document with one h1 and substantial h2 sections should not be flagged"

    template = parse_html("https://example.test/product", THIN_FLAT_SECTIONS_HTML)
    assert "flat_typography" in _triggered(run_all_checks(template)), \
        "a thin row of near-identical h2 blurbs should still be flagged"
    print("[PASS] flat_typography: quiet on a real document, still fires on thin template sections")


SHORT_UTILITY_HTML = """
<html><head><title>Sign in</title></head><body>
<h1>Pick up where you left off</h1>
<p>Sign in to see your sites, findings and scan history in one place, kept
exactly where you left them the last time you visited this workspace, so
nothing has to be reconstructed from memory or dug up out of an old email
thread that has since been buried under a hundred other unrelated messages.</p>
<h3>A fix for every finding</h3>
<p>Each one says where it is, why it matters and what to change about it,
written in plain language rather than a raw rule name or an error code that
would mean nothing to someone reading it for the first time on a Monday
morning before the rest of the team has even had a chance to log in yet.</p>
<h3>Reads any public site</h3>
<p>Whatever the site is built with, the service checks the pages a real
visitor can actually see when they load the page in an ordinary browser,
not a hidden admin view or a staging environment nobody else can reach,
because a finding that nobody outside the company can see is not useful.</p>
<h3>History and re-scans</h3>
<p>Run a check again after making a change and see exactly what moved, and
by how much, compared with the version you started from a week earlier, so
progress is something you can point at in a meeting rather than something
you have to take somebody's word for because nobody wrote the old numbers down.</p>
<h3>Built for people, not committees</h3>
<p>One person can sign up, connect a site, and see something useful within
a couple of minutes, without first having to invite a team or fill out a
form describing what department they work in or who their manager happens
to be this quarter, because most of the people who try this are working alone.</p>
</body></html>
"""

LONG_CONTENT_HTML = """
<html><head><title>Guide</title></head><body>
<h1>Choosing a scheduling tool for a small clinic</h1>
<p>Most small clinics start with a paper calendar and a phone line, and that
works fine right up until two people try to book the same slot on the same
afternoon. The first real sign a clinic has outgrown that setup is not lost
revenue, it is the fifteen minutes at the front desk every morning spent
untangling who was actually supposed to be seen first, and in what order,
before the first patient of the day has even had a chance to sit down and
take off their coat, let alone explain what they are actually there for.</p>
<p>A scheduling tool solves that specific problem, and not much else, so it
is worth being honest about what it will and will not fix. It will stop the
double-booking. It will not fix a clinic that is chronically understaffed
for the number of patients it is trying to see, and it will not make a slow
intake process faster on its own, though a good one can shorten the wait by
cutting down on the paperwork a patient has to fill out while they sit there.</p>
<p>The things worth checking before picking one are boring on purpose: does
it handle recurring appointments cleanly, does it send reminders without
needing a staff member to trigger them by hand every single day, and does
it let a patient reschedule themselves without a phone call in the middle
of a shift. Most tools claim all three. Fewer of them are pleasant to use
once the trial period ends and the staff using it every day stop noticing
the marketing screenshots and start noticing the five extra clicks it takes
to do the one thing they do fifty times before lunch, and that is where the
real difference between one tool and the next actually shows up in practice,
long after the sales call that convinced someone to sign the contract.</p>
<p>None of this is a reason to avoid switching. It is a reason to trial two
tools for a real week rather than a demo afternoon, with the actual front
desk staff typing into it between real patients, because that is the only
way anyone finds out whether the five extra clicks are really there at all,
and whether the people doing the work every day would actually pick it
themselves if nobody from management was in the room watching them decide.</p>
</body></html>
"""


def test_faq_check_ignores_short_pages_but_still_catches_long_thin_content():
    """A page under ~400 words is far more likely a utility page (sign-in,
    contact, a settings screen) than content competing to be found or quoted
    -- FIG's own 264-word sign-in and 380-word sign-up pages were both
    tripping this at the old 250-word threshold. A genuinely long page
    (400+ words) with real prose and still no FAQ or question heading has to
    keep firing, or the check stops meaning anything on content that matters."""
    short = parse_html("https://example.test/signin", SHORT_UTILITY_HTML)
    assert 250 <= short.word_count < 400, f"fixture drifted out of range: {short.word_count} words"
    assert "no_answerable_questions" not in _triggered(run_all_checks(short)), \
        f"a {short.word_count}-word utility page should not be flagged"

    long_ = parse_html("https://example.test/guide", LONG_CONTENT_HTML)
    assert long_.word_count >= 400, f"fixture drifted out of range: {long_.word_count} words"
    assert "no_answerable_questions" in _triggered(run_all_checks(long_)), \
        f"a {long_.word_count}-word content page with no Q&A should still be flagged"
    print(f"[PASS] no_answerable_questions: quiet at {short.word_count} words, "
          f"fires at {long_.word_count} words")


NOSCRIPT_APP_HTML = """
<html><head><title>App</title></head><body>
<noscript>You need to enable JavaScript to run this app.</noscript>
<div id="root"></div>
<script src="/static/js/main.abc123.js"></script>
</body></html>
"""

EMPTY_MOUNT_HTML = """
<html><head><title>App</title></head><body>
<div id="app"></div>
<script src="/assets/index-9f8e7d.js"></script>
</body></html>
"""

REAL_SHORT_PAGE_WITH_ROOT_ID_HTML = """
<html><head><title>Contact</title></head><body>
<div id="root"><h1>Contact us</h1><p>Call us at 555-0100 or email hello@example.test
if you would rather write than dial, and someone will get back to you soon.</p></div>
</body></html>
"""


def test_js_dependent_pages_are_flagged_without_running_anything():
    """The scraper never executes JavaScript (CLAUDE.md's stated ceiling), so
    a client-only route -- content that only appears once a bundle mounts and
    fetches -- used to just read as thin or empty with no explanation. Two
    cheap, real signals catch most of it: the "enable JavaScript" <noscript>
    block create-react-app/Vue-CLI/Angular-CLI apps ship almost universally,
    and a known framework mount point (#root, #app, #__next, ...) still empty
    on an otherwise-thin page. Neither is scored as a finding -- it's a
    caveat about the page's other signals, not a design tell."""
    noscript = parse_html("https://example.test/app", NOSCRIPT_APP_HTML)
    assert noscript.js_dependent and "noscript" in noscript.js_dependent_reason, noscript.js_dependent_reason

    empty_mount = parse_html("https://example.test/app2", EMPTY_MOUNT_HTML)
    assert empty_mount.js_dependent and "#app" in empty_mount.js_dependent_reason, empty_mount.js_dependent_reason

    real_short = parse_html("https://example.test/contact", REAL_SHORT_PAGE_WITH_ROOT_ID_HTML)
    assert not real_short.js_dependent, \
        f"a short but genuinely server-rendered page should not be flagged ({real_short.js_dependent_reason!r})"

    ordinary = parse_html("https://example.test/plain", HANDCRAFTED_HTML)
    assert not ordinary.js_dependent, "an ordinary page with no framework mount ids at all should not be flagged"

    print("[PASS] js_dependent: noscript and empty-mount both caught, "
          "real short content and ordinary pages both left alone")


NOINDEX_UTILITY_HTML = """
<html><head><title>Reset your password</title>
<meta name="robots" content="noindex">
</head><body>
<h1>Choose a new password</h1>
<p>At least 8 characters.</p>
</body></html>
"""


def test_noindex_pages_skip_the_findability_checks_but_not_the_rest():
    """A page that opts itself out of search (a login screen, a
    password-reset link target) doesn't deserve missing_canonical,
    missing_meta_description, thin_page or few_internal_links -- their whole
    premise is being found or ranked, which the page has explicitly declined.
    It still deserves everything that's good practice regardless of indexing
    (missing_lang, structured data). Found running this scanner against
    FIG's own /forgot-password."""
    noindex = parse_html("https://example.test/reset-password", NOINDEX_UTILITY_HTML)
    indexed_same_page = parse_html(
        "https://example.test/reset-password",
        NOINDEX_UTILITY_HTML.replace('<meta name="robots" content="noindex">\n', ""))

    exempted = _triggered(run_all_checks(noindex))
    baseline = _triggered(run_all_checks(indexed_same_page))

    still_gone = exempted & {"missing_canonical", "missing_meta_description", "thin_page"}
    assert not still_gone, f"these should be exempt on a noindex page: {still_gone}"
    assert baseline & {"missing_canonical", "missing_meta_description", "thin_page"}, \
        "the same page WITHOUT noindex should trip these -- the fixture isn't testing anything otherwise"
    assert "missing_lang" in exempted, "missing_lang is accessibility, not search -- must still fire"
    print(f"[PASS] noindex page: {sorted(exempted)}  |  same page indexed: {sorted(baseline)}")


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
    test_a_react_streaming_loading_fallback_is_not_read_as_page_content()
    test_strip_suspense_fallbacks_leaves_ordinary_html_and_unterminated_markers_alone()
    test_flat_typography_spares_a_real_document_but_still_catches_a_thin_template()
    test_faq_check_ignores_short_pages_but_still_catches_long_thin_content()
    test_js_dependent_pages_are_flagged_without_running_anything()
    test_noindex_pages_skip_the_findability_checks_but_not_the_rest()
    test_checklist_ids_are_unique_and_cover_observed_flags()
    print("\nAll local rule-engine tests passed.")
