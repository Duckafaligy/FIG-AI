"""Generates the static content pages for site/.

The site has no build step and is deployed as plain files, so this is an
authoring tool, not part of the deploy: it writes real .html into site/ and
those files are what ship. Run it after editing anything here.

    python scripts/build_pages.py

Every page shares one shell so the nav, footer, theme switch and cookie
notice stay identical across the site. Content lives in PAGES below.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
V = "9"          # cache-buster for the shared stylesheets

# Every canonical URL and contact address on the site comes from here. There
# are no hardcoded domains anywhere else, so moving to a real domain is:
#
#   python scripts/build_pages.py --site-url https://fig.tools --email hello@fig.tools
#
# The defaults point at the Vercel deployment and a real inbox, so nothing on
# the site references an address that does not exist.
SITE_URL = "https://fig-ai.vercel.app"
CONTACT_EMAIL = "brendanhllau@gmail.com"

for _i, _a in enumerate(sys.argv):
    if _a == "--site-url" and _i + 1 < len(sys.argv):
        SITE_URL = sys.argv[_i + 1].rstrip("/")
    if _a == "--email" and _i + 1 < len(sys.argv):
        CONTACT_EMAIL = sys.argv[_i + 1]

APP = "/app"     # where the dashboard lives once deployed

NAV = """<nav class="nav" id="nav">
  <div class="nav-pill" id="navPill">
    <a class="brand" href="index.html">
      <span class="brand-mark" aria-hidden="true"></span>
      <span class="brand-name">FIG</span>
    </a>
    <span class="nav-sep" aria-hidden="true"></span>
    <div class="nav-links" id="navLinks">
      <a href="index.html#catches">What it catches</a>
      <a href="glossary.html">Learn</a>
      <a href="pricing.html">Pricing</a>
      <a href="demo.html" class="nav-demo">Demo</a>
    </div>
    <a class="nav-signin" href="#" data-app="/login">Sign in</a>
    <a class="btn21 btn21-solid btn21-sm" href="#" data-app="/signup"><span>Try For Free</span></a>
  </div>
</nav>"""

FOOTER_COLS = [
    ("Product", [
        ("What it catches", "index.html#catches"),
        ("Pricing", "pricing.html"),
        ("Compare plans", "pricing.html"),
        ("Recent reads", "history.html"),
        ("Changelog", "changelog.html"),
        ("Status", "status.html"),
    ]),
    ("Learn", [
        ("Blog", "blog.html"),
        ("Glossary", "glossary.html"),
        ("The AI slop rulebook", "rulebook.html"),
        ("Spotting AI-written pages", "spotting-ai-pages.html"),
        ("Schema for AI crawlers", "schema-for-crawlers.html"),
        ("robots.txt reference", "robots-reference.html"),
    ]),
    ("Build", [
        ("Docs", "docs.html"),
        ("Domain verification", "domain-verification.html"),
        ("API reference", "api.html"),
        ("Webhooks", "webhooks.html"),
        ("Fix recipes", "fix-recipes.html"),
    ]),
    ("Company", [
        ("About", "about.html"),
        ("Contact", "contact.html"),
        ("Privacy policy", "privacy.html"),
        ("Terms of service", "terms.html"),
        ("Cookie notice", "cookies.html"),
        ("Security", "security.html"),
    ]),
]


def footer() -> str:
    cols = []
    for title, links in FOOTER_COLS:
        items = "".join(f'\n        <a href="{h}">{t}</a>' for t, h in links)
        cols.append(f'      <div class="foot-col">\n        <h4>{title}</h4>{items}\n      </div>')
    return f"""<footer class="footer">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="index.html">
          <span class="brand-mark" aria-hidden="true"></span>
          <span class="brand-name">FIG</span>
        </a>
        <p class="foot-blurb">Find out what AI gets wrong about your website,
          where the answer came from, and exactly what to change.</p>
      </div>
{chr(10).join(cols)}
    </div>
    <div class="foot-bar">
      <span class="mono foot-left">&copy; 2026 FIG &middot; Built for people who publish on the web</span>
      <span class="foot-right">
        <a href="privacy.html">Privacy</a><i>&middot;</i><a href="terms.html">Terms</a><i>&middot;</i><a href="cookies.html">Cookies</a>
      </span>
    </div>
  </div>
</footer>"""


THEME = """<div class="theme-switch" role="group" aria-label="Colour theme">
  <button class="ts-btn" type="button" data-theme-set="dark" aria-pressed="true" title="Dark">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>
    <span class="sr-only">Dark</span>
  </button>
  <button class="ts-btn" type="button" data-theme-set="light" aria-pressed="false" title="Light">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>
    <span class="sr-only">Light</span>
  </button>
</div>"""

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{site_url}/{slug}.html">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="{og_type}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800;900&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<script>
/* applied before first paint so a saved light theme never flashes dark */
(function(){{try{{
  var t=localStorage.getItem('fig_theme');
  if(!t){{var m=document.cookie.match(/(?:^|; )fig_theme=([^;]*)/);t=m?decodeURIComponent(m[1]):null;}}
  if(!t&&window.matchMedia&&matchMedia('(prefers-color-scheme: light)').matches)t='light';
  if(t==='light')document.documentElement.setAttribute('data-theme','light');
}}catch(e){{}}}})();
</script>
<link rel="stylesheet" href="styles.css?v={v}">
<link rel="stylesheet" href="page.css?v={v}">
<script src="config.js?v={v}"></script>
<script src="device.js?v={v}" defer></script>
{head_extra}
</head>
<body>
{nav}
<main class="pg">
  <div class="pg-wrap{wide}">
    <p class="pg-crumb"><a href="index.html">FIG</a> / {crumb}</p>
    <h1>{h1}</h1>
    <p class="pg-lede">{lede}</p>
    {meta}
    <div class="pg-body">
{body}
    </div>
  </div>
</main>
{footer}
{theme}
{body_extra}
</body>
</html>
"""


def page(slug, *, title, description, h1, lede, body, crumb=None, meta="",
         og_type="article", wide=False, head_extra="", body_extra=""):
    return slug, SHELL.format(
        title=title, description=description, slug=slug, og_type=og_type,
        v=V, nav=NAV, footer=footer(), theme=THEME, site_url=SITE_URL,
        crumb=crumb or h1, h1=h1, lede=lede,
        body=body.replace("{contact}", CONTACT_EMAIL).replace("{site_url}", SITE_URL),
        meta=f'<p class="pg-meta">{meta}</p>' if meta else "",
        wide=" pg-wide" if wide else "", head_extra=head_extra,
        body_extra=body_extra,
    )


# ----------------------------------------------------------------------
# Content
# ----------------------------------------------------------------------

