# Platforms this project depends on

A single reference for every external service FIG is wired to, so you never
have to go hunting for "wait, where does this live again." Credentials
themselves stay in `.env` (backend) and each platform's own dashboard
(frontend env vars) — this file only ever holds pointers, never secret
values.

## GitHub

- **What for:** source control. Both Vercel and Render deploy straight from
  pushes to `main`.
- **Where:** `github.com/Duckafaligy/FIG-AI`

## Vercel — frontend hosting

Two separate projects, same codebase (`frontend/`), same org (`ducakfaligy`):

| Project | URL | Purpose |
|---|---|---|
| `fig-ai` | https://fig-ai-seven.vercel.app | The real, live site. `NEXT_PUBLIC_API_URL` is left unset here (proxied — see below); `FIG_BACKEND_URL` points at Render. |
| `fig-demo` | https://fig-demo-ecru.vercel.app | Public showcase only. `NEXT_PUBLIC_DEMO_MODE=1` — structurally incapable of calling a real backend or account, whatever else is set. |

- **Dashboard:** vercel.com → your account → each project by name above.
- **Deploy from the CLI:** run `vercel --prod` from the **repo root** (not
  `frontend/`) — Root Directory is set to `frontend` in the project settings,
  and running it from inside `frontend/` too causes a double-nested path
  Vercel can't find (`frontend/frontend/`).
- **Why a proxy:** `fig-ai`'s `next.config.mjs` proxies every browser
  `/api/*` call to the Render backend server-side, so the backend's session
  cookie is readable by this app's own Server Components. See
  `frontend/lib/api.ts`'s docstring for the full "why."

## Render — backend hosting

- **Service:** `fig-ai-backend` — https://fig-ai-backend.onrender.com
- **What for:** the FastAPI backend (`uvicorn app.main:app`). Free tier.
- **Deploy:** a Blueprint (`render.yaml` at the repo root), auto-deploys on
  push to `main`. No secrets are in that file — every credential is entered
  once in Render's dashboard under the service's **Environment** tab.
- **Known limitation:** free tier sleeps after 15 minutes with no traffic;
  the next request cold-starts it (30-60s). Mitigated by the UptimeRobot
  monitor below, not eliminated — upgrading to the $7/mo Starter plan is the
  actual fix if this ever needs to feel instant for a stranger.
- **Editing env vars without the dashboard:** needs a personal API key from
  Account Settings → API Keys, then
  `PUT https://api.render.com/v1/services/<service-id>/env-vars/<KEY>`
  (see git history around 2026-09-19 for the exact curl shape). The same key
  reads deploy status/logs: `GET /v1/services/<id>/deploys` and
  `GET /v1/logs?ownerId=<owner>&resource=<id>` (owner id comes from
  `GET /v1/services/<id>`) — the actual boot log line is more trustworthy
  than `/health` when something looks stuck (see the Sentry entry above for
  why).
- **Every push to `main` rebuilds this service**, even a `frontend/`-only
  change with nothing Python in it — Render has no path filter configured, so
  a purely cosmetic frontend commit still costs a ~1-2 minute Python rebuild
  and a few seconds of downtime while it swaps in. It also installs Node
  during every one of those builds (buildpack auto-detection sees
  `frontend/package.json` from the full repo checkout, even though
  `buildCommand` never touches it). Harmless, just wasteful — worth a path
  filter in Render's dashboard if this gets noisy.

## UptimeRobot — keep-alive

- **What for:** pings `https://fig-ai-backend.onrender.com/health` every 5
  minutes so Render's free tier never sees 15 idle minutes and never sleeps.
  Also gives a free email alert if the backend goes down for real.
- **Dashboard:** uptimerobot.com → your account → the one monitor.
- Nothing to maintain — just leave it running.

## Supabase

- **Project:** `frpoykqldlsysitiqnhz` — `frpoykqldlsysitiqnhz.supabase.co`
- **What for:** real user auth (email/password sign-in, sign-up, email
  templates) and the real Postgres database (`DATABASE_URL` in the backend
  `.env`, same project).
