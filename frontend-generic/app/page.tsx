import Image from "next/image";
import Link from "next/link";
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
  Sparkles,
  TrendingUp,
  Upload,
  Users
} from "lucide-react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";
import { PublicNav } from "@/components/public-nav";
import { VisibilityChart } from "@/components/visibility-chart";

const featureCards = [
  { icon: PenLine, tone: "violet", title: "AI-assisted planning", copy: "Turn ideas and search opportunities into structured, on-brand briefs." },
  { icon: Search, tone: "blue", title: "SEO review queue", copy: "Review drafts against keywords, intent, links, and on-page essentials." },
  { icon: Sparkles, tone: "indigo", title: "GEO optimization", copy: "Prepare content for AI answers, citations, and generative discovery." },
  { icon: Upload, tone: "green", title: "CMS publishing", copy: "Move approved work into connected publishing workflows." },
  { icon: BarChart3, tone: "blue", title: "Analytics & tracking", copy: "Follow visibility, content health, traffic, and publishing progress." },
  { icon: Users, tone: "violet", title: "Approvals & collaboration", copy: "Keep comments, decisions, permissions, and sign-off together." },
  { icon: Bell, tone: "amber", title: "Useful notifications", copy: "Surface reviews, failed jobs, and scheduled work that need attention." },
  { icon: Settings, tone: "indigo", title: "Settings & API", copy: "Shape integrations and workspace defaults around your team." }
];

const workflowSteps = [
  { icon: Link2, title: "Connect", copy: "Link your CMS and analytics tools." },
  { icon: FileText, title: "Generate", copy: "Create SEO + GEO content with AI." },
  { icon: Users, title: "Review", copy: "Collaborate and refine with your team." },
  { icon: Eye, title: "Preview", copy: "See how the final content will look." },
  { icon: Upload, title: "Publish", copy: "Send approved work to your CMS." },
  { icon: BarChart3, title: "Track", copy: "Measure performance and iterate." }
];

const outcomes = [
  { icon: TrendingUp, value: "+187%", label: "avg. organic traffic growth", tone: "purple" },
  { icon: Sparkles, value: "3.4x", label: "more AI visibility", tone: "blue" },
  { icon: FileCheck2, value: "10,000+", label: "content pieces optimized", tone: "green" },
  { icon: Users, value: "92%", label: "of teams see positive ROI", tone: "amber" }
];

const audiences = [
  {
    title: "Marketers",
    copy: "Drive organic growth with less manual work.",
    image: "https://images.unsplash.com/photo-1758876021859-bd2371d8f0a2?auto=format&fit=crop&w=900&q=88",
    alt: "Woman working on a laptop and taking notes in a shared office",
    position: "center 45%"
  },
  {
    title: "Agencies",
    copy: "Manage multiple clients from the same workflow.",
    image: "https://images.unsplash.com/photo-1758873268023-15a6e6d739ed?auto=format&fit=crop&w=900&q=88",
    alt: "Professional wearing glasses at an office desk with a laptop",
    position: "center 45%"
  },
  {
    title: "Commerce teams",
    copy: "Increase product visibility and discoverability.",
    image: "https://images.unsplash.com/photo-1758873268745-dd2cf0d677b5?auto=format&fit=crop&w=900&q=88",
    alt: "Colleagues collaborating around a computer in a shared workspace",
    position: "center 45%"
  }
];

const testimonialPreviews = [
  {
    quote: "FIG has streamlined how our content moves from an idea to something the team can review and ship.",
    name: "Sarah K.",
    role: "Marketing lead",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=180&q=88"
  },
  {
    quote: "The GEO workspace gives us one clear view of prompts, citations, and content opportunities.",
    name: "Daniel M.",
    role: "Head of growth",
    image: "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=180&q=88"
  },
  {
    quote: "It is easy to use, and the review flow makes it obvious what needs attention next.",
    name: "Priya S.",
    role: "Content manager",
    image: "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=180&q=88"
  }
];

