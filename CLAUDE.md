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
- **Auth:** Supabase Auth — live end to end (email/password; Google/Shopify
  "continue with" buttons are still placeholders). Supabase's own email
  templates were replaced with branded HTML on 2026-09-19; its shared default
  email sender is low-volume and returned "Error sending confirmation email"
  under repeated test signups — a real SMTP provider is the fix at any volume.
- **Scraping:** BeautifulSoup4 + requests (Playwright only if/when computed
  CSS values are needed — not needed for v1)
- **AI:** Claude API (`anthropic` SDK), currently `claude-haiku-4-5-20251001`
  — cheap model, task doesn't need more
- **Scheduled jobs:** APScheduler for v1, consider Celery+Redis only once
  scale requires it
- **Email:** Resend (not yet wired up — needed for verification instructions
  and Watch alerts)
- **Payments:** Stripe, **live mode since 2026-09-21** — checkout, portal and
  webhook (see roadmap item 6). Payouts are off until the account's ID step is
  finished. Local `.env` holds the live key too, so scripts and tests that
  touch Stripe act on real money: use the sandbox account's `sk_test_` key for
  anything experimental, and never point Render at it.
- **Hosting:** Render (backend, free tier, `render.yaml`) + Vercel (frontend).
  Railway and Fly.io no longer have free tiers. UptimeRobot pings `/health`
  every 5 minutes so Render's free tier doesn't sleep. See `PLATFORMS.md`.
- **Error tracking:** Sentry — wired 2026-09-22 for the backend, gated on
  `SENTRY_DSN` (unset = off). See roadmap item 9 and `PLATFORMS.md`.

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
  each sitemap. Stable error codes, returned by the API. DNS rebinding is
  closed (2026-09-19): `check_url` returns the addresses it just validated and
  `pinned()` forces the connection to use one, via a thread-local
  `socket.getaddrinfo` patch scoped per hostname so concurrent scans of
  different hosts never see each other's pin. `app/scraper.py` pins every
  request. `app/verification.py`'s ownership meta-tag check had a related,
  worse gap found alongside it — zero real-time revalidation (it trusted
  whatever the hostname was when the Site was created) and unrestricted
  redirect-following — now closed the same way, with a bounded, re-validated
  redirect loop.
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
  under-report a JS-heavy site instead of failing on it. **The "this page may
  need JS" signal this section used to call for is built (2026-09-22):**
  `_detect_js_dependency` catches the two real patterns that need no browser —
  an "enable JavaScript" `<noscript>` block (what create-react-app/Vue-CLI/
  Angular-CLI ship almost universally) and a known framework mount point
  (`#root`, `#app`, `#__next`, `#__nuxt`, `#___gatsby`, `#svelte-app`) still
  empty on an otherwise-thin page. It is stored per page
  (`Page.js_dependent`/`js_dependent_reason`, exposed at
  `GET /v1/scans/{id}/pages`) and is deliberately **not** a `Flag` — it costs
  no score, because it isn't a design tell, it's a caveat that the page's
  *other* findings may be incomplete. **Surfaced in the frontend (2026-09-23),
  with zero frontend code changes:** `app/pages.py:_js_rendering_health`
  turns the latest scan's `js_dependent` count into a 5th row on Overview's
  already-live "Workspace Health" panel — that panel was already wired end
  to end to `overview-health`, so this only needed a backend entry with the
  exact shape `frontend/lib/api.ts` already typed for it. Reads "All
  server-rendered" when clean, or "N of M may need JS" with the caveat spelled
  out, never scored.
  `parse_html` also strips React/Next's streaming-SSR Suspense fallback
  markup (`<!--$?-->...<!--/$-->`) before extracting anything — found because
  it put a phantom "Loading your page" `<h2>` on every route of FIG's own
  site; this is a React 18+ wire-format thing, not Next-specific, so it will
  show up on any site built with streaming SSR, not just ours.
- `app/rules/checks.py` — **19** deterministic checks across four layers:
  craft (the original six), structure, search, answers. Every `Flag` carries
  its own `why` and `fix`. **Tuned against FIG's own dogfooded pages
  (2026-09-22), the first real accuracy pass since launch (see CLAUDE.md's
  "tuning is a standing task" note):** `flat_typography` no longer fires on a
  genuine long-form document (one h1, flat h2 sections, real prose under
  each) — only on a page that also fails a words-per-heading-of-60 density
  check, so a thin row of templated cards at the same heading level still
  fires. `check_faq`'s word-count floor moved from 250 to 400
  (`FAQ_MIN_WORDS`): a sub-400-word page reads as a utility page (sign-in,
  contact) far more often than content actually competing to be quoted.
  Running FIG's own rules against FIG's own rendered pages went from 37
  findings to 4 (all `no_answerable_questions` on the two genuinely long
  legal pages, which is a real, if low-priority, finding — adding a short
  Q&A section there would resolve it honestly rather than tuning it away).
  **A second tuning pass (2026-09-23)** found a related, more general
  problem: a page that deliberately opts out of search
  (`<meta name="robots" content="noindex">` — a login screen, a
  password-reset link target) was still getting flagged for missing
  canonical, thin content and no inbound links, none of which mean anything
  once a page has explicitly declined to be found. `NOINDEX_EXEMPT_CHECKS`
  drops `missing_canonical`/`missing_meta_description`/
  `meta_description_length`/`few_internal_links`/`thin_page` on a page
  `PageSignal.noindex` reads true for, while leaving accessibility-shaped
  checks (`missing_lang`, alt text) and structured data alone — found on
  FIG's own `/forgot-password`, but this is a real, general pattern any
  noindexed utility page on any site would trip.
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
  **Orphaned jobs are reclaimed** (`reclaim_stale`, 2026-09-21): a worker that
  dies mid-scan (every Render restart or deploy kills the process) used to leave
  its job `running` forever and its scan spinning for whoever was waiting; two
  were found stuck for over a day in production. Jobs claimed more than 20
  minutes ago are requeued with partial pages/findings dropped, or failed with a
  reason if out of attempts or over 6 hours old. Age-based, not "everything at
  startup", so a rolling deploy can't steal a job the old instance is still
  running. Runs at worker start and every 5 minutes (`test_jobs.py`).
- `app/scheduler.py` — Scheduled Watches: an APScheduler sweep, off by
  default (`FIG_WATCH_ENABLED`), that finds verified/monitored/active sites
  due for a re-scan and calls `app/jobs.py:enqueue_scan` the same way a
  manual audit does. A Watch is a queue depth, same as everything else here.
