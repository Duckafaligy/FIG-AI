"use client";

import Link from "next/link";
import { ArrowRight, BarChart3, Bell, Check, Layers3, ShieldCheck, Sparkles, Users, Workflow } from "lucide-react";
import { useState } from "react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { ProductLaptop } from "@/components/product-laptop";
import { PublicNav } from "@/components/public-nav";

const plans = [
  { name: "Starter", price: "$29", annualPrice: "$23", description: "For individuals and small teams getting started.", cta: "Get started", features: ["5 projects", "1 CMS connection", "AI-assisted creation", "SEO review", "Basic analytics", "Up to 3 seats"] },
  { name: "Pro", price: "$79", annualPrice: "$63", description: "For growing teams with a steady content rhythm.", cta: "Start free", popular: true, features: ["25 projects", "5 CMS connections", "Advanced generation", "SEO + GEO workflows", "Full analytics", "Up to 10 seats"] },
  { name: "Scale", price: "$199", annualPrice: "$159", description: "For larger teams with complex content operations.", cta: "Start free", features: ["100 projects", "10 CMS connections", "Advanced generation", "SEO + GEO workflows", "Automation rules", "Up to 25 seats"] },
  { name: "Enterprise", price: "Custom", description: "For organizations with tailored requirements.", cta: "Contact sales", features: ["Unlimited projects", "Unlimited connections", "Custom workflows", "Unlimited seats", "SSO / SAML", "Dedicated success"] }
];

const comparison = [
  ["Projects", "5", "25", "100", "Unlimited"],
  ["CMS connections", "1", "5", "10", "Unlimited"],
  ["AI-assisted creation", "✓", "✓", "✓", "✓"],
  ["SEO review", "✓", "✓", "✓", "✓"],
  ["GEO workflows", "—", "✓", "✓", "✓"],
  ["Analytics", "Basic", "Advanced", "Advanced", "Advanced"],
  ["Approval workflows", "—", "✓", "✓", "✓"],
  ["Automations", "—", "—", "✓", "✓"],
  ["SSO / SAML", "—", "—", "—", "✓"]
];

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const annual = billingCycle === "yearly";

  return (
    <div className="public-page pricing-page">
      <PublicNav active="pricing" />
      <main>
        <section className="pricing-hero section-glow">
          <div className="page-shell pricing-hero-grid">
            <div><span className="section-kicker">Pricing</span><h1>Simple, transparent pricing for teams that create content that <span>gets found</span></h1><p>Choose the plan that fits your team. Every plan begins with the same calm, connected FIG workflow.</p><div className="billing-toggle" aria-label="Billing cycle"><button className={!annual ? "active" : ""} onClick={() => setBillingCycle("monthly")} aria-pressed={!annual}>Monthly</button><button className={annual ? "active" : ""} onClick={() => setBillingCycle("yearly")} aria-pressed={annual}>Yearly</button><span>Save up to 20%</span></div><p className="billing-note">{annual ? "Annual preview — shown as a monthly equivalent, billed yearly." : "Monthly preview — payment setup arrives with the backend phase."}</p><div className="pricing-trust"><span><Check size={15} />No credit card required</span><span><Check size={15} />Change plans anytime</span></div></div>
            <div className="pricing-product"><ProductLaptop compact variant="overview" /><span className="scribble-note">Turn ideas into measurable work</span></div>
          </div>
        </section>

        <section className="section page-shell">
          <div className="section-heading centered"><span className="eyebrow">Pricing plans</span><h2>Plans for every stage of your content journey</h2><p>Start small and scale as your team and workflow grow.</p></div>
          <div className="plan-grid">{plans.map((plan) => <article className={plan.popular ? "popular" : ""} key={plan.name}>{plan.popular && <span className="popular-tag">Most popular</span>}<span className="plan-icon">{plan.name === "Starter" ? <Sparkles /> : plan.name === "Pro" ? <BarChart3 /> : plan.name === "Scale" ? <Layers3 /> : <ShieldCheck />}</span><h3>{plan.name}</h3><p>{plan.description}</p><strong className="plan-price">{plan.price !== "Custom" && (annual ? plan.annualPrice : plan.price)}<span>{plan.price === "Custom" ? "Custom pricing" : annual ? "/month, billed yearly" : "/month"}</span></strong><ul>{plan.features.map((feature) => <li key={feature}><Check size={16} />{feature}</li>)}</ul><Link className={plan.popular ? "button" : "secondary-button"} href="/signup">{plan.cta}</Link></article>)}</div>
        </section>

        <section className="section page-shell compare-section"><div className="section-heading centered"><span className="section-kicker">Compare plans</span><h2>Find the right plan for your team</h2><p>A clear breakdown of the features available at each stage.</p></div><div className="comparison-wrap"><table><thead><tr><th>Feature</th>{plans.map((plan) => <th key={plan.name}>{plan.name}</th>)}</tr></thead><tbody>{comparison.map((row) => <tr key={row[0]}>{row.map((cell, i) => i === 0 ? <th key={cell}>{cell}</th> : <td className={cell === "✓" ? "yes" : ""} key={`${cell}-${i}`}>{cell}</td>)}</tr>)}</tbody></table></div></section>

        <section className="section included-section"><div className="page-shell"><div className="section-heading centered"><span className="section-kicker">Built for modern teams</span><h2>Included in every plan</h2></div><div className="included-grid">{[
          { icon: Sparkles, title: "AI-assisted creation", copy: "On-brand briefs and content support." },
          { icon: Workflow, title: "SEO foundations", copy: "Structured review and recommendations." },
          { icon: BarChart3, title: "Clear reporting", copy: "A connected view of performance." },
          { icon: Users, title: "Team collaboration", copy: "Comments, approvals, and shared work." },
          { icon: Bell, title: "Smart notifications", copy: "Updates when something needs attention." },
          { icon: ShieldCheck, title: "Security & reliability", copy: "Practical controls for responsible access." }
        ].map(({ icon: Icon, title, copy }) => <article key={title}><span className="feature-icon"><Icon size={21} /></span><div><h3>{title}</h3><p>{copy}</p></div></article>)}</div></div></section>

        <section className="section page-shell faq-section"><div className="section-heading"><span className="section-kicker">Questions?</span><h2>Frequently asked questions</h2></div><Faq items={[
          { question: "Can I change plans later?", answer: "Yes. The billing architecture is designed to support upgrades and downgrades through a Stripe customer portal once billing is connected." },
          { question: "Is there a discount for annual billing?", answer: "The design includes annual billing, but final pricing and discounts should be confirmed before Stripe products are created." },
          { question: "What counts as a project?", answer: "A project is a distinct site or content workspace with its own scans, findings, content queue, and reporting context." },
          { question: "Do you offer onboarding and support?", answer: "Support levels can be mapped to plan entitlements during the backend phase." }
        ]} /></section>
        <section className="page-shell cta-band cta-band--light"><div><h2>Start creating content that <span>gets found</span></h2><p>Try the FIG workspace and choose a plan when you are ready.</p></div><div><Link className="button" href="/signup">Start free</Link><Link className="secondary-button" href="/app">View demo <ArrowRight size={16} /></Link></div></section>
      </main>
      <Footer />
    </div>
  );
}