const frequentlyAsked = [
  {
    question: "What CMS platforms does FIG support?",
    answer: "FIG is being designed around flexible integrations, beginning with the CMS and analytics workflows shown in this product preview. Production availability will be confirmed as each connection is tested."
  },
  {
    question: "Do I need technical knowledge to use FIG?",
    answer: "No. The core workspace is designed for marketers and content teams, while API and automation controls can stay out of the way until they are needed."
  },
  {
    question: "Can FIG optimize content for AI search?",
    answer: "The product design includes GEO workflows for prompt coverage, answer previews, citation opportunities, and source visibility. The values in this frontend are illustrative until live data is connected."
  },
  {
    question: "Can I try FIG before paying?",
    answer: "The current build includes a frontend demo and signup experience. Billing, trial entitlements, and production integrations will be connected during the backend phase."
  }
];

function ProductPreviewCards() {
  return (
    <div className="platform-tour-cards" aria-label="FIG workspace previews">
      <article className="platform-tour-card platform-tour-card--projects">
        <div className="tour-card-ui tour-card-ui--projects" aria-hidden="true">
          <div className="tour-project-content">
            <div className="tour-ui-heading"><b>All projects</b><span>1 project</span></div>
            <div className="tour-project-tile"><span className="tour-project-avatar">DW</span><div><b>Demo workspace</b><small>AI learning & resources</small></div><Check size={9} /></div>
            <div className="tour-project-metrics"><span><strong>28</strong>Published</span><span><strong>4.2K</strong>Traffic</span><span><strong>84</strong>Impact score</span></div>
            <div className="tour-project-activity"><FileCheck2 size={9} /><span>AI agents guide · Ready for review</span></div>
          </div>
        </div>
        <h3><Link href="/projects">Projects dashboard <ArrowRight size={14} /></Link></h3>
        <p>Manage your content pipeline across teams and sites.</p>
      </article>
      <article className="platform-tour-card platform-tour-card--performance">
        <div className="tour-card-ui" aria-hidden="true">
          <div className="tour-ui-heading"><b>Content performance</b><span>Last 30 days</span></div>
          <div className="tour-mini-kpis"><div><small>Organic traffic</small><b>4.2K</b><em>↑ 18.7%</em></div><div><small>Impact score</small><b>84</b><em>↑ 6 points</em></div><div><small>Published</small><b>28</b><em>↑ 27%</em></div></div>
          <svg className="tour-mini-chart" viewBox="0 0 220 82" preserveAspectRatio="none">
            <path d="M0 69 C25 64 37 68 56 57 S89 55 108 43 S142 49 164 31 S198 30 220 16" fill="none" stroke="#6047ff" strokeWidth="3" />
            <path d="M0 76 C26 72 38 74 56 68 S89 63 108 57 S143 59 164 48 S199 44 220 36" fill="none" stroke="#2f80ed" strokeWidth="2.5" />
          </svg>
        </div>
        <h3><Link href="/app">Content performance <ArrowRight size={14} /></Link></h3>
        <p>Track rankings, traffic, and engagement over time.</p>
      </article>
      <article className="platform-tour-card platform-tour-card--geo">
        <div className="tour-card-ui tour-card-ui--geo" aria-hidden="true">
          <div className="tour-ui-heading"><b>AI visibility growth</b><span>Demo workspace</span></div>
          <div className="tour-geo-content"><div className="tour-score-ring"><strong>78</strong><span>GEO score</span></div><div className="tour-geo-sources"><span>ChatGPT <b>62%</b></span><span>Google AI <b>78%</b></span><span>Perplexity <b>48%</b></span></div></div>
        </div>
        <h3><Link href="/app/geo">GEO visibility <ArrowRight size={14} /></Link></h3>
        <p>See how content appears across AI search and answers.</p>
      </article>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="public-page public-home">
      <PublicNav />
      <main>
        <section className="home-hero section-glow">
          <div className="home-hero-shape home-hero-shape--left" />
          <div className="home-hero-shape home-hero-shape--right" />
          <div className="page-shell home-hero-grid">
            <div className="home-hero-copy">
              <span className="eyebrow"><Sparkles size={13} />SEO + GEO content operations</span>
              <h1>Launch SEO and GEO content that gets <span>your brand found</span></h1>
              <p>Plan, create, review, and publish—all in one place. Bring your team, content, and insights together to get found in search and AI answers.</p>
              <div className="home-hero-actions">
                <Link className="button" href="/projects">Try the demo <ArrowRight size={17} /></Link>
                <Link className="secondary-button" href="/signup">Start free</Link>
              </div>
              <div className="home-hero-proof">
                <div className="avatar-stack avatar-stack--photos" aria-hidden="true">
                  {audiences.map((audience) => <Image key={audience.title} src={audience.image} width={48} height={48} alt="" />)}
                </div>
                <p>Built for marketers, agencies, and commerce teams. Product figures shown are illustrative.</p>
              </div>
            </div>
            <div className="home-hero-product">
              <ProductLaptop variant="queue" />
            </div>
          </div>
        </section>

        <section className="home-integrations" id="integrations" aria-label="Integration platforms">
          <div className="page-shell">
            <span className="section-kicker">Connect with the platforms your team already uses</span>
            <PlatformLogos />
          </div>
        </section>

        <section className="page-shell home-outcomes" aria-label="Illustrative product outcomes">
          <span className="home-outcomes-label">Illustrative product outcomes</span>
          {outcomes.map(({ icon: Icon, value, label, tone }) => (
            <article className={`home-outcome home-outcome--${tone}`} key={label}>
              <Icon size={20} />
              <strong>{value}</strong>
              <span>{label}</span>
            </article>
          ))}
        </section>

        <section className="section page-shell home-features" id="features">
          <div className="section-heading centered">
            <span className="section-kicker">Everything you need</span>
            <h2>A complete content operations platform</h2>
            <p>From idea to impact, FIG keeps planning, optimization, review, publishing, and measurement in one organized workflow.</p>
          </div>
          <div className="home-feature-grid">
            {featureCards.map(({ icon: Icon, tone, title, copy }) => (
              <article className={`home-feature-card home-feature-card--${tone}`} key={title}>
                <span className="home-feature-icon"><Icon size={21} /></span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section home-workflow" id="workflow">
          <div className="page-shell">
            <div className="section-heading centered">
              <span className="section-kicker">How FIG works</span>
              <h2>From idea to impact in six simple steps</h2>
              <p>A connected path from your existing tools to content that can be reviewed, shipped, and improved.</p>
            </div>
            <ol className="home-workflow-grid">
              {workflowSteps.map(({ icon: Icon, title, copy }, index) => (
                <li key={title}>
                  <span className="home-workflow-icon"><Icon size={20} /></span>
                  <div><small>{index + 1}</small><h3>{title}</h3></div>
                  <p>{copy}</p>
                  {index < workflowSteps.length - 1 && <ArrowRight className="home-workflow-arrow" size={16} aria-hidden="true" />}
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section home-platform-tour">
          <div className="page-shell home-platform-tour-grid">
            <div className="home-platform-tour-copy">
              <span className="section-kicker">The platform</span>
              <h2>A modern workspace for high-performing content</h2>
              <p>Your content, reviews, and performance in one workspace. See what’s ready, what needs attention, and where to focus next.</p>
              <Link href="/projects">See the full demo <ArrowRight size={15} /></Link>
            </div>
            <ProductPreviewCards />
          </div>
        </section>

        <section className="section home-geo-feature">
          <div className="page-shell home-geo-grid">
            <div className="home-geo-copy">
              <span className="eyebrow"><MessageSquareText size={13} />AI search ready</span>
              <h2>Be found beyond Google</h2>
              <p>Shape content for generative answers while keeping traditional search fundamentals visible in the same workflow.</p>
              <Link className="button" href="/app/geo">Explore GEO <ArrowRight size={16} /></Link>
            </div>
            <div className="home-visibility-card">
              <div className="home-visibility-chart-panel">
                <div className="home-visibility-heading">
                  <div><strong>AI visibility growth</strong><small>Illustrative demo data · Demo workspace</small></div>
                  <span><b>3.4x</b> more AI visibility</span>
                </div>
                <VisibilityChart />
              </div>
              <div className="home-visibility-sources">
                <span><MessageSquareText size={15} /><b>ChatGPT</b><strong>+210%</strong></span>
                <span><Globe2 size={15} /><b>Perplexity</b><strong>+180%</strong></span>
                <span><Search size={15} /><b>Google AI</b><strong>+150%</strong></span>
              </div>
            </div>
          </div>
        </section>

        <section className="section page-shell home-audience" id="teams">
          <div className="home-audience-copy">
            <span className="section-kicker">Built for your team</span>
            <h2>Made for marketers, agencies, and commerce teams</h2>
            <p>Whether you are building a brand, coordinating client work, or scaling a content library, FIG keeps the next action clear.</p>
          </div>
          <div className="home-audience-grid">
            {audiences.map((audience) => (
              <article key={audience.title}>
                <Image src={audience.image} width={900} height={700} alt={audience.alt} style={{ objectPosition: audience.position }} />
                <div><h3>{audience.title}</h3><p>{audience.copy}</p></div>
              </article>
            ))}
          </div>
        </section>

        <section className="section page-shell home-testimonials">
          <div className="home-testimonial-heading">
            <span className="section-kicker">Customer story preview</span>
            <h2>Less busywork. More content that matters.</h2>
            <p>Representative copy for this frontend prototype—not published customer endorsements.</p>
          </div>
          <div className="home-testimonial-grid">
            {testimonialPreviews.map((testimonial) => (
              <article key={testimonial.name}>
                <Image src={testimonial.image} width={96} height={96} alt="" />
                <div>
                  <p>“{testimonial.quote}”</p>
                  <strong>{testimonial.name}</strong>
                  <small>{testimonial.role}</small>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section page-shell home-pricing-preview">
          <div className="home-pricing-heading">
            <div><span className="section-kicker">Simple, transparent pricing</span><h2>Plans for every stage of growth</h2><p>Frontend pricing preview. Billing rules will be finalized during the backend phase.</p></div>
            <Link href="/pricing">View full pricing <ArrowRight size={15} /></Link>
          </div>
          <div className="home-plan-grid">
            <article>
              <h3>Starter</h3><p>For individuals and small teams.</p><strong>$29<span>/month</span></strong>
              <ul><li><Check size={14} />AI content generation</li><li><Check size={14} />One CMS connection</li><li><Check size={14} />Basic analytics</li></ul>
              <Link className="secondary-button" href="/signup">Start free</Link>
            </article>
            <article className="home-plan-card--featured">
              <span className="popular-tag">Most popular</span><h3>Pro</h3><p>For growing businesses and agencies.</p><strong>$79<span>/month</span></strong>
              <ul><li><Check size={14} />Everything in Starter</li><li><Check size={14} />SEO + GEO workflows</li><li><Check size={14} />Approvals and analytics</li></ul>
              <Link className="button" href="/signup">Start free</Link>
            </article>
            <article>
              <h3>Scale</h3><p>For larger teams with more needs.</p><strong>$199<span>/month</span></strong>
              <ul><li><Check size={14} />Everything in Pro</li><li><Check size={14} />Advanced automation</li><li><Check size={14} />Priority support</li></ul>
              <Link className="secondary-button" href="/pricing">See all plans</Link>
            </article>
          </div>
        </section>

        <section className="section page-shell home-faq" id="faq">
          <div className="home-faq-heading"><span className="section-kicker">Frequently asked questions</span><h2>Everything you need to know</h2><p>A few straight answers about this FIG frontend preview, its demo workspace, and what comes next.</p></div>
          <Faq items={frequentlyAsked} />
        </section>

        <section className="page-shell home-cta">
          <div className="home-cta-copy"><span>See FIG in motion</span><h2>Ready to make the content workflow feel less scattered?</h2><p>Explore the demo workspace first, then shape the product around the way your team actually works.</p></div>
          <div className="home-cta-actions"><div><Link className="secondary-button secondary-button--light" href="/projects">Explore demo</Link><Link className="button button--light" href="/signup">Create preview</Link></div><small>No account or payment is created in this frontend preview.</small></div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