- `app/models.py` — `Account` → `Site` → `Scan` → `Finding`/`Page`, plus
  `ApiKey`, `Job`, `User`. **The meter is sites, not seats.** A column added to
  an existing table also goes in `app/db.py:_ADDED_COLUMNS`, because
  `create_all` never alters a table. **`TRIAL_DAYS` is 3 (2026-09-23, was 7),
  and it is now enforced, not just displayed:** `Account.trial_expired()`
  gates the three cost-incurring actions in `app/webapp.py` (adding a
  project, auditing one, auditing the estate) with a 402 once the trial has
  run out and nothing is subscribed. Everything else — existing data,
  drafts, settings, billing — stays fully visible and editable, so a lapsed
  trial can still see what it had and subscribe. A subscription always
  overrides it, and an account that was never given a `trial_ends_at` at all
  (a row from before trials existed) is never gated — not having a deadline
  is different from having missed one. The seeded demo account is exempt by
  slug at the call site, since `FIG_DEV_NO_AUTH` and the public showcase
  both resolve to it and its trial (set once, at seed time) is permanently
  in the past. `frontend/lib/legal.ts`'s `TRIAL_DAYS` moved to 3 alongside
  it (`test_pricing_sync.py` fails if the two drift).
- `app/api.py` — `/v1` with API-key auth: provision a site, scan one or the
  whole estate, poll a scan and pull its pages and trace, pull `/v1/report` as
  a partner-renderable roll-up, run ownership verification. `GET /v1/checklist`
  (no auth, no scan needed, mirrors `/v1/layers`) serves
  `rules/checks.py:CHECKLIST` — every deterministic check and what triggers
  it, so a user or partner UI can see what a scan actually looks for.
- `app/public.py` — `/scan`, the free read: validated, capped per browser, per
  network and globally per day. `X-Forwarded-For` is only trusted when
  `FIG_TRUST_PROXY=1`. **The per-domain cache is real now (2026-09-20).**
  It was documented and even implemented (`pipeline.is_cached`) but never
  called by anything, so every free read re-crawled the site. `start_public_read`
  now reuses the latest completed scan of that site (returns `cached: true`)
  and copies `score`/`pages`/`top_check` onto the new `PublicRead` row, because
  `pipeline._record_public` only runs once, when a scan actually finishes.
  `GET /scan/library` is the browsable public library: one row per site, its
  most recent read (`/reads/recent` is the raw per-visit log, where a popular
  cached site repeats). **Register it before `/scan/{scan_id}`** — the path
  parameter route greedily matches "library" and 404s otherwise (this shipped
  broken once). Domains are shown **by default** (2026-09-20 decision): `/scan`
  only ever reads a site's own already-public homepage, never a student's
  private project (that path is account-owned and opt-in via
  `Site.reports_public`), so this is not the leaderboard/shaming case the ONE
  rule forbids. A read can still opt out with `share: false`. Rows recorded
  before this change keep the old anonymous default.
- `app/auth.py` — `fig_live_*` keys, SHA-256 stored, plaintext shown once.
- `app/billing.py` — Stripe: **volume** per-site tiers (not graduated — at 30
  sites every site costs the 30-site rate, matching
  `Account.monthly_cents`), checkout, portal,
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

**Both are deployed for real (2026-09-19)** — `fig-ai-backend.onrender.com`
(Render, free tier, `render.yaml` Blueprint) and `fig-ai-seven.vercel.app`
(Vercel). See `PLATFORMS.md` for every external service and its dashboard.
Two genuinely different domains for the same product surfaced a class of bug
that never shows up in local dev, where frontend and backend are both
"localhost" and count as same-site by accident:

- The session cookie needs `SameSite=None; Secure` once the backend is on a
  real `https://` URL (`app/main.py`) — `Lax` silently drops it on every
  cross-site `fetch()`, which looks exactly like "login succeeds, then
  nothing stays signed in."
- That alone isn't enough. A cookie set by `fig-ai-backend.onrender.com` can
  never be read by `fig-ai-seven.vercel.app`'s own Server Components no
  matter what `SameSite` says — browsers only ever attach a cookie to
  requests aimed at the domain that issued it. Every SSR auth gate and live
  data fetch (`lib/api.ts`'s `apiServer`, used by `/app/layout.tsx` and every
  overlay-driven page) was therefore always forwarding an empty cookie
  header once deployed. Fixed by having `frontend/next.config.mjs` proxy
  `/api/:path*` and `/oauth/:path*` through to the backend
  (`FIG_BACKEND_URL`, server-only), so from the browser's perspective it
  never talks to a different domain at all — the cookie ends up belonging to
  the frontend's own origin, which is what both the browser's later fetches
  and the frontend's own Server Components need. `lib/api.ts` splits
  `CLIENT_BASE` (relative, proxied) from `SERVER_BASE` (direct, for Server
  Components' own server-to-server calls, which were never affected by any
  of this). Making `CLIENT_BASE` relative broke one thing that wasn't
  obviously related: `apiUrl()` also builds the Google OAuth "Connect"
  `<a href>` on Settings, and that 404'd until `/oauth/:path*` was added to
  the same proxy — same lesson twice, add every path the browser actually
  hits, not just the fetch-shaped ones.
