/**
 * Facts every legal page shares, in one place.
 *
 * The privacy policy, terms, refund policy and crawler page all read from here,
 * so the operator's name, the contact address and the list of services that
 * touch user data change once, not four times. The statements themselves were
 * checked against the code (see the notes beside each), because a policy that
 * describes a product that isn't this one is worse than no policy.
 *
 * BEFORE PUBLISHING: fill in `OPERATOR`. Until every field is real, each legal
 * page shows a visible "draft" notice (`legalIsDraft`), so an unfinished page
 * cannot quietly pass as a finished one. These pages are written to common
 * standards (GDPR Art. 13, CCPA/CPRA, PIPEDA, Google's API Services User Data
 * Policy) but are not legal advice; have a qualified person read them before
 * relying on them.
 */

export const OPERATOR = {
  /** The person or company that runs FIG and is party to the Terms. */
  name: "Brendan Ho Lok Lau",
  /** A monitored address for privacy, refund and removal requests. */
  email: "Brendanhllau@gmail.com",
  /** A postal address (required by CASL and by GDPR Art. 13 for the controller). */
  address: "Markham, Ontario, Canada",
  /** Whose law governs the Terms, e.g. "Ontario, Canada". */
  jurisdiction: "Ontario, Canada",
};

/** Every field must be filled before the pages stop saying "draft". */
export const legalIsDraft = Object.values(OPERATOR).some((value) => value.startsWith("["));

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "https://fig-ai-seven.vercel.app").replace(/\/+$/, "");

/** Bump when the text of any legal page changes in a way that matters. */
export const LAST_UPDATED = "September 21, 2026";

/** Matches `Account.TRIAL_DAYS` in app/models.py; keep the two in step.
 *  test_pricing_sync.py fails if these two ever drift apart. */
export const TRIAL_DAYS = 3;

/** Days after a first payment during which a full refund is available. */
export const REFUND_WINDOW_DAYS = 14;

/**
 * The services that receive personal data on FIG's behalf. Each row is a real
 * dependency (see PLATFORMS.md). An email provider is not listed because none
 * is wired up yet; add it here the day one is.
 */
export const SERVICE_PROVIDERS = [
  { name: "Supabase", role: "Sign-in, password storage and the main database", data: "Email, name, workspace and project data, content drafts, scan results" },
  { name: "Render", role: "Runs FIG's backend", data: "Everything the backend handles while it runs, plus server logs" },
  { name: "Vercel", role: "Serves the website and passes requests to the backend", data: "Web requests (IP address, browser details) and server logs" },
  { name: "Stripe", role: "Takes payments and manages subscriptions", data: "Name, email, billing details and payment method (held by Stripe, not FIG)" },
  { name: "Anthropic", role: "Writes the plain-language explanation of each finding", data: "The site's hostname, short descriptions of the patterns found, and short examples the rules matched (a phrase, a colour, an icon name). Never whole pages or your drafts" },
  { name: "Google", role: "Only if you connect Analytics or Search Console", data: "Read-only reports about your own site, fetched on your behalf" },
] as const;
