import Link from "next/link";
import type { Metadata } from "next";
import { BarChart3, PenLine, Search, Share2 } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";
import { TRIAL_DAYS } from "@/lib/legal";

const signupBenefits = [
  { icon: PenLine, title: "See what reads as generic", copy: "19 checks across design, structure, search and answers." },
  { icon: Search, title: "Know where and why", copy: "Every finding names the page, the reason and a concrete fix." },
  { icon: BarChart3, title: "Track what changed", copy: "Re-scan after a fix and compare it with your history." },
  { icon: Share2, title: "Share when you choose", copy: "A public report link stays off until you turn it on." },
];

export const metadata: Metadata = {
  title: "Create your account — FIG",
  description: "Create a FIG account for a 7-day free trial with no card, then scan your sites and track what changes.",
  alternates: { canonical: "/signup" },
};

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
            <span className="eyebrow">Free scan or {TRIAL_DAYS}-day trial</span>
            <h1>See what makes your site <span>read as generic.</span></h1>
            <p>FIG checks the public pages of your site and tells you what to change. An account adds scan history, up to 40 pages per scan, and connections to Google and WordPress.</p>
            <div className="signup-benefits signup-benefits--grid">
              {signupBenefits.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={24} /></span><h3>{title}</h3><p>{copy}</p></article>)}
            </div>
            <div className="signup-laptop-frame">
              <div className="signup-laptop"><ProductLaptop compact variant="queue" /></div>
              <span className="scribble-note signup-annotation">From idea to impact</span>
            </div>
          </section>
          <div className="auth-card auth-card--signup signup-card"><AuthForm mode="signup" /></div>
        </section>

        <section className="signup-platform-proof page-shell" aria-label="Sites FIG can read">
          <span className="section-kicker">Reads any public site, whatever it is built with</span>
          <PlatformLogos />
          <p>Creating an account starts a {TRIAL_DAYS}-day free trial. No card is needed, and nothing is charged unless you subscribe.</p>
        </section>
      </main>
      <footer className="auth-footer auth-footer--signup page-shell"><span><Brand /><i />© 2026 FIG. All rights reserved.</span><span><Link href="/#features">Product</Link><Link href="/pricing">Pricing</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/#faq">Help</Link></span></footer>
    </div>
  );
}
