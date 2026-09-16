# FIG generic frontend functionality reference

**Snapshot:** September 15, 2026
**Audience:** product, design, frontend, and backend handoff
**Demo workspace:** one illustrative project — **Demo workspace**

This file documents the behavior that exists in the neutral, generic frontend variant. It deliberately separates a working browser interaction from an actual product integration so nobody mistakes the prototype for a live CMS, billing, authentication, analytics, or AI system. It contains no imported customer content or other customer data.

## What the current frontend is — and is not

| Status | Meaning in this build |
| --- | --- |
| **Navigation** | Changes route or scrolls to a section. |
| **Local preview interaction** | Changes React state in the current browser session. It resets after a page refresh. |
| **Read-only preview** | Shows illustrative Demo workspace information only. |
| **Planned integration** | Opens an explanatory dialog or status message. It never sends data to an external service. |

- All dashboard charts, counts, content titles, notifications, scores, users, and status labels are illustrative data for Demo workspace.
- No frontend page currently saves a record to Supabase, calls OpenAI or Anthropic, publishes into a CMS, creates Stripe customers, sends a notification, authenticates a user, or stores an API key.
- Browser validation still runs where native form fields use `required`, `type="email"`, `type="url"`, or a minimum password length. Passing validation only unlocks a local preview message; it does not submit the form.
- The project is intentionally frontend-first. The backend can replace the static page data later without changing the visual structure.

## Route map

| Route | Surface | Primary purpose |
| --- | --- | --- |
| `/` | Public home | Product story, feature preview, demo and signup routes. |
| `/pricing` | Public pricing | Monthly/yearly illustrative pricing and plan comparison. |
| `/signin` | Public auth | Sign-in interface preview. |
| `/signup` | Public auth | Account-creation interface preview. |
| `/projects` | Project chooser | The one Demo workspace project, trend, calendar, and workspace summary. |
| `/app` | Private overview | Content-performance dashboard preview. |
| `/app/seo` | Private SEO | SEO content queue and optimization view. |
| `/app/geo` | Private GEO | Generative-engine visibility and answer optimization view. |
| `/app/notifications` | Private notifications | Alerts, approvals, reminders, and reliability view. |
| `/app/history` | Private history | Activity and audit-log view. |
| `/app/settings` | Private settings | Tabbed workspace, team, connection, preference, and usage preview. |
| `/app/live` | Diagnostic only | Read-only check of the backend overlay contract; deliberately absent from product navigation. |

## Shared public-site behavior

### Header / primary navigation

The FIG wordmark returns to `/`. The header contains the following controls:

| Control | Behavior |
| --- | --- |
| **Demo** | Navigates to `/projects`. |
| **Pricing** | Navigates to `/pricing`; it is visually marked active only on the pricing page. |
| **Sign in** | Navigates to `/signin`. |
| **Sign up** | Navigates to `/signup`. |
| **Mobile menu** | Opens and closes the responsive navigation. Choosing a link closes it again. The button exposes its open state to assistive technology. |

### Platform-logo strip

Shopify, Wix, Webflow, WordPress, BigCommerce, and Google Analytics use the real brand symbols supplied by the `simple-icons` package. They are visual compatibility signals, not OAuth buttons, hyperlinks, confirmed integrations, or endorsements.

### Reusable FAQ accordion

Each FAQ question is a button. Selecting one opens its answer and closes the previously open answer; selecting the open question closes it. The open state is announced using `aria-expanded`. FAQ answers are product copy only and do not initiate support requests.

### Reusable informational dialog

Some links labelled **Privacy**, **Terms**, **Help**, or similar use a local informational dialog. Its backdrop, close button, and **Got it** button all dismiss the dialog. These dialogs do not open legal pages because those documents have not been connected yet.

### Footer

The footer provides route and on-page links:

- **Product:** feature anchors or the pricing/demo routes.
- **Resources:** workflow, GEO workspace, SEO workspace, FAQ, and help anchors/routes.
- **Company:** team/account-oriented routes where shown.
- **Workspace:** overview, notifications, history, and settings.
- **Newsletter field:** uses a regular `GET` form to `/signup`. It places the entered email into the browser URL query string only. It does **not** subscribe the address or store it. The sign-up page does not currently read that query string back into its form.

## Public home — `/`

The home page is a visual marketing page. Its cards and product-laptop illustrations use static HTML/CSS content, not embedded screenshots or live dashboard instances.