- **Dashboard:** supabase.com/dashboard → this project.
- **Settings that matter and where:**
  - Authentication → URL Configuration — **required or emails break.** Site
    URL: `https://fig-ai-seven.vercel.app` (it was `http://localhost:3000`,
    which is where every confirmation and recovery link went). Redirect URLs:
    `https://fig-ai-seven.vercel.app/**`, `http://localhost:3000/**`,
    `http://localhost:3001/**` (the wildcard is what lets `/signin` and
    `/reset-password` through; the bare origin alone does not).
  - `SUPABASE_SERVICE_ROLE_KEY` must be set on **Render** too (it is in
    `render.yaml`): the backend uses it only to delete a person's sign-in record
    when they delete their workspace. Never expose it to the frontend.
  - Authentication → Email Templates: the six templates were replaced with
    branded HTML on 2026-09-19 (Confirm signup, Invite, Magic Link/OTP,
    Change email, Reset password, Reauthentication)
  - Authentication → Providers → Email: confirmation requirement, rate
    limits (the shared default email sender is low-volume/testing-only —
    a real SMTP provider is the fix if signups ever need real volume)

## Stripe

- **Mode:** **live** (`sk_live_...`, account `FIG`) since 2026-09-21. Real
  money. Payouts stay off until the ID/bank step in Stripe is finished —
  charges are enabled and funds accumulate until then.
- **What for:** per-site subscription billing, **volume** tiers (at 30 sites
  every site costs the 30-site rate; see `scripts/stripe_setup.py`). Checkout,
  customer portal, and a webhook, all wired end to end.
- **Live objects:** product `prod_VIXXfDZbv0o5C8`, price
  `price_1UHwSSEHHPscpAUrKPKmULPz` (lookup key `fig_per_site_monthly`),
  created by `python scripts/stripe_setup.py --write` against the live key.
  Not secrets, safe to record.
- **Dashboard:** dashboard.stripe.com. The old **FIG sandbox** account
  (`sk_test_...`) is a separate account with its own product, price and keys;
  nothing in it carries over to live.
- **Customer portal (live):** Settings → Billing → Customer portal. One
  default configuration exists (`bpc_1UIFQtEHHPscpAUr2S0fDiT2`): cancel at
  period end, no self-service quantity change, invoices and card updates on,
  privacy/terms links to the site. Without it `start_portal()` fails in live
  mode and nobody can cancel.
- **Webhook endpoint:** Developers → Webhooks → the live endpoint pointed at
  `https://fig-ai-backend.onrender.com/v1/billing/webhook`. It must subscribe
  to `checkout.session.completed`, `customer.subscription.created`,
  `customer.subscription.updated` and `customer.subscription.deleted` (the
  handler in `app/billing.py` acts on those four). Missing `.deleted` means a
  cancelled customer keeps showing as subscribed.
- **Render env vars that must be the LIVE values:** `STRIPE_SECRET_KEY`,
  `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` (the live endpoint's own signing
  secret, revealed in the dashboard — it differs from any sandbox one).
- **To go back to test mode for development:** use the sandbox account's
  `sk_test_...` key locally only, never on Render.

## Google Cloud Console

- **What for:** one OAuth 2.0 Client (Web application) covering both Google
  Analytics (`analytics.readonly`) and Search Console
  (`webmasters.readonly`) — one consent screen grants whichever scopes the
  connecting account has.
- **Dashboard:** console.cloud.google.com → APIs & Services → Credentials →
  the OAuth client (Client ID starts with `256216963904-...`).
- **Redirect URI on file:**
  `https://fig-ai-backend.onrender.com/oauth/google/callback` (plus
  `http://localhost:8000/oauth/google/callback` for local dev — both must
  stay listed).
- **Consent screen is in Testing mode** — only test users you've explicitly
  added can complete the OAuth flow until it's submitted for verification.

## Shopify Partners — app created, client ID/secret live (2026-09-23)

- **What for:** the OAuth app `/oauth/shopify/start` and `/oauth/shopify/callback`
  (`app/oauth.py`) run against. Only the connect step is real — see CLAUDE.md
  roadmap item 3b for why the write adapter (title/content fixes, the
  Shopify equivalent of `app/wordpress.py`) isn't built yet.
