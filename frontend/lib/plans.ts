import { OPERATOR } from "./legal";
// Marketing catalogue, not Stripe price IDs. Existing subscriptions are unchanged.
// price/projects/scans mirror Account.PLAN_LIMITS; test_pricing_sync.py fails if they drift.
export const PLANS = [
  { name: "Standard", audience: "Business", price: 49, projects: 2, scans: 100, description: "Understand what your website communicates and fix the avoidable issues." },
  { name: "Premium", audience: "Business", price: 99, projects: 5, scans: 250, description: "Make website quality an ongoing routine across more of your sites." },
  { name: "Enterprise", audience: "Business", price: null, projects: null, scans: null, description: "Requirements across many websites, workflows and teams. Scoped with you." },
  { name: "Education", audience: "Education", price: 19, projects: 1, scans: 200, description: "Learn how design, structure, search and clear answers work on real websites." },
  { name: "School Registered", audience: "Education", price: null, projects: null, scans: null, description: "Website analysis as a classroom activity. Never grading or AI-use accusations." },
] as const;
export function planContact(name: string) { return `mailto:${OPERATOR.email}?subject=${encodeURIComponent(`FIG ${name} plan enquiry`)}`; }
