"use client";

import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Bell,
  CalendarDays,
  Check,
  CircleDollarSign,
  Layers3,
  Leaf,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { ProductLaptop } from "@/components/product-laptop";
import { PublicNav } from "@/components/public-nav";

type Plan = {
  name: string;
  eyebrow: string;
  price: string;
  annualPrice?: string;
  description: string;
  cta: string;
  icon: LucideIcon;
  popular?: boolean;
  features: string[];
};

const plans: Plan[] = [
  {
    name: "Starter",
    eyebrow: "Start focused",
    price: "$29",
    annualPrice: "$23",
    description: "For individuals and small teams getting started.",
    cta: "Get started",
    icon: Leaf,
    features: ["5 projects", "1 CMS connection", "AI-assisted creation", "SEO review & recommendations", "Basic analytics", "Up to 3 team seats"],
  },
  {
    name: "Pro",
    eyebrow: "For growing teams",
    price: "$79",
    annualPrice: "$63",
    description: "For teams building a repeatable, review-ready content rhythm.",
    cta: "Start free",
    icon: BarChart3,
    popular: true,
    features: ["25 projects", "5 CMS connections", "Advanced AI generation", "SEO + GEO optimization", "Full analytics suite", "Up to 10 team seats"],
  },
  {
    name: "Scale",
    eyebrow: "For content operations",
    price: "$199",
    annualPrice: "$159",
    description: "For larger teams with complex publishing and automation needs.",
    cta: "Start free",
    icon: Layers3,
    features: ["100 projects", "10 CMS connections", "Advanced AI generation", "SEO + GEO optimization", "Automation rules & triggers", "Up to 25 team seats"],
  },
  {
    name: "Enterprise",
    eyebrow: "Tailored to your team",
    price: "Custom",
    description: "For organizations with custom governance and rollout needs.",
    cta: "Contact sales",
    icon: ShieldCheck,
    features: ["Unlimited projects", "Unlimited CMS connections", "Custom workflows", "Unlimited team seats", "SSO / SAML", "Dedicated success partner"],
  },
];

const comparison = [
  ["Projects", "5", "25", "100", "Unlimited"],
  ["CMS connections", "1", "5", "10", "Unlimited"],
  ["AI-assisted creation", "✓", "✓", "✓", "✓"],
  ["SEO review & recommendations", "✓", "✓", "✓", "✓"],
  ["GEO optimization (AI search)", "—", "✓", "✓", "✓"],
  ["Analytics & insights", "Basic", "Advanced", "Advanced", "Advanced"],
  ["Approval workflows", "—", "✓", "✓", "✓"],
  ["Automation rules & triggers", "—", "—", "✓", "✓"],
  ["Team seats", "Up to 3", "Up to 10", "Up to 25", "Unlimited"],
  ["API access", "—", "—", "✓", "✓"],
  ["SSO / SAML", "—", "—", "—", "✓"],
  ["Priority support", "—", "✓", "✓", "✓"],
];

const included = [
  { icon: Sparkles, title: "AI-powered content creation", copy: "Turn ideas into on-brand, SEO-optimized content." },
  { icon: Workflow, title: "SEO & GEO optimization", copy: "Improve traditional and AI-powered discovery." },
  { icon: BarChart3, title: "Analytics & reporting", copy: "Track performance across search, AI, and your content library." },
  { icon: Users, title: "Team collaboration", copy: "Work together with comments, approvals, and shared workspaces." },
  { icon: Bell, title: "Smart notifications", copy: "Get notified about opportunities, updates, and performance changes." },
  { icon: Layers3, title: "Workspace history", copy: "Keep changes, review decisions, and context close at hand." },
  { icon: Workflow, title: "Integrations", copy: "Connect the tools and publishing workflows your team already uses." },
  { icon: ShieldCheck, title: "Security & reliability", copy: "A deliberate foundation for enterprise-grade access and uptime." },
];

