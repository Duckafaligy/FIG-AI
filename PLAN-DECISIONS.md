# FIG plan decisions

## Owner-approved limits

Recorded September 23, 2026. These are product decisions, not yet enforced
entitlements or active Stripe prices.

| Plan | Monthly price | Active projects | Scans per month |
| --- | --- | --- | --- |
| Standard | $49 | 2 | 100 |
| Premium | $99 | 5 | 250 |
| Education | $19 | 1 | 200 |
| Enterprise | Contact us | Custom, not defined | Custom, not defined |
| School Registered | Contact us | Custom, not defined | Custom, not defined |

Monthly scan limits are interpreted from the preceding monthly-plan discussion.
Currency remains USD in the current catalogue; confirm before checkout activation.

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