| Section / control | Current behavior |
| --- | --- |
| Hero **Try the demo** | Navigates to `/projects`. |
| Hero **Start free** | Navigates to `/signup`. |
| Hero laptop mockup | Visual preview only. It has no controls or live workspace data. |
| Platform strip and outcome statistics | Informational visuals only. |
| Eight feature cards | Explain AI-assisted planning, SEO queue, GEO optimization, CMS publishing, analytics, collaboration, notifications, and settings/API. They do not open a feature page. |
| Six-step workflow | Explains Connect → Generate → Review → Preview → Publish → Track. It is informational. |
| Platform-tour **See the full demo** | Navigates to `/projects`. |
| Platform-tour cards | Preview the project, performance, and GEO views. They are visual only. |
| GEO **Explore GEO** | Navigates to `/app/geo`. |
| AI-visibility bar chart | Hovering, focusing, or selecting a bar reveals the selected month/platform value in the chart area. The values are illustrative. |
| Audience cards | Use stock photos and descriptive content for marketers, agencies, and eCommerce teams. They do not link to people or organizations. |
| Testimonials | Representative preview testimonials; no carousel, external identity lookup, or submission mechanism. |
| Pricing-card actions | Starter and Pro **Start free** route to `/signup`; Scale routes to `/pricing`; **View full pricing** routes to `/pricing`. |
| FAQ | Uses the shared one-at-a-time accordion. |
| Bottom CTA | **Explore demo** routes to `/projects`; **Create preview** routes to `/signup`. |

## Pricing — `/pricing`

| Control / section | Current behavior |
| --- | --- |
| Monthly / Yearly switch | Recalculates display prices locally: Starter `$29` → `$23`, Pro `$79` → `$63`, Scale `$199` → `$159`. Enterprise remains custom pricing. It does not start billing, retain a preference, or calculate tax. |
| Four plan cards | Show illustrative included features. Starter, Pro, and Scale actions route to `/signup`; Enterprise **Contact sales** also routes to `/signup` as a temporary placeholder. |
| Comparison table | Static plan comparison; on a narrow display, its own container scrolls horizontally. |
| Included-in-every-plan cards | Informational feature summaries. |
| FAQ | Uses the shared accordion. |
| Bottom CTA | **Start free** routes to `/signup`; **View demo** routes to `/projects`. |

## Authentication previews — `/signin` and `/signup`

### Shared form behavior

| Control | Current behavior |
| --- | --- |
| Email field | Native email validation. No address is transmitted or retained after reload. |
| Password field | Required, minimum eight characters. The eye button switches between masked and visible text in the current form only. |
| Primary submit | Prevents network submission and replaces it with a local “frontend preview” message after native validation. No account or session is created. |
| Continue with Google / Shopify | Shows a local message explaining that the provider connection is not enabled. It does not redirect to Google or Shopify. |
| Platform strip / laptop | Informational visual content only. |

### Sign in (`/signin`)

- **Remember me** is a visual checkbox only; it does not create a persistent login preference.
- **Forgot password?** shows the local preview message; it does not send a reset email.
- **Sign up for free** navigates to `/signup`.
- Footer privacy, terms, and help are informational dialogs/anchors as described above.

### Sign up (`/signup`)

- Adds required fields for full name, company name, and website URL.
- The terms/privacy checkbox is required by browser validation. The two linked labels open informational dialogs.
- The reassurance row (“14-day free trial,” “No credit card required,” “Cancel anytime”) is descriptive only.
- **Sign in** navigates to `/signin`.
- The benefit grid, laptop preview, platform strip, and footer are informational. No trial, customer, or subscription is created.

## Projects — `/projects`

This is the only project selector in the demo. It is scoped to one Demo workspace card so the visual layout stays believable before customer records exist.

| Control / section | Current behavior |
| --- | --- |
| FIG / Demo workspace brand | Links back to `/projects`. |
| Top search and panel search | Share one local query. They filter the single project by project/domain/content text. When no match remains, **Clear search** resets it. |
| Workspace and date chips | Present the demo workspace/date range only; they are not dropdowns. |
| **New project** / **Create new project** | Opens a native dialog explaining that this preview has one project. **Open Demo workspace** routes to `/app`; close controls dismiss the dialog. No project is created. |
| Notifications icon | Navigates to `/app/notifications`. |
| Grid / List | Switches a local layout class and reports state with `aria-pressed`. With one project, the visual difference is intentionally subtle. |
| Sort select | Shows “Last updated” and “Name A–Z”; it is presentational for the single-project preview and does not reorder data yet. |
| Demo workspace card | Navigates to `/app`. |
| Workspace summary cards | Static illustrative indicators. |
| Workspace Performance Trend range | A real select changes local sample data and labels between **1 day**, **3 days**, **7 days**, and **30 days**. Hover/focus details are available on chart points. Values remain illustrative. |
| SEO / GEO **View details** | Route to `/app/seo` and `/app/geo` respectively. |
| Top content / activity / opportunities links | Route to the related overview, history, or SEO dashboard. |
| All Projects Performance search | Visible design affordance only; it does not currently filter the one static row. |
| Content Calendar arrows | Move the displayed month backwards or forwards. |
| Content Calendar month select | Selects a month in the displayed year. |
| Content Calendar day | Selects a date; dates outside the current month also switch the visible month. Event chips show the sample item(s) planned for that day. |
| Calendar agenda | Updates live to show the selected date’s title, time, content type, template, and demo status. It does not schedule/publish content. |
| Automation summary | Informational current-state preview only. |

