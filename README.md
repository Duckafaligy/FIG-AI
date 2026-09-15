# FIG — backend

Reads a website for four things and says what to change about each:

| Layer | What it asks |
|---|---|
| **Craft** | how the page reads — the slop layer |
| **Structure** | whether the sections are in an order that makes sense |
| **Search** | whether a crawler can reach and understand it |
| **Answers** | whether a model has anything specific it can quote |

Findings are always probabilistic and educational. Nothing in here says a page
"is" AI-written — see the rule that shapes the whole project in `CLAUDE.md`.

## Two processes

```
frontend/   Next.js 16, the UI          npm run dev -- --port 3001
app/        FastAPI, JSON only          uvicorn app.main:app --port 8000
```

The backend renders no HTML. It serves:

| Route | For | Auth |
|---|---|---|
| `/v1` | the partner API — provision sites, queue scans, pull findings, traces and reports | `fig_live_…` API key |
| `/scan` | the free public read — any public site, no account | none; capped per browser, per network and per day |
| `/api` | the workspace API the frontend reads, one endpoint per surface | session cookie |
| `/health`, `/docs` | what is configured; the OpenAPI schema | none |

**Running disconnected from the frontend.** `FIG_WORKSPACE_API=0` unmounts
`/api` and allows no browser origin at all — no CORS headers are sent — while
`/v1`, `/scan` and `/health` are untouched. That is how the backend is run and
tested right now; set it back to `1` to reconnect.

When connected: set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if the
backend is not on port 8000, and `FIG_CORS_ORIGINS` if the frontend is not on
3000/3001. `FIG_DEV_NO_AUTH=1` resolves every `/api` request to the seeded demo
workspace so the frontend has data without a sign-in flow — set it to 0 before
anything is public.

## Run it

```bash
pip install -r requirements.txt
python -m app.seed --reset      # optional: a demo agency with 22 client sites
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs**. With nothing configured it runs on a
local SQLite file. If `DATABASE_URL` points at Supabase but is unreachable it
falls back to SQLite and says so; `FIG_DB_STRICT=1` makes that an error
instead.

## Sign-in

Supabase Auth, with the verification done server-side:

1. The browser signs in with the Supabase JS client and gets an access token.
2. It POSTs that token to `/api/session` exactly once.
3. The server checks it against `GET /auth/v1/user`, finds or creates the
   `User` and its `Account`, then sets its own signed HttpOnly cookie.

The access token is never stored. Checking with Supabase rather than verifying
the JWT locally means there is no third copy of a signing secret to look
after, and a token revoked upstream stops working here immediately.

`FIG_OWNER_EMAIL` inherits the seeded account on first sign-in. Anyone else
signing in gets an empty account of their own rather than landing inside
somebody else's client list.

To create the first user: Supabase → Authentication → Users → Add user, with
"auto confirm" on. No email delivery needed.

API keys are a separate path and are unaffected — a partner's server holds a
`fig_live_…` key and never signs in.

## The shape

```
Account          a billing entity: direct customer, agency, or platform
 └── Site        one website. THE METER IS SITES, NOT SEATS.
      └── Scan   one crawl → Findings across four layers + scores + a trace
```

An agency's own clients are **Sites, never Accounts** — the client stays
inside the partner's product and never signs up here. That is what makes
white-labelled resale possible, and it is why an account with three logins and
four hundred client sites pays for four hundred.

## Pipeline

```
validate_target()     app/validation.py     $0 — syntax, then DNS: public
                                            addresses only
crawl()               app/scraper.py        $0 — robots.txt, sitemap, then
                                            internal links; one request per
                                            host, spaced out
