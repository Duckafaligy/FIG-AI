import { SITE_URL } from "@/lib/legal";

// llmstxt.org: a short, factual guide for AI answer engines. FIG's own
// scanner flags sites without one (check_llms_txt), so FIG serves its own.
export function GET() {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "1") return new Response("Not found", { status: 404 });
  const body = `# FIG

> FIG is a self-check tool for website owners and students. It scans a site's public pages for patterns commonly associated with generic, templated design, and explains where each one is, why it reads as generic, and a concrete fix. It is for improving your own site, not for judging anyone else's work, and its findings are probabilities, never proof of how a page was made.

Checks run across four layers: craft (visual design), structure, search, and answers (how easily an AI answer engine can quote the page).

## Pages

- [Free scan](${SITE_URL}/): scan up to six public pages of any site, no account needed.
- [Pricing](${SITE_URL}/pricing): Standard $49, Premium $99 and Education $19 per month; Enterprise and School Registered by enquiry.
- [About FIGBot](${SITE_URL}/bot): how FIG's crawler identifies itself, respects robots.txt, and how to contact us about it.

## Legal

- [Privacy Policy](${SITE_URL}/privacy)
- [Terms & Conditions](${SITE_URL}/terms)
- [Refunds & cancellation](${SITE_URL}/refunds)
`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600" } });
}
