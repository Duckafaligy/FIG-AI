import Link from "next/link";
import { BarChart3, Database, Globe2, PenLine, Search, Share2, ShieldCheck, Sparkles, Users } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";
import { PreviewInfo } from "@/components/preview-info";

const signupBenefits = [
  { icon: PenLine, title: "Create with AI", copy: "Turn ideas into high-performing content in minutes." },
  { icon: BarChart3, title: "Optimize every surface", copy: "Prepare content for SEO, GEO, and AI-ready discovery." },
  { icon: Share2, title: "Publish with confidence", copy: "Move through collaborative review from draft to live." },
  { icon: Search, title: "Get found everywhere", copy: "Increase visibility across Google, AI search, and beyond." },
];

const proofMetrics = [
  { icon: BarChart3, value: "+187%", label: "illustrative organic-growth preview", tone: "purple" },
  { icon: Users, value: "3.4x", label: "illustrative AI-visibility preview", tone: "blue" },
  { icon: Database, value: "10,000+", label: "illustrative content-capacity preview", tone: "green" },
  { icon: Sparkles, value: "92%", label: "illustrative ROI-preview benchmark", tone: "amber" },
];

const foundations = [
  { icon: ShieldCheck, title: "Secure by design", copy: "Your data stays yours." },
  { icon: Users, title: "Built for teams", copy: "From startups to enterprises." },
  { icon: Sparkles, title: "Ready for what’s next", copy: "Built for Google, ChatGPT, and beyond." },
  { icon: Globe2, title: "Global scale", copy: "A flexible platform foundation." },
];

export default function SignUpPage() {
  return (
    <div className="auth-page auth-page--signup signup-page">
      <header className="auth-nav page-shell">
        <Brand />
        <nav aria-label="Account navigation"><Link href="/projects">Demo</Link><Link href="/pricing">Pricing</Link><Link href="/signin">Sign in</Link><Link className="button button--small" href="/signup" aria-current="page">Sign up</Link></nav>
      </header>
      <main>
        <section className="signup-layout signup-layout--refined page-shell">
          <section className="signup-story" aria-label="Why choose FIG">
            <span className="eyebrow"><Sparkles size={13} />Built for the next generation of search</span>
            <h1>Turn your content into growth. <span>Get found everywhere.</span></h1>
            <p>FIG helps marketing, product, and content teams create, optimize, and publish content that performs across Google, AI search, and every discovery channel.</p>
            <div className="signup-benefits signup-benefits--grid">
              {signupBenefits.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={24} /></span><h2>{title}</h2><p>{copy}</p></article>)}
            </div>
            <div className="signup-laptop-frame">
              <div className="signup-laptop"><ProductLaptop compact variant="queue" /></div>
              <span className="scribble-note signup-annotation">From idea to impact</span>
            </div>
          </section>
          <div className="auth-card auth-card--signup signup-card"><AuthForm mode="signup" /></div>
        </section>

        <section className="signup-platform-proof page-shell" aria-label="Supported platform integrations">
          <span className="section-kicker">Connect with your favorite platforms</span>
          <PlatformLogos />
        </section>

        <section className="signup-metric-band page-shell" aria-label="Illustrative product impact metrics">
          {proofMetrics.map(({ icon: Icon, value, label, tone }) => <article className={`signup-metric signup-metric--${tone}`} key={value}><Icon size={24} /><strong>{value}</strong><span>{label}</span></article>)}
        </section>

        <section className="signup-trust signup-trust--foundations">
          <div className="page-shell">
            <div className="signup-trust-heading"><span className="section-kicker">A complete content operations platform</span><h2>Built to help you grow with confidence</h2><p>A calm, connected workspace for the work behind visible, useful content.</p></div>
            <div className="signup-foundations">
              {foundations.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={25} /></span><strong>{title}</strong><p>{copy}</p></article>)}
            </div>
          </div>
        </section>
      </main>
      <footer className="auth-footer auth-footer--signup page-shell"><span><Brand /><i />© 2026 FIG. All rights reserved.</span><span><Link href="/#features">Product</Link><Link href="/pricing">Pricing</Link><PreviewInfo label="Privacy" message="The privacy policy will be published before authentication is enabled. This form does not send or store the information you enter." /><PreviewInfo label="Terms" message="FIG’s terms will be published before account creation is enabled." /><Link href="/#faq">Help</Link></span></footer>
    </div>
  );
}
