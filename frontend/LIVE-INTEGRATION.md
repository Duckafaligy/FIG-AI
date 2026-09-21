# Live integration status

## Implemented in this pass

- Authenticated library at /app/library (distinct from public scan library /library).
- Added GET /api/content with account ownership checks, project/status/title filters, and bounded pagination.
- Library creates and saves drafts through existing content endpoints; review transitions use the backend state machine.
- Calendar loads actual scheduled drafts. It shows up to 100 records and explicitly identifies load failures.
- Account gates fail closed when the API is unavailable; unauthenticated users are redirected to sign in.
- Projects and Settings no longer display fallback demo records on failed requests.
- Live dashboards no longer retain sample rows, metrics, or generated chart curves when an API field is absent.
- Unsupported local-only settings tabs are hidden. Supported integration, billing, and report-sharing actions remain connected.
- Project card links pass the project ID to Overview, SEO, and GEO. Dashboard navigation preserves it.
- Workspace branding uses the authenticated account, not hardcoded LaunchVault.
- The separate frontend-generic edition remains a prototype.

## Tested

- Frontend production build succeeds.
- test_workspace_library.py: 4 isolated in-memory API tests (auth, ownership, empty state, persistence/review, pagination/filter validation).
- test_content.py: 10 existing scoring/state-machine tests.
- No real account, subscription, publishing action, or production database mutation was performed.

## Not production-ready yet

The backend deliberately refuses AI drafting and new-post publishing. This pass does not bypass those safeguards or invent a successful result. New-post publishing is different from the existing WordPress field-change adapter.

Team invitations/profile editing, notification preference persistence, and several analytics sources remain absent. Existing Settings information controls describe those limitations. PLATFORMS.md now documents Stripe as live mode; billing actions can involve real money and were not exercised during these tests. Google OAuth verification and production email delivery still need deployment setup.

The hosted backend is https://fig-ai-backend.onrender.com, proxied by https://fig-ai-seven.vercel.app. Its health and session endpoints were verified without authentication. Local production builds can use FIG_BACKEND_URL pointed at that same backend; no local Python process is required. A full signed-in browser acceptance test remains outstanding. Deploy/restart the backend with the new GET /api/content endpoint before testing the new library.

The public marketing pages still contain illustrative product imagery and pricing copy; those are not live account metrics. This work is not a claim of complete production readiness.