- **Status:** `SHOPIFY_CLIENT_ID`/`SHOPIFY_CLIENT_SECRET` are set on Render —
  a Custom app, embed disabled, legacy install flow enabled, scopes
  `read_content,write_content`. **`SHOPIFY_OAUTH_REDIRECT_URI` was found
  still missing on Render on 2026-09-23** (`SHOPIFY_OAUTH_ENABLED` only
  checks the first two vars, so `/health` read `true` while the real
  redirect sent to Shopify was still the localhost default) — confirm this
  got added before trusting a real connection attempt to work; `app/main.py`'s
  startup check now logs an error on boot if it's still wrong.
- **To set it up:**
  1. Create a free account at partners.shopify.com if there isn't one already.
  2. Apps → Create app → **Custom app** (not "Public app" — this doesn't need
     Shopify's App Store review, since it's for FIG's own use). Give it any
     name.
  3. App setup → **Allowed redirection URL(s)**: add
     `https://fig-ai-backend.onrender.com/oauth/shopify/callback` and, for
     local dev, `http://localhost:8000/oauth/shopify/callback`.
  4. Under scopes, the app will ask what Admin API access to request —
     `read_content`/`write_content` (Online Store pages and blog articles) is
     what `app/oauth.py` currently requests; if the dashboard shows different
     current scope names, tell me and I'll update `SHOPIFY_TOKEN_SCOPE`.
  5. Copy the **Client ID** and **Client secret** from the app's API
     credentials page.
  6. **To actually test a connection**, you also need a store to connect —
     Partners gives you a free development store for exactly this (Stores →
     Add store → Development store), no real Shopify subscription needed.
- **Render env vars once you have them:** `SHOPIFY_CLIENT_ID` and
  `SHOPIFY_CLIENT_SECRET` — both already declared in `render.yaml`
  (`sync: false`, blank), so Render will prompt for them the next time it
  reads the Blueprint. `SHOPIFY_OAUTH_REDIRECT_URI` defaults to the right
  production URL already; only override it for local dev.

## Webflow — not set up yet

- **What for:** `/oauth/webflow/start` and `/oauth/webflow/callback`
  (`app/oauth.py`) need a real app to exist against. Right now
  `WEBFLOW_CLIENT_ID`/`WEBFLOW_CLIENT_SECRET` are unset everywhere, so
  `WEBFLOW_OAUTH_ENABLED` is `False` and Settings' "Connect" button for
  Webflow 404s (no href rendered). Shaped closer to Google than Shopify: one
  fixed authorize URL, no per-merchant shop domain and no extra callback
  signature check beyond `state` — only the connect step is built; same
  "no write adapter without a real site to verify against" reasoning as
  Shopify (CLAUDE.md roadmap item 3b).
- **To set it up:**
  1. Sign in at webflow.com with the account that will own the app (a free
     Workspace is enough — Apps & Integrations doesn't require a paid site).
  2. Workspace settings → **Apps & Integrations** → Manage App Development
     → **Build an App**. Give it any name.
  3. **Redirect URI(s):** add
     `https://fig-ai-backend.onrender.com/oauth/webflow/callback` and, for
     local dev, `http://localhost:8000/oauth/webflow/callback`.
  4. **Scopes:** `cms:read`, `cms:write`, `pages:read`, `pages:write`,
     `sites:read` — matches `WEBFLOW_SCOPE` in `app/oauth.py`; if Webflow's
     dashboard shows different current scope names, tell me and I'll update it.
  5. Copy the **Client ID** and **Client Secret** from the app's building
     blocks / API access page.
  6. **To actually test a connection**, install the app on a real Webflow
     site (even a free "Starter" site works — Sites → Add site).
- **Render env vars once you have them:** `WEBFLOW_CLIENT_ID` and
  `WEBFLOW_CLIENT_SECRET` — both already declared in `render.yaml`
  (`sync: false`, blank), so Render will prompt for them the next time it
  reads the Blueprint. `WEBFLOW_OAUTH_REDIRECT_URI` defaults to the right
  production URL already; only override it for local dev.

## Anthropic

- **What for:** the one LLM call in the whole pipeline
  (`app/ai_explain.py`), turning already-flagged findings into plain-
  language explanations. `claude-haiku-4-5` by default. Everything else in
  the product is deterministic code, on purpose (see `CLAUDE.md`).
- **Dashboard:** console.anthropic.com — API keys and usage.

## Sentry

- **What for:** backend error tracking (`app/main.py`). Off entirely with no
  `SENTRY_DSN` set — `sentry_sdk.init()` is never called, same degrade-
  quietly pattern as everything else here. `send_default_pii=False` on
  purpose: Sentry isn't in `frontend/lib/legal.ts`'s `SERVICE_PROVIDERS`
  list yet, and this keeps it that way until it needs to be.
- **Org / project:** `fig-ai` org, `fig-ai-backend` project (Python/FastAPI
  platform), both created via Sentry's Claude Code plugin
  (`npx @sentry/agent-plugin install`, installed at the user level —
  restart Claude Code to (re)gain its skills and the `mcp.sentry.dev` MCP
  connection).
- **Dashboard:** fig-ai.sentry.io.
- **Render env vars:** `SENTRY_DSN` (Settings → Client Keys (DSN) on the
  project) and `SENTRY_ENVIRONMENT=production` (committed directly in
  `render.yaml` — not a secret, and it's what keeps production events out of
  the same stream as a local `development`-tagged run).
- **Verified (2026-09-22):** booted the backend locally with a real DSN, hit
  a temporary route that deliberately raised, and confirmed the event landed
  in Sentry (`FIG-AI-BACKEND-1`) with `environment=development` and the
  release auto-detected from the local git SHA. Resolved and the route
  removed before committing.
- **Confirmed live in production too (2026-09-22).** First attempt looked
  broken for ~10 minutes — `/health`'s `sentry` field stayed `false` after
  what looked like a successful save. The Render env var had been saved as
  **`SENTRY_DNS`** (letters swapped), so `os.environ.get("SENTRY_DSN")` never
  found it — not a deploy or code problem, just that one typo. **If this ever
  looks stuck again:** don't trust `/health` or "deploy: live" alone; pull the
  actual boot log line (`FIG API up - ... sentry %s`) via the Render API
  (`GET /v1/logs?ownerId=...&resource=<service-id>`) — that's what caught a
  second, real race: an env-var-triggered redeploy landed at nearly the same
  moment as one of the other AI tool's frontend-only pushes (see CLAUDE.md's
  roadmap item 8's note on that), and the container that came up used an
  environment snapshot from just before the fix. A second explicit manual
  deploy (`POST /v1/services/<id>/deploys`) resolved it; its own boot log
  read `sentry production`.
- **Traces:** off by default (`SENTRY_TRACES_SAMPLE_RATE=0.0`) — this is
  error tracking, not performance monitoring, and traces count against a
  separate, smaller free quota.

## Quick sanity checks

- Backend alive: `curl https://fig-ai-backend.onrender.com/health`
- Frontend alive: open https://fig-ai-seven.vercel.app
- Frontend actually talking to the backend (not just showing the static
  preview): visiting `/app` while signed out should redirect to `/signin`
  rather than silently show demo content.

## Paper — design tool

- **What for:** the whole frontend is being replicated into a Paper file
  (`FIG AI Frontend UI`) so it can be restyled visually and ported back into
  the Next.js files. Design tokens (colors, Inter, radii, spacing) were
  seeded from `frontend/app/redesign.css`, the layer that actually renders.
- **How it connects:** Paper Desktop must be open with the file loaded — that
  starts a local MCP server at `http://127.0.0.1:29979/mcp`. In Claude Code,
  `/mcp` -> `paper` -> Reconnect after it has dropped.
- **Limits:** the free plan has a weekly MCP call limit (hit on
  2026-09-20; resets after 5 days, or upgrade to Paper Pro). Building many
  pages in parallel also got the Claude API rate-limited — go one page at a
  time.
- **Status:** Home and Pricing are built. Other artboards exist but are
  mostly empty.
