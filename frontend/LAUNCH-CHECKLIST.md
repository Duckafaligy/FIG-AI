# Pricing and search launch checklist

## Implemented
- Shared Business/Education catalogue on home and pricing: Standard $49, Premium $99, Enterprise contact; Education $19, School Registered contact.
- USD retained from the existing site. Confirm currency before accepting new subscriptions.
- Enquiry buttons use the existing operator email and include the plan name. They do not start the old per-site checkout.
- Responsive footer with public resources, plans, account navigation, contact, and legal links.
- Removed public demo-workspace wording and obsolete per-site prices/structured offers.
- /sitemap.xml lists editorial public pages only. /robots.txt references it.
- noindex response headers for workspace, authentication, user reports, and scan-library pages. Authentication remains the security boundary; robots is not access control.

## Required before selling the new plans
- Define Standard/Premium feature differences and usage limits, plus Education eligibility and School Registered requirements.
- Create and map new Stripe prices server-side; verify webhook handling and plan entitlements in test mode.
- DONE locally (2026-09-23): direct-account checkout refuses the legacy per-site product before contacting Stripe. Existing subscriptions retain their portal, webhooks and quantity synchronization; partner contracts remain unchanged. New fixed-plan checkout is still blocked pending plan definitions and Stripe mapping.
- Review revised commercial terms and tax/currency presentation.
- Verify the deployed sitemap, canonical URLs, noindex headers, and mobile layouts. Submit the sitemap in Google Search Console using the property owner account.
- Set NEXT_PUBLIC_SITE_URL to the permanent domain if it changes. No indexing or ranking guarantee is implied.

No hidden keyword pages, doorway pages, fabricated reviews, or invented plan entitlements were added. Feature previews describing actual article layouts remain accurately labeled; unsupported actions are not relabeled as working.

## Launch-hardening implementation — September 23, 2026

Local changes, not a claim of production deployment:

- Successful email/password authentication navigates to `/projects`.
- Signup no longer requires an unused website URL. Company name persists in verified Supabase metadata through email confirmation and is only used when creating the workspace.
- New accounts remain empty; existing projects are not deleted.
- Google authorization remains account-scoped. Each project's Settings now has an explicit GA4 property selector backed by the real Google account summaries API. Selection is revalidated server-side against authorized properties; the shared legacy endpoint is never a reporting fallback.
- `sites.ga_property` is a nullable additive migration. Deploy/restart the backend (normal `init_db()` path) before deploying the new property-picker frontend. Existing projects will show GA data as unavailable until a property is chosen; no old guessed assignment is migrated automatically.
- Search Console refuses unmatched domains instead of displaying the first unrelated property.
- Settings no longer shows unconfigured usage caps or labels an unsubscribed account Active. Unknown allowances have no percentage bar.
- Stripe return links now point to the account-wide `/projects/settings?tab=billing` page.

### Still blocked / not represented as complete

- Owner decision: Standard/Premium/Education limits, feature differences and eligibility. No new entitlements invented; no Stripe products or customer subscriptions changed.
- Real SMTP configuration and authenticated production signup/confirmation/recovery/session-expiry tests.
- Real CMS/provider consent, permissions, token expiry, supported write and reversal tests. Offline adapter tests cannot establish these.
- Full deployed responsive/keyboard visual regression pass, frontend monitoring, backup restoration and release rollback drill.
- Article generation, new-post CMS publishing, automatic post scheduling and AI-engine citation measurement remain unsupported. Do not advertise those as live.
- Current working tree includes other ongoing integration changes; coordinate review and deployment together. This pass does not commit/push those changes on another contributor's behalf.