- **A third, unrelated bug hid behind the first two**: `api.projects()` and
  `api.settings()` were both defined with `apiServer`, which needs
  `next/headers` — a server-only API — but their real call sites
  (`app/projects/page.tsx`, `app/app/settings/page.tsx`) are both `"use
  client"` components fetching in a `useEffect`. That never worked in a
  deployed browser (`next/headers` doesn't exist client-side), so both pages
  silently showed their static preview for every signed-in account, not just
  ones without a project — indistinguishable from "not wired up yet" until
  traced. Fixed by switching those two to `apiClient` instead; every other
  `api.*` entry runs inside a genuine Server Component and correctly keeps
  `apiServer`.
- `/health` needs `HEAD` too, not just `GET` (`app/main.py`) — an uptime
  monitor's keep-alive ping uses `HEAD`, and the route only accepted `GET`,
  so the monitor's own 405 looked like a real outage.

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
  `NEXT_PUBLIC_DEMO_MODE=1` (2026-09-19) makes that fallback a guarantee: both
  functions short-circuit before touching the network at all, so a
  deployment with this set can never show real data no matter what
  `NEXT_PUBLIC_API_URL` points at. `auth-form.tsx` has the same check before
  it calls Supabase directly (that call bypasses `lib/api.ts` entirely, so it
  needed its own gate). Live at a second, real Vercel project on this same
  `frontend/` directory — one codebase, not a second `frontend-generic/`-style
  copy: `fig-demo` (`https://fig-demo-ecru.vercel.app`), no Supabase env vars
  set at all, alongside the real `fig-ai` (`https://fig-ai-seven.vercel.app`).
  Deploying it surfaced a real bug: `lib/supabase.ts`'s `createClient()`
  validates its URL argument eagerly and throws at construction, not lazily —
  an empty `NEXT_PUBLIC_SUPABASE_URL` crashed the build on every page
  importing `AuthForm`. Fixed with a placeholder URL/key fallback;
  `supabaseConfigured` (unchanged) is still what gates real use.
- `frontend/lib/live.ts` — `fetchOverlay()` on the server produces a **plain
  JSON overlay** of values keyed by the `area` names the design already sets;
  `applyOverlay()` on the client merges it into the statically imported page.
  The split exists because `DashboardPage.icon` is a lucide component and a
  function cannot cross the server/client boundary.
- Wiring a designed page is two lines, and it's now done for all five overlay
  routes (2026-09-17): `/app`, `/app/seo`, `/app/geo`, `/app/notifications`,
  and `/app/history` all fetch their overlay and render through
  `LiveDashboardPage` instead of the static `DashboardPage`. Verified against
  a real signed-in account and site, not just a type-check — see the git log
  for that commit. `frontend/app/app/live/page.tsx` remains as a diagnostics
  route (connection/session state, one page at a time via `?page=`), now
  redundant with the real routes but still useful for debugging a broken
  connection in isolation. The design in `frontend/lib/dashboard-pages.ts`
  stays the source of truth for structure; the overlay only replaces values.
  **Settings (`/app/settings`) and Projects (`/projects`) are different** —
  neither is part of the `LivePageKey` overlay system (their shapes don't
  fit the metric/section model), so each fetches its own endpoint directly
  (`api.settings()`, `api.projects()`) and live-wires what it needs.
  Settings: workspace profile, team, plan, usage, webhook stats, integration
  status — security, notifications, and content-defaults tabs stay
  local-only UI state, since there's no persistence endpoint for them yet.
  Projects: cards, KPIs, SEO/GEO health, top content, distribution,
  activity, the performance table, opportunities, automation, and the real
  "Add project" form — the trend chart and content calendar stay static
  (bespoke components, not this shape).

- `app/dashboard.py` + `templates/dash/` (archived) — the previous dashboard: an
  overview built to the Figma design, the sites list and site detail, findings
  across the estate, notifications, history, and settings (account, billing,
  keys, integrations, and the checklist from `app/roadmap.py`).
- `app/publishing.py` — mechanical findings become queued changes. Nothing is
  written without approval and every change keeps a before-state so it can be
  reverted. Judgement calls stay advice. `app/wordpress.py` is the one CMS
  adapter written so far; `publish()` still refuses out loud for every
  other platform rather than pretending.
- `app/wordpress.py` — the WordPress adapter: Application Passwords, title
  and post-content heading fixes are real, everything else (meta
  description, canonical, lang, schema, alt text) refuses out loud rather
  than guess at a plugin's private field.
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
- `app/search_console.py` — same shape as `app/ga.py`, sharing the same
  Google OAuth client (`app/oauth.py` requests both scopes on one consent
  screen). Discovers the matching verified Search Console property and
  returns real daily clicks/impressions plus top queries — the first real
  day-by-day time series in the product, which is what makes Overview's
  trend chart real for a connected account rather than demo-only.
- `app/content.py` — the content queue behind `/app/seo`. Findings that need a
  *page* rather than a field edit (an unanswered question, a thin page, copy
  with no figures, a site with no structured data) become briefs, which move
  queued → in progress → review → scheduled → published. `score_post` is nine
  weighted deterministic rules on the draft. **It does not write the prose:**
  `draft()` raises `Refused`. See the AI-calls rule below. Review is a gate,
  not a label: editing a *scheduled* post's title or body sends it back to
  Review and clears its date (`reopen_if_scheduled`), because the approval was
  for the text a person read. A scheduled date is a reminder, not a timer —
  nothing publishes on a schedule (no CMS push exists), so a post past its date
  is reported `overdue` (`is_overdue`) instead of quietly still saying
  "scheduled". `_owned` gives one identical answer for "doesn't exist" and
  "isn't yours" so ids can't be probed.
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

1. **Scheduled Watches — done (2026-09-17).** `app/scheduler.py` sweeps
   verified/monitored/active sites hourly (`FIG_WATCH_SWEEP_HOURS`) and
   enqueues a scan through the normal `app.jobs.enqueue_scan` for any whose
   `monitor_days` interval has elapsed, guarding against duplicate-enqueueing
   a site whose previous watch scan hasn't finished yet. Off by default
   (`FIG_WATCH_ENABLED=0`) so nothing runs silently in dev or a test.
   Verified against the real database, not just a type-check — see that
   commit. **Still open:** no API to toggle `Site.monitor`/`monitor_days`
   after a site is created (only settable at `POST /v1/sites` time).
2. **Tune the reference lists and the role patterns — ongoing, not finished.**
   This matters more than new checks. Run real generated sites and real
   hand-made ones through the engine until they separate cleanly —
   `scripts/test_run.py` is how. Three real false positives found this way
   were fixed 2026-09-17 (see that commit): the weak price-heuristic
   outranking named-role keywords, a card grid's first-item heading bleeding
   into the section's own role, and bare-HTML pages losing their body text
   to no section at all. `KNOWN_DEFAULT_COLORS`, `GENERIC_COPY_PHRASES`, and
   `OVERUSED_ICON_NAMES` were also expanded — accuracy-focused (verified each
   new color is genuinely distinct by RGB distance, not padding), not just
   larger. This is a standing task, not a one-time fix: keep running real
   sites through it and watching for the next pattern that doesn't separate
   cleanly.
3. **Shareable report output — done except the PDF (2026-09-17).** The
   public per-scan URL exists: `frontend/app/report/[scanId]/page.tsx`
   renders `GET /scan/{scan_id}` (`app/public.py`), with real Open Graph
   metadata for when the link gets shared. Free-tier reads (`trigger ==
   "demo"`) are always public. Account-owned site scans need explicit
   opt-in — `Site.reports_public`, off by default, toggled from Settings'
   Workspace tab (`POST /api/projects/{id}/share`) — found and closed a real
   gap while building this: `GET /scan/{scan_id}` had no ownership check at
   all before this, serving any scan by id regardless of who owned it.
   **A branded PDF is still not built** — needs a PDF-rendering dependency
   (e.g. WeasyPrint) not yet in `requirements.txt`.
3b. **CMS write adapters — WordPress done (2026-09-17), everything else
   still refuses.** `app/wordpress.py` uses Application Passwords (core
   since WP 5.6, no OAuth needed); `app/publishing.py:connect()` makes a
   real test call and stores the credential via `app/secrets_store.py`;
   `publish()` dispatches to it. Scoped to what WordPress core's REST API
   actually exposes on any install — title and post-content heading
   structure are real; meta description, canonical, lang, schema, and
   `heading_skips` refuse out loud, honestly, because those are
   theme/SEO-plugin output with no stable REST field to target; `missing_alt`
   refuses too (needs a real image description nothing here invents, and no
   per-image id is tracked yet). No real WordPress instance could be stood
   up locally to test against (this machine's Docker has a broken data-root
   config, unrelated to this work) — verified instead with 9 fake-network
   tests plus a request/response-shape check against a real live WordPress
   install (wordpress.org's own) and a full round trip through the actual
   running backend against that same real site. Every other platform
   (Shopify, Webflow, ...) still refuses unconditionally, same as before.

   **Shopify OAuth connect step — done (2026-09-23); the write adapter is
   deliberately still absent.** `app/oauth.py`'s `/oauth/shopify/start` and
   `/oauth/shopify/callback` follow the file's own three-step OAuth shape,
   with the two things Shopify's flow needs that Google's doesn't: the
   authorize URL lives on the merchant's own store
   (`https://{shop}.myshopify.com/admin/oauth/authorize`, so `/start` takes a
   `shop` query param, validated against `^[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com$`
   both when supplied and again when Shopify echoes it back), and the
   callback's whole query string is HMAC-SHA256 verified against the app's
   client secret (Shopify's documented algorithm, constant-time compared) —
   proof the redirect really came from Shopify, not a forged URL carrying a
   guessed or stolen `code`. `publish()` in `app/publishing.py` already
   refuses out loud for any platform but WordPress, so a connected Shopify
   integration is honest on its own with zero extra code: "Connected," and
   nothing pretends to write through it. **Why no write adapter yet:**
   there is no real Shopify store to verify field names, API version or
   response shapes against — the same bar `app/wordpress.py` had to clear,
   except WordPress's REST API is publicly probeable even unauthenticated
   (verified against wordpress.org's own install) and Shopify's requires a
   real OAuth grant first, so not even that much could be checked here.
   Covered by 13 fake-network tests in `test_oauth_shopify.py`, including a
   genuinely-computed HMAC (the same algorithm the endpoint itself runs,
   used to prove the verification is actually correct — not just "some
   function got called") and confirmed to fail without it by disabling the
   check and rerunning. **Found and fixed in the same pass:** `app/pages.py`'s
   `_api_rows()` named the Shopify row `"Shopify Store API"` against a
   static `"Shopify"` in `frontend/app/app/settings/page.tsx` — the exact
   same class of bug the Search Console naming mismatch already was (see
   roadmap item 4b), just never noticed because nothing had tried to
   connect Shopify yet. Now covered by
   `test_settings_integration_names_match_the_frontends_static_list` in
   `test_backend.py`, which reads both files for real rather than hardcoding
   a second copy of either list, so it can't itself drift out of sync.
   Settings' Integrations tab has a real "Connect" flow for it now (a small
   store-domain form, since Shopify has no one fixed authorize URL to link
   straight to).
   **Pre-launch checklist for Shopify:** a real app logo/icon (cosmetic for
   the private Custom app this is today, but worth doing before launch
   regardless); the "convert to a Public app on the Shopify App Store"
   question stays parked on purpose (2026-09-23 decision) — it's a separate
   business decision (Shopify's own billing, its own App Store review, a
   second revenue relationship that doesn't automatically tie to FIG's own
   Stripe subscriptions), not something to do because Shopify's dashboard
   nudges toward it. **Found live on Render (2026-09-23):** `SHOPIFY_CLIENT_ID`/
   `SHOPIFY_CLIENT_SECRET` were added, but not `SHOPIFY_OAUTH_REDIRECT_URI` —
   `SHOPIFY_OAUTH_ENABLED` only checks the first two, so `/health` correctly
   read `true` while the actual authorize redirect being sent was still
   `http://localhost:8000/...`, which Shopify would have rejected outright on
   a real attempt. Proven with a real request through the live proxy (a
   disposable account, `/api/projects`, then `/oauth/shopify/start`), not
   assumed from `/health` alone — worth remembering for the next platform
   too: a "some keys are set" boolean is not the same claim as "the actual
   request is correctly formed." **Re-check before trusting a live
   connection attempt** — this was flagged as unresolved at the point this
   note was last written and hasn't been re-verified since.

   **Webflow OAuth connect step — coded, tested and deployed (2026-09-23).**
   `app/oauth.py`'s `/oauth/webflow/start` and
   `/oauth/webflow/callback` follow the same three-step shape, but Webflow's
   flow needs none of Shopify's extra machinery — it's shaped like Google's:
   one fixed authorize URL (`https://webflow.com/oauth/authorize`), no
   per-merchant shop domain, no HMAC-signed callback, just the signed
   `state` token every platform here already carries. Scope requested:
   `cms:read cms:write pages:read pages:write sites:read`
   (`WEBFLOW_SCOPE`). Same honesty pattern as Shopify: `publish()` in
   `app/publishing.py` still refuses out loud for any platform but
   WordPress, so a connected Webflow integration says "Connected" and
   writes nothing through it — no real Webflow site exists yet to verify a
   write adapter's field names or API shape against, so none is built.
   Covered by 13 fake-network tests in `test_oauth_webflow.py`, including
   one proving a stolen/replayed `state` still resolves to the state's own
   signed account rather than whichever account presents it (mirrors
   Shopify's equivalent test). Settings shows a Webflow row with a plain
   Connect link once a real site exists to connect
   (`frontend/app/app/settings/page.tsx`). **Not yet live:**
   `WEBFLOW_CLIENT_ID`/`WEBFLOW_CLIENT_SECRET` aren't set anywhere — no
   Webflow app has been created yet (see `PLATFORMS.md` for the exact
   dashboard steps) — so `/health`'s `webflow_oauth` will read `false`
   until that happens.

   **Wix OAuth connect step — coded and tested (2026-09-23), not yet
   deployed. Genuinely different shape, not a fourth variant of the same
   pattern:** new Wix apps can no longer use a redirect-with-authorization-
   code flow at all — Wix retired "custom authentication" for new apps (see
   `app/oauth.py`'s module docstring and the "wix" section beneath it, and
   [dev.wix.com's OAuth 2 introduction](https://dev.wix.com/docs/api-reference/app-management/oauth-2/introduction)).
   The current model is Wix's **external install flow**: `/oauth/wix/start`
   redirects to a fixed installer URL (`https://www.wix.com/app-installer`)
   carrying the app id, a `shareUrlId` (required for a private/unlisted app
   — see `PLATFORMS.md` for exactly where that GUID comes from), and a
   `postInstallationUrl` with FIG's signed `state` riding along on it,
   exactly the pattern Wix's own docs recommend for passing state through.
   The site owner approves the install on Wix's own screen; Wix redirects
   back to `/oauth/wix/callback` with `instanceId` and `signedInstance` —
   **not** a `code`, so there is no server-side token exchange call at all
   here, unlike every other platform in this file. Wix's client-credentials
   model mints access tokens on demand from `client_id`/`client_secret`/
   `instance_id` whenever one is actually needed (not built yet — no write
   adapter exists to need one), so `instance_id` is the only thing worth
   storing per site, still routed through `app/secrets_store.py` for
   consistency even though it isn't secret on its own.

   **The raw `instanceId` query param is explicitly documented as
   untrusted** — Wix's own warning: "Don't trust an instanceId sent to your
   backend as plain text, as it can be manipulated by an attacker." The
   trust anchor is `signedInstance`: `_wix_verify_signed_instance` in
   `app/oauth.py` verifies it locally (HMAC-SHA256 over the still-
   base64url-encoded, unpadded data string, using the app secret,
   constant-time compared) per the exact algorithm Wix's docs give across
   several language examples, and only the verified payload's own
   `instanceId` is ever stored — the raw query param is never trusted for
   that, confirmed by a test that sends the two values mismatched on
   purpose. Covered by 13 fake-network tests in `test_oauth_wix.py`,
   including one that disables the verification call and confirms the
   tamper-detection test then fails (not vacuously passing) and one proving
   a stolen/replayed `state` still resolves to the state's own signed
   account, mirroring Shopify's and Webflow's equivalent tests. `app/pages.py`'s
   `_api_rows()` got a `"Wix"` row in the same pass that added the Settings
   Connect link, both named to match exactly — the Shopify naming mismatch
   (see above) made this a checked step this time, not an afterthought, and
   `test_settings_integration_names_match_the_frontends_static_list` was
   extended to actually check Webflow and Wix (it had silently only ever
   checked Google/WordPress/Shopify, even after Webflow shipped — found and
   fixed in the same pass). **Not yet live:** `WIX_CLIENT_ID`/
   `WIX_CLIENT_SECRET`/`WIX_SHARE_URL_ID` aren't set anywhere — no Wix app
   has been created yet (see `PLATFORMS.md` for the exact dashboard steps,
   including where the `shareUrlId` GUID comes from) — so `/health`'s
   `wix_oauth` will read `false` until that happens.
4. **Google Analytics OAuth — done (2026-09-17), real credentials
   configured.** `app/oauth.py`, `app/secrets_store.py`, `app/ga.py` (reads
   the stored token, refreshes it, auto-discovers the GA4 property, pulls
   real metrics into `pages.py`'s `ga` panel), and Settings' real "Connect"
   button are all live against a real `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`.
   `app/ga.py`'s property auto-discovery picks the first GA4 property the
   connected account can see — fine for one property, needs a real picker
   before an account with several is more than a coin flip.
4b. **Google Search Console — done (2026-09-19), reused the same OAuth
   client, no new setup needed.** `app/search_console.py` (same shape as
   `app/ga.py`) pulls real daily traffic/impressions and top queries into
   `pages.py:overview()` — the first real daily time-series source in the
   product, which is what actually makes the trend-chart wiring from
   2026-09-17 show something real for an actual signed-up user instead of
   only the demo account. `app/oauth.py`'s single consent screen now
   requests both Google scopes together and connects whichever the account
   grants. Still open: the estate-level `/projects` page's traffic/
   impressions stay demo-only — summing Search Console across every site on
   that page on every load needs batching/caching first, not a straight
   per-site call.

   Settings' Search Console row had its own frontend bug, found once a real
   deployment made it visible: the static service list named it `"Search
   Console"` while the backend's real integration row is `"Google Search
   Console"` — the exact-match lookup in `settings/page.tsx` never found it,
   and only `isGoogleAnalytics` had the real `/oauth/google/start` href
   anyway. Both fixed; connecting either Analytics or Search Console from
   Settings now grants whichever scopes the account has.

   **Verified end to end against a real Google account (2026-09-19)** —
   full round trip: Settings' Connect button, Google's consent screen, a
   real access/refresh token stored via `app/secrets_store.py`. One
   real-world wrinkle worth knowing about, not a bug: the OAuth consent
   screen is still in Google's **Testing** publishing status, so only
   accounts explicitly added under Test users can get through it at all —
   anyone else sees "hasn't completed verification." A supervised (Family
   Link) Google account additionally needs a parent/guardian to approve the
   request before the actual permission screen ever appears. And because
   Analytics/Search Console scopes are sensitive, a Testing-status app's
   refresh tokens expire after about a week — a connection can go quiet on
   its own and need reconnecting, not a code bug when it does. Submitting
   for verification (a privacy policy, terms, possibly a demo video, a
   review that takes days to weeks) is the real fix for both of these, and
   is worth doing before this reaches anyone outside a small testing group.
5. **`POST /scan` from the frontend — done (2026-09-20).** The homepage hero
   has a real "paste your URL" form (`components/free-scan-form.tsx`, a small
   client island so the page itself stays statically prerendered). It posts to
   `/scan`, polls `/scan/{id}` until done or failed, then navigates to
   `/report/{id}` so the report always opens finished instead of on its
   "still scanning, refresh" state. `/library` (server-rendered, reads
   `/scan/library`) is linked from the nav. `next.config.mjs` proxies `/scan`
   and `/scan/*` like `/api` and `/oauth` — same "add every path the browser
   hits" lesson. **Still open:** the library currently shows one stale row,
   `127.0.0.1:8123`, from before URL validation existed. It is old test data
   in the production database, not a live hole (today's validation rejects
   it), but it sits on a public page. Deleting it is a production-data
   decision left to the owner.
5b. **`/projects` → real data — done (2026-09-17).** Was 100% static, one
   hardcoded demo card, an "Add project" dialog that only explained why it
   couldn't add one. Now fetches `api.projects()` (the shape `app/pages.py`
   already matched field for field) and the dialog is a real form calling
   `actions.addProject()`, which queues a real scan the same way every other
   path does. This was the actual blocker behind everything else wired this
   session: without it, a real signed-in user had no way to get a real site
   into their own account through the UI at all. Verified against a real
   account end to end — see that commit. Left static on purpose:
   `/projects`' own `WorkspaceTrendChart` and the content calendar, both
   bespoke components with their own internal sample-data generators, not
   part of the dashboard's row/stat-overlay shape.
5c. **Trend-chart geometry — wired 2026-09-17, real for Overview since
   2026-09-19.** Overview/GEO/Notifications/History's line charts draw
   `app/charts.py`'s real SVG path geometry
   (`components/dashboard-shell.tsx:LiveTrendChart`) instead of
   `PreviewChart`'s illustrative per-point math, via a `liveChart` field
   threaded through `lib/live.ts`'s overlay. Overview's "Organic Traffic" /
   "Impressions" series now draws from real Search Console daily data
   (`app/search_console.py`) for any real account that's connected it — the
   first check this genuinely closed, not just plumbed. GEO's `platforms`
   and Notifications' `over_time` are still `fill`-gated (demo-account-only)
   — no real per-platform AI-visibility or notification-volume time series
   exists yet. `/projects`' own trend chart and SEO's "Keyword Ranking
   Momentum" bars remain unwired — the former is a different component
   entirely, the latter has no matching `ApiChart` field on the backend yet.
6. **Stripe — done end to end (2026-09-19), including real buttons in the
   product.** Tested against real test-mode keys 2026-09-17, one real bug
   found and fixed then: `stripe.Webhook.construct_event()` returns a typed
   Stripe object, not a dict; every `.get()` call in `webhook()` crashed on
   every real event with `'get' is a dict method, but a Subscription is not
   a dict` — fixed with `.to_dict()`. Two more real bugs found and fixed
   2026-09-19, before any UI was wired: the Stripe product's name/description
   were stale and garbled (fixed via the Stripe API to describe what the
   subscription actually is), and `checkout()`/`portal()` sent Stripe's
   redirect at `config.PUBLIC_URL` — the JSON-only backend's own URL, not
   the Next.js frontend where `/app/settings` lives — so completing checkout
   would have landed on a 404. `app/billing.py`'s logic is now
   `start_checkout()`/`start_portal()`, plain functions both `/v1` (partner)
   and the new `/api/billing/checkout` + `/api/billing/portal` (workspace,
   session-cookie auth) call, so partners and our own frontend share one
   implementation. Settings' billing buttons are real: checkout when
   unsubscribed, the real Stripe customer portal (invoices included, no
   custom invoice UI needed) when subscribed — decided by a real
   `plan.subscribed` flag (`account.stripe_subscription_id` exists), not
   guessed from trial state. Verified against a real (temporary, since
   deleted) account and a real test subscription — checkout's `success_url`
   confirmed pointing at `localhost:3001` after the fix, portal confirmed
   returning a real URL once subscribed.

   **Webhook delivery — done (2026-09-19), once the backend had a real
   public URL to register.** A real endpoint now exists in the Stripe
   dashboard, pointed at `https://fig-ai-backend.onrender.com/v1/billing/webhook`
   with a real `STRIPE_WEBHOOK_SECRET`. Verified against the actual code
   path, not just presence of the secret: a locally-constructed event,
   signed with the real secret exactly as Stripe would sign one
   (`t=<ts>,v1=<hmac-sha256>`), got a real `200 {"received": true}` back —
   proves `stripe.Webhook.construct_event()` and the `.to_dict()` fix both
   still work against the live deployment, not simulated.

   **Correction (2026-09-20) and live mode (2026-09-21).** The paragraph above
   proved the *receiving* side only. Listing `/v1/webhook_endpoints` on the
   sandbox account showed **zero registered endpoints**: a valid signature
   against Render says nothing about whether Stripe is configured to send
   anything. Check the account, not just the secret. Stripe then moved to
   **live mode**: a separate `FIG` account (`sk_live_...`), its own webhook
   endpoint, and a product/price created with
   `python scripts/stripe_setup.py --write` (see `PLATFORMS.md` for the ids).
   The live endpoint was first registered with only two events
   (`checkout.session.completed`, `customer.subscription.updated`) — the
   handler also needs `customer.subscription.created` and
   `customer.subscription.deleted`, or a cancellation never reaches the app.
   `scripts/stripe_setup.py --check` also had the same `.get()`-on-a-Stripe-
   object crash the webhook once had; fixed with `.to_dict()`.
   **Webhook hardening (2026-09-21)** — found by reading the handler while
   testing, then covered by `test_billing.py` (7 of its 13 tests fail on the
   old code): the handler linked an account on *any* `subscription.updated`
   whatever the subscription's status, so a late event for an already-cancelled
   subscription re-linked a cancelled customer, and an `incomplete`
   subscription (first payment not cleared) granted access before money moved.
   The logic is now `billing.apply_event()`, driven by the subscription's own
   status (`active`/`trialing`/`past_due` link; `canceled`/`unpaid`/
   `incomplete_expired` clear), matching on subscription id so ending an old
   subscription never unlinks a newer one. `start_checkout` also refuses (409)
   when the account already has a subscription: only the Settings *button*
   used to switch to the portal, so a second tab could have charged twice.
   **Still open:** one real live purchase, confirmed against the app and then
   refunded, has not been done — until it has, live mode is configured, not
   verified.
7. **Pin crawler connections to the validated address — done (2026-09-19).**
   See `app/validation.py` above. Verified three ways: a fake-network test
   proving the pin overrides resolution and never bleeds across
   threads/hostnames (`test_pinning_closes_the_rebinding_gap`), a full real
   end-to-end crawl of launchvault.ca (54/54, `Test Runs.md`), and a fresh
   real crawl of neverssl.com against the deployed backend. **Process note:**
   this fix was verified locally and then sat uncommitted — the deployed
   backend was running the old code until it was noticed. A green local test
   is not the same as deployed; confirm what is actually live.

8. **Legal pages, password recovery, and a launch audit — built 2026-09-21.**
   `/privacy`, `/terms`, `/refunds` and `/bot` (`frontend/app/*`, one shared
   `components/legal-page.tsx`, facts in `frontend/lib/legal.ts`). Written to
   GDPR Art. 13, CCPA/CPRA, PIPEDA and Google's API Services User Data Policy
   (the Limited Use sentence is required wording), and every factual claim was
   checked against the code, which caught real errors (below). **They are
   drafts until `OPERATOR` in `lib/legal.ts` is filled in** — name, contact
   email, postal address, governing jurisdiction; each page shows a visible
   "Draft" notice until then (`legalIsDraft`). Not legal advice; the founder is a
   minor, so a parent/guardian should read them and decide who the contracting
   party is. Refund policy (14-day money-back on the first payment, cancel at
   period end) is a business default in `REFUND_WINDOW_DAYS`, not a legal
   minimum. `/bot` is what the crawler's user agent links to; it used to point
   at `fig.tools/bot`, a domain FIG doesn't own, and now follows
   `FIG_FRONTEND_URL`. Password recovery: `/forgot-password` and
   `/reset-password` (`components/recovery-form.tsx`), verified end to end with
   a disposable user through Supabase's admin link generator; the tokens live in
   the URL fragment and are scrubbed from the address bar immediately. Social
   login buttons are hidden behind `SOCIAL_LOGIN_AVAILABLE` (they only ever
   showed "will be available"), and the free-scan form now offers the
   anonymous-library opt-out the API always supported.

   **Real bugs the audit found and fixed** (each has tests that fail on the old
   code): (a) `disconnect()` and every reconnect left the encrypted Google token
   / WordPress password in `secrets` forever, so "disconnect deletes your
   token" was false; (b) adding or removing a site never changed the Stripe
   subscription quantity — `sync_quantity` had no caller outside the archived
   dashboard — so customers were under- or over-billed; `billing.try_sync` now
   runs after every add/remove and never fails the request; (c) the privacy
   policy first said "never page content" to the AI provider, but the evidence
   snippets the rules quote (a phrase, a colour, an icon name) do go — the
   policy now says so.

   **Stripe live setup found missing:** no Customer Portal configuration existed
   in live mode, so `start_portal()` would have failed and no customer could
   cancel or update a card. Created (`bpc_1UIFQtEHHPscpAUr2S0fDiT2`, default):
   cancel at period end, no self-service quantity changes (FIG owns the site
   count), invoice history and card updates on.

   **Supabase must be configured or signup and recovery emails go to
   localhost:** Authentication → URL Configuration → Site URL was still
   `http://localhost:3000`, and `/reset-password` is not in the Redirect URLs.
   Email confirmation is required and `signUp` had no `emailRedirectTo`, so every
   real user's confirmation link would have pointed at `localhost:3000`
   (`signUp` now passes one; the dashboard allow-list still has to be set).

   **Built after that audit (same day):** self-serve workspace deletion
   (`app/account_data.py`, `POST /api/account/delete`, Settings → Workspace):
   cancels the Stripe subscription *first* and refuses to delete anything if
   Stripe won't cancel, deletes sites/scans/content/changes/credentials/API keys/
   people, keeps Stripe's invoice records, and removes the Supabase sign-in
   record when `SUPABASE_SERVICE_ROLE_KEY` is set on the backend (it is in
   `render.yaml`). Password resets now end every other session: `User.
   session_epoch` is bumped by `POST /api/session/revoke` (called from the
   reset page) and a cookie from an older epoch stops working; cookies issued
   before epochs existed count as epoch 0, so deploying signed nobody out.
   `app/retention.py` blanks the hashed IP/device identifiers on free scans after
   30 days (run from the job loop). `PATCH /api/settings/profile` has a real
   form. The migration path for the new column is tested against an old-schema
   database (`test_account_lifecycle.py`), because production had no
   `users.session_epoch` until the backend started once after deploy.

   **The site no longer says "preview" or shows invented numbers (2026-09-21).**
   Every public page was rewritten to describe what FIG does today: 19 checks in
   four layers, a free scan of up to 6 pages with no account, real per-site
   volume prices from `frontend/lib/pricing.ts` (held equal to the backend and so
   to Stripe by `test_pricing_sync.py`, with a live calculator). The invented
   outcome stats (+187%, 3.4x, 92%...), the stock-photo "customer quotes", the
   fabricated GEO "AI visibility" figures and the plan/seat/SSO/annual-billing
   pricing were **removed, not relabelled**: a disclaimer does not make a made-up
   testimonial acceptable. The sign-in/sign-up pages had said "no account is
   created from this form" while signup really creates one; that and "Create
   with AI" / "publish" claims (FIG writes and publishes nothing new) are gone.
   The in-app demo screens keep their "sample data" labels: they are honest
   labels on a real demo. **Rule for future copy:** if a claim, number or quote
   can't be traced to code or a real customer, don't ship it.

   **Dogfooding worked.** Running FIG's own rules on FIG's own rendered pages
   found 37 findings (overused arrow/sparkles icons, a 182-character meta
   description, no canonical link and no JSON-LD on any page, flat `h2`-only
   auth pages, the stale "Content that gets found" title) and got it to 14. The
   remainder are false positives worth **tuning in `app/rules/checks.py`**, not
   fixing in the site: `flat_typography` and `no_answerable_questions` fire on
   long legal documents and auth forms where a lone `h1` over many `h2` sections
   and no Q&A block are correct. (`numbered_eyebrows` also fired on the legal
   pages' "1." section labels; those now come from a CSS counter, which is
   cleaner anyway.) Run it again after any large copy change:
   `next start`, fetch pages, `parse_html` + `run_all_checks`.

   **Production-data cleanup needs a human.** The auto-mode permission system
   blocked a bulk delete of test accounts and stale library rows in the live
   database, correctly. It is now `scripts/cleanup_test_data.py` (dry run by
   default, `--apply` to delete, fixed named list, guards on each deletion) to
   be read and run by the owner: `python scripts/cleanup_test_data.py`. It
   refuses to run until the backend has migrated `users.session_epoch`.

   **Still open, found here and not built:** (1) ~~the trial is not
   enforced~~ done 2026-09-23, see `app/models.py`'s entry above — it is now
   3 days and actually gates scanning; (2) Supabase's shared email sender
   only delivers to team members and is rate-limited, so signup and recovery
   emails still need real SMTP (which needs a domain to send from) — but
   ~~the dashboard Site URL / Redirect URLs still point at localhost~~ fixed
   2026-09-22 (Site URL is `https://fig-ai-seven.vercel.app`; `/signin` and
   `/reset-password` are both allow-listed; verified with a real
   `generate_link` call, not just read from the dashboard); (3) the
   Google consent screen is published but **unverified** (100-user cap, warning
   screen) until there is a custom domain and a logo; (4) ~~`PLATFORMS.md`'s
   Sentry is still not added~~ done 2026-09-22, see below; (5) the Watch
   scheduler is off by default (`FIG_WATCH_ENABLED=0`), so nothing may claim
   daily monitoring.

   **A second AI tool has been editing `frontend/` concurrently since
   2026-09-22** (via a separately-installed agent-plugin flow, pushing
   straight to `main`) — worth knowing before touching any public page, and
   the reason recent frontend commits don't all trace back to this file.
   Coordination gap found the hard way: its pricing redesign (`Introduce
   business/education pricing`, `Redesign pricing...`) replaced
   `frontend/app/pricing/page.tsx` with **invented flat pricing** ("Standard
   $49/month, Premium $99/month", "Education $19/month") that does not
   match what Stripe actually charges (real billing is still the per-site
   volume tiers in `frontend/lib/pricing.ts`/`Account.TIERS`) — live on the
   real site as of 2026-09-22, **not yet resolved as of 2026-09-23**,
   flagged to the owner, awaiting a decision on whether to fix the numbers
   inside the new design or change the billing model to match it. `lib/
   pricing.ts` itself is untouched and still correct — only the page stopped
   reading from it. **Lesson: re-check pricing.py page /pricing against
   `Account.TIERS` after any frontend session from here on**, not just once.
9. **Sentry — wired 2026-09-22.** `app/main.py` calls `sentry_sdk.init()`
   before the FastAPI app is built, gated entirely on `SENTRY_DSN` (unset =
   no call at all, same degrade-quietly pattern as Stripe/Anthropic/every
   other key here). `send_default_pii=False` on purpose — Sentry isn't in
   `frontend/lib/legal.ts`'s `SERVICE_PROVIDERS` list, and this keeps it that
   way. Traces are off (`SENTRY_TRACES_SAMPLE_RATE=0.0`, error tracking only —
   traces are a separate, smaller free quota). Org and project (`fig-ai` /
   `fig-ai-backend`) were created via Sentry's own Claude Code plugin
   (`npx @sentry/agent-plugin install`), which installs at the user level and
   needs a session restart before its skills/MCP connection are usable — see
   PLATFORMS.md. **Verified for real**, not just wired: booted the backend
   locally with a live DSN, hit a temporary route that deliberately raised,
   and confirmed the exact event landed in Sentry
   (`FIG-AI-BACKEND-1` — environment tagged `development`, release
   auto-detected from the local git SHA with zero config), then resolved the
   issue and removed the route before committing. **Live in production
   (2026-09-23)**, after finding and fixing a real typo — the Render env var
   had been saved as `SENTRY_DNS`, so `config.SENTRY_DSN` read `None` and
   `/health`'s `sentry` field stayed `false` despite the dashboard looking
   configured. Fixed via the Render API, then a second issue: the fix's
   redeploy raced a concurrent push from another tool and booted with a
   stale env snapshot — confirmed only by triggering an explicit manual
   deploy and reading *that* deploy's own boot log line, not by trusting
   `/health` alone.

   **Excludes its own deliberate 501s (2026-09-23).** Both Sentry's
   Starlette and FastAPI integrations report every 5xx response as an issue
   by default, which includes `POST /api/content/{post_id}/draft`'s
   permanent, on-purpose refusal (`app/content.py:draft()` — "FIG does not
   write the copy yet") — every legitimate hit of it, including
   `scripts/e2e_signed_in.py`'s own check that it still correctly refuses,
   was piling up as a Sentry issue. `sentry_sdk.init()` now passes both
   integrations `failed_request_status_codes=range(500,600) minus {501}`
   explicitly, so a real 500/502/503/504 is still reported but this one
   isn't. Two issues that had already leaked from a local test run
   (`FIG-AI-BACKEND-2`, this one; `FIG-AI-BACKEND-3`, a redirect-URI test
   message that predates `test_backend.py` zeroing `SENTRY_DSN` before
   importing `app.main` — see that file's top) were found via
   `search_issues` and resolved with an explanation on each. Not wired into
   the frontend (Next.js) — a separate Sentry project if that ever matters.

**Design tool:** the UI is being replicated into Paper (`FIG AI Frontend UI`,
`PLATFORMS.md`) so it can be restyled visually and ported back to the Next.js
files. Home and Pricing are built; the rest of the pages are not. Paper's free
plan has a weekly MCP call limit, and running many workers in parallel got the
Claude API throttled — build one page at a time. Paper exports exact values
with `get_jsx`/`get_computed_styles`; never read sizes off a screenshot.

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
python -m unittest test_workspace_library test_billing test_jobs test_secrets_cleanup \n                   test_account_lifecycle test_pricing_sync
                          # the /api contract (auth, isolation, content lifecycle,
                          # profile), the Stripe webhook + checkout guard + quantity
                          # sync, orphaned-job recovery, and credential deletion. The
                          # billing tests patch dummy Stripe settings and a fake Stripe
                          # module, so they can never reach the live account whatever
                          # .env holds.
```

The signed-in end-to-end test drives a *deployed* site as two disposable users
(real Supabase auth, through the real proxy) and deletes everything it made. It
is the only test that has caught a bug "the tests pass" and "health is green"
both missed, so run it after any change to auth, sessions or content:

```bash
python scripts/e2e_signed_in.py                    # the live Vercel proxy
python scripts/e2e_signed_in.py http://localhost:8765   # a local backend
python scripts/e2e_signed_in.py --cleanup <tag>    # remove rows a crashed run left
```

It never touches billing (a checkout here is real money in live mode) and does
not cover session expiry. Point it at a local backend started with
`FIG_DATABASE_URL=sqlite:///...` to check a change before pushing it.

The end-to-end run — real network, real database, real Claude tokens (under a
cent). It appends `## Test #N` to `Test Runs.md`; read the output, not just the
pass count:

```bash
python scripts/test_run.py launchvault.ca
```