RULEBOOK = """
<p>None of this proves anything about how a page was made, and FIG will never
tell you a page &ldquo;is&rdquo; AI-written. Detectors that claim to do that
are wrong often enough to ruin somebody's week &mdash; false-positive rates in
the published research run between 5% and 17%, one university logged nearly
1,500 false accusations in a single semester, and dozens have since banned the
tools outright.</p>

<p>What these patterns actually show is where a page <strong>stopped making
decisions</strong>. Every one of them is a choice somebody skipped. Every one
is yours to take back.</p>

<h2 id="one">1. The same card, forty times</h2>
<p>Identical corner radius and drop shadow on every block. Nothing sits
forward, nothing sits back, so the page reads flat no matter how much is on
it.</p>
<p><strong>Fix:</strong> pick one tier of card and give it a heavier surface.
Let everything else sit quieter. Hierarchy is contrast, not decoration.</p>

<h2 id="two">2. Numbered eyebrows</h2>
<p><code>01</code> <code>02</code> <code>03</code> above every section
heading. It fills space without deciding what matters, and readers skip
it.</p>
<p><strong>Fix:</strong> drop the numbers. If the order genuinely matters, say
so in the heading.</p>

<h2 id="three">3. The untouched palette</h2>
<p>Stock indigo, violet, the default blue. Framework defaults are recognisable
precisely because nobody changed them &mdash; it is the fastest signal that a
theme was accepted rather than chosen.</p>
<p><strong>Fix:</strong> rotate the hue 10&ndash;15 degrees and adjust
lightness. That is usually enough to stop it reading as stock.</p>

<h2 id="four">4. A type scale that barely moves</h2>
<p>Headings within a few pixels of body text. The eye needs a clear first
stop; a crawler needs to know which heading owns which block.</p>
<p><strong>Fix:</strong> one h1, real h2s for sections, h3s inside them. If you
are carrying four levels, cut one.</p>

<h2 id="five">5. The same four icons</h2>
<p>Sparkles, ArrowRight, Zap, CheckCircle. They are not wrong. They are
invisible from familiarity.</p>
<p><strong>Fix:</strong> keep them where they earn it, but make at least one
visual on the page specific to you.</p>

<h2 id="six">6. Copy that describes no product in particular</h2>
<p>&ldquo;Elevate your workflow.&rdquo; &ldquo;Unlock the power of.&rdquo;
&ldquo;Seamlessly integrate.&rdquo; These turn up everywhere because they
commit to nothing. A model reading the page learns nothing it could repeat
back about you.</p>
<p><strong>Fix:</strong> replace each with the specific thing it does. If a
sentence would be true of any company, it is not saying anything.</p>

<h2 id="seven">7. Equal spacing everywhere</h2>
<p>Identical padding on every section removes grouping. Things that belong
together should sit closer than things that do not.</p>
<p><strong>Fix:</strong> tighten space inside a group, open it up between
groups.</p>

<h2 id="eight">8. Sections in an order nobody chose</h2>
<p>The one most people miss. Pricing above the section that justifies it.
A closing call to action before the page has explained itself. An FAQ
answering questions nobody has been given a reason to ask yet.</p>
<p><strong>Fix:</strong> make the case, then ask. See
<a href="glossary.html#section-order">section order</a>.</p>

<h2 id="nine">9. Nothing a machine can quote</h2>
<p>No structured data, no plainly-worded questions with direct answers, no
concrete numbers. A page of adjectives has to be paraphrased, and paraphrase
loses you.</p>
<p><strong>Fix:</strong> put a real number or a real name in every section.
Add three or four questions people actually ask, with two-sentence answers.
See <a href="schema-for-crawlers.html">schema for AI crawlers</a>.</p>

<hr>
<p class="pg-meta">This list is the human-readable half of what
<a href="demo.html">the free read</a> checks. The other half is in
<a href="fix-recipes.html">fix recipes</a>.</p>
"""

GLOSSARY_TERMS = [
    ("AI slop", "ai-slop",
     "Output that is fluent and shaped correctly but decided nothing. On a web "
     "page it shows up as uniform cards, stock palettes, filler verbs and a flat "
     "type scale. It is a description of the result, never a claim about the tool "
     "that made it &mdash; hand-written pages produce it too, usually under deadline.",
     "See also: the rulebook"),
    ("GEO", "geo",
     "Generative engine optimisation. The work of making a site legible to models "
     "that answer questions rather than return ten blue links. Overlaps heavily "
     "with SEO, but weights different things: structured data, plainly-worded "
     "answers, and specifics a model can quote with confidence.",
     "See also: AEO, structured data"),
    ("AEO", "aeo",
     "Answer engine optimisation. Used more or less interchangeably with GEO. "
     "Where the two are distinguished, AEO tends to mean optimising for direct "
     "answer boxes and GEO for generated prose.", ""),
    ("Section order", "section-order",
     "The sequence of blocks down a page, and whether it makes its case before it "
     "asks for anything. Pricing above the section explaining what you get is the "
     "common failure: a reader hitting a number with no context has nothing to "
     "weigh it against, so it reads as expensive by default.",
     "FIG checks this deterministically"),
    ("Structured data", "structured-data",
     "JSON-LD in the page head describing what the page is about in a form a "
     "machine does not have to infer. <code>Organization</code>, "
     "<code>LocalBusiness</code>, <code>Product</code>, <code>FAQPage</code>. "
     "The one place you get to state plainly who you are.",
     "See also: schema for AI crawlers"),
    ("Crawl budget", "crawl-budget",
     "How much of your site a crawler will actually read before it moves on. "
     "Thin, duplicated and orphaned pages spend it without earning anything.", ""),
    ("Orphan page", "orphan-page",
     "A page nothing links to. Readers cannot reach it and crawlers usually will "
     "not either, so whatever is on it may as well not exist.", ""),
    ("Canonical", "canonical",
     "A <code>&lt;link rel=\"canonical\"&gt;</code> naming the preferred URL for a "
     "page. Without it, the same page reached two ways can be treated as two "
     "pages, splitting whatever weight it has earned.", ""),
    ("Type scale", "type-scale",
     "The set of sizes used across headings and body text, and the ratio between "
     "them. A scale that barely changes gives a reader nothing to land on.", ""),
    ("Component uniformity", "component-uniformity",
     "Every card carrying an identical radius and shadow. Nothing sits forward or "
     "back, so the page reads flat regardless of how much is on it.", ""),
    ("False positive", "false-positive",
     "An AI detector saying a human wrote something with a machine. Published "
     "rates run 5&ndash;17%. It is the reason FIG reports patterns and never "
     "verdicts about authorship, and the reason this is a self-check tool rather "
     "than a grading one.", ""),
    ("Craft, Structure, Search, Answers", "layers",
     "The four layers FIG reports on. Craft is how a page reads; Structure is what "
     "sits where; Search is what a crawler can reach; Answers is what a model has "
     "to quote. A site can be immaculate on one and invisible on another.", ""),
]


def glossary_body() -> str:
    rows = []
    for term, anchor, body, also in GLOSSARY_TERMS:
        extra = f'\n        <p class="also">{also}</p>' if also else ""
        rows.append(
            f'      <div class="pg-term" id="{anchor}">\n'
            f'        <dt>{term}</dt>\n        <dd>{body}</dd>{extra}\n      </div>')
    return '<dl class="pg-terms">\n' + "\n".join(rows) + "\n    </dl>"


BLOG_POSTS = [
    ("The section order problem nobody checks", "section-order-problem",
     "Pricing above the reason for it is the most common structural mistake on the "
     "web, and no tool flags it."),
    ("Why your site is invisible to ChatGPT", "invisible-to-chatgpt",
     "Not a ranking problem. A quotability problem &mdash; and the fix is mostly "
     "structured data and plainly-worded answers."),
    ("Reading 50 agency portfolios", "reading-50-portfolios",
     "What the sites built by people who build sites for a living actually score."),
]


def blog_body() -> str:
    cards = "".join(
        f'\n      <a class="pg-card" href="blog.html">\n'
        f'        <span class="k">Coming soon</span>\n'
        f'        <b>{t}</b>\n        <span>{d}</span>\n      </a>'
        for t, _s, d in BLOG_POSTS)
    return f"""<p>Notes on what makes a page legible &mdash; to a reader, to a
crawler, and to a model being asked about you. Written as we work out the
answers, not after.</p>

<div class="pg-cards">{cards}
    </div>

<div class="pg-note">
  <p><b>Nothing published yet.</b> These are the three we are writing first.
  Rather than pad this page with filler &mdash; which would be a slightly
  embarrassing thing for this particular product to do &mdash; it says so.
  The <a href="glossary.html">glossary</a> and
  <a href="rulebook.html">rulebook</a> are finished and worth reading now.</p>
</div>"""


