import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, CalendarDays, CircleDollarSign, FileCheck2, Layers3, ListChecks, Lock, MoveRight, Search, Undo2, Users, Workflow } from "lucide-react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { JsonLd, faqJsonLd } from "@/components/json-ld";
import { PriceCalculator } from "@/components/price-calculator";
import { PublicNav } from "@/components/public-nav";
import { REFUND_WINDOW_DAYS, TRIAL_DAYS } from "@/lib/legal";
import { TIERS, dollars, tierRange } from "@/lib/pricing";

export const metadata: Metadata = {
  title: "Pricing — FIG",
  description: "FIG costs from $20 down to $5 per site per month. Every check is included at every size, with a 7-day free trial and no card to start.",
  alternates: { canonical: "/pricing" },
};

/**
 * Prices come from lib/pricing.ts, which test_pricing_sync.py holds equal to the
 * backend (and so to the Stripe price). Nothing on this page is a plan that
 * doesn't exist: there are no seats, no SSO and no annual plan, so none is shown.
 */

const included = [
  { icon: Search, title: "All 19 checks, every size", copy: "Design, structure, search and answer-readiness checks across four layers. The tiers change the rate, never the product." },
  { icon: FileCheck2, title: "Where, why and how to fix it", copy: "Every finding names the page it is on, why it reads as generic, and a concrete fix." },
  { icon: Layers3, title: "History and re-scans", copy: "Run a scan again after you make changes and compare, on demand, for every site." },
  { icon: BarChart3, title: "Analytics and Search Console", copy: "Connect Google Analytics and Search Console, read-only, to see your own traffic and queries beside the findings." },
  { icon: Workflow, title: "WordPress fixes you approve", copy: "Title and heading fixes can be applied to a connected WordPress site, only after you approve each one, and every change can be reverted." },
  { icon: ListChecks, title: "A content queue", copy: "Gaps in your pages become briefs. Paste a draft and it is scored on nine rules and moved through review by you." },
  { icon: Users, title: "Shareable reports", copy: "Turn on a public report link for a site when you want to show someone. It is off until you choose." },
  { icon: Lock, title: "Your data, your call", copy: "Disconnect a service and its stored credential is deleted. Findings are signals, never accusations." },
];

const faqs = [
  { question: "How does per-site pricing work?", answer: `You pay a monthly rate for each active site, and the rate depends on how many sites you have in total. It is volume pricing: at 30 sites, every one of the 30 costs the 25–99 rate. Use the calculator above to see your own number.` },
  { question: "What counts as a site?", answer: "One website (a hostname) that you add as a project. Removing a project stops monitoring and billing for it; its history stays in your account until you ask us to delete it." },
  { question: "What happens when I add or remove a site?", answer: "Your subscription follows your site count. If you add one partway through a billing period you pay the difference for the rest of it, prorated; if you remove one, the unused part is credited to your next invoice." },
  { question: "Do you offer a free trial?", answer: `Yes: ${TRIAL_DAYS} days, and we don't ask for a card. Nothing is charged unless you start a subscription yourself. You can also run a free scan of any public site without an account.` },
  { question: "Do you offer refunds?", answer: `Your first payment is refundable in full for ${REFUND_WINDOW_DAYS} days if FIG isn't right for you. The details are on the refunds and cancellation page.` },
  { question: "How do I cancel?", answer: "In Settings → Billing, choose Manage billing and cancel your plan. You keep access until the end of the period you have paid for, and you are not charged again." },
  { question: "Is there an annual plan?", answer: "Not yet. Billing is monthly." },
];

export default function PricingPage() {
  return (
    <div className="public-page pricing-page">
      <JsonLd data={faqJsonLd(faqs)} />
      <PublicNav active="pricing" />
      <main>
        <section className="pricing-hero section-glow">
          <div className="pricing-hero-decor" aria-hidden="true" />
          <div className="page-shell pricing-hero-grid pricing-hero-grid--calc">
            <div className="pricing-hero-copy">
              <span className="section-kicker">Pricing</span>
              <h1>One rate per site, and it gets <span>lower as you grow</span></h1>
              <p>FIG costs from {dollars(TIERS[0][1])} down to {dollars(TIERS[TIERS.length - 1][1])} per site per month. Every check is included at every size; only the rate changes.</p>
              <div className="pricing-trust-list" aria-label="What to expect">
                <span><CircleDollarSign size={16} />{TRIAL_DAYS}-day free trial, no card</span>
                <span><CalendarDays size={16} />Cancel anytime</span>
                <span><Undo2 size={16} />{REFUND_WINDOW_DAYS}-day money-back on your first payment</span>
              </div>
              <div className="pricing-hero-actions">
                <Link className="button" href="/signup">Start free trial</Link>
                <Link className="secondary-button" href="/#scan">Scan a site free</Link>
              </div>
            </div>
            <div className="pricing-hero-visual"><PriceCalculator /></div>
          </div>
        </section>

        <section className="section page-shell pricing-plans-section">
          <div className="section-heading centered pricing-section-heading">
            <span className="eyebrow">Volume pricing</span>
            <h2>The more sites you run, the less each one costs</h2>
            <p>The rate for your total number of sites applies to every site, so growing never makes an existing site cost more.</p>
          </div>
          <div className="plan-grid plan-grid--tiers">
            {TIERS.map(([, cents], index) => (
              <article className="plan-card" key={tierRange(index)}>
                <div className="plan-card-heading">
                  <span className="plan-eyebrow">{tierRange(index)}</span>
                </div>
                <div className="plan-price-wrap">
                  <strong className="plan-price">{dollars(cents)}</strong>
                  <span className="plan-price-detail">per site / month</span>
                </div>
                <p className="plan-tier-example">{index === 0 ? "Where most people start." : `For example, ${TIERS[index][0]} sites is ${dollars(TIERS[index][0] * cents)} a month.`}</p>
              </article>
            ))}
          </div>
          <p className="pricing-disclaimer">Prices are in US dollars, billed monthly through Stripe, and exclude any taxes that apply to you.</p>
        </section>

        <section className="section included-section">
          <div className="page-shell">
            <div className="section-heading centered">
              <span className="eyebrow">Everything is included</span>
              <h2>What you get at any size</h2>
              <p>There are no feature tiers, seat limits or add-ons. Here is what FIG does today.</p>
            </div>
            <div className="included-grid included-grid--eight">
              {included.map(({ icon: Icon, title, copy }) => <article className="included-card" key={title}><span className="feature-icon"><Icon size={21} /></span><div><h3>{title}</h3><p>{copy}</p></div></article>)}
            </div>
            <p className="pricing-honest-note">Not part of FIG today: FIG does not write your content for you, and it does not publish new posts to your site. Fixes to an existing WordPress site are the only thing it can change, and only when you approve them.</p>
          </div>
        </section>

        <section className="section page-shell faq-section faq-section--pricing">
          <div className="section-heading">
            <span className="section-kicker">Questions?</span>
            <h2>Frequently asked questions</h2>
            <p>Everything you need to know about FIG pricing. More detail in the <Link href="/refunds">refund policy</Link> and <Link href="/terms">terms</Link>.</p>
          </div>
          <Faq columns items={faqs} />
        </section>
        <section className="page-shell cta-band cta-band--light pricing-cta">
          <div><span className="section-kicker">Ready to start?</span><h2>See how your site <span>reads</span></h2><p>Run a free scan with no account, or start the {TRIAL_DAYS}-day trial to keep a history.</p></div>
          <div className="cta-band-actions"><Link className="button" href="/signup">Start free trial</Link><Link className="secondary-button" href="/projects">View the demo <MoveRight size={16} /></Link></div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
