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

**Same call, made again on 2026-09-15: no vision-model "here's your fixed
design" feature.** The idea comes up naturally — screenshot the page, send it
to a vision model, get back a mocked-up redesign. Rejected on purpose, twice
over: (1) it's the same cost-shape problem as `content.py:draft()` above —
image tokens and image generation are not the same bill as a batched text
rewrite of already-flagged findings, and (2) it works against the point of
the product. This is a self-check tool for someone learning to see the
pattern themselves; handing back an AI-generated "corrected" design is the
easy path to the redesign itself reading generically, on a tool whose whole
job is catching that. If a screenshot-based feature gets built, the
deterministic-and-cheap version is: Playwright screenshot + rule-based
highlight boxes drawn from the evidence/coordinates checks already produce —
no model in that loop at all. That still means adding Playwright, which
CLAUDE.md's tech stack section marks as not-yet-needed, so it's not a small
addition either.

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
- **Auth:** Supabase Auth (server-side token check built; not yet exercised
  end to end with the frontend)
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

Backend v0.3 (September 2026). `uvicorn app.main:app` boots with nothing
configured: SQLite on disk, API at `/v1`, free read at `/scan`, docs at
`/docs`. See `README.md` for the run steps and the route table.

**Now connected to the frontend:** `FIG_WORKSPACE_API=1` in the local `.env`
mounts `/api` and allows the Next.js dev origins. Set it to 0 to disconnect
again (unmounts `/api`, allows no browser origin); `/v1`, `/scan` and
`/health` are unaffected either way.

- `app/validation.py` — **the validation system**, and the reason the crawler
  cannot be used as an SSRF proxy. Syntax first (no IP literals, no reserved
  names like `localhost` or `*.internal`, http(s) only, standard ports), then
  DNS: every resolved address must be globally routable. `check_url` re-runs
  both on every request the crawler makes, including each redirect hop and
  each sitemap. Stable error codes, returned by the API. The residual risk
  (DNS rebinding between check and connect) is written up in its docstring.
- `app/robots.py` — robots.txt read the RFC 9309 way: groups by user-agent
  lines only, longest match wins, `*` and `$` wildcards. **Do not switch back to
  `urllib.robotparser`:** it drops every rule after a blank line and applies
  the first matching rule, and on launchvault.ca it let the crawler read
  `/login` and `/signup` against the site's robots.txt (found in Test #1).
- `app/scraper.py` — every request goes through `_http_get`: validated,
  robots-checked on every hop, redirects followed by hand, bodies capped at
  5 MB, one request per host at a time. `crawl()` resolves the base, discovers
  URLs from the sitemap (stdlib XML parser — BeautifulSoup's `"xml"` mode needs
  lxml, which was silently missing and had broken discovery on every scan),
  then goes breadth-first over internal links, filling a `CrawlReport` with
  every page read or skipped and why. `parse_html` is still a pure function.
  Empty blocks (no words, images or controls) are not counted as sections.
  **No JavaScript execution — `requests` + BeautifulSoup only.** This is the
  scraper's real ceiling, not the page-count or robots limits: a client-rendered
  route (content that only appears after a client component mounts/fetches)
  reads as thin or empty rather than erroring loudly, so a scan can quietly
  under-report a JS-heavy site instead of failing on it. Worth a "this page
  may need JS to render" signal before Playwright is worth adding for it.
- `app/rules/checks.py` — **18** deterministic checks across four layers:
  craft (the original six), structure, search, answers. Every `Flag` carries
  its own `why` and `fix`.
- `app/rules/sections.py` — section role classification and the order check.
  This is the one the product leads with: it reports things like pricing
  sitting above the section that justifies it.
- `app/rules/scoring.py` — four layer scores plus a weighted headline.
  Findings are counted per check, not per page, so a 40-page scan is not
  punished for one site-wide mistake.
- `app/pipeline.py` — validate → resolve base → robots → discover → fetch →
  rules → explain → score → persist, every stage written to `Scan.trace` and
  served at `GET /v1/scans/{id}/trace`.
- `app/ai_explain.py` — the one LLM call, `claude-haiku-4-5` by default
  (`FIG_AI_MODEL`). It is sent one item per *distinct* finding plus the
  hostname, never page content, and the prompt is layer-aware so only craft
  findings are framed as generic or AI-made. Tokens and cost land in the trace.
- `app/jobs.py` — DB-backed queue and worker threads. An estate scan is a
  queue depth, not a long request.
- `app/models.py` — `Account` → `Site` → `Scan` → `Finding`/`Page`, plus
  `ApiKey`, `Job`, `User`. **The meter is sites, not seats.** A column added to
  an existing table also goes in `app/db.py:_ADDED_COLUMNS`, because
  `create_all` never alters a table.