SCHEMA_PAGE = """
<p>Structured data is the one place on a page where you get to state plainly
what you are, in a form nothing has to infer. Everything else on the page is
prose a model has to interpret. This is the part it can read directly.</p>

<h2>Start with two blocks</h2>
<p>Almost every site needs exactly two things and no more. An
<code>Organization</code> (or <code>LocalBusiness</code>, if people physically
visit you) on the homepage, and something page-specific on the pages that
warrant it.</p>

<pre><code>&lt;script type="application/ld+json"&gt;
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Harborline Dental",
  "url": "https://harborlinedental.com",
  "telephone": "+1-555-0142",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "41 Bell Street",
    "addressLocality": "Portland",
    "addressRegion": "OR",
    "postalCode": "97205"
  },
  "openingHours": "Mo-Fr 08:00-17:00"
}
&lt;/script&gt;</code></pre>

<h2>Then FAQPage, if you have real questions</h2>
<p>Models answer questions. A page that already contains a plainly-worded
question and a direct answer is the easiest thing in the world for one to
lift. A page with no questions on it has to be paraphrased instead, and
paraphrase loses you.</p>

<pre><code>{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Do you take walk-ins?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Yes, before 10am on weekdays."
    }
  }]
}</code></pre>

<h2>Rules that actually matter</h2>
<ul>
  <li><strong>Only mark up what is visible on the page.</strong> Schema that
    describes content a reader cannot see is the fastest way to get ignored.</li>
  <li><strong>One Organization block per site</strong>, on the homepage. Not
    on every page.</li>
  <li><strong>Answer in the answer.</strong> &ldquo;It depends on your
    situation, contact us&rdquo; is not an answer and will not be quoted.</li>
  <li><strong>Keep it in sync.</strong> Stale opening hours in JSON-LD are
    worse than none, because something will repeat them confidently.</li>
</ul>

<div class="pg-note">
  <p><b>FIG checks this.</b> The Answers layer flags a page with no JSON-LD, a
  page whose JSON-LD does not describe the business or the thing on the page,
  and a page with no question-and-answer block on it.
  <a href="demo.html">Run a free read</a> to see where yours sits.</p>
</div>
"""

ROBOTS_PAGE = """
<p><code>robots.txt</code> is a plain text file at the root of your domain
telling crawlers what they may read. It is a request, not a lock &mdash;
well-behaved crawlers honour it, badly-behaved ones ignore it, and it is not a
security measure for anything.</p>

<h2>The minimum useful file</h2>
<pre><code>User-agent: *
Allow: /

Sitemap: https://yourdomain.com/sitemap.xml</code></pre>
<p>That is genuinely it for most sites. The <code>Sitemap:</code> line is the
part people forget and the part that helps most.</p>

<h2>AI crawlers, specifically</h2>
<p>Model providers use named agents. You can allow or refuse them
individually, and it is worth doing deliberately rather than by accident:</p>
<table class="pg-t">
  <thead><tr><th>Agent</th><th>Who</th><th>What it feeds</th></tr></thead>
  <tbody>
    <tr><td><code>GPTBot</code></td><td>OpenAI</td><td>Model training</td></tr>
    <tr><td><code>OAI-SearchBot</code></td><td>OpenAI</td><td>Search results in ChatGPT</td></tr>
    <tr><td><code>ChatGPT-User</code></td><td>OpenAI</td><td>Live fetches during a conversation</td></tr>
    <tr><td><code>ClaudeBot</code></td><td>Anthropic</td><td>Model training</td></tr>
    <tr><td><code>Claude-User</code></td><td>Anthropic</td><td>Live fetches during a conversation</td></tr>
    <tr><td><code>PerplexityBot</code></td><td>Perplexity</td><td>Search index</td></tr>
    <tr><td><code>Google-Extended</code></td><td>Google</td><td>Gemini training</td></tr>
    <tr><td><code>FIGBot</code></td><td>FIG</td><td>The read you asked us for</td></tr>
  </tbody>
</table>

<h2>The distinction worth understanding</h2>
<p>Blocking a <em>training</em> agent keeps your writing out of the next model.
Blocking a <em>search</em> or <em>user</em> agent stops you being cited when
somebody asks about you today. People routinely block both when they meant to
block the first &mdash; and then wonder why they never come up.</p>
<pre><code># out of training, still citable
User-agent: GPTBot
Disallow: /

User-agent: OAI-SearchBot
Allow: /</code></pre>

<div class="pg-note">
  <p><b>FIGBot honours robots.txt.</b> One request per host at a time with a
  delay between them, and a <code>Disallow</code> is respected on every fetch
  including the free read. If you block us, we do not read you.</p>
</div>
"""

SPOTTING_PAGE = """
<p>This page is about noticing patterns in your own work. It is not a
detection guide, and it is deliberately not usable as one.</p>

<div class="pg-note">
  <p><b>Read this first.</b> You cannot tell whether a person used a model to
  write something by looking at it, and neither can any tool that says it can.
  Published false-positive rates run 5&ndash;17%. Non-native English speakers
  are flagged disproportionately. People have failed courses over it. If you
  are here to check somebody else's work, this is the wrong site &mdash; and
  we will not build that feature.</p>
</div>

<h2>What is actually observable</h2>
<p>Not authorship. What you can observe is <strong>whether a page committed to
anything</strong>, and that is worth knowing regardless of how it was
written:</p>
<ul>
  <li><strong>Sentences true of any company.</strong> &ldquo;We believe great
    design starts with understanding your needs.&rdquo; Swap the logo and it
    still reads fine. That is the tell &mdash; not the phrasing, the
    interchangeability.</li>
  <li><strong>Three of everything.</strong> Three benefits, three steps, three
    tiers. Not wrong, but when every section is a triptych nobody decided how
    many of anything there actually are.</li>
  <li><strong>Balance where there should be a position.</strong> &ldquo;While
    X has advantages, Y also offers benefits.&rdquo; A page that refuses to
    prefer anything gives a reader nothing to act on.</li>
  <li><strong>No numbers.</strong> No prices, dates, counts, place names.
    Specifics are what get quoted; adjectives do not.</li>
  <li><strong>Nothing that could only be you.</strong> No anecdote, no
    constraint, no thing that went wrong. This is the big one.</li>
</ul>

<h2>The useful question</h2>
<p>Not &ldquo;was this generated?&rdquo; but <strong>&ldquo;what did this page
decide?&rdquo;</strong> Read a section and ask what a competitor could not
have written. If the answer is nothing, that section is doing no work &mdash;
and that is true whether a person or a model produced it.</p>

<hr>
<p>The <a href="rulebook.html">rulebook</a> covers the visual half of the same
question, and <a href="demo.html">the free read</a> runs both against a page
you own.</p>
"""

FIX_RECIPES = """
<p>Each finding FIG reports comes with a fix. These are the longer versions,
for when the one-line version is not enough.</p>

<h2 id="uniformity">Every card looks the same</h2>
<p>Pick the one card that matters most on the page &mdash; usually the
recommended plan, the flagship feature, the thing you want clicked. Give it a
heavier surface: a stronger border, a lifted background, slightly more
padding. Then take a step back from everything else: lighter borders, flatter
backgrounds.</p>
<p>You are not adding decoration. You are removing it from three quarters of
the page so one thing can be seen.</p>

<h2 id="palette">The palette is a framework default</h2>
<p>Take your primary colour into any HSL picker. Rotate the hue by 10&ndash;15
degrees, then drop lightness by 5&ndash;10%. Check contrast against your
background &mdash; 4.5:1 for body text, 3:1 for large text. That is the whole
job, and it takes about four minutes.</p>

<h2 id="type">The type scale is flat</h2>
<p>Pick a ratio and stick to it. 1.25 is safe, 1.333 has more drama. From a
16px body: 16 / 20 / 27 / 36 / 48. Assign h1 through h4 and stop using tag
choice to control size &mdash; that is CSS's job, and mixing the two is what
produces the skipped heading levels FIG flags separately.</p>

<h2 id="order">Pricing sits above what justifies it</h2>
<p>Move it. If it has to stay high for a business reason, put a short summary
of what is included directly above the number &mdash; three lines is
enough &mdash; so the price lands on some context rather than none.</p>

<h2 id="schema">No structured data</h2>
<p>One <code>Organization</code> or <code>LocalBusiness</code> block on the
homepage. That is the 80% fix. See
<a href="schema-for-crawlers.html">schema for AI crawlers</a> for the block to
paste.</p>

<h2 id="answers">Nothing a model can quote</h2>
<p>Write down the five questions you are actually asked, in the words people
use to ask them. Answer each in two sentences, directly, in the first
sentence. Put them on the page and mark them up as <code>FAQPage</code>.</p>
<p>&ldquo;It depends on your situation&rdquo; is not an answer and will not be
quoted.</p>

<h2 id="alt">Images without alt text</h2>
<p>Describe the meaningful ones in a sentence. Mark the purely decorative ones
<code>alt=""</code> &mdash; explicitly empty, not missing. The distinction is
the point: empty means &ldquo;deliberately nothing here&rdquo;, missing means
&ldquo;nobody thought about it&rdquo;.</p>
"""

