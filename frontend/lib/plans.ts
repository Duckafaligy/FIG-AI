import { OPERATOR } from "./legal";
// Marketing catalogue, not Stripe price IDs. Existing subscriptions are unchanged.
// price/projects/scans mirror Account.PLAN_LIMITS; test_pricing_sync.py fails if they drift.
// Contact-only plans keep price: null (no checkout); `from` and their limits are published
// starting points (PLAN-DECISIONS.md, 2026-09-26), agreed per customer.
export const PLANS = [
  { name: "Standard", audience: "Business", price: 49, projects: 3, scans: 100, from: null, description: "Understand what your website communicates and fix the avoidable issues." },
  { name: "Premium", audience: "Business", price: 99, projects: 5, scans: 250, from: null, description: "Make website quality an ongoing routine across more of your sites." },
  { name: "Enterprise", audience: "Business", price: null, projects: 15, scans: 1000, from: 299, description: "Requirements across many websites, workflows and teams. Scoped with you." },
  { name: "Education", audience: "Education", price: 19, projects: 1, scans: 200, from: null, description: "Learn how design, structure, search and clear answers work on real websites." },
  { name: "School Registered", audience: "Education", price: null, projects: 25, scans: 1000, from: 99, description: "Website analysis as a classroom activity. Never grading or AI-use accusations." },
] as const;
export type Plan = (typeof PLANS)[number];
/** Monthly price for display: the fixed price, or the published starting point. */
export const monthly = (p: Plan) => (p.price ?? p.from)!;
export function planContact(name: string) { return `mailto:${OPERATOR.email}?subject=${encodeURIComponent(`FIG ${name} plan enquiry`)}`; }