const pricingFaqs = [
  { question: "Can I change plans later?", answer: "Yes. The billing architecture is designed to support upgrades and downgrades through a Stripe customer portal once billing is connected." },
  { question: "Is there a discount for annual billing?", answer: "The interface previews annual billing, but final discounts will be confirmed before Stripe products are created." },
  { question: "What counts as a project?", answer: "A project is a distinct site or content workspace with its own findings, content queue, and reporting context." },
  { question: "Do you offer a free trial?", answer: "The frontend includes a trial flow. Account creation and billing rules will be activated only during the backend phase." },
  { question: "Do you offer refunds?", answer: "Refund policy and billing support will be defined with the final Stripe implementation." },
  { question: "Do you provide onboarding and support?", answer: "Support levels can be mapped to plan entitlements during the backend phase." },
];

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const annual = billingCycle === "yearly";

  return (
    <div className="public-page pricing-page">
      <PublicNav active="pricing" />
      <main>
        <section className="pricing-hero section-glow">
          <div className="pricing-hero-decor" aria-hidden="true" />
          <div className="page-shell pricing-hero-grid">
            <div className="pricing-hero-copy">
              <span className="section-kicker">Pricing</span>
              <h1>Simple, transparent pricing for teams that create content that <span>gets found</span></h1>
              <p>Choose the plan that fits your team. Every plan includes the core tools you need to create, optimize, and publish content that performs in search and AI results.</p>
              <div className="billing-toggle" aria-label="Billing cycle">
                <button className={!annual ? "active" : ""} onClick={() => setBillingCycle("monthly")} aria-pressed={!annual}>Monthly</button>
                <button className={annual ? "active" : ""} onClick={() => setBillingCycle("yearly")} aria-pressed={annual}>Yearly</button>
                <span>Save up to 20%</span>
              </div>
              <p className="billing-note">{annual ? "Annual interface preview — monthly equivalent shown, billed yearly." : "Monthly interface preview — payment setup arrives with the backend phase."}</p>
              <div className="pricing-trust-list" aria-label="Plan guarantees">
                <span><CircleDollarSign size={16} />No credit card required</span>
                <span><Workflow size={16} />Upgrade or downgrade anytime</span>
                <span><CalendarDays size={16} />Cancel anytime</span>
              </div>
            </div>
            <div className="pricing-hero-visual">
              <div className="pricing-product"><ProductLaptop compact variant="overview" /></div>
              <span className="scribble-note pricing-annotation">Turn ideas into measurable results</span>
            </div>
          </div>
        </section>

        <section className="section page-shell pricing-plans-section">
          <div className="section-heading centered pricing-section-heading">
            <span className="eyebrow">Pricing plans</span>
            <h2>Plans for every stage of your content journey</h2>
            <p>Start small and scale as you grow. Upgrade or downgrade at any time.</p>
          </div>
          <div className="plan-grid plan-grid--four">
            {plans.map((plan) => {
              const Icon = plan.icon;
              const visiblePrice = plan.price === "Custom" ? plan.price : annual ? plan.annualPrice ?? plan.price : plan.price;
              return (
                <article className={`plan-card ${plan.popular ? "plan-card--popular popular" : ""}`} key={plan.name}>
                  {plan.popular && <span className="popular-tag">Most popular</span>}
                  <div className="plan-card-heading">
                    <span className="plan-icon"><Icon size={22} /></span>
                    <span className="plan-eyebrow">{plan.eyebrow}</span>
                    <h3>{plan.name}</h3>
                    <p>{plan.description}</p>
                  </div>
                  <div className="plan-price-wrap">
                    <strong className="plan-price">{visiblePrice}</strong>
                    <span className="plan-price-detail">{plan.price === "Custom" ? "custom pricing" : annual ? "/ month · billed yearly" : "/ month"}</span>
                  </div>
                  <ul className="plan-feature-list">
                    {plan.features.map((feature) => <li key={feature}><Check size={16} aria-hidden="true" />{feature}</li>)}
                  </ul>
                  <Link className={plan.popular ? "button" : "secondary-button"} href={`/signup?plan=${encodeURIComponent(plan.name)}&billing=${annual ? "yearly" : "monthly"}`}>{plan.name === "Enterprise" ? "Explore Enterprise" : plan.cta}{plan.name !== "Enterprise" && <ArrowRight size={16} />}</Link>
                </article>
              );
            })}
          </div>
          <p className="pricing-disclaimer">Pricing and billing are frontend previews until the Stripe backend is connected and verified.</p>
        </section>

        <section className="section page-shell compare-section">
          <div className="section-heading centered">
            <span className="section-kicker">Compare plans</span>
            <h2>Find the right plan for your team</h2>
            <p>A detailed breakdown of features across every plan.</p>
          </div>
          <div className="comparison-wrap" role="region" aria-label="FIG plan comparison" tabIndex={0}>
            <table>
              <thead><tr><th scope="col">Feature</th>{plans.map((plan) => <th scope="col" key={plan.name}>{plan.name}</th>)}</tr></thead>
              <tbody>{comparison.map((row) => <tr key={row[0]}>{row.map((cell, index) => index === 0 ? <th scope="row" key={cell}>{cell}</th> : <td className={cell === "✓" ? "yes" : ""} key={`${cell}-${index}`}>{cell}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </section>

        <section className="section included-section">
          <div className="page-shell">
            <div className="section-heading centered">
              <span className="eyebrow">Built for modern teams</span>
              <h2>What’s included in every plan</h2>
              <p>No matter which plan you choose, you’ll get a powerful set of tools to create, optimize, and ship high-performing content.</p>
            </div>
            <div className="included-grid included-grid--eight">
              {included.map(({ icon: Icon, title, copy }) => <article className="included-card" key={title}><span className="feature-icon"><Icon size={21} /></span><div><h3>{title}</h3><p>{copy}</p></div></article>)}
            </div>
          </div>
        </section>

        <section className="section page-shell faq-section faq-section--pricing">
          <div className="section-heading">
            <span className="section-kicker">Questions?</span>
            <h2>Frequently asked questions</h2>
            <p>Everything you need to know about FIG pricing.</p>
          </div>
          <Faq columns items={pricingFaqs} />
        </section>
        <section className="page-shell cta-band cta-band--light pricing-cta">
          <div><span className="section-kicker">Ready to get started?</span><h2>Start creating content that <span>gets found</span></h2><p>Try FIG free or book a demo to find the right plan for your team.</p></div>
          <div className="cta-band-actions"><Link className="button" href="/signup">Start free</Link><Link className="secondary-button" href="/projects">View demo <ArrowRight size={16} /></Link></div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