DOCS_PAGE = """
<p>FIG reads a site across four layers and tells you what to change. This is
how to use it.</p>

<div class="pg-cards">
  <a class="pg-card" href="demo.html"><span class="k">Start here</span>
    <b>Run a free read</b><span>One URL. No account. It reads up to six pages
    and explains every finding.</span></a>
  <a class="pg-card" href="api.html"><span class="k">Build</span>
    <b>API reference</b><span>Provision sites, trigger reads, pull results
    into your own product.</span></a>
  <a class="pg-card" href="domain-verification.html"><span class="k">Build</span>
    <b>Domain verification</b><span>Only needed for scheduled monitoring,
    never for a one-off read.</span></a>
  <a class="pg-card" href="webhooks.html"><span class="k">Build</span>
    <b>Webhooks</b><span>Get told when a read lands instead of polling.</span></a>
</div>

<h2>The four layers</h2>
<table class="pg-t">
  <thead><tr><th>Layer</th><th>The question it asks</th></tr></thead>
  <tbody>
    <tr><td>Craft</td><td>How does the page read? Uniform cards, stock palette,
      filler copy, a flat type scale.</td></tr>
    <tr><td>Structure</td><td>What sits where? Section order, heading
      hierarchy, thin pages.</td></tr>
    <tr><td>Search</td><td>What can a crawler reach and understand? Titles,
      descriptions, canonicals, alt text, internal links.</td></tr>
    <tr><td>Answers</td><td>What can a model quote? Structured data,
      answerable questions, concrete specifics.</td></tr>
  </tbody>
</table>
<p>Each is scored 0&ndash;100 and every point lost traces back to a specific
finding on a specific page. A site can be immaculate to read and completely
invisible to a model &mdash; the layers exist so the report says which.</p>

<h2>Verdicts</h2>
<p>Findings are reported as <strong>clean</strong>, <strong>check</strong> or
<strong>fix</strong>. They describe patterns, never authorship. FIG does not
say a page &ldquo;is&rdquo; AI-written, because nothing can reliably tell you
that.</p>

<h2>Rate limits</h2>
<p>The free read is limited per browser per day and per network per hour. The
limit is what keeps it free &mdash; it crawls real sites and calls a model,
and both cost something. A plan lifts it.</p>
"""

API_PAGE = """
<p>The API is the primary interface. The dashboard is the first thing built on
it, and anything possible there is possible here &mdash; which is what makes
it embeddable inside somebody else's product.</p>

<h2>Authenticating</h2>
<p>Every request carries a key, as a header. Keys are created in the dashboard
under API keys and shown once.</p>
<pre><code>curl {site_url}/v1/account \\
  -H "X-API-Key: fig_live_xxxx_yyyy"</code></pre>
<p><code>Authorization: Bearer &lt;key&gt;</code> works identically.</p>

<h2>Provision a site</h2>
<p>The call a partner makes when their own customer turns the feature on.
Billing follows the site count, so this is the moment the invoice changes.</p>
<pre><code>POST /v1/sites
{
  "hostname": "clientdomain.com",
  "client_name": "Their Client Ltd"
}</code></pre>
<p><code>client_name</code> is who you are delivering it for. It appears on
your report, not ours.</p>

<h2>Read a site</h2>
<pre><code>POST /v1/sites/{site_id}/scans      &rarr; 202, a scan in "queued"
GET  /v1/scans/{scan_id}            &rarr; status, scores, findings</code></pre>
<p>Reads are queued, not synchronous. A crawl takes a minute or two and an
estate read of four hundred sites is a queue depth rather than four hundred
long requests.</p>

<h2>The whole estate at once</h2>
<pre><code>POST /v1/scans      &rarr; queues every active site on the account
GET  /v1/report     &rarr; every site, worst first, with top findings</code></pre>
<p><code>/v1/report</code> is the payload to render as your own client-facing
report. It carries the account's brand name rather than ours when the account
is white-labelled.</p>

<h2>Everything else</h2>
<table class="pg-t">
  <thead><tr><th>Endpoint</th><th>Does</th></tr></thead>
  <tbody>
    <tr><td><code>GET /v1/account</code></td><td>Site count, rate, monthly total, queue depth</td></tr>
    <tr><td><code>GET /v1/sites</code></td><td>Every site with its latest score</td></tr>
    <tr><td><code>DELETE /v1/sites/{id}</code></td><td>Deactivate. History is kept, billing stops</td></tr>
    <tr><td><code>GET /v1/scans/{id}/pages</code></td><td>Every page read, with its section order</td></tr>
    <tr><td><code>GET /v1/layers</code></td><td>The four layers and what they mean</td></tr>
    <tr><td><code>GET /v1/billing/quote</code></td><td>What this estate size costs, and the tiers</td></tr>
  </tbody>
</table>

<div class="pg-note">
  <p><b>Full schema.</b> The running API serves an OpenAPI document and an
  interactive reference at <code>/docs</code>.</p>
</div>
"""

VERIFY_PAGE = """
<p>Proving you own a domain unlocks <strong>scheduled monitoring</strong> on
it. It is never required for a one-off read.</p>

<div class="pg-note">
  <p><b>Why one-off reads are not gated.</b> Studying a site you admire, or a
  competitor, to understand how it is built is the entire point of the free
  tier. Locking that behind ownership would kill it. Ownership is only checked
  before we start visiting a site repeatedly on a schedule.</p>
</div>

<h2>Two ways, same as Search Console</h2>
<h3>DNS TXT record</h3>
<pre><code>POST /v1/sites/{site_id}/verification
{ "method": "dns_txt" }</code></pre>
<p>Add the returned token as a TXT record on the domain, then:</p>
<pre><code>POST /v1/sites/{site_id}/verification/confirm</code></pre>

<h3>Meta tag</h3>
<pre><code>&lt;meta name="ai-tell-verification" content="ai-tell-verify=..."&gt;</code></pre>
<p>Put it in the homepage <code>&lt;head&gt;</code> and confirm the same way.
Faster if you can deploy quicker than DNS propagates; the record is more
durable if the homepage changes often.</p>

<h2>After verification</h2>
<ul>
  <li>Scheduled re-reads on a cadence you set</li>
  <li>Change alerts when a score moves</li>
  <li>Before-and-after comparison across reads</li>
</ul>
"""

WEBHOOKS_PAGE = """
<p>Rather than polling <code>GET /v1/scans/{id}</code> until a read lands, have
us tell you.</p>

<div class="pg-note">
  <p><b>Not shipped yet.</b> This page describes the intended shape so you can
  build against it, and it will be marked done in the
  <a href="changelog.html">changelog</a> when it is real. Until then, polling
  works &mdash; a read takes a minute or two, so every few seconds is
  plenty.</p>
</div>

<h2>Planned shape</h2>
<pre><code>POST https://your-endpoint
X-FIG-Signature: sha256=...

{
  "event": "scan.completed",
  "scan_id": "...",
  "site_id": "...",
  "hostname": "clientdomain.com",
  "score": 62,
  "verdict": "check",
  "layers": { "craft": 70, "structure": 71, "search": 76, "answers": 22 }
}</code></pre>

<h2>Events</h2>
<table class="pg-t">
  <thead><tr><th>Event</th><th>Fires when</th></tr></thead>
  <tbody>
    <tr><td><code>scan.completed</code></td><td>A read finishes successfully</td></tr>
    <tr><td><code>scan.failed</code></td><td>A site could not be read</td></tr>
    <tr><td><code>score.changed</code></td><td>A monitored site moves by more than a threshold</td></tr>
  </tbody>
</table>
<p>Every delivery will be signed. Verify the signature before trusting the
body &mdash; an unsigned webhook endpoint is an open door.</p>
"""

