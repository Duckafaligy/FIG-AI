# FIG frontend preview

Updated September 15, 2026. Visual direction follows the supplied public FIG pages and private Demo workspace dashboard references. The only demo project is **Demo workspace**.

## Included

- Homepage, pricing, sign-in, sign-up, projects, overview, SEO, GEO, notifications, history, and settings layouts.
- Locally served Inter, real platform symbols, Google's official sign-in mark, and licensed workplace stock photos. Asset sources are recorded under `public/`.
- CSS laptop hardware with a populated HTML display, metallic base, bezel highlights, and layered shadows.
- Chart scales, legends, keyboard/focus tooltips, stacked bars, distribution rings, and indexed project-growth comparisons.
- Local content search/filtering, detail dialogs, demo publish/reject state, project grid/list/search, monthly/yearly pricing, password visibility, and mobile navigation.

## Preview boundaries

All dashboard figures and content are illustrative. Local demo edits reset on reload. Signup, third-party sign-in, billing, publishing, invitations, and integration setup do not create external actions. Settings dialogs describe these boundaries; they do not verify API keys. Existing backend code was not modified during this frontend pass.

## Verification

- TypeScript (`npm run lint`) and production build (`npm run build`) pass.
- All eleven frontend routes were checked at a 390px viewport with no document-level horizontal overflow. Wide tables scroll within their own panels.
- Desktop visual checks covered every page, including loaded stock-photo crops and the laptop preview.
- Browser checks exercised review search, preview dialogs, demo publishing, chart details, project list/search, password visibility, yearly pricing, and mobile navigation.

Preview server: `http://localhost:3001`. This is a reviewed prototype, not a claim of pixel-perfect fidelity or production-ready backend functionality.
