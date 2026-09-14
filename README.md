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

The backend renders no HTML. `/api` is the workspace API the frontend reads
(session cookie, one endpoint per surface); `/v1` is the partner API (API key,
versioned, for resellers). `FIG_DEV_NO_AUTH=1` resolves every `/api` request to
the seeded demo workspace so the frontend has data without a sign-in flow — set
it to 0 before anything is public.

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if the backend is not on
port 8000, and `FIG_CORS_ORIGINS` if the frontend is not on 3000/3001.
`/app/live` in the frontend shows whether the two are talking.

## Run it

```bash
pip install -r requirements.txt
python -m app.seed --reset      # fills the demo agency with 22 client sites
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/app**. While `FIG_DEV_NO_AUTH=1` every
request resolves to the seeded demo account with no sign-in — convenient
locally, an open admin panel in public. **Set it to 0 before this is
reachable by anyone else.**

## Sign-in

Supabase Auth, with the verification done server-side:

1. The browser signs in with the Supabase JS client on `/login` — password or
   an emailed link — and gets an access token.
2. It POSTs that token to `/auth/session` exactly once.
3. The server checks it against `GET /auth/v1/user`, finds or creates the
   `User` and its `Account`, then sets its own signed HttpOnly cookie and
   calls `signOut()` in the browser.

The access token is never stored, and after that call it never touches
JavaScript on any page of ours. Checking with Supabase rather than verifying
the JWT locally means there is no third copy of a signing secret to look
after, and a token revoked upstream stops working here immediately.

`FIG_OWNER_EMAIL` inherits the seeded account on first sign-in. Anyone else
signing in gets an empty account of their own rather than landing inside
somebody else's client list.

To create the first user: Supabase → Authentication → Users → Add user, with
"auto confirm" on. No email delivery needed.

API keys are a separate path and are unaffected — a partner's server holds a
`fig_live_…` key and never signs in.

- Dashboard — `/app`
- API — `/v1`, schema at `/docs`
- Health — `/health`

With nothing configured it runs on a local SQLite file. If `DATABASE_URL`
points at Supabase but is unreachable it falls back to SQLite and says so;
`FIG_DB_STRICT=1` makes that an error instead.

## The shape

```
Account          a billing entity: direct customer, agency, or platform
 └── Site        one website. THE METER IS SITES, NOT SEATS.
      └── Scan   one crawl → Findings across four layers + scores
```

An agency's own clients are **Sites, never Accounts** — the client stays
inside the partner's product and never signs up here. That is what makes
white-labelled resale possible, and it is why an account with three logins and
four hundred client sites pays for four hundred.

## Pipeline

```
crawl()            app/scraper.py      $0 — sitemap, then internal links,
                                       one request per host, spaced out
run_all_checks()   app/rules/checks.py $0 — 18 deterministic checks
check_section_order() app/rules/sections.py  $0 — the flagship check
summarise()        app/rules/scoring.py $0 — four layer scores
explain_flags()    app/ai_explain.py   the ONLY LLM call, and it is optional
```

`ai_explain` receives already-flagged structured data, never a page, and never
runs at all without `ANTHROPIC_API_KEY`. Every finding ships with its own
`why` and `fix`, so pulling the key changes the prose, not the product.

**Do not add LLM calls anywhere else.** If you are tempted to "just ask the
model" for something a rule could check — uniformity, keyword presence, colour
similarity, size ratios — write the rule.

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

Everything degrades quietly: with no `STRIPE_SECRET_KEY` the billing page says
so and nothing else is affected.

## Tests

```bash
python test_local.py     # the rules engine: no network, no API key
python test_content.py   # the content queue's scorer and state machine
```

Craft checks must stay quiet on hand-made HTML; the hygiene layers are
asserted separately because a bare fixture legitimately fails them.

## Where the real work is

Per `CLAUDE.md`, tuning matters more than new checks. The reference lists in
`app/rules/checks.py` — `KNOWN_DEFAULT_COLORS`, `GENERIC_COPY_PHRASES`,
`OVERUSED_ICON_NAMES` — and the role patterns in `app/rules/sections.py` are
the differentiating IP. Run real generated sites and real hand-made ones
through the engine and tune until they separate cleanly.

## Deploying

Two targets from one repo, because they are different shapes of thing.

**`site/` → Vercel.** Static HTML/CSS/JS, no build step. In the Vercel project
set **Root Directory: `site`** and Framework Preset: **Other**. That is the
whole configuration.

**`app/` → Railway or Render.** This half cannot go on Vercel: it runs
background worker threads that must survive between requests, and a crawl of
40 pages at a 0.8s politeness delay runs far past any serverless function
timeout. It needs a persistent process.

`Procfile` has the start command. Set every variable from `.env.example` in
the host's dashboard, and in particular:

```
FIG_DEV_NO_AUTH=0        # there is no sign-in yet; see below
FIG_PUBLIC_URL=https://your-backend-host
FIG_DB_STRICT=1          # fail loudly instead of silently using SQLite
```

`FIG_DEV_NO_AUTH=0` will lock the dashboard out entirely until Supabase Auth
is wired into `app/auth.py:current_account` — that is deliberate. **Do not
deploy this with `FIG_DEV_NO_AUTH=1`:** every request resolves to the demo
account, so a public URL is an open admin panel that can add sites, mint API
keys and start checkouts.

Once the backend has a URL, add the Stripe webhook endpoint at
`https://your-backend-host/v1/billing/webhook` and put the signing secret in
`STRIPE_WEBHOOK_SECRET`.
