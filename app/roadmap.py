"""The checklist: everything this product is meant to do, and where each part is.

Kept in code rather than in a document so it is visible inside the product and
hard to let drift. Status is one of:

    done      built and exercised
    partial   built, with a named gap
    planned   designed, not built

If something here says `done` and is not, that is a bug in this file.
"""
from __future__ import annotations

# (area, [(title, status, note)])
CHECKLIST = [
    ("The audit", [
        ("Crawl a site", "done",
         "Sitemap discovery, then breadth-first over internal links. robots.txt "
         "honoured, one request per host at a time, https with an http fallback."),
        ("Craft checks", "done",
         "Uniform cards, numbered eyebrows, filler copy, default palettes, flat "
         "type scale, over-used icons."),
        ("Structure checks", "done",
         "Section order, h1 presence and count, heading level skips, thin pages."),
        ("Search checks", "done",
         "Title, meta description, canonical, lang, alt text, internal links."),
        ("Answers checks", "done",
         "Structured data, answerable questions, copy specificity."),
        ("Section-order check", "done",
         "Roles inferred from what is in each block, then reported when pricing "
         "sits above the section that justifies it. Nothing else does this."),
        ("A why and a fix on every finding", "done",
         "Written by the rule. ai_explain rewrites them per page when a key is set."),
        ("Four layer scores", "done",
         "Craft, Structure, Search, Answers, each traceable to a finding."),
        ("Tune the reference lists", "partial",
         "The colour, phrase and icon lists exist and work. They need calibrating "
         "against real generated-vs-handmade sites; section roles still over-match "
         "pricing on pages that quote figures in prose."),
        ("Estate audits", "done", "Every site on an account queued at once."),
        ("Scheduled monitoring", "planned",
         "Site.monitor and monitor_days exist and nothing reads them. Needs "
         "APScheduler enqueueing the same jobs on a cadence."),
    ]),

    ("Publishing back to the site", [
        ("Propose changes from findings", "done",
         "Mechanical fixes -- titles, descriptions, canonicals, lang, schema, alt, "
         "headings -- become a queued change. Judgement calls stay advice."),
        ("Approve and reject", "done", "Nothing is written without a person approving it."),
        ("Keep a before-state", "done",
         "Every change records what was there, so a publish can be undone."),
        ("WordPress adapter", "planned", "The write path itself."),
        ("Shopify adapter", "planned", ""),
        ("Webflow adapter", "planned", ""),
        ("Secret store for CMS credentials", "planned",
         "Integrations currently hold a reference and a hint, never the key, and "
         "refuse to publish until a real store is wired up."),
        ("Auto-publish per scope", "partial",
         "The flag and the scope list exist on the integration; no adapter reads "
         "them yet."),
    ]),

    ("The content queue", [
        ("Briefs from findings", "done",
         "An unanswered question, a thin page, copy with no figures in it and a "
         "site with no structured data each become a brief with the phrase it "
         "is aimed at. One per gap, not one per page."),
        ("Queued to published", "done",
         "Queued, In Progress, Review, Scheduled, Published, with only the legal "
         "moves allowed. Review cannot be skipped and nothing can be sent there "
         "with no draft in it."),
        ("Score the draft", "done",
         "Nine weighted rules -- length for its category, the phrase in the "
         "title and the opening, subheadings, quotable specifics, a real "
         "question, a liftable opening paragraph, internal links, and not "
         "repeating the phrase every other paragraph."),
        ("Write the draft", "planned",
         "Deliberately not built. Every model call lives in ai_explain.py and "
         "receives flagged data, never a page; a generation step is a different "
         "call with a different cost per run. The button refuses and says so."),
        ("Keyword volume and difficulty", "planned",
         "Needs a keyword source. The columns are empty rather than estimated."),
        ("Publish a post to the CMS", "planned",
         "Same adapters as the change queue. Refuses until one is connected."),
        ("Per-post traffic", "planned",
         "Clicks per published post needs Search Console."),
    ]),

    ("Visibility", [
        ("SEO report", "done",
         "Per-layer, leading with what already passes. Lives at /app/seo/audit "
         "now that the content queue is the SEO page."),
        ("GEO report", "done", "Same shape, for what a model can quote."),
        ("Search Console connection", "planned",
         "Clicks, impressions, CTR and position are all measured there. Until it "
         "is connected those panels carry a badge instead of numbers."),
        ("Model-visibility crawl", "planned",
         "Run buyer questions against ChatGPT and Claude on a schedule and record "
         "who got cited. This is the half the marketing site leads with."),
        ("Site tracker", "planned",
         "A first-party script for visits and performance after each change, so "
         "the effect of a published fix is measurable."),
        ("Core Web Vitals", "planned", "Needs either CrUX or the tracker above."),
    ]),

    ("The dashboard", [
        ("Overview", "done", "Metric cards, performance chart, and the panel grid."),
        ("Sites list", "done", "Sortable, filterable, with layer scores inline."),
        ("Site detail", "done",
         "Score, layers, change since the last audit, score history, findings by "
         "layer, pages read with their section order."),
        ("Findings across the estate", "done",
         "Grouped by problem rather than by site, ranked by severity times reach."),
        ("Notifications", "partial",
         "Derived from failed audits, moved scores and high-severity findings. "
         "Email delivery is not built."),
        ("History and analytics", "done", "Audit log, direction of travel, layer movement."),
        ("Settings", "done", "Account, billing, API keys, integrations, this checklist."),
        ("Edit Dashboard", "planned",
         "The button exists. Rearranging and hiding panels does not."),
        ("Project switcher", "planned",
         "The pill exists and shows the current account. It does not switch yet."),
        ("Dashboard search", "partial",
         "Cmd-K focuses the field. It does not search anything."),
    ]),

    ("Accounts and money", [
        ("Sign in", "done", "Supabase Auth, verified server-side, own session cookie."),
        ("Sign up", "done", "With a workspace name, so nobody inherits someone else's sites."),
        ("Google sign-in", "partial",
         "Wired up; needs the provider switching on in the Supabase project."),
        ("Free first week", "done",
         "Seven days from account creation, no card, carried over into checkout."),
        ("Per-site billing", "done",
         "Volume tiers, subscription quantity tracks the active site count."),
        ("Stripe webhook", "planned", "Needs a public URL before the secret exists."),
        ("Live payments", "planned", "Test-mode keys today."),
        ("Team members and roles", "planned",
         "The marketing site describes handing a fix to whoever owns the page."),
        ("White-labelled reports", "partial",
         "The account flag exists and the dashboard respects it. There is no "
         "report export to brand yet."),
    ]),

    ("The public side", [
        ("Free read, no account", "done",
         "Rate limited per browser and per network before any work is queued."),
        ("Recent reads feed", "done",
         "Anonymous unless the person who ran it chose to share the domain."),
        ("Homepage", "partial", "Being rebuilt to the new design."),
        ("Content pages", "partial",
         "Twenty pages written -- rulebook, glossary, schema and robots "
         "references, fix recipes, docs, API, legal. Archived pending the redesign."),
        ("Shareable report links", "planned",
         "A per-audit public URL with an OG image. The growth mechanic."),
    ]),

    ("Running it", [
        ("Job queue", "done", "DB-backed, worker threads, retries with backoff."),
        ("Postgres on Supabase", "done", "Through the session pooler."),
        ("REST API", "done", "Provision, audit, poll, estate report, verification."),
        ("API keys", "done", "SHA-256 stored, plaintext shown once."),
        ("Webhooks out", "planned", "Documented shape; no delivery yet."),
        ("Deployment", "planned",
         "Marketing site to Vercel, backend to Railway or Render. Neither done."),
        ("Error tracking", "planned", "No Sentry, no structured logging."),
        ("Email", "planned", "Needed for verification instructions and alerts."),
    ]),
]


def summary() -> dict:
    flat = [(area, t, s, n) for area, items in CHECKLIST for t, s, n in items]
    return {
        "areas": CHECKLIST,
        "total": len(flat),
        "done": sum(1 for *_r, s, _n in [(a, t, s, n) for a, t, s, n in flat] if s == "done"),
        "partial": sum(1 for a, t, s, n in flat if s == "partial"),
        "planned": sum(1 for a, t, s, n in flat if s == "planned"),
    }
