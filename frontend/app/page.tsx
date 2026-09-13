import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Check,
  Eye,
  FileCheck2,
  FileText,
  Globe2,
  Link2,
  MessageSquareText,
  PenLine,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Upload,
  Users,
  Workflow
} from "lucide-react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { ProductLaptop } from "@/components/product-laptop";
import { PublicNav } from "@/components/public-nav";

const features = [
  { icon: PenLine, title: "AI-assisted planning", copy: "Turn ideas into structured, on-brand content briefs and outlines." },
  { icon: Search, title: "SEO review queue", copy: "Review and optimize content with clear, actionable suggestions." },
  { icon: Sparkles, title: "GEO optimization", copy: "Shape content for AI discovery, answer inclusion, and citations." },
  { icon: Upload, title: "CMS publishing", copy: "Move approved work into your publishing workflow with confidence." },
  { icon: BarChart3, title: "Analytics & tracking", copy: "See what is discoverable, what changed, and what to improve next." },
  { icon: Users, title: "Approvals & collaboration", copy: "Keep feedback, permissions, and sign-off in one shared system." },
  { icon: Bell, title: "Useful notifications", copy: "Get alerts for work that needs attention—not noise for its own sake." },
  { icon: Settings, title: "Settings & API", copy: "Connect your stack and adapt FIG to the way your team works." }
];

const flow = [
  { icon: Link2, title: "Connect", copy: "Add your site and data sources." },
  { icon: FileText, title: "Generate", copy: "Create a focused content brief." },
  { icon: Users, title: "Review", copy: "Collaborate and refine." },
  { icon: Eye, title: "Preview", copy: "Check the final experience." },
  { icon: Upload, title: "Publish", copy: "Send approved work live." },
  { icon: BarChart3, title: "Track", copy: "Measure and improve." }
];

const faqs = [
  { question: "What CMS platforms does FIG support?", answer: "The first release is designed around flexible API connections, with Shopify and common CMS workflows planned first. Exact production connections will be shown only when they are tested and available." },
  { question: "Do I need technical knowledge to use FIG?", answer: "No. The interface is designed for marketers, content teams, and operators. Advanced API options can stay out of the way until your team needs them." },
  { question: "Can FIG optimize for AI search?", answer: "Yes. GEO workflows are part of the product design, including prompt monitoring, answer previews, citation opportunities, and source trust signals." },
  { question: "Can I try FIG before paying?", answer: "The frontend supports a free-trial flow. Billing and entitlement rules will be finalized during the backend phase before launch." }
];