ABOUT_PAGE = """
<p>FIG reads a website the way a crawler does, and tells you what reads as
machine-made, what sits in the wrong order, what search can never reach, and
what a model has nothing to quote from.</p>

<h2>Why it exists</h2>
<p>It started as a way to study other people's sites properly. Looking at a
site you admire and asking <em>why does this work</em> is how most people
learn to build, and there was no tool that answered in specifics rather than a
number.</p>
<p>The second half arrived later. A site that reads as generic to a person is
also thin to a model &mdash; nothing specific to quote, nothing distinctive to
remember. Fixing one fixes the other. That is the whole product.</p>

<h2>What it will never be</h2>
<p>FIG is a self-check tool. It is not a way to catch anyone.</p>
<ul>
  <li>It will never tell you a page &ldquo;is&rdquo; AI-written. Nothing can do
    that reliably &mdash; false-positive rates in the research run
    5&ndash;17%, and real people have been failed over it.</li>
  <li>No feature will give an institution visibility into an individual's
    results without that person choosing to share them.</li>
  <li>No public leaderboard naming real sites. The
    <a href="history.html">recent reads</a> feed is anonymous unless the person
    who ran the read chooses otherwise.</li>
</ul>
<p>We researched this space before building. Several companies built the
opposite thing &mdash; institutional, admin-visible detection &mdash; and it
caused real harm. We are deliberately building the other one.</p>

<h2>How it is built</h2>
<p>Over 95% of the pipeline is deterministic code: fetch, parse, count,
compare. A model is called exactly once, at the end, on already-flagged
structured data &mdash; never on your page. That is why the free read can stay
free, and why every finding is explainable without hand-waving.</p>
"""

CONTACT_PAGE = """
<p>One person builds this. You will get a real reply, usually within a day.</p>

<h2>Email</h2>
<p><a href="mailto:{contact}">{contact}</a> &mdash; questions,
bugs, agency and platform enquiries, or to tell us a finding was wrong.</p>

<h2>Wrong findings are worth reporting</h2>
<p>The rules are tuned against real sites, and the fastest way to improve them
is a specific example that was flagged badly. Send the URL and the finding.
That feedback is more useful than a feature request.</p>

<h2>Security</h2>
<p>See <a href="security.html">security</a> for how to report a vulnerability.
Please do not open a public issue for one.</p>

<h2>Ask us to stop reading your site</h2>
<p>Add <code>FIGBot</code> to your <code>robots.txt</code> and we stop
immediately &mdash; it is honoured on every fetch, including free reads. Or
email and we will block the domain at our end.</p>
<pre><code>User-agent: FIGBot
Disallow: /</code></pre>
"""

SECURITY_PAGE = """
<h2>Reporting a vulnerability</h2>
<p>Email <a href="mailto:{contact}">{contact}</a>. Please do
not open a public issue. We will acknowledge within 72 hours and keep you
updated until it is resolved. We will not take legal action against
good-faith research.</p>

<h2>How the product handles credentials</h2>
<ul>
  <li><strong>API keys</strong> are stored as SHA-256 hashes. The plaintext is
    shown once, at creation, and cannot be recovered &mdash; a database dump
    does not hand anyone working credentials.</li>
  <li><strong>Sign-in</strong> goes through Supabase Auth. The access token is
    verified server-side and immediately discarded; the browser holds a signed,
    HttpOnly session cookie instead and never keeps the token.</li>
  <li><strong>Privileged keys stay server-side.</strong> The only Supabase key
    that reaches a browser is the anon key, which carries no privileges of its
    own.</li>
  <li><strong>Payments</strong> go through Stripe Checkout. Card details never
    touch our servers.</li>
</ul>

<h2>How the crawler behaves</h2>
<ul>
  <li>Identifies itself as <code>FIGBot</code> with a contact URL</li>
  <li>Honours <code>robots.txt</code> on every fetch, including free reads</li>
  <li>One request per host at a time, with a delay between them</li>
  <li>Reads publicly accessible pages only. It does not attempt logins, submit
    forms, or follow anything behind authentication</li>
  <li>Stores extracted structure and findings, not full page copies</li>
</ul>

<h2>Known gaps</h2>
<p>Stated plainly because a security page that claims everything is fine is
not worth reading:</p>
<ul>
  <li>No SOC 2 or ISO certification. We are too early for either to mean
    anything.</li>
  <li>No bug bounty programme yet.</li>
  <li>Data is held in a single region.</li>
</ul>
"""

PRIVACY_PAGE = """
<p>Short version: we keep as little as we can, we do not sell anything to
anyone, and there is no advertising or cross-site tracking on this site.</p>

<h2>What we collect</h2>
<table class="pg-t">
  <thead><tr><th>What</th><th>Why</th><th>Kept</th></tr></thead>
  <tbody>
    <tr><td>Your email</td><td>To have an account and sign in</td><td>Until you delete the account</td></tr>
    <tr><td>Domains you add</td><td>To read them and show you results</td><td>Until you remove them</td></tr>
    <tr><td>Read results</td><td>To show history and change over time</td><td>Until you delete them</td></tr>
    <tr><td>A device identifier</td><td>To limit the free read to a few per browser</td><td>One year, in a first-party cookie</td></tr>
    <tr><td>A hash of your IP</td><td>To limit free reads per network</td><td>One-way hash; the IP itself is not stored</td></tr>
  </tbody>
</table>

<h2>What we do not do</h2>
<ul>
  <li>No advertising, no ad networks, no third-party trackers.</li>
  <li>No selling or sharing of personal data. There is no arrangement under
    which anyone pays us for it.</li>
  <li>No cross-site tracking. The cookie we set is first-party and readable
    only by this site.</li>
</ul>

<h2>Pages we read</h2>
<p>When you point FIG at a site we fetch publicly accessible pages from it, the
way any crawler does. We store the extracted structure and the findings, not
copies of the pages. We honour <code>robots.txt</code>.</p>

<h2>The recent reads feed</h2>
<p>Reads appear on <a href="history.html">recent reads</a>
<strong>anonymously</strong> &mdash; a score, a page count, which pattern came
up. The domain is shown only if the person who ran the read ticked the box to
share it. A site never appears there because a stranger pointed FIG at it.</p>

<h2>Processors we use</h2>
<ul>
  <li><strong>Supabase</strong> &mdash; database and authentication</li>
  <li><strong>Anthropic</strong> &mdash; writes the explanation for an already
    detected finding. It receives the finding, never your page</li>
  <li><strong>Stripe</strong> &mdash; payments. We never see card details</li>
</ul>

<h2>Your rights</h2>
<p>Ask for a copy of your data, a correction, or deletion, by emailing
<a href="mailto:{contact}">{contact}</a>. Deleting your account
removes your sites and their read history.</p>

<h2>Children</h2>
<p>FIG is not directed at children under 13 and we do not knowingly collect
their data.</p>
"""

TERMS_PAGE = """
<h2>The agreement</h2>
<p>Using FIG means agreeing to this. If you do not, do not use it.</p>

<h2>What FIG is</h2>
<p>A tool that reads publicly accessible web pages and reports patterns, with
suggestions. <strong>It reports patterns, not verdicts about authorship.</strong>
FIG does not determine whether content was written by a person or a model, and
no output should be used as if it did.</p>

<h2>What you must not use it for</h2>
<ul>
  <li>Accusing anyone of using AI, or as evidence in any academic-integrity,
    disciplinary or employment process.</li>
  <li>Surveillance of individuals, or building a profile of a person's work.</li>
  <li>Reading sites you have been asked to stop reading.</li>
  <li>Anything unlawful, or attempting to disrupt the service.</li>
</ul>
<p>These are not decorative. Accounts used this way are closed.</p>

<h2>Accuracy</h2>
<p>Findings are heuristic. They may be wrong, and they may miss things. FIG is
provided as-is, without warranty. Decisions about your site remain yours.</p>

<h2>Your content</h2>
<p>You keep all rights to your site and its content. You give us permission to
fetch and analyse the pages you point us at, only to provide the service.</p>

<h2>Payment</h2>
<p>Plans are billed monthly per site through Stripe. Adding sites changes the
amount from the next invoice. Cancel any time; the current period is not
refunded pro rata unless required by law.</p>

<h2>Liability</h2>
<p>To the extent the law allows, our total liability is capped at what you paid
us in the previous twelve months.</p>

<h2>Changes</h2>
<p>We will note material changes in the <a href="changelog.html">changelog</a>
and email account holders.</p>
"""