## Private workspace shell — `/app/*`

### Persistent shell controls

| Control | Current behavior |
| --- | --- |
| Sidebar Demo workspace logo | Returns to `/projects`. |
| Overview / SEO / GEO / Notifications / History / Settings | Navigate to the corresponding private route. The notification badge is illustrative. |
| **Back to projects** | Navigates to `/projects`. |
| Mobile menu button | Opens/closes the sidebar on compact screens; choosing a navigation link closes it. |
| Search current dashboard | Filters visible data rows in the current dashboard by title, meta text, category, status, and cells. It does not change KPI cards, charts, workflows, or answer previews. The X button clears the query. |
| Workspace/date controls | Label the fixed Demo workspace preview and illustrative date range. They are not switches. |
| Bell | Navigates to `/app/notifications`. |
| JD avatar / trailing caret | Decorative current-account display only. |

### Shared dashboard headers

- **Project settings** and **Manage alerts** navigate to `/app/settings`.
- Other header buttons open a local explanatory dialog:
  - **Create brief** describes the future brief-creation flow.
  - **Add query** describes future prompt tracking.
  - **Export log** describes future activity export.
  - **Edit profile** describes future workspace profile storage.
- Every dialog includes a clear statement that no live data changed, a close action, and a shortcut to workspace settings.

### Shared metrics, filters, charts, and tables

| Component | Current behavior |
| --- | --- |
| KPI cards | Read-only illustrative numbers, trend labels, and iconography. |
| Range select on line/bar charts | Uses local sample series for 1, 3, 7, or 30 days. The range control changes labels/data in the current page only. |
| Line-chart points | SVG point markers are round, not stretched. Mouse hover and keyboard focus expose the selected point’s details. |
| Bar-chart columns | Hover/focus exposes local sample detail. |
| Donuts/reliability rings | Read-only visual summaries. |
| Table tabs | Filter the table’s local rows by selected tab/category/status where configured. |
| Table search | Filters matching rows in the current table only. |
| Table status/category selects | Apply local filtering where configured. |
| Row title / action button | Opens the content-detail dialog or a compact activity/details dialog. |
| Publish / Reject in content dialogs | Updates only that row’s local status and a local notice. A refresh restores the demo dataset. |
| Remove draft | Requires confirmation, then removes the local row for the current session only. |

## Content detail and publishing preview

Content-related row actions intentionally show more than a shallow modal so designers and backend work can target the eventual CMS workflow.

| Dialog area / control | Current behavior |
| --- | --- |
| **Page preview** tab | Renders a full, styled content snapshot rather than only metadata. It includes a mock browser frame, article hierarchy, table of contents/anchors, body sections, calls to action, related links, and a template-aware presentation. |
| Template visuals | Uses a **Guide**, **Blog**, or **Tutorial/Resources** visual pattern. The choice changes the information architecture and path preview; no external template is retrieved. |
| In-preview anchors | Scroll to the corresponding local content section. |
| **SEO & metadata** tab | Provides editable local SEO title, slug, and meta description fields with character indicators and a live SERP-style preview. |
| **Regenerate** | Cycles through alternative sample SEO title, description, prompt, and introduction copy for the current browser session. It does not call an AI model. |
| **Publish setup** tab | Lets the user choose a mock CMS template, timing, and destination path. The preview updates the path and a local checklist responds to valid title, description, slug, and template choices. |
| **Review full page** | Returns to the rendered snapshot. |
| **Schedule review** | Shows a local tomorrow-at-9AM demo status. It does not create a calendar event. |
| **Publish in demo** / **Schedule in demo** | Update the local row status and dialog notice only; no CMS endpoint is used. |
| **Remove draft** | Opens a local confirmation state and removes the demo row after confirmation. |
| Arrow/Home/End keys in content tabs | Move through the three tabs for keyboard users. |

