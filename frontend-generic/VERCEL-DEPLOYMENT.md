# Deploy the generic FIG frontend on Vercel

The repository contains the future Python backend plus two deployable Next.js interfaces. This neutral variant lives in **`frontend-generic`**, which must be the Vercel project root for this deployment.

## GitHub import (recommended)

1. In Vercel, choose **Add New → Project** and import `Duckafaligy/FIG-AI`.
2. Before the first deployment, open the project configuration and set **Root Directory** to `frontend-generic`.
3. Confirm Vercel detects **Next.js**. The deployment root then contains [`vercel.json`](./vercel.json), `package.json`, and `package-lock.json`.
4. Keep the defaults supplied by this repository:

   | Setting | Value |
   | --- | --- |
   | Install command | `npm ci` |
   | Build command | `npm run build` |
   | Output directory | Leave unset — Vercel detects Next.js output. |
   | Node.js | `20.9.0` or newer (declared in `package.json`). |

5. Click **Deploy**. Future pushes to the connected GitHub branch will create Vercel deployments automatically.

You can also start the import with this prefilled link: [Deploy the generic FIG frontend on Vercel](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FDuckafaligy%2FFIG-AI&root-directory=frontend-generic).

## Environment variables

The designed public and demo dashboard pages work without a backend environment variable.

Only add the following when the public backend URL, CORS policy, and authentication flow are ready:

```text
NEXT_PUBLIC_API_URL=https://your-api.example.com
```

That variable is intentionally public because browser code may read it. Never put Supabase service-role keys, OpenAI/Anthropic keys, Stripe secret keys, CMS tokens, webhook secrets, or database passwords in `NEXT_PUBLIC_*` variables. Put secrets in the backend host’s server-only environment instead.

`/app/live` is a read-only diagnostic page that can display API reachability and a live overlay when `NEXT_PUBLIC_API_URL` is configured. The normal designed pages remain static/demo pages until their data layer is deliberately wired to the backend.

## Local production preflight

Run this from the repository root before deploying:

```powershell
cd frontend-generic
npm ci
npm run lint
npm run build
```

To serve the production build locally:

```powershell
npm run start -- --port 3001
```

## Optional Vercel CLI deployment

If using the Vercel CLI, run it from the `frontend-generic` directory so Vercel uses the correct app:

```powershell
cd frontend-generic
npx vercel
```

## Why the root directory matters

The root repository is not a standalone JavaScript app: it contains the backend and other project files. The `frontend-generic` directory is the neutral Next.js application Vercel needs to install, build, and serve. Selecting it as the Root Directory prevents Vercel from looking for `package.json` in the wrong place or deploying the customer-specific variant by accident.

For Vercel’s current configuration details, see its official guidance on [monorepo root directories](https://vercel.com/docs/monorepos), [project settings](https://vercel.com/docs/project-configuration/project-settings), and [build settings](https://vercel.com/docs/deploy-button/build-settings).