- `app/api.py` — `/v1` with API-key auth: provision a site, scan one or the
  whole estate, poll a scan and pull its pages and trace, pull `/v1/report` as
  a partner-renderable roll-up, run ownership verification. `GET /v1/checklist`
  (no auth, no scan needed, mirrors `/v1/layers`) serves
  `rules/checks.py:CHECKLIST` — every deterministic check and what triggers
  it, so a user or partner UI can see what a scan actually looks for.
- `app/public.py` — `/scan`, the free read: validated, capped per browser, per
  network and globally per day. `X-Forwarded-For` is only trusted when
  `FIG_TRUST_PROXY=1`.
- `app/auth.py` — `fig_live_*` keys, SHA-256 stored, plaintext shown once.
- `app/billing.py` — Stripe: graduated per-site tiers, checkout, portal,
  webhook, and `sync_quantity` so provisioning changes the invoice without a
  renegotiation. Degrades quietly with no key.
- `scripts/test_run.py` — the end-to-end test: starts the API disconnected,
  drives it over HTTP, scans a real site with the real key, cross-checks the
  database, and appends `## Test #N` to `Test Runs.md`. **Read a run's output,
  not just its pass count** — Test #1 passed 53/53 and still hid three bugs.
### Two processes: API here, frontend in `frontend/`

**This backend serves no HTML.** The Jinja frontend it used to render was
archived to `archive/jinja-frontend-2026-09-13/` when the frontend moved to
its own Next.js 16 app in `frontend/`, built separately. This process is JSON
only. Do not add templates back.

`frontend/` has its own `AGENTS.md`: **Next 16 differs from training data —
read `frontend/node_modules/next/dist/docs/` before writing any Next code.**
Two differences that already bit: `cookies()` is async (`await cookies()`),
and `searchParams` is a Promise in Server Components.

**Two APIs, deliberately different:**

- `/v1` (`app/api.py`) — the **partner** API. `fig_live_*` key auth,
  versioned, stable, meant to be embedded by an agency or a platform
  reselling FIG. Changing it breaks someone else's build.
- `/api` (`app/webapp.py`) — the **workspace** API, for our own frontend.
  Session-cookie auth, one endpoint per surface (a page does one request, not
  eleven), free to change alongside the UI. Every endpoint delegates to
  `app/pages.py`, so there is one implementation of "what is on the overview"
  rather than two that drift.

`app/pages.py` returns JSON-safe payloads. It keeps a few `_`-prefixed keys
holding ORM objects for its own internal use; `webapp._public()` strips
anything starting with `_` before it leaves the process. **Read its docstring
before touching it** — the zero-versus-unknown rule below lives there.

- **A real zero renders `0`. Something not knowable yet renders `null`**,
  which the frontend draws as an em dash with a note naming what it needs
  (Search Console, the model-visibility crawl, a keyword source). Nothing is
  estimated to make a panel look alive. Gaps are tagged `NEEDS:`.
- `app/demo.py` supplies filler metrics **for the seeded demo account only**,
  derived from a hash of the site id so figures never jump between reloads.
  Any other workspace still gets `null`. One module, easy to delete.

**The frontend's data layer** (added here, kept additive so it never collides
with frontend work in flight):

- `frontend/lib/api.ts` — typed client. `apiServer` forwards the session
  cookie from a Server Component; `apiClient`/`apiSend` use
  `credentials: "include"` from the browser. Nothing throws: every call
  returns a result object so the UI can fall back to its static preview.
- `frontend/lib/live.ts` — `fetchOverlay()` on the server produces a **plain
  JSON overlay** of values keyed by the `area` names the design already sets;
  `applyOverlay()` on the client merges it into the statically imported page.
  The split exists because `DashboardPage.icon` is a lucide component and a
  function cannot cross the server/client boundary.
- Wiring a designed page is two lines — see `frontend/app/app/live/page.tsx`,
  a diagnostics route that shows connection state and renders each surface
  live. The design in `frontend/lib/dashboard-pages.ts` stays the source of
  truth for structure; the overlay only replaces values.

- `app/dashboard.py` + `templates/dash/` (archived) — the previous dashboard: an
  overview built to the Figma design, the sites list and site detail, findings
  across the estate, notifications, history, and settings (account, billing,
  keys, integrations, and the checklist from `app/roadmap.py`).
- `app/publishing.py` — mechanical findings become queued changes. Nothing is
  written without approval and every change keeps a before-state so it can be
  reverted. Judgement calls stay advice. No CMS adapter is written yet, so
  `publish()` refuses out loud rather than pretending.
- `app/secrets_store.py` — Fernet encryption (key: `FIG_SECRET_KEY`) around
  whatever `Integration.credential_ref` points at (table: `Secret` in
  `app/models.py`). Not a real vault — one symmetric key, good enough to stop
  a database dump handing over live tokens, meant to be swapped out before
  this fronts real customer CMS credentials at scale. `store_secret`/
  `read_secret`/`update_secret`/`delete_secret`; every call raises
  `SecretsNotConfigured` rather than writing plaintext if the key is unset.