run_all_checks()      app/rules/checks.py   $0 — 18 deterministic checks
check_section_order() app/rules/sections.py $0 — the flagship check
explain_flags()       app/ai_explain.py     the ONLY LLM call; optional, cheap
summarise()           app/rules/scoring.py  $0 — four layer scores
```

**The validation system** (`app/validation.py`). The crawler makes requests on
a caller's behalf, so every target is checked before anything is fetched, and
refused with a stable code: `ip_literal`, `reserved_name` (`localhost`,
`*.internal`, `*.local`…), `bad_scheme`, `has_port`, `bad_hostname`,
`dns_failed`, or `non_public_address` when a name resolves anywhere private —
loopback, RFC 1918, link-local (including the `169.254.169.254` cloud metadata
endpoint), carrier-grade NAT. The same check runs again on **every** request
the crawler makes, including each redirect hop and each sitemap URL, so a
public page cannot redirect it somewhere private. robots.txt is honoured on
every hop, read the RFC 9309 way (`app/robots.py`): `urllib.robotparser` drops
every rule after a blank line, which let an early crawl read pages a site
disallows. Responses are capped at 5 MB, and redirects at 5.

**The AI step** sends one item per *distinct* finding — a check that fired on
twelve pages is explained once — to `claude-haiku-4-5` (`FIG_AI_MODEL`). It
receives already-flagged structured data, never a page, and never runs at all
without `ANTHROPIC_API_KEY`. Every finding ships with its own `why` and `fix`,
so pulling the key changes the prose, not the product. Each scan records the
tokens and cost it spent.

**Do not add LLM calls anywhere else.** If you are tempted to "just ask the
model" for something a rule could check — uniformity, keyword presence, colour
similarity, size ratios — write the rule.

**The trace.** Every stage writes to `Scan.trace`, served at
`GET /v1/scans/{id}/trace`: what validation resolved, which scheme answered,
what robots.txt allowed, every page read or skipped and why, the flags by
check, the AI step's calls, tokens and cost, and the scores.

## Scanning at estate scale

A scan is a queued job, not a request. `POST /v1/scans` queues every active
site on the account at once; workers claim jobs from the `jobs` table. That is
what makes "read this agency's 400 client sites" a queue depth rather than a
forty-minute HTTP call.

## Billing

Graduated per-site pricing lives in `Account.TIERS` — $20 at one site down to
$5 at a thousand. The Stripe subscription carries a **quantity** equal to the
active site count, so provisioning a site through the API changes the invoice
without anyone re-signing. `POST /v1/billing/sync` pushes the current count.

Everything degrades quietly: with no `STRIPE_SECRET_KEY` the billing routes say
so and nothing else is affected.

## Tests

```bash
python test_local.py      # the rules engine: no network, no API key
python test_content.py    # the content queue's scorer and state machine
python test_backend.py    # validation, crawler network rules, AI accounting: no network
```

Craft checks must stay quiet on hand-made HTML; the hygiene layers are
asserted separately because a bare fixture legitimately fails them.

### Test runs — real network, real key

```bash
python scripts/test_run.py launchvault.ca [--max-pages N]
```

Starts the API as its own process with `FIG_WORKSPACE_API=0` and
`FIG_DB_STRICT=1`, then drives it over HTTP the way a client would: health,
auth, the frontend API really being gone, the validation system refusing
unsafe targets, provisioning, ownership, a full scan polled to completion, the
findings, pages, trace and report — cross-checked against the database. It
appends `## Test #N` to **`Test Runs.md`**. The run uses its own account
(`test-runs`) and mints an API key that it revokes when it finishes. It crawls
the site for real and spends real Claude tokens — a few cents.

## Where the real work is

Per `CLAUDE.md`, tuning matters more than new checks. The reference lists in
`app/rules/checks.py` — `KNOWN_DEFAULT_COLORS`, `GENERIC_COPY_PHRASES`,
`OVERUSED_ICON_NAMES` — and the role patterns in `app/rules/sections.py` are
the differentiating IP. Run real generated sites and real hand-made ones
through the engine and tune until they separate cleanly.

## Deploying

The frontend in `frontend/` deploys on its own.

**`app/` → Railway or Render.** The backend cannot go on Vercel: it runs
background worker threads that must survive between requests, and a crawl of
40 pages at a 0.8s politeness delay runs far past any serverless function
timeout. It needs a persistent process.

`Procfile` has the start command. Every setting is read in `app/config.py`,
each with a comment; in particular:

```
FIG_DEV_NO_AUTH=0        # never 1 on a public URL
FIG_PUBLIC_URL=https://your-backend-host
FIG_DB_STRICT=1          # fail loudly instead of silently using SQLite
FIG_TRUST_PROXY=1        # only behind a proxy you control that sets X-Forwarded-For
```

**Do not deploy this with `FIG_DEV_NO_AUTH=1`:** every workspace request
resolves to the demo account, so a public URL is an open admin panel that can
add sites, mint API keys and start checkouts. `FIG_TRUST_PROXY` matters for the
free read: without a trusted proxy the per-network limit uses the connecting
address, and with one it believes `X-Forwarded-For` — which, anywhere else, is
a header the caller writes.

Once the backend has a URL, add the Stripe webhook endpoint at
`https://your-backend-host/v1/billing/webhook` and put the signing secret in
`STRIPE_WEBHOOK_SECRET`.