## Workspace overview — `/app`

The overview contains these read-only or locally interactive sections:

| Section | Behavior |
| --- | --- |
| Content Performance Trend | Local range selector and interactive line-chart point details. |
| Google Analytics (Blog Content) | Read-only illustrative session, bounce, conversion, and reader cards. |
| Search Presence & AI Visibility | Read-only indicator rows. |
| Highest Impact Blog Posts | Read-only ranked table; row action opens its content preview where available. |
| Content Publishing Funnel | Read-only workflow/ring summary. |
| Recent Activity | Read-only activity preview; the view-all path routes to History. |
| Top Ranking Keywords | Read-only ranked keyword table. |
| Content Opportunities | Read-only opportunity list; view-all routes to SEO. |
| Published Blog Library | Local search/status filtering and row-detail dialogs. |
| Workspace Health | Read-only connection/health preview. |

## SEO workspace — `/app/seo`

| Section | Behavior |
| --- | --- |
| Content Creation Flow | Read-only Connect → intake → template → review flow. |
| Template Preview | Read-only sample template/status preview. |
| Blog Posts for Review | Tabs, local table filtering, row previews, local Publish/Reject status changes, and the full content/publishing dialog. |
| Highest Impact Blog Posts | Read-only ranking. |
| Keyword Ranking Momentum | Range-selectable local stacked-bar sample. |
| Optimization Opportunities | Read-only opportunity list. |
| Internal Linking Suggestions | Read-only suggested source/target/anchor list. |
| Published SEO Library | Local search/category filtering and content detail dialogs. |
| Keyword Cluster Coverage | Read-only donut/summary. |
| SEO Health Summary | Read-only health items. |

## GEO workspace — `/app/geo`

| Section | Behavior |
| --- | --- |
| From Content to AI Visibility | Read-only four-step workflow. |
| AI Answer Preview | Read-only sample answer, source ordering, and quality state. |
| Visibility Across AI Platforms | Range-selectable local multi-line sample. |
| GEO-Optimized Content | Local tabs/filters, detail dialogs, and local Publish/Reject actions where shown. |
| Top Blogs by AI Mentions | Read-only ranked list. |
| Citation Opportunities | Read-only potential-reach list. |
| Prompt Cluster Performance | Read-only inclusion-rate list. |
| Answer Snippet Quality Review | Read-only source/quality table. |
| Source Citation Breakdown | Read-only distribution ring. |

## Notifications — `/app/notifications`

| Section | Behavior |
| --- | --- |
| Notification Feed | Local tabs for All, Unread, Approvals, Automations, Syncs, and Reminders. **View**, **Resolve**, and **Review** open local details; they do not send, acknowledge, or resolve a real alert. |
| Alerts Over Time | Range-selectable local line chart. |
| Automation Reliability | Read-only reliability ring and indicator list. |
| Automation Alerts | Read-only priority list. |
| Scheduled Content Reminders | Read-only schedule preview. |
| Approval Needed | Read-only approval list. |
| Failed Jobs / Sync Errors | Read-only error table. |
| Notification Channels & Delivery | Read-only delivery-health table. |
| Escalation Rules | Read-only rules preview. |
| Recently Resolved | Read-only resolved-item table. |

## History — `/app/history`

| Section | Behavior |
| --- | --- |
| Activity Trend | Range-selectable local line chart. |
| Actions by Category | Read-only category ring. |
| Recent Activity Stream | Read-only latest-event list. |
| Quick Filters | A visual summary of future filter choices; these chips do not filter the page yet. |
| Activity by Actor | Read-only ranked actor list. |
| Detailed Audit Log | Local search/filter controls where configured; event actions open local record details. **Export log** in the header is explanatory only. |
| Most Active Work Areas | Read-only ranking. |
| Most Edited Content | Read-only ranking. |
| Publish History | Read-only timeline. |
| Reverts & Rejections | Read-only timeline. |

## Settings — `/app/settings`

Settings use an application-style vertical tab list rather than one long, unstructured page. Choosing a tab replaces the content panel in the current session; the selected tab resets after a page refresh.