COOKIES_PAGE = """
<p>Two cookies, both doing a job. No advertising cookies, no third-party
trackers, no cross-site tracking.</p>

<table class="pg-t">
  <thead><tr><th>Cookie</th><th>What it does</th><th>How long</th></tr></thead>
  <tbody>
    <tr><td><code>fig_did</code></td><td>Recognises this browser, which is what
      keeps the free read to a few per device</td><td>One year</td></tr>
    <tr><td><code>fig_theme</code></td><td>Remembers whether you chose the light
      or dark theme</td><td>One year</td></tr>
    <tr><td><code>fig_consent</code></td><td>Remembers your answer to the cookie
      notice, so it stops asking</td><td>One year</td></tr>
    <tr><td><code>fig_session</code></td><td>Signs you in to the dashboard.
      HttpOnly, only set once you sign in</td><td>Two weeks</td></tr>
  </tbody>
</table>

<h2>Choosing essential only</h2>
<p>The notice offers &ldquo;Essential only&rdquo;. Choosing it removes the
device identifier. The free read then falls back to limiting by network, which
is coarser &mdash; a shared office or campus connection may hit the limit
sooner.</p>

<h2>Clearing them</h2>
<p>Clear site data for this domain in your browser and all of them go. Nothing
is stored anywhere else that could restore them.</p>
"""

CHANGELOG_PAGE = """
<p>What actually shipped, newest first. Things not yet built are marked in the
page that describes them rather than promised here.</p>

<h2>September 2026</h2>
<ul>
  <li><strong>Sign in and sign up.</strong> Supabase Auth, with the access token
    verified server-side and exchanged for a signed HttpOnly session.</li>
  <li><strong>The free read is real.</strong> It crawls the site you give it,
    runs every check, and explains each finding. It used to be a scripted
    demonstration.</li>
  <li><strong>Recent reads.</strong> An anonymous feed of what the free read has
    been finding lately.</li>
  <li><strong>Section order check.</strong> Reports things like pricing sitting
    above the section that justifies it.</li>
  <li><strong>Four layers.</strong> Craft, Structure, Search and Answers, each
    scored separately, every point traceable to a finding.</li>
  <li><strong>Estate reads.</strong> Queue every site on an account at once.</li>
  <li><strong>API and keys.</strong> Provision sites, trigger reads, pull an
    estate report.</li>
  <li><strong>Per-site billing.</strong> Volume tiers, with the subscription
    quantity following the site count.</li>
  <li><strong>These pages.</strong> The footer used to be twenty-four links to
    nothing.</li>
</ul>

<h2>Next</h2>
<ul>
  <li>Scheduled monitoring for verified domains</li>
  <li>Shareable report links</li>
  <li>White-labelled reports for agencies</li>
  <li><a href="webhooks.html">Webhooks</a></li>
</ul>
"""

STATUS_PAGE = """
<div class="pg-note">
  <p><b>No automated status page yet.</b> A green tick that is hard-coded to be
  green is worse than nothing, so this page says what to do when something is
  wrong instead of claiming everything is fine.</p>
</div>

<h2>If a read is stuck</h2>
<p>Reads are queued and typically take one to three minutes depending on how
many pages the site has. A read still queued after ten minutes has probably
failed; the site page will show why.</p>

<h2>Common reasons a read fails</h2>
<table class="pg-t">
  <thead><tr><th>Message</th><th>Means</th></tr></thead>
  <tbody>
    <tr><td>robots.txt disallows fetching</td><td>The site asks crawlers not to read it. We honour that</td></tr>
    <tr><td>could not fetch</td><td>The site was unreachable, timed out, or returned an error</td></tr>
    <tr><td>not HTML</td><td>The URL returned something else &mdash; a PDF, JSON, a redirect loop</td></tr>
    <tr><td>nothing could be read</td><td>The page rendered no server-side HTML. Heavily client-rendered sites can do this</td></tr>
  </tbody>
</table>

<h2>Something else</h2>
<p>Email <a href="mailto:{contact}">{contact}</a> with the domain
and roughly when you tried.</p>
"""

HISTORY_BODY = """
<div class="rd-stats">
  <div class="rd-stat"><div class="n" id="rdTotal">&mdash;</div><div class="l">Reads so far</div></div>
  <div class="rd-stat"><div class="n" id="rdAvg">&mdash;</div><div class="l">Average score</div></div>
  <div class="rd-stat"><div class="n" id="rdTop">&mdash;</div><div class="l">Most common finding</div></div>
</div>

<div class="pg-note">
  <p><b>Anonymous unless someone chooses otherwise.</b> A domain appears here
  only when the person who ran the read ticked the box to share it. A site is
  never named because a stranger pointed FIG at it &mdash; there is no
  leaderboard here, deliberately. See <a href="privacy.html">privacy</a>.</p>
</div>

<div class="rd-list" id="rdList">
  <div class="rd-empty">Loading recent reads&hellip;</div>
</div>

<p class="pg-meta" style="margin-top:26px">
  <a href="demo.html">Run your own read &rarr;</a>
</p>
"""

HISTORY_SCRIPT = """<script>
(function () {
  'use strict';
  var list = document.getElementById('rdList');

  function ago(iso) {
    if (!iso) return '';
    var s = Math.max(0, (Date.now() - new Date(iso + (iso.endsWith('Z') ? '' : 'Z'))) / 1000);
    if (s < 90) return 'just now';
    if (s < 3600) return Math.round(s / 60) + 'm ago';
    if (s < 86400) return Math.round(s / 3600) + 'h ago';
    return Math.round(s / 86400) + 'd ago';
  }
  function nice(check) {
    return (check || '').replace(/_/g, ' ');
  }

  fetch(FIG_API + '/reads/recent')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      document.getElementById('rdTotal').textContent = d.total || 0;
      document.getElementById('rdAvg').textContent =
        d.average_score === null || d.average_score === undefined ? '—' : d.average_score;
      var top = (d.most_common || [])[0];
      var el = document.getElementById('rdTop');
      el.textContent = top ? nice(top.check) : '—';
      el.style.fontSize = '15px';
      el.style.lineHeight = '1.3';

      if (!d.reads || !d.reads.length) {
        list.innerHTML = '<div class="rd-empty">No reads yet. ' +
          '<a href="demo.html" style="color:var(--text)">Be the first</a>.</div>';
        return;
      }
      list.innerHTML = d.reads.map(function (r) {
        var who = r.site
          ? '<b>' + r.site + '</b>'
          : '<span class="rd-anon">a ' + (r.pages || 1) + '-page site</span>';
        return '<div class="rd-row">' +
          '<div class="rd-score">' + (r.score === null ? '—' : r.score) + '</div>' +
          '<div class="rd-what">' + who +
            '<span>' + (r.top_check ? nice(r.top_check) + ' · ' + (r.top_layer || '') : 'nothing flagged') + '</span>' +
          '</div>' +
          '<div class="rd-when">' + ago(r.at) + '</div>' +
        '</div>';
      }).join('');
    })
    .catch(function () {
      list.innerHTML = '<div class="rd-empty">Could not load recent reads. ' +
        'The API may not be running.</div>';
    });
})();
</script>"""



