# FIG generic frontend

The neutral, independently deployable FIG marketing site and private content-operations workspace. It is a frontend-first baseline with a clearly labeled, single-project Demo workspace preview; live workspace data is connected in the backend phase.

This variant contains no customer brand, domain, account, or imported content. Its project, content, metrics, people, and connection states are illustrative local sample data only.

## Run locally

```powershell
npm install
npm run dev -- --port 3001
```

Open `http://localhost:3001`.

For a production deployment, configure Vercel's **Root Directory** as `frontend-generic`. See [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md).

## Routes

- `/` — public product homepage
- `/pricing` — public pricing page
- `/signin` and `/signup` — authentication interface
- `/app` — workspace overview
- `/app/seo`, `/app/geo`, `/app/notifications`, `/app/history`, `/app/settings` — private workspace surfaces

## Backend handoff

The next phase should replace the Demo workspace preview with authenticated workspace data, using the existing FIG API and configured Supabase, OpenAI, Anthropic, and Stripe services. The UI does not claim that any connection or billing feature is live until that integration is verified.

`NEXT_PUBLIC_API_URL` is reserved in `.env.example` for the API base URL.
