import { OPERATOR } from "./legal";
// Marketing catalogue, not Stripe price IDs. Existing subscriptions are unchanged.
export const PLANS = [
  { name: "Standard", audience: "Business", price: 49, description: "For business owners building a stronger website." },
  { name: "Premium", audience: "Business", price: 99, description: "For businesses making website improvement a priority." },
  { name: "Enterprise", audience: "Business", price: null, description: "For organizations with specific website and team requirements." },
  { name: "Education", audience: "Education", price: 19, description: "For students and curious minds learning to create and analyze websites." },
  { name: "School Registered", audience: "Education", price: null, description: "For schools bringing website analysis into the classroom." },
] as const;
export function planContact(name: string) { return `mailto:${OPERATOR.email}?subject=${encodeURIComponent(`FIG ${name} plan enquiry`)}`; }