PRICING_PAGE = """
<div class="pr-cards">
  <div class="pr-card">
    <span class="pr-k">Solo</span>
    <div class="pr-p"><b>$20</b><span>per site / month</span></div>
    <p class="pr-for">Your own site, or a couple of projects.</p>
    <a class="pr-cta" href="#" data-app="/signup">Start free week</a>
    <ul class="pr-list">
      <li>Up to 4 sites</li>
      <li>All four layers, every check</li>
      <li>A why and a fix on every finding</li>
      <li>Unlimited manual audits</li>
      <li>Full API access</li>
    </ul>
  </div>

  <div class="pr-card pr-best">
    <span class="pr-flag">Most agencies land here</span>
    <span class="pr-k">Studio</span>
    <div class="pr-p"><b>$12</b><span>per site / month</span></div>
    <p class="pr-for">A client roster of 25 to 99 sites.</p>
    <a class="pr-cta pr-cta-solid" href="#" data-app="/signup">Start free week</a>
    <ul class="pr-list">
      <li>Everything in Solo</li>
      <li><b>White-labelled reports</b> &mdash; your logo, no FIG chrome</li>
      <li>Estate audits: every site queued at once</li>
      <li>Scheduled monitoring on verified domains</li>
      <li>Findings grouped across the whole roster</li>
    </ul>
  </div>

  <div class="pr-card">
    <span class="pr-k">Platform</span>
    <div class="pr-p"><b>$5&ndash;9</b><span>per site / month</span></div>
    <p class="pr-for">300 sites and up, or embedding FIG in your own product.</p>
    <a class="pr-cta" href="contact.html">Talk to us</a>
    <ul class="pr-list">
      <li>Everything in Studio</li>
      <li>Wholesale rate with a volume floor</li>
      <li>Per-site provisioning over the API</li>
      <li>Results rendered inside your own UI</li>
      <li>A named person to email</li>
    </ul>
  </div>
</div>

<p class="pr-note">Every tier includes every check. The rate changes with estate
size; the product does not.</p>

<div class="pr-trial">
  <b>Your first week is free.</b>
  <span>No card. The account starts on a seven-day trial the moment you create
  it, so nothing can begin billing without a decision from you.</span>
  <a class="btn21 btn21-solid" href="#" data-app="/signup"><span>Start free week</span></a>
</div>

<h2 id="how">You pay per site, not per person</h2>
<p>This is the part worth understanding before the numbers, because it is the
thing most tools get backwards. An agency with three logins and four hundred
client sites pays for <strong>four hundred</strong>, not three. A solo owner
with one site pays for one.</p>
<p>Charging per seat would mean a three-person agency auditing four hundred
sites for the price of three logins. That is not a discount, it is a broken
meter &mdash; and it would mean the product could not survive its best
customers.</p>

<h2 id="tiers">Rates</h2>
<p>The rate is <strong>volume</strong>, not graduated: at 30 sites every site
costs the 30-site rate, rather than the first four costing more. Whatever your
estate size, one number applies to all of it.</p>

<table class="pg-t pr-tiers">
  <thead><tr><th>Sites</th><th>Per site / month</th><th>At the top of that tier</th><th>Who this is</th></tr></thead>
  <tbody>
    <tr><td>1&ndash;4</td><td>$20.00</td><td>$80</td><td>Your own site, or a couple of projects</td></tr>
    <tr><td>5&ndash;24</td><td>$15.00</td><td>$360</td><td>A freelancer with a handful of clients</td></tr>
    <tr><td>25&ndash;99</td><td>$12.00</td><td>$1,188</td><td>A small agency&rsquo;s client roster</td></tr>
    <tr><td>100&ndash;299</td><td>$9.00</td><td>$2,691</td><td>An SEO agency, or a multi-location group</td></tr>
    <tr><td>300&ndash;999</td><td>$7.00</td><td>$6,993</td><td>A platform, or a franchisee network</td></tr>
    <tr><td>1,000+</td><td>$5.00</td><td>&mdash;</td><td>Talk to us about a floor and a contract</td></tr>
  </tbody>
</table>

<h2 id="included">What every plan includes</h2>
<ul>
  <li><strong>All four layers.</strong> Craft, Structure, Search and Answers.
    There is no tier that withholds half the product.</li>
  <li><strong>Every check.</strong> Including the section-order check, which
    nothing else does.</li>
  <li><strong>A written why and fix</strong> on every finding, not just a
    score.</li>
  <li><strong>The full API.</strong> Provision sites, trigger reads, pull an
    estate report. Not gated behind an enterprise call.</li>
  <li><strong>Unlimited manual reads</strong> of the sites on your account.</li>
</ul>

<h2 id="agencies">If you run an agency</h2>
<p>Two things are worth knowing, and neither is behind a sales call:</p>
<ul>
  <li><strong>White-labelled reports.</strong> Your logo, your colours, no FIG
    chrome anywhere your client can see. Most tools gate this at
    &ldquo;Enterprise&rdquo;. We do not, because it is the feature agencies
    actually want and hiding it behind a call is just friction.</li>
  <li><strong>Adding a site is an API call</strong>, not a renegotiation. The
    subscription quantity follows your site count, so site 401 changes the
    invoice by itself.</li>
</ul>
<p><a href="api.html">See the API</a> or
<a href="contact.html">get in touch</a> about a volume floor.</p>

<h2 id="free">The free read</h2>
<p>Anyone can read any public site, without an account, a few times a day per
browser. No ownership proof required &mdash; studying a site you admire to
work out why it holds together is how most people learn, and locking that
behind a login would kill the most useful thing here.</p>
<p><a href="demo.html">Run one now &rarr;</a></p>

<h2 id="faq">Questions people actually ask</h2>

<h3>What counts as a site?</h3>
<p>One hostname. <code>example.com</code> and <code>shop.example.com</code>
are two. Pages within a site are not charged separately.</p>

<h3>What happens after the free week?</h3>
<p>Nothing automatic. There is no card on file, so it cannot start charging
you. Your reads stay visible and you decide whether to subscribe.</p>

<h3>Can I change how many sites I have?</h3>
<p>Any time, in either direction. Adding sites is billed pro rata from the
next invoice; removing them stops the charge. An annual commitment can set a
floor if you would rather lock a rate.</p>

<h3>Do you charge per page?</h3>
<p>No. A read covers up to 40 pages of a site by default and that is included.
Very large estates &mdash; catalogues in the thousands of pages &mdash; are a
conversation rather than a checkbox; <a href="contact.html">say hello</a>.</p>

<h3>Is there a free plan?</h3>
<p>There is a free <em>read</em>, permanently, for anyone. There is no free
tier of the dashboard beyond the trial week, because a scheduled crawler that
costs us money on a schedule cannot be free forever without becoming somebody
else's bill.</p>

<h3>Can I cancel?</h3>
<p>Whenever you like, from the billing page. You keep access until the end of
the period you have paid for.</p>

<div class="pg-note">
  <p><b>One thing we will not sell you.</b> There is no plan that lets you
  check somebody else&rsquo;s work for AI use, and there never will be. FIG
  reports patterns on sites you choose to read; it does not judge authorship,
  because nothing reliably can. <a href="about.html">Why that matters &rarr;</a></p>
</div>
"""

