# Generic FIG frontend variant

`frontend-generic` is a neutral, self-contained FIG demo for showing the product without a customer or site-specific identity.

- It uses **Demo workspace** as a fictional project, with fictional sample content, people, metrics, CMS state, and integration state.
- It contains no customer name, domain, logo, account information, or imported customer material.
- It is intentionally static/frontend-first: browser interactions stay local and reset on reload unless the future backend data layer is connected.
- It is separate from the customer-specific demo in `../frontend`, so either version can be deployed as its own Vercel project.

## Deployment

Set Vercel's **Root Directory** to `frontend-generic`. Then use the included `npm ci` install command and `npm run build` build command. Full instructions and the deployment link are in [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md).

## Before adding real data

Replace the sample records through an authorized backend export or API integration. Keep credentials and private tokens server-side; do not put them in `NEXT_PUBLIC_*` variables.