| Tab | Controls and current behavior |
| --- | --- |
| **Workspace** | Workspace profile, plan summary, and usage cards are read-only. **Edit profile** and **Manage billing** open informational dialogs; no profile or billing data changes. |
| **Team & roles** | Shows sample members, roles, permissions, and activity. **Invite member** and each **Manage** button open local explanatory dialogs; no invitation is sent. |
| **Integrations** | Shows Supabase, OpenAI, Anthropic, Stripe, Shopify, Google Analytics, Search Console, and Webhooks as readiness/optional/pending preview states. **Connect service** and **Setup** only explain the future setup flow. There are no secret fields, credential tests, OAuth redirects, or API writes. |
| **Billing & usage** | Presents illustrative Pro-plan price/usage cards. **View billing details** is informational; it does not access Stripe. |
| **Security** | Two-factor and login/session notification toggles update local UI state only. SSO and active-session rows are informational. Nothing is persisted or enforced. |
| **Notifications** | Each preference toggle updates local UI state only and resets on reload. It does not alter email, Slack, browser, or system delivery. |
| **Content defaults** | Six selects allow local browser values for voice, audience, tone, language, AI model, and post format. **Save local preview** shows a local confirmation only; it does not save preferences or configure a model. |
| **Webhooks** | Endpoint count/delivery metrics are illustrative. **Add endpoint** and **View example** are informational; no endpoint, signing secret, request, or event is created. |

## Diagnostic live-data route — `/app/live`

`/app/live` is intentionally separate from the designed product navigation. It exists to verify the future frontend/backend contract without silently making the polished screens look live before they are wired.

| Item | Behavior |
| --- | --- |
| Backend status card | Calls the configured API’s `me` endpoint and reports reachable/unreachable, session state, development no-auth state, and workspace label. |
| Page links | Switch between read-only live-overlay checks for overview, SEO, GEO, notifications, and history using `?page=`. |
| Live overlay | Requests an overlay for the selected page. If unavailable, it explicitly falls back to the static preview and explains why. |
| Data safety | It is read-only from this frontend. It does not create data, expose secret values, or change an external system. |

For a deployed backend connection, set `NEXT_PUBLIC_API_URL` to the public API base, ensure CORS/auth are configured for the Vercel domain, and replace the designed dashboard route with the live overlay component only after the API response is validated. Do not put server secrets in any `NEXT_PUBLIC_*` variable.

## Visual, responsive, and accessibility behavior

- Shared focus rings make keyboard position clear on links, buttons, inputs, selects, and textareas.
- Cards and dashboard panels get restrained hover elevation on pointer devices; interactive buttons receive color, border, shadow, and transform transitions.
- Hero, auth, dashboard-card, and project-panel entry animations use a short fade-up sequence. They do not block content.
- `prefers-reduced-motion: reduce` disables animation and transitions and uses normal scrolling.
- Wide tables and the calendar retain their own scroll area on narrow viewports instead of causing document-level horizontal overflow.
- The footer newsletter controls stack on small screens, dashboard headers avoid awkward button compression, and project workspace/date chips hide when they no longer fit.
- Chart points and bars expose their local detail using pointer and keyboard focus rather than relying on color alone.
- Dialog close controls have accessible labels, FAQ questions use expanded state, and calendar days use a detailed accessible date/event label.

## Code map for the next implementation phase

| Concern | Main files |
| --- | --- |
| App metadata and global styles | `app/layout.tsx`, `app/globals.css`, `app/redesign.css`, `app/interaction-polish.css` |
| Public home and pricing | `app/page.tsx`, `app/pricing/page.tsx` |
| Public nav, footer, FAQ, marketing illustrations | `components/public-nav.tsx`, `components/footer.tsx`, `components/faq.tsx`, `components/product-laptop.tsx`, `components/platform-logos.tsx`, `components/visibility-chart.tsx` |
| Auth previews | `app/signin/page.tsx`, `app/signup/page.tsx`, `components/auth-form.tsx` |
| Project chooser and calendar | `app/projects/page.tsx`, `app/projects/projects-calendar.module.css`, `lib/chart-range.ts` |
| Private shell and dashboard mechanics | `app/app/layout.tsx`, `components/dashboard-shell.tsx`, `components/dashboard-page.tsx` |
| Dashboard content/data model | `lib/dashboard-pages.ts` |
| Full preview and publishing dialog | `components/dashboard-shell.tsx`, `components/content-template-preview.tsx` |
| Live-data diagnostic surface | `app/app/live/page.tsx`, `components/live-dashboard-page.tsx`, `lib/api.ts`, `lib/live.ts` |
| Vercel deployment instructions | `VERCEL-DEPLOYMENT.md`, `vercel.json` |

## Deployment handoff

The frontend is a standalone Next.js app inside the repository’s `frontend-generic` directory. The exact Vercel setup, environment-variable boundary, and production verification command are in [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md).
