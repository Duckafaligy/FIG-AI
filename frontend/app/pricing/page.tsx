import type { Metadata } from "next";
import Link from "next/link";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { PlanCatalogue } from "@/components/plan-catalogue";
import { Faq } from "@/components/faq";
export const metadata: Metadata = { title: "Business & Education Pricing — FIG", description: "FIG Business: Standard $49/month, Premium $99/month, Enterprise by enquiry. Education $19/month, with School Registered plans by enquiry.", alternates: { canonical: "/pricing" } };
export default function PricingPage() {
  return <div className="public-page pricing-page"><PublicNav active="pricing" /><main>
    <section className="section page-shell fig-pricing-intro"><span className="section-kicker">Plans for building and learning</span><h1>A better website.<br /><span>A deeper understanding.</span></h1><p>Whether you run a business or want to learn how websites work, find a FIG plan that fits your next step.</p><div className="fig-pricing-audiences"><a href="#business">For businesses</a><a href="#education">For education</a></div></section>
    <div className="page-shell"><PlanCatalogue /></div>
    <section className="section page-shell"><div className="section-heading"><h2>A few things to know</h2></div><Faq items={[
      { question: "Which plan is right for me?", answer: "Standard and Premium are for business owners. Education is for students and individual learners. Contact us about Enterprise or School Registered for an organizational arrangement." },
      { question: "How do I subscribe?", answer: "Use the enquiry button on your chosen plan. We’ll confirm its inclusions and subscription details before you make a payment." },
      { question: "Can I try website analysis first?", answer: "Yes. You can run a free public website scan from the homepage without an account." },
      { question: "Are prices monthly?", answer: "Yes. Standard, Premium, and Education prices are monthly USD amounts. Any applicable taxes are additional." },
    ]} /></section>
    <section className="page-shell home-cta"><div className="home-cta-copy"><h2>Start with your website.</h2><p>Understand what’s working and what you can improve.</p></div><Link className="button button--light" href="/#scan">Run a free scan</Link></section>
  </main><Footer /></div>;
}
