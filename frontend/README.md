# FIG frontend

The visual frontend for FIG's marketing site and private content-operations workspace. It is intentionally a frontend-first baseline: the product surfaces show honest empty states until real workspace data is connected.

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

The next phase should replace the intentional empty states with authenticated workspace data, using the existing FIG API and configured Supabase, OpenAI, Anthropic, and Stripe services. The UI does not claim that any connection or billing feature is live until that integration is verified.

`NEXT_PUBLIC_API_URL` is reserved in `.env.example` for the API base URL.
