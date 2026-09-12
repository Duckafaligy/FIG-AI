# Archive — 2026-09-11

The site and dashboard as they stood before the Figma redesign.

- `site/` — the full marketing site: homepage, demo, pricing, and 20 content
  pages (glossary, rulebook, schema and robots references, fix recipes, docs,
  API reference, privacy, terms, cookies, about, contact, security, changelog,
  status, recent reads, blog index).
- `templates/` — the first dashboard: sidebar shell, overview, sites, audits,
  findings, SEO, GEO, analytics, settings, auth pages.
- `static/` — `dash.css` and `auth.css` for the above.

Everything here is also in git history up to the commit that added this
folder, so it can be restored with `git checkout` rather than by copying.

## Why it was archived

The dashboard is being rebuilt to a Figma design (an analytics-style layout:
dark sidebar, metric cards, a performance chart, and per-panel reports). Only
the homepage stays live from the old site while the rest is redesigned.