PAGES = [
    page("pricing",
         title="Pricing — FIG",
         description="Per site, not per seat. Volume rates from $20 down to $5 a site, every feature on every plan, and the first week free with no card.",
         h1="Pricing",
         crumb="Product / Pricing",
         lede="Per site, not per seat. Every plan includes every check — the tiers change the rate, never the product.",
         body=PRICING_PAGE,
         og_type="website"),

    page("rulebook",
         title="The AI slop rulebook — FIG",
         description="Nine patterns that make a web page read as machine-made, why each one lands flat, and what to change. Patterns, not accusations.",
         h1="The AI slop rulebook",
         crumb="Learn / Rulebook",
         lede="Nine patterns that make a page read as machine-made — what each one is, why it lands flat, and the change that fixes it.",
         meta="Updated September 2026 · 6 minute read",
         body=RULEBOOK),

    page("glossary",
         title="Glossary — FIG",
         description="Plain definitions for the terms FIG uses: AI slop, GEO, AEO, section order, structured data, crawl budget, and the four layers.",
         h1="Glossary",
         crumb="Learn / Glossary",
         lede="Plain definitions for everything FIG reports on, without the jargon that usually surrounds it.",
         body=glossary_body()),

    page("spotting-ai-pages",
         title="Spotting AI-written pages — FIG",
         description="Why you cannot reliably detect AI authorship, what is actually observable about a page, and the better question to ask instead.",
         h1="Spotting AI-written pages",
         crumb="Learn / Spotting",
         lede="Why nobody can reliably detect authorship, what is genuinely observable, and the more useful question to ask instead.",
         body=SPOTTING_PAGE),

    page("schema-for-crawlers",
         title="Schema for AI crawlers — FIG",
         description="The two JSON-LD blocks almost every site needs, the rules that actually matter, and why structured data decides whether a model can quote you.",
         h1="Schema for AI crawlers",
         crumb="Learn / Schema",
         lede="The two structured-data blocks almost every site needs, and why they decide whether a model can quote you at all.",
         body=SCHEMA_PAGE),

    page("robots-reference",
         title="robots.txt reference — FIG",
         description="A working robots.txt, the named AI crawler agents, and the difference between blocking training and blocking citation.",
         h1="robots.txt reference",
         crumb="Learn / robots.txt",
         lede="A file that fits on a postcard, the AI crawler agents worth knowing by name, and the distinction most people get wrong.",
         body=ROBOTS_PAGE),

    page("fix-recipes",
         title="Fix recipes — FIG",
         description="The longer version of every fix FIG suggests: uniform cards, default palettes, flat type scales, section order, structured data, alt text.",
         h1="Fix recipes",
         crumb="Learn / Fixes",
         lede="Every fix FIG suggests, in the longer form — for when the one-line version is not enough.",
         body=FIX_RECIPES),

    page("blog",
         title="Blog — FIG",
         description="Notes on what makes a page legible to a reader, a crawler, and a model being asked about you.",
         h1="Blog",
         crumb="Learn / Blog",
         lede="Notes on what makes a page legible — to a reader, to a crawler, and to a model being asked about you.",
         body=blog_body()),

    page("docs",
         title="Docs — FIG",
         description="How to use FIG: the four layers, how findings are reported, the API, domain verification and rate limits.",
         h1="Docs",
         crumb="Build / Docs",
         lede="What FIG checks, how it reports it, and how to drive the whole thing from your own product.",
         body=DOCS_PAGE),

    page("api",
         title="API reference — FIG",
         description="Provision sites, trigger reads, and pull results into your own product. The API is the primary interface; the dashboard is built on it.",
         h1="API reference",
         crumb="Build / API",
         lede="Provision a site, read it, pull the result into your own product. Your customer never has to leave it.",
         body=API_PAGE),

    page("domain-verification",
         title="Domain verification — FIG",
         description="Proving domain ownership by DNS TXT record or meta tag. Required only for scheduled monitoring, never for a one-off read.",
         h1="Domain verification",
         crumb="Build / Verification",
         lede="Two ways to prove a domain is yours — and why a one-off read never asks you to.",
         body=VERIFY_PAGE),

    page("webhooks",
         title="Webhooks — FIG",
         description="Be told when a read lands instead of polling for it. Planned shape, events, and signature verification.",
         h1="Webhooks",
         crumb="Build / Webhooks",
         lede="Be told when a read lands, instead of asking repeatedly whether it has.",
         body=WEBHOOKS_PAGE),

    page("about",
         title="About — FIG",
         description="Why FIG exists, what it will never be, and how it is built. A self-check tool, never an accusation tool.",
         h1="About",
         crumb="Company / About",
         lede="Why this exists, what it will never become, and how it works underneath.",
         body=ABOUT_PAGE),

    page("contact",
         title="Contact — FIG",
         description="Get in touch about questions, bugs, wrong findings, agency and platform enquiries, or to ask us to stop reading your site.",
         h1="Contact",
         crumb="Company / Contact",
         lede="One person builds this. You will get a real reply.",
         body=CONTACT_PAGE),

    page("security",
         title="Security — FIG",
         description="How to report a vulnerability, how credentials are handled, how the crawler behaves, and the gaps we have not closed yet.",
         h1="Security",
         crumb="Company / Security",
         lede="How to report something, how credentials are handled, how the crawler behaves — and what we have not done yet.",
         body=SECURITY_PAGE),

    page("privacy",
         title="Privacy policy — FIG",
         description="What FIG collects and why, what it never does, the processors it uses, and how to get your data removed.",
         h1="Privacy policy",
         crumb="Company / Privacy",
         lede="We keep as little as we can, we sell nothing to anyone, and there is no advertising or cross-site tracking here.",
         meta="Last updated 7 September 2026",
         body=PRIVACY_PAGE),

    page("terms",
         title="Terms of service — FIG",
         description="The agreement for using FIG, including the uses that are not permitted: accusation, academic integrity processes, and surveillance.",
         h1="Terms of service",
         crumb="Company / Terms",
         lede="Short, and with one section that matters more than the rest.",
         meta="Last updated 7 September 2026",
         body=TERMS_PAGE),

    page("cookies",
         title="Cookie notice — FIG",
         description="The four first-party cookies FIG sets, what each does, how long it lasts, and what changes if you choose essential only.",
         h1="Cookie notice",
         crumb="Company / Cookies",
         lede="Four first-party cookies, each doing a specific job. No advertising, no third-party trackers.",
         meta="Last updated 7 September 2026",
         body=COOKIES_PAGE),

    page("changelog",
         title="Changelog — FIG",
         description="What has actually shipped in FIG, newest first.",
         h1="Changelog",
         crumb="Product / Changelog",
         lede="What actually shipped, newest first.",
         body=CHANGELOG_PAGE),

    page("status",
         title="Status — FIG",
         description="What to do when a read is stuck or fails, and what each failure message means.",
         h1="Status",
         crumb="Product / Status",
         lede="What to do when something is not working, and what each failure message actually means.",
         body=STATUS_PAGE),

    page("history",
         title="Recent reads — FIG",
         description="What the free read has been finding lately. Anonymous by default: a domain appears only if the person who ran the read chose to share it.",
         h1="Recent reads",
         crumb="Product / Recent reads",
         lede="What the free read has been finding lately, live.",
         body=HISTORY_BODY,
         body_extra=HISTORY_SCRIPT,
         og_type="website"),
]


def main() -> int:
    written = []
    for slug, html in PAGES:
        path = SITE / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        written.append(path.name)

    # Point the existing hand-written pages at the real ones.
    link_map = {t: h for _c, links in FOOTER_COLS for t, h in links}
    for name in ("index.html", "demo.html"):
        p = SITE / name
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        before = s
        # replace the whole footer's dead links, matched on their visible text
        for text, href in link_map.items():
            s = re.sub(rf'<a href="#">({re.escape(text)})</a>', rf'<a href="{href}">\1</a>', s)
        s = s.replace('<a href="#">Privacy</a>', '<a href="privacy.html">Privacy</a>')
        s = s.replace('<a href="#">Terms</a>', '<a href="terms.html">Terms</a>')
        s = s.replace('<a href="#">Cookies</a>', '<a href="cookies.html">Cookies</a>')
        s = s.replace('<a href="#">GitHub</a>',
                      '<a href="https://github.com/Duckafaligy/FIG-AI">GitHub</a>')
        s = s.replace('<a class="nav-signin" href="#">Sign in</a>',
                      f'<a class="nav-signin" href="{APP}/login">Sign in</a>')
        s = s.replace('<a href="#learn">Read the AI slop rulebook</a>',
                      '<a href="rulebook.html">Read the AI slop rulebook</a>')
        s = s.replace('<a href="#">Cookie notice</a>', '<a href="cookies.html">Cookie notice</a>')
        if s != before:
            p.write_text(s, encoding="utf-8")
            written.append(f"{name} (links)")

    print(f"wrote {len(PAGES)} pages")
    remaining = 0
    for name in ("index.html", "demo.html"):
        p = SITE / name
        if p.exists():
            # data-app links are rewritten by config.js at load;
            # they are placeholders, not dead ends
            text = p.read_text(encoding="utf-8")
            n = len(re.findall(r'<a(?![^>]*data-app)[^>]*href="#"', text))
            remaining += n
            print(f"  {name}: {n} dead links left")
    return 0 if remaining == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
