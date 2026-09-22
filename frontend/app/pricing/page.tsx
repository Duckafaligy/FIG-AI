import type { Metadata } from "next";
import Link from "next/link";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { PlanCatalogue } from "@/components/plan-catalogue";
import { Faq } from "@/components/faq";
import { PricingPhotography, PricingComparison } from "@/components/pricing-visuals";
export const metadata: Metadata = { title: "Business & Education Pricing — FIG", description: "FIG Business: Standard $49/month, Premium $99/month, Enterprise by enquiry. Education $19/month, with School Registered plans by enquiry.", alternates: { canonical: "/pricing" } };
export default function PricingPage() {
  return <div className="public-page pricing-page"><PublicNav active="pricing" /><main>
    <section className="section page-shell fig-pricing-intro"><span className="fig-pricing-pill">Two paths. One better web.</span><h1>Invest in your website.<br /><span>Or in what you know.</span></h1><p>Practical tools for business. Fresh perspectives for learning.<br />Find your place with FIG.</p><div className="fig-pricing-audiences"><a href="#business"><span>For businesses</span><small>From $49 / month ↓</small></a><a href="#education"><span>For education</span><small>From $19 / month ↓</small></a></div></section>
    <PricingPhotography />
    <div className="page-shell"><PlanCatalogue /></div>
    <PricingComparison />
    <section className="section page-shell fig-pricing-faq"><div className="section-heading"><span className="section-kicker">Before you choose</span><h2>Good questions.<br />Clear answers.</h2><p>A little clarity for your next step.</p></div><Faq items={[
      { question: "Which plan is right for me?", answer: "Standard and Premium are for business owners. Education is for students and individual learners. Contact us about Enterprise or School Registered for an organizational arrangement." },
      { question: "How do I subscribe?", answer: "Use the enquiry button on your chosen plan. We’ll confirm its inclusions and subscription details before you make a payment." },
      { question: "Can I try website analysis first?", answer: "Yes. You can run a free public website scan from the homepage without an account." },
      { question: "Are prices monthly?", answer: "Yes. Standard, Premium, and Education prices are monthly USD amounts. Any applicable taxes are additional." },
    ]} /></section>
    <section className="page-shell home-cta"><div className="home-cta-copy"><h2>Start with your website.</h2><p>Understand what’s working and what you can improve.</p></div><Link className="button button--light" href="/#scan">Run a free scan</Link></section>
  </main><Footer /></div>;
}
