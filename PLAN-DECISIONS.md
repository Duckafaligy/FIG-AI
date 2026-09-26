# FIG plan decisions

## Owner-approved limits

Recorded September 23, 2026. **Implemented and enforced 2026-09-24** (see
"Implementation" below) -- the limits in the table are now real entitlements,
not just a plan.

| Plan | Monthly price | Active projects | Scans per month |
| --- | --- | --- | --- |
| Standard | $49 | 3 | 100 |
| Premium | $99 | 5 | 250 |
| Education | $19 | 1 | 200 |
| Enterprise | Contact us, from $299 | From 15 | From 1,000 |
| School Registered | Contact us, from $99 | From 25 | From 1,000 |

Monthly scan limits are interpreted from the preceding monthly-plan discussion.
Currency remains USD in the current catalogue; confirm before checkout activation.

**Updated 2026-09-26 (owner decision):** Standard raised from 2 to 3 active
projects (enforced via `Account.PLAN_LIMITS`). Enterprise and School Registered
now publish *starting points* on the pricing page: Enterprise from $299/month
with 15 projects and 1,000 scans (about Premium's cost per scan), School
Registered from $99/month with 25 projects and 1,000 scans (Education's rate,
sized for a class). Both stay contact-only: no Stripe price, no checkout, final
limits agreed per customer. The live Stripe product description for Standard,
written by `scripts/stripe_plans_setup.py`, may still say "up to 2" projects.

## Feature inventory from implementation

- Website crawl and deterministic checks across Craft, Structure, Search and Answers; findings include reasons and suggested fixes (`app/rules/checks.py`, `app/pipeline.py`). No proof of AI authorship is implied.
- Optional AI explanation of already-flagged findings, not full article generation (`app/ai_explain.py`).
- Project management, audit history, reports and account-owned sharing opt-in (`app/webapp.py`, `app/pages.py`, `app/public.py`).
- Google Analytics and Search Console reads. Google authorization is workspace-scoped; GA reporting selection is per project (`app/ga.py`, `app/search_console.py`). Production provider access still requires verification.
- Content briefs from findings, saved drafts, deterministic draft scoring, review and scheduling reminders (`app/content.py`). Scheduling does not publish automatically.
- Approved fixes to existing CMS content, with platform-specific limitations (`app/publishing.py`, WordPress/Shopify/Webflow/Wix adapters). GitHub creates reviewable pull requests, not direct live-site changes. Real provider write/reversal validation remains outstanding.
- Audit all projects and versioned API-key authenticated partner API (`app/api.py`, `app/webapp.py`). Tier permissions are not implemented yet.
- Scheduled site monitoring exists but is off by default and needs user controls, ownership verification and quota integration (`app/scheduler.py`). Not a launch-ready promise.

Not available to sell as working: full AI article generation, new-post CMS publishing,
automatic article publishing, measured AI-engine citations, keyword volume/difficulty,
Core Web Vitals reporting, team-role administration, SSO, branded PDF export,
outbound customer webhooks or email alerts.

`app/roadmap.py` contains stale statuses; implementation takes precedence.

## Suggested packaging — NOT approved or enforced

- All three: core website analysis, explanations, findings, history, reports, content briefs/draft library and review.
- Standard and Premium: Google Analytics/Search Console reporting.
- Education: also allow analytics as a learning tool; do not artificially weaken the core checks.
- Premium: supported approved CMS fixes / GitHub PRs, bulk audits, API access, after their release acceptance checks pass.
- Enterprise/School: scoped conversation, no invented seats, SSO, SLA or oversight features.

## Decisions before implementing the meter

- Approve or revise feature packaging and Education eligibility.
- Define one scan as one website audit, with a bounded pages-per-scan limit
  (current configured code default is 40 pages; not a promised plan entitlement).
- Suggested: quota shared across projects, reset each subscription billing period,
  no rollover or automatic overage charges; failed jobs release reserved quota;
  a bulk audit consumes one scan per website; monitoring counts toward the same quota.
- Define trial allowance separately and confirm currency.

No checkout, subscription, live account or feature access was changed while listing these options.

## Implementation (2026-09-24)

All of the "Suggested" quota mechanics above were adopted as written, with
one explicit assumption this document had left open: **Education eligibility
is self-declared, not verified** -- anyone can subscribe to the Education
price through the same checkout as Standard/Premium. No .edu-email check or
similar exists. This is a decision made in code, worth revisiting before
relying on Education revenue being restricted to actual students.

What's real now:

- `Account.plan` (`standard`/`premium`/`education`/`None`), `scans_used_this_period`,
  and `current_period_end` (`app/models.py`, migrated via `app/db.py`'s
  `_ADDED_COLUMNS`). `Account.PLAN_LIMITS` is the one source of truth for
  price/project-cap/scan-cap per plan. The matching Stripe price is *not* an
  env var: each price was created with a `lookup_key` (`fig_plan_{plan}`,
  `scripts/stripe_plans_setup.py`), and `app/billing.py:_plan_price_id`
  resolves it from the live Stripe account at checkout time. That means no
  plan-specific config has to be duplicated onto Render (or any other
  deployment) beyond the `STRIPE_SECRET_KEY` it already needs -- the id
  lives once, in Stripe, not copied into every environment's `.env`.
- `app/billing.py:start_checkout(session, account, plan=...)` -- a "direct"
  (self-serve) account must pass a plan; there is no fixed-price fallback.
  Partner/agency accounts and any pre-existing direct subscription keep the
  legacy per-site volume checkout (`plan` omitted). The chosen plan rides on
  the Stripe subscription's own metadata (`fig_plan`), not the price id, so
  the webhook (`_apply_plan_and_period`) reads back what was actually bought
  once `customer.subscription.created`/`.updated` fires. `current_period_end`
  changing is what resets `scans_used_this_period` to 0 -- no cron job.
- Enforcement lives in three places: `app/webapp.py:_require_scanning_allowed`
  (trial expiry, now also scan-quota exhaustion -- shared by add_project,
  single audit, and audit_all), `add_project`'s own active-project-cap check,
  and `app/jobs.py:enqueue_scan`/`enqueue_estate` (the actual reservation --
  every scan, including a Watch's, goes through `enqueue_scan`, which is why
  quota is charged there and not at each call site individually).
  `enqueue_estate` caps a bulk audit at whatever quota remains rather than
  refusing it outright, matching "a bulk audit consumes one scan per website."
  A scan that ultimately fails (`app/jobs.py`'s `_run` and `reclaim_stale`)
  releases its reservation.
- Settings' billing panel (`app/pages.py:settings()`) reports a real plan
  subscriber correctly now -- `account.plan`, not `stripe_subscription_id`
  alone, decides whether the legacy per-site block or the fixed-price block
  renders (both set `stripe_subscription_id` the same way). Usage now shows
  a real project cap and a "Scans this period" row when a plan is active.
- The pricing page's Standard/Premium/Education cards
  (`frontend/components/plan-catalogue.tsx`) call real checkout instead of a
  mailto link; Enterprise/School Registered are unchanged (still Contact Us,
  correctly -- they have no Stripe price to check out). A signed-out visitor
  gets a clear "sign up or sign in first" message rather than a confusing
  401.
- Tested without touching the real Stripe account: `test_billing.py`
  (`PlanCheckoutTests`, `PlanWebhookTests`), `test_jobs.py` (`QuotaTests`,
  plus a reclaim-releases-quota case), `test_workspace_library.py`
  (`PlanQuotaEnforcementTests`), `test_launch_hardening.py` (Settings
  reporting a real plan). The highest-severity assertions were verified
  non-vacuous by reverting the fix and confirming the new tests fail first.

**The three real Stripe Price objects are live (2026-09-24).** Created via
the new `scripts/stripe_plans_setup.py` (`--check` reads without creating;
plain run creates, idempotent by `lookup_key` so a second run reuses rather
than duplicates) -- confirmed nothing existed first, then created against
the live account. Checkout for all three plans is live end to end in this
codebase, on every deployment that already has `STRIPE_SECRET_KEY` -- Render
included, with nothing further to add there (see the `lookup_key` point
above; this was originally built as three more Render env vars to set, then
corrected the same day once it was clear that just duplicates Stripe's own
mapping for no reason). Verified for real, not just unit-tested: resolved
all three prices by `lookup_key` against the live account directly.
Currency is USD, unchanged, so no further confirmation was needed there.
