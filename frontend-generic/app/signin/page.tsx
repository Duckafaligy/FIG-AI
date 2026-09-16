import Link from "next/link";
import { ArrowDownRight, BarChart3, LockKeyhole, Search, Sparkles, Users } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";
import { PreviewInfo } from "@/components/preview-info";

const benefits = [
  { icon: Sparkles, title: "Create faster", copy: "Turn ideas into high-performing content in minutes." },
  { icon: Search, title: "Get found everywhere", copy: "Optimize for SEO and GEO to reach more people across search and AI." },
  { icon: Users, title: "Drive real results", copy: "Give your team a shared view of visibility, traffic, and growth." },
];

export default function SignInPage() {
  return (
    <div className="auth-page auth-page--signin">
      <header className="auth-nav page-shell">
        <Brand />
        <nav aria-label="Account navigation"><Link href="/projects">Demo</Link><Link href="/signin" aria-current="page">Sign in</Link><Link className="button button--small" href="/signup">Sign up</Link></nav>
      </header>
      <main>
        <section className="auth-layout auth-layout--signin page-shell">
          <div className="auth-card auth-card--signin"><AuthForm mode="signin" /></div>
          <section className="auth-story auth-story--signin" aria-label="FIG product overview">
            <div className="auth-story-copy">
              <span className="auth-story-kicker">Ideas <i>→</i> Content <i>→</i> Growth</span>
              <h1>Smarter content for <span>bigger results</span></h1>
              <p>SEO and GEO content that helps your brand get found, attract the right audience, and drive real growth — all in one platform.</p>
            </div>
            <div className="auth-benefits auth-benefits--stacked">
              {benefits.map(({ icon: Icon, title, copy }) => <article key={title}><span><Icon size={25} /></span><div><h2>{title}</h2><p>{copy}</p></div></article>)}
            </div>
            <div className="auth-laptop-frame">
              <div className="auth-stat auth-stat--preview"><BarChart3 size={20} /><div><strong>+187%</strong><span>Illustrative organic-growth preview</span></div></div>
              <span className="auth-scribble-note">Turn ideas<br />into real growth <ArrowDownRight size={30} /></span>
              <div className="auth-laptop"><ProductLaptop compact variant="library" /></div>
            </div>
          </section>
        </section>
        <section className="auth-platform-proof page-shell" aria-label="Supported platform integrations">
          <span className="section-kicker">Trusted by modern brands on every platform</span>
          <PlatformLogos />
        </section>
      </main>
      <footer className="auth-footer page-shell">
        <span className="auth-security-note"><LockKeyhole size={14} />Account preview <i /> Your form entries stay in this browser</span>
        <span><PreviewInfo label="Privacy" message="The privacy policy will be published before authentication is enabled. This form does not send or store the information you enter." /><PreviewInfo label="Terms" message="FIG’s terms will be published before account creation is enabled." /><Link href="/#faq">Help</Link></span>
      </footer>
    </div>
  );
}
