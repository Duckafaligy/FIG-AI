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
  (see git history around 2026-09-19 for the exact curl shape).

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
  - Authentication → URL Configuration: Site URL / Redirect URLs (must
    include `https://fig-ai-seven.vercel.app`)
  - Authentication → Email Templates: the six templates were replaced with
    branded HTML on 2026-09-19 (Confirm signup, Invite, Magic Link/OTP,
    Change email, Reset password, Reauthentication)
  - Authentication → Providers → Email: confirmation requirement, rate
    limits (the shared default email sender is low-volume/testing-only —
    a real SMTP provider is the fix if signups ever need real volume)

## Stripe

- **Mode:** test mode (`sk_test_...` key) — not live/real money yet.
- **What for:** graduated per-site subscription billing. Checkout, customer
  portal, and a webhook, all wired end to end (2026-09-19).
- **Dashboard:** dashboard.stripe.com (make sure the **Test mode** toggle is
  on to see anything relevant).
- **Webhook endpoint:** Developers → Webhooks → the one pointed at
  `https://fig-ai-backend.onrender.com/v1/billing/webhook`.
- **Going live later:** means a second, separate `sk_live_...` key, a
  second live-mode webhook endpoint (new signing secret), and switching
  `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`/`STRIPE_PRICE_ID` on Render to
  the live-mode equivalents — not a code change.

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

## Anthropic

- **What for:** the one LLM call in the whole pipeline
  (`app/ai_explain.py`), turning already-flagged findings into plain-
  language explanations. `claude-haiku-4-5` by default. Everything else in
  the product is deterministic code, on purpose (see `CLAUDE.md`).
- **Dashboard:** console.anthropic.com — API keys and usage.

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
