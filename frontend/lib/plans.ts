import { OPERATOR } from "./legal";
// Marketing catalogue, not Stripe price IDs. Existing subscriptions are unchanged.
export const PLANS = [
  { name: "Standard", audience: "Business", price: 49, description: "For owners who want to understand what their website communicates, identify avoidable issues, and make more informed improvements." },
  { name: "Premium", audience: "Business", price: 99, description: "For businesses making website quality an ongoing priority—from reviewing findings to planning content and assessing changes." },
  { name: "Enterprise", audience: "Business", price: null, description: "For organizations with requirements to discuss across websites, workflows, and teams. Talk through your scope before choosing an arrangement." },
  { name: "Education", audience: "Education", price: 19, description: "For students and independent learners exploring how design, page structure, search fundamentals, and clear answers work together on real websites." },
  { name: "School Registered", audience: "Education", price: null, description: "For schools exploring website analysis as a learning activity—not automated grading or AI-use accusations. Discuss your classroom needs with us." },
] as const;
export function planContact(name: string) { return `mailto:${OPERATOR.email}?subject=${encodeURIComponent(`FIG ${name} plan enquiry`)}`; }
