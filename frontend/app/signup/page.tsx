import { BarChart3, Globe2, PenLine, Search, Share2, ShieldCheck, Sparkles, Users } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { ProductLaptop } from "@/components/product-laptop";
import Link from "next/link";

export default function SignUpPage() {
  return (
    <div className="auth-page signup-page">
      <header className="auth-nav page-shell"><Brand /><nav><Link href="/app">Demo</Link><Link href="/pricing">Pricing</Link><Link href="/signin">Sign in</Link><Link className="button button--small" href="/signup">Sign up</Link></nav></header>
      <main className="signup-layout page-shell">
        <section className="signup-story"><span className="eyebrow"><Sparkles size={13} />Built for the next generation of search</span><h1>Turn your content into growth. <span>Get found everywhere.</span></h1><p>FIG helps marketing, product, and content teams create, optimize, and publish across search and AI discovery channels.</p><div className="signup-benefits">{[
          { icon: PenLine, title: "Create with AI", copy: "Turn ideas into focused content." },
          { icon: BarChart3, title: "Optimize every surface", copy: "Prepare for SEO and GEO." },
          { icon: Share2, title: "Publish with confidence", copy: "Move through clear reviews." },
          { icon: Search, title: "Get found everywhere", copy: "Improve discoverability." }
        ].map(({ icon: Icon, title, copy }) => <div key={title}><span><Icon /></span><h3>{title}</h3><p>{copy}</p></div>)}</div><div className="signup-laptop"><ProductLaptop compact variant="queue" /><span className="scribble-note">From idea to impact</span></div></section>
        <div className="auth-card signup-card"><AuthForm mode="signup" /></div>
      </main>
      <section className="signup-trust"><div className="page-shell"><span className="section-kicker">A complete content operations platform</span><div>{[
        { icon: ShieldCheck, title: "Secure by design", copy: "Your data stays yours." },
        { icon: Users, title: "Built for teams", copy: "From startups to enterprises." },
        { icon: Sparkles, title: "Ready for what’s next", copy: "Search and AI workflows." },
        { icon: Globe2, title: "Global scale", copy: "A flexible platform foundation." }
      ].map(({ icon: Icon, title, copy }) => <article key={title}><Icon /><strong>{title}</strong><span>{copy}</span></article>)}</div></div></section>
      <footer className="auth-footer page-shell"><Brand /><span>© 2026 FIG. All rights reserved.</span><span><Link href="/pricing">Pricing</Link><Link href="#">Privacy</Link><Link href="#">Terms</Link><Link href="#">Contact</Link></span></footer>
    </div>
  );
}
