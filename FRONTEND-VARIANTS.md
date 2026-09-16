# FIG frontend variants

This repository currently contains two independently deployable Next.js frontends.

| Directory | Intended use | Workspace identity |
| --- | --- | --- |
| `frontend` | LaunchVault-specific product demo | LaunchVault.ca sample workspace |
| `frontend-generic` | Neutral product demo | No LaunchVault name, domain, initials, or project data |

Both variants contain the same product routes, interactions, responsive behavior, and Vercel configuration. Deploy them as two separate Vercel projects from the same repository by selecting the applicable directory as the Vercel **Root Directory**.

## Data boundary

The LaunchVault variant preserves the existing illustrative frontend data. It is not a synchronized copy of the live LaunchVault website, and no public-site content, media, account data, analytics, or private routes have been imported into this repository.

Before a live-content import is enabled, confirm that you own or are authorized to import the source and provide the intended scope. An owner-provided CMS, Supabase, or API export is the preferred source because it supports accurate fields, media rights, deletes, and incremental updates without mirroring a public site.

## Deployment

- LaunchVault demo: set Vercel Root Directory to `frontend`.
- Generic demo: set Vercel Root Directory to `frontend-generic`.

Each directory includes its own `vercel.json`, package manifest, and deployment guide.