- `app/oauth.py` — `/oauth/{platform}/start` and `/oauth/{platform}/callback`,
  mounted unconditionally (like `billing_router`) since a platform's redirect
  URI has to be stable regardless of `FIG_WORKSPACE_API`. Only Google
  (Analytics, `analytics.readonly`, read-only) is wired up; `state` is a
  signed, 10-minute-lived token (reuses `FIG_SESSION_SECRET`) carrying the
  site/account being connected, so the callback can't be replayed or pointed
  at a site the caller doesn't own. The token exchange happens server-side —
  Google's code and the resulting access/refresh tokens never reach browser
  JS. Every other OAuth platform in the roadmap (all but WordPress, which
  uses Application Passwords, not OAuth) follows this same three-step shape.
- `app/ga.py` — the GA4 Data API client `app/oauth.py` hands off to: reads
  the stored token via `app/secrets_store.py`, refreshes it against Google
  when expired, auto-discovers the connected account's GA4 property (no
  picker yet — first one wins), and returns real sessions/engagement/bounce
  numbers for the overview's `ga` panel, current vs. prior 30 days in one
  request. No connected integration means `None`, same as before this
  existed — `app/pages.py` never guesses a number.
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
- `test_local.py` — the rules engine; passes with no network and no API key.
- `test_backend.py` — the validation system, robots.txt (RFC 9309), the
  crawler's network rules against a fake network, and the AI step's grouping
  and usage accounting; no network, no database, no key.

**Auth:** wired end to end and verified against a real Supabase user and the
real Postgres database (2026-09-16) — `frontend/components/auth-form.tsx`
calls Supabase directly for sign-in/sign-up, exchanges the access token for
this app's session cookie via `POST /api/session`
(`frontend/lib/api.ts:actions.signIn`), and `frontend/app/app/layout.tsx`
gates every `/app/*` route server-side, redirecting to `/signin` only when
the backend affirmatively answers "not signed in" — an unreachable backend
still falls back to the static preview rather than locking everyone out.
Sign-out is wired from the dashboard's account menu. `FIG_DEV_NO_AUTH` must
stay `0` for this gate to mean anything; `.env` already has it at `0`.
**Google/Shopify "continue with" buttons on the auth form are still
placeholders** — only email/password goes through Supabase for now.

## Not yet wired up — the real next steps, roughly in order

1. **Scheduled Watches** — `Site.monitor` / `monitor_days` exist and nothing
   reads them yet. APScheduler enqueueing the same jobs is the whole task.
2. **Tune the reference lists and the role patterns.** This matters more than
   new checks. Run real generated sites and real hand-made ones through the
   engine until they separate cleanly — `scripts/test_run.py` is how. Known
   weak spots: section role classification over-matches `pricing` on pages
   that quote figures in prose; and where a page's body lives outside
   `<section>` landmarks (launchvault.ca's legal pages), most of its copy is
   not attributed to any section at all.
3. **Shareable/white-label report output** — a public per-scan URL and a
   branded PDF. This is the growth mechanic, not just a feature.
3b. **CMS write adapters** — WordPress first, still not built. The secret
   store this needed now exists (`app/secrets_store.py`, below), so this is
   down to per-platform adapter code + OAuth app registration, not a missing
   architecture piece. `publish()` in `app/publishing.py` still refuses out
   loud for every platform.
4. **Finish Google Analytics OAuth — one manual step left.** `app/oauth.py`
   (start/callback), `app/secrets_store.py` (`FIG_SECRET_KEY` is generated
   and set locally), `app/ga.py` (reads the stored token, refreshes it,
   auto-discovers the GA4 property, pulls real metrics into `pages.py`'s
   `ga` panel), and the Settings page's real "Connect" button are all done.
   The only missing piece is `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` — a
   Google Cloud Console OAuth 2.0 Client (Web application, redirect URI
   `http://localhost:8000/oauth/google/callback`, consent screen can stay in
   "Testing" mode) that only a human with a Google account can create.
   `app/ga.py`'s property auto-discovery picks the first GA4 property the
   connected account can see — fine for one property, needs a real picker
   before an account with several is more than a coin flip.
5. **Call `POST /scan` from the frontend** — the free read is mounted,
   validated and rate-limited; nothing calls it yet.
6. **Stripe end to end** — the code is there; it has never run against a live
   key.
7. **Pin crawler connections to the validated address** — closes the DNS
   rebinding gap described in `app/validation.py`.

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

Tests with no network, database or API key required:

```bash
python test_local.py      # the rules engine
python test_content.py    # the content queue
python test_backend.py    # validation, robots.txt, crawler network rules, AI accounting
```

The end-to-end run — real network, real database, real Claude tokens (under a
cent). It appends `## Test #N` to `Test Runs.md`; read the output, not just the
pass count:

```bash
python scripts/test_run.py launchvault.ca
```
