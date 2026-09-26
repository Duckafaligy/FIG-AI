import type { Metadata } from "next";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { NeonCta } from "@/components/neon-cta";
import { NeonFaq } from "@/components/neon-faq";
import { PricingNeon } from "@/components/pricing-neon";
import { REFUND_WINDOW_DAYS, TRIAL_DAYS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Pricing - FIG",
  description: "Standard $49, Premium $99 and Education $19 per month. Every plan runs all 21 checks; plans differ in projects and scans per month.",
  alternates: { canonical: "/pricing" },
};

const faq = [
  { question: "What counts as a scan?", answer: "One audit of one website. Auditing several projects at once uses one scan per website, and a scan that fails doesn't count." },
  { question: "What happens when I run out of scans?", answer: "You can't start new scans until your billing period resets. Unused scans don't roll over, and nothing is charged beyond your plan price." },
  { question: "Can I try it before paying?", answer: `Yes. Scan up to six public pages from the homepage with no account, or create an account for a ${TRIAL_DAYS}-day trial with no card.` },
  { question: "Who is Education for?", answer: "Students and independent learners studying their own projects. It runs the same checks as the business plans, never grading or AI-use accusations." },
  { question: "How do I cancel?", answer: `From Settings, Billing, at any time. Your plan runs to the end of the period you paid for, and your first payment is refundable within ${REFUND_WINDOW_DAYS} days.` },
];

export default function PricingPage() {
  return (
    <div className="public-page pricing-page neon-home">
      <PublicNav active="pricing" />
      <main>
        <PricingNeon />
        <NeonFaq title="Questions about plans." items={faq} />
        <NeonCta />
      </main>
      <Footer />
    </div>
  );
}
