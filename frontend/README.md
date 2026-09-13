# FIG frontend

The visual frontend for FIG's marketing site and private content-operations workspace. It is a frontend-first baseline with a clearly labeled, single-project LaunchVault.ca preview; live workspace data is connected in the backend phase.

## Run locally

```powershell
npm install
npm run dev -- --port 3001
```

Open `http://localhost:3001`.

## Routes

- `/` — public product homepage
- `/pricing` — public pricing page
- `/signin` and `/signup` — authentication interface
- `/app` — workspace overview
- `/app/seo`, `/app/geo`, `/app/notifications`, `/app/history`, `/app/settings` — private workspace surfaces

## Backend handoff

The next phase should replace the LaunchVault preview with authenticated workspace data, using the existing FIG API and configured Supabase, OpenAI, Anthropic, and Stripe services. The UI does not claim that any connection or billing feature is live until that integration is verified.

`NEXT_PUBLIC_API_URL` is reserved in `.env.example` for the API base URL.
