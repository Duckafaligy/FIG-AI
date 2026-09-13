# AI Tell Checker — Project Context

This document exists so a fresh Claude Code session has full context on this
project without needing it re-explained. Read this whole file before making
changes or suggestions.

## What this is

A tool that scans websites (and eventually code) for patterns that read as
"generic AI-generated output" — things like numbered eyebrow labels (01/02/03),
uniform rounded-2xl+shadow-lg on every card, default gradient palettes,
overused icons ("Sparkles", "ArrowRight", "Zap"), flat typography hierarchy,
and generic copy ("Elevate your workflow"). For each flag it shows: where,
why it reads as generic, and a concrete fix — not just a score.

## Who it's for, and the ONE rule that shapes everything

Built for students learning web dev / CS who want to understand and improve
their OWN projects. This is a **self-check learning tool, never an accusation
or grading tool.**

**This constraint is not optional and must be preserved in every future
decision:**

- Never position or build this as a way to catch OTHER people's AI use
  (classmates' submissions, coursework grading, plagiarism/collusion checks).
- No feature should give a teacher/admin visibility into an individual
  student's results without that student's explicit choice to share them.
- No public "leaderboard" or shaming feature naming real sites/people.
- Language in the product must always be probabilistic and educational
  ("this pattern is commonly associated with...") — never "this IS AI-written."
- If a future feature idea points toward institutional
  oversight/surveillance, stop and flag it rather than building it. We
  researched this space extensively — Grammarly's "Authorship" and various
  "AI Code Checker" tools built exactly this (institutional, admin-visible
  detection) and it caused real harm: false-positive rates of 5-17%,
  Washington State University had 1,485 false positives in one semester,
  50+ universities have banned AI detectors outright. We are deliberately
  building the other thing.

## Why this is buildable and different from existing tools

We researched the landscape thoroughly before starting:

- **Slopdar** (free novelty "Slop Score" tool) and **avoid-ai-design**
  (a Claude Code skill for auditing AI-generated frontend code) both exist
  but are one-time scanners, not continuous/educational tools.
- **AIWebsiteDetector** is a mature, monetized competitor but focuses on
  *infrastructure* signals (tech stack, security headers, SEO files) —
  NOT visual design taste. It won't tell you your hero section is generic.
- **Grammarly for Education** already dominates the *text/writing*
  AI-detection-for-institutions space (1,000+ seat licenses, SSO, admin
  visibility) — this is exactly why we are NOT pursuing the institutional/
  school-board sales model, at least not as a v1. See the "ONE rule" section
  above.
- The **code AI-detection space** splits into two camps: academic-integrity
  tools (AI Aware's "Code Checker," published CS1-cheating-detection
  research — avoid this framing) vs. developer self-improvement tools
  (AISlop CLI, Span's AI Code Detector — this is our lane).

## Architecture (cost is the whole point — read this before adding AI calls)

```
URL → scraper.py       (pure code, $0 — BeautifulSoup, extracts class names,
                         headings, text nodes, hex colors, inline styles)
    → rules/checks.py  (pure code, $0 — deterministic pattern detection:
                         string/regex matching, counting, bucketing continuous
                         values into ranges, RGB color-distance calculations
                         against a maintained "known AI defaults" reference list)
    → ai_explain.py    (the ONLY place that calls an LLM — receives already-
                         flagged, small structured data, NEVER the raw page.
                         Turns flags into plain-language explanation + fix.)
```

**Do not add AI calls anywhere else in the pipeline.** The whole cost model
depends on 95%+ of the logic being deterministic.

This came up for real when the content queue was built. The queue's whole
purpose is pages that need writing, so "generate the draft" is the obvious
next button — and it is deliberately not built. `app/content.py:draft()`
raises `Refused` with an explanation, and the UI says so on the page. A
900-word generation call is a different cost shape from `ai_explain`'s small
batched flag-rewrites, and it is a decision to take on purpose rather than one
that arrives behind a button. **If it gets built: it needs its own cost cap,
its own file, and Review must stay unskippable** — a queue that writes copy
and publishes it with nobody reading it is the thing this product exists as a
reaction to. If you're tempted to "just
ask the AI" for something a rule could check instead (uniformity, keyword
presence, color similarity, size ratios), write the rule instead.

The "known tells" reference lists (`KNOWN_DEFAULT_COLORS`,
`GENERIC_COPY_PHRASES`, `OVERUSED_ICON_NAMES` in `app/rules/checks.py`) are
the actual differentiating IP of this product. They should be expanded over
time by testing against real AI-generated sites vs. real hand-crafted ones —
this tuning work matters more than adding new categories of check.

## Two-tier product/access model

| Tier | Access | Cost behavior |
|---|---|---|
| **Free / Learning** | Anyone, any public URL, no ownership proof required | Cached **per domain**, refreshed weekly. If 50 users watch the same site, it's scraped once, not 50 times. |
| **Verified / Project** | Requires domain ownership proof (DNS TXT record or `<meta name="ai-tell-verification">` tag — same pattern as Google Search Console) | Unlocks daily scheduled monitoring (included in subscription) + on-demand manual re-checks (metered, deducts credits) |

Ownership verification is **only** required to set up recurring/scheduled
Watches on a specific domain — never for one-off checks. Locking one-off
checks behind ownership would kill the core "study any site to learn from
it" use case (this is literally how the project idea originated — studying
a real competitor's site, Citalis, to understand its design).

## Tech stack

- **Backend:** FastAPI (Python)
- **DB:** Postgres via Supabase
- **Auth:** Supabase Auth (not yet wired up)
- **Scraping:** BeautifulSoup4 + requests (Playwright only if/when computed
  CSS values are needed — not needed for v1)
- **AI:** Claude API (`anthropic` SDK), currently `claude-haiku-4-5-20251001`
  — cheap model, task doesn't need more
- **Scheduled jobs:** APScheduler for v1, consider Celery+Redis only once
  scale requires it
- **Email:** Resend (not yet wired up — needed for verification instructions
  and Watch alerts)
- **Payments:** Stripe (not yet wired up)
- **Hosting:** Railway or Render (not yet deployed)
- **Error tracking:** Sentry (not yet added)

## Current state — what's actually built and tested

Backend v0.2 (September 2026). `uvicorn app.main:app` boots with nothing
configured: SQLite on disk, dashboard at `/app`, API at `/v1`, docs at
`/docs`. See `README.md` for the run steps.

- `app/scraper.py` — fetch, robots courtesy check, and `crawl()`: sitemap
  discovery (robots `Sitemap:` directives, then the conventional paths, one
  level of index nesting) falling back to breadth-first over internal links.
  One request per host at a time, spaced by `CRAWL_DELAY`. `parse_html` is
  still a pure function usable with no network. It now also extracts sections
  in document order, meta/canonical/lang, JSON-LD types, alt coverage,
  internal vs external links and copy-specificity counts.
- `app/rules/checks.py` — **18** deterministic checks across four layers:
  craft (the original six), structure, search, answers. Every `Flag` carries
  its own `why` and `fix`.
- `app/rules/sections.py` — section role classification and the order check.
  This is the one the product leads with: it reports things like pricing
  sitting above the section that justifies it.
- `app/rules/scoring.py` — four layer scores plus a weighted headline.
  Findings are counted per check, not per page, so a 40-page scan is not
  punished for one site-wide mistake.
- `app/pipeline.py` — crawl → rules → score → persist, in one function.
- `app/jobs.py` — DB-backed queue and worker threads. An estate scan is a
  queue depth, not a long request.
- `app/models.py` — `Account` → `Site` → `Scan` → `Finding`/`Page`, plus
  `ApiKey`, `Job`, `User`. **The meter is sites, not seats.**
- `app/api.py` — `/v1` with API-key auth: provision a site, scan one or the
  whole estate, poll a scan, pull `/v1/report` as a partner-renderable
  roll-up, run ownership verification.
- `app/auth.py` — `fig_live_*` keys, SHA-256 stored, plaintext shown once.
- `app/billing.py` — Stripe: graduated per-site tiers, checkout, portal,
  webhook, and `sync_quantity` so provisioning changes the invoice without a
  renegotiation. Degrades quietly with no key.
### The frontend (rebuilt September 2026, to supplied designs)

Eleven pages, server-rendered Jinja, one stylesheet, no build step. Built 1:1
from design images the founder produced; `static/fig.css` is the design system
and `templates/_ui.html` holds every repeated shape as a macro, so a component
change lands on all eleven pages at once.

- `app/frontend.py` — every page route. Thin: resolve the workspace, call
  `pages`, render. **This replaced the page half of `dashboard.py` and
  `public.py`**, whose templates were archived; those two modules are still in
  the tree for their POST handlers but are no longer mounted. `/v1` and billing
  are unaffected.
- `app/pages.py` — one function per page, each a real query against Supabase.
  **Read the docstring before touching it.** The rule it follows: a count that
  is genuinely zero renders `0`; a value that *cannot be known yet* (traffic
  with no Search Console, citations with no model crawl) renders `None`, which
  the templates draw as an em dash plus a note saying what it needs. Zero and
  unknown are different and the UI says which. Nothing is estimated to make a
  panel look alive. Gaps are marked `NEEDS:`.
- `app/charts.py` — line, donut and ring geometry as pure functions, rendered
  as inline SVG. With no data the builders return empty and the macro draws an
  explicit "no data yet" panel rather than an invented curve.
- `templates/site/` — homepage, pricing, sign in, sign up.
- `templates/app/` — projects dashboard, overview, SEO, GEO, notifications,
  history, settings.

The workspace the app pages resolve to is a separate empty account, so the
seeded demo estate is untouched and still available as fillers
(`python -m app.seed`). Sign-in is **not** wired into the new auth pages yet —
the forms say so out loud instead of failing silently.

- `app/dashboard.py` + `templates/dash/` (archived) — the previous dashboard: an
  overview built to the Figma design, the sites list and site detail, findings
  across the estate, notifications, history, and settings (account, billing,
  keys, integrations, and the checklist from `app/roadmap.py`).
- `app/publishing.py` — mechanical findings become queued changes. Nothing is
  written without approval and every change keeps a before-state so it can be
  reverted. Judgement calls stay advice. No CMS adapter is written yet, so
  `publish()` refuses out loud rather than pretending.
- `app/content.py` — the content queue behind `/app/seo`. Findings that need a
  *page* rather than a field edit (an unanswered question, a thin page, copy
  with no figures, a site with no structured data) become briefs, which move
  queued → in progress → review → scheduled → published. `score_post` is nine
  weighted deterministic rules on the draft. **It does not write the prose:**
  `draft()` raises `Refused`. See the AI-calls rule below.
- `app/roadmap.py` — the product checklist, in code so it is visible in the
  product and hard to let drift. Rendered at `/app/settings?tab=roadmap`.
- `app/seed.py` — an invented agency with 22 invented client sites. The
  findings are produced by running fixture pages through the real pipeline,
  not typed by hand.
- `test_local.py` — passes with no network and no API key.

**Auth is still a placeholder.** `FIG_DEV_NO_AUTH=1` resolves every dashboard
request to the seeded demo account. It must be 0 before anything is public.

## Not yet wired up — the real next steps, roughly in order

1. **Auth** — Supabase Auth on the dashboard; `app/auth.py:current_account`
   is the single function that changes.
2. **Scheduled Watches** — `Site.monitor` / `monitor_days` exist and nothing
   reads them yet. APScheduler enqueueing the same jobs is the whole task.
3. **Tune the reference lists and the role patterns.** This matters more than
   new checks. Run real generated sites and real hand-made ones through the
   engine until they separate cleanly. Known weak spot: section role
   classification over-matches `pricing` on pages that quote figures in prose.
4. **Shareable/white-label report output** — a public per-scan URL and a
   branded PDF. This is the growth mechanic, not just a feature.
4b. **CMS adapters and a secret store** — WordPress first. Both the change
   queue and the content queue stop at the same missing piece: there is
   nowhere safe to keep a customer's CMS credential, so `Integration` holds a
   reference and a last-four hint and nothing else.
5. **Wire `site/demo.js` to `POST /scan`** — the marketing demo is still a
   scripted read and says so in its own header comment.
6. **Stripe end to end** — the code is there; it has never run against a live
   key.

## Funding path (for context, not urgent)

Plan is to bootstrap on a lean free tier (cheap model, hard usage caps,
mostly-deterministic architecture keeps cost near-zero per check) rather
than seek funding immediately. If/when needed: Anthropic Startup Program
offers non-dilutive API credits ($1K-$25K+ tiers) but requires an
incorporated company — as the founder is a minor, this requires a parent/
guardian to help incorporate first. An AppSumo-style lifetime-deal launch
is the preferred first funding move (real revenue, no equity given up, no
incorporation prerequisite blocking it).

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
export DATABASE_URL="postgresql://..."   # e.g. from Supabase
uvicorn app.main:app --reload
```

Test the rules engine with no network/API key required:

```bash
python test_local.py
```