export default function HomePage() {
  return (
    <div className="public-page">
      <PublicNav />
      <main>
        <section className="hero section-glow">
          <div className="hero-orb hero-orb--one" /><div className="hero-orb hero-orb--two" />
          <div className="page-shell hero-grid">
            <div className="hero-copy">
              <span className="eyebrow"><Sparkles size={13} />SEO + GEO content operations</span>
              <h1>Launch content that gets <span>your brand found</span></h1>
              <p>Plan, create, review, optimize, and publish high-performing content from one beautifully organized workspace.</p>
              <div className="hero-actions"><Link className="button" href="/app">Try the demo <ArrowRight size={18} /></Link><Link className="secondary-button" href="/signup">Start free</Link></div>
              <div className="hero-proof"><div className="avatar-stack"><span>MC</span><span>DR</span><span>PL</span><span>+9</span></div><p>Designed for modern marketing, agency, and commerce teams.</p></div>
            </div>
            <div className="hero-product"><ProductLaptop /><span className="scribble-note">From idea to impact</span></div>
          </div>
        </section>

        <section className="integrations page-shell" aria-label="Planned integrations">
          <span className="section-kicker">Connect with the platforms your team already uses</span>
          <div className="logo-row"><strong><i className="shopify-glyph">S</i>shopify</strong><strong>WIX</strong><strong><i className="webflow-glyph">W</i>Webflow</strong><strong>ⓦ WordPress</strong><strong>BIGCOMMERCE</strong><strong><i className="analytics-glyph">▥</i>Google Analytics</strong></div>
        </section>

        <section className="capability-band page-shell">
          {[{ icon: Workflow, title: "One clear workflow", copy: "From idea to published work" }, { icon: Sparkles, title: "Search + AI ready", copy: "Built for SEO and GEO" }, { icon: FileCheck2, title: "Human approval", copy: "You stay in control" }, { icon: ShieldCheck, title: "Private by design", copy: "Thoughtful data boundaries" }].map(({ icon: Icon, title, copy }) => <div key={title}><Icon size={22} /><strong>{title}</strong><span>{copy}</span></div>)}
        </section>

        <section className="section page-shell" id="product">
          <div className="section-heading centered"><span className="section-kicker">Everything you need</span><h2>A complete content operations platform</h2><p>Move from first idea to measurable impact without losing context between tools.</p></div>
          <div className="feature-grid">{features.map(({ icon: Icon, title, copy }) => <article className="feature-card" key={title}><span className="feature-icon"><Icon size={22} /></span><h3>{title}</h3><p>{copy}</p></article>)}</div>
        </section>

        <section className="section flow-section">
          <div className="page-shell">
            <div className="section-heading centered"><span className="section-kicker">How FIG works</span><h2>From idea to impact in six simple steps</h2><p>A straightforward workflow that keeps strategy, creation, and measurement connected.</p></div>
            <div className="flow-grid">{flow.map(({ icon: Icon, title, copy }, index) => <article key={title}><span className="flow-icon"><Icon size={21} /></span><small>{index + 1}</small><h3>{title}</h3><p>{copy}</p>{index < flow.length - 1 && <ArrowRight className="flow-arrow" size={17} />}</article>)}</div>
          </div>
        </section>

        <section className="section product-showcase">
          <div className="page-shell showcase-grid">
            <div className="showcase-copy"><span className="section-kicker">The platform</span><h2>A modern workspace for high-performing content</h2><p>Every important task is visible, actionable, and connected to the bigger picture.</p><Link href="/app">See the product demo <ArrowRight size={16} /></Link></div>
            <div className="showcase-window"><div className="showcase-window-bar"><i /><i /><i /></div><ProductLaptop compact /></div>
          </div>
        </section>

        <section className="section editorial-section">
          <div className="page-shell editorial-grid">
            <div className="editorial-photo-frame">
              <Image src="/images/fig-editorial-studio-web.png" width={1600} height={900} alt="Content strategist reviewing work at a studio table" priority={false} />
              <div className="editorial-photo-shade" />
              <div className="editorial-photo-label"><span className="editorial-dot" />A calmer content operation</div>
              <div className="editorial-quote">“The work matters.<br />The system should help.”</div>
            </div>
            <div className="editorial-copy">
              <span className="section-kicker">Built around real work</span>
              <h2>Make room for better decisions—not more busywork.</h2>
              <p>FIG gives your team a shared home for strategy, content context, review, and what to do next. The result is a clearer process before any dashboard needs to show a number.</p>
              <div className="editorial-points">
                <article><span><PenLine size={17} /></span><div><strong>Start with the brief</strong><p>Keep the intent, audience, and search opportunity close to the work.</p></div></article>
                <article><span><Users size={17} /></span><div><strong>Review in one place</strong><p>Make ownership and approval visible before anything is published.</p></div></article>
                <article><span><BarChart3 size={17} /></span><div><strong>Let the evidence arrive</strong><p>When data connects, FIG fills in the story without pretending it exists first.</p></div></article>
              </div>
            </div>
          </div>
        </section>

        <section className="section ai-search-section">
          <div className="page-shell ai-search-grid">
            <div><span className="eyebrow"><Sparkles size={13} />AI search ready</span><h2>Be found beyond Google</h2><p>Build content that is structured for traditional search and understandable to generative answer engines.</p><Link className="button" href="/app/geo">Explore GEO <ArrowRight size={17} /></Link></div>
            <div className="visibility-card"><div className="visibility-heading"><span>AI visibility</span><strong>Awaiting data</strong></div><div className="visibility-empty"><Sparkles size={24} /><strong>No visibility data yet</strong><span>Connect a site and choose prompts to begin monitoring.</span></div><div className="visibility-sources"><span><MessageSquareText size={16} />Answer engines</span><span><Search size={16} />Search platforms</span><span><Globe2 size={16} />Web mentions</span></div></div>
          </div>
        </section>

        <section className="section page-shell audience-section">
          <div className="audience-copy"><span className="section-kicker">Built for your team</span><h2>Made for marketers, agencies, and commerce teams</h2><p>FIG keeps complex content operations approachable, even as your work scales.</p></div>
          <div className="audience-grid">
            <article><Image src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=85" width={900} height={700} alt="Marketing professional" /><div><h3>Marketers</h3><p>Plan and improve content with a clear view of impact.</p></div></article>
            <article><Image src="https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=900&q=85" width={900} height={700} alt="Agency professional" /><div><h3>Agencies</h3><p>Manage clients, reviews, and delivery from one workspace.</p></div></article>
            <article><Image src="https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=900&q=85" width={900} height={700} alt="Ecommerce professional" /><div><h3>Commerce teams</h3><p>Connect discovery, content, and publishing workflows.</p></div></article>
          </div>
        </section>

        <section className="section page-shell pricing-preview">
          <div className="section-heading"><span className="section-kicker">Simple, transparent pricing</span><h2>Plans for every stage of growth</h2><p>Start focused, then expand the workspace as your content operation grows.</p></div>
          <div className="pricing-mini-grid">
            <article><h3>Starter</h3><p>For individuals and small teams.</p><strong>$29<span>/month</span></strong><ul><li><Check size={15} />Core content workflows</li><li><Check size={15} />One connected site</li><li><Check size={15} />Basic analytics</li></ul><Link className="secondary-button" href="/signup">Start free</Link></article>
            <article className="featured"><span className="popular-tag">Most popular</span><h3>Pro</h3><p>For growing content teams.</p><strong>$79<span>/month</span></strong><ul><li><Check size={15} />Everything in Starter</li><li><Check size={15} />SEO + GEO workflows</li><li><Check size={15} />Team approvals</li></ul><Link className="button" href="/signup">Start free</Link></article>
            <article><h3>Scale</h3><p>For larger teams and agencies.</p><strong>$199<span>/month</span></strong><ul><li><Check size={15} />Everything in Pro</li><li><Check size={15} />Advanced automation</li><li><Check size={15} />Priority support</li></ul><Link className="secondary-button" href="/pricing">See all plans</Link></article>
          </div>
        </section>

        <section className="section page-shell faq-section"><div className="section-heading"><span className="section-kicker">Frequently asked questions</span><h2>Everything you need to know</h2></div><Faq items={faqs} /></section>
        <section className="page-shell cta-band"><div><h2>Ready to create content that gets found?</h2><p>Start with the FIG workspace and shape it around your team.</p></div><div><Link className="secondary-button secondary-button--light" href="/app">Try the demo</Link><Link className="button button--light" href="/signup">Start free</Link></div></section>
      </main>
      <Footer />
    </div>
  );
}
