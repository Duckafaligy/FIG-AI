import Link from "next/link";
import type { Metadata } from "next";
import { ArrowDownRight, BarChart3, LockKeyhole, PenLine, Search } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { PublicNav } from "@/components/public-nav";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";

const benefits = [
  { icon: PenLine, title: "A fix for every finding", copy: "Each one says where it is, why it matters and what to change." },
  { icon: Search, title: "Reads any public site", copy: "Whatever it is built with, FIG checks the pages a visitor can see." },
  { icon: BarChart3, title: "History and re-scans", copy: "Run it again after a change and see what moved." },
];

export const metadata: Metadata = {
  title: "Sign in — FIG",
  description: "Sign in to your FIG workspace to see your sites, findings and scan history.",
  alternates: { canonical: "/signin" },
};

export default function SignInPage() {
  return (
    <div className="auth-page auth-page--signin">
      <PublicNav />
      <main>
        <section className="auth-layout auth-layout--signin page-shell">
          <div className="auth-card auth-card--signin"><AuthForm mode="signin" /></div>
          <section className="auth-story auth-story--signin" aria-label="FIG product overview">
            <div className="auth-story-copy">
              <span className="auth-story-kicker">Scan <i>→</i> Fix <i>→</i> Re-scan</span>
              <h1>Pick up where <span>you left off</span></h1>
              <p>Your sites, findings and history are waiting. Sign in to see what changed since your last scan.</p>
            </div>
            <div className="auth-benefits auth-benefits--stacked">
              {benefits.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={25} /></span><div><h3>{title}</h3><p>{copy}</p></div></article>)}
            </div>
            <div className="auth-laptop-frame">
              <div className="auth-stat auth-stat--preview"><BarChart3 size={20} /><div><strong>19 checks</strong><span>across craft, structure, search and answers</span></div></div>
              <span className="auth-scribble-note">A fix for every<br />finding <ArrowDownRight size={30} /></span>
              <div className="auth-laptop"><ProductLaptop compact variant="library" /></div>
            </div>
          </section>
        </section>
        <section className="auth-platform-proof page-shell" aria-label="Sites FIG can read">
          <span className="section-kicker">Reads any public site, whatever it is built with</span>
          <PlatformLogos />
        </section>
      </main>
      <footer className="auth-footer page-shell">
        <span className="auth-security-note"><LockKeyhole size={14} />Your password goes straight to our sign-in provider and never touches FIG&rsquo;s servers</span>
        <span><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/#faq">Help</Link></span>
      </footer>
    </div>
  );
}
