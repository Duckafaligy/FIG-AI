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
- Replace or disable legacy per-site checkout for new customers; preserve existing subscribers unless a migration is explicitly approved.
- Review revised commercial terms and tax/currency presentation.
- Verify the deployed sitemap, canonical URLs, noindex headers, and mobile layouts. Submit the sitemap in Google Search Console using the property owner account.
- Set NEXT_PUBLIC_SITE_URL to the permanent domain if it changes. No indexing or ranking guarantee is implied.

No hidden keyword pages, doorway pages, fabricated reviews, or invented plan entitlements were added. Feature previews describing actual article layouts remain accurately labeled; unsupported actions are not relabeled as working.
