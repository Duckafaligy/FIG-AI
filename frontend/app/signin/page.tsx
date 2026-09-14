import { BarChart3, Search, Sparkles, Users } from "lucide-react";
import { AuthForm } from "@/components/auth-form";
import { Brand } from "@/components/brand";
import { ProductLaptop } from "@/components/product-laptop";
import Link from "next/link";

export default function SignInPage() {
  return (
    <div className="auth-page">
      <header className="auth-nav page-shell"><Brand /><nav><Link href="/app">Demo</Link><Link href="/signin">Sign in</Link><Link className="button button--small" href="/signup">Sign up</Link></nav></header>
      <main className="auth-layout page-shell">
        <div className="auth-card"><AuthForm mode="signin" /></div>
        <section className="auth-story"><span className="auth-story-kicker">Ideas <i>→</i> Content <i>→</i> Growth</span><h2>Smarter content for <span>bigger results</span></h2><p>SEO and GEO content that helps your brand get found, attract the right audience, and drive meaningful growth.</p><div className="auth-benefits">{[
          { icon: Sparkles, title: "Create faster", copy: "Turn ideas into focused content workflows." },
          { icon: Search, title: "Get found everywhere", copy: "Optimize for search and generative answers." },
          { icon: Users, title: "Drive real results", copy: "Keep the whole team connected to impact." }
        ].map(({ icon: Icon, title, copy }) => <div key={title}><span><Icon /></span><div><h3>{title}</h3><p>{copy}</p></div></div>)}</div><div className="auth-laptop"><span className="auth-stat"><BarChart3 />LaunchVault library preview</span><ProductLaptop compact variant="library" /></div></section>
      </main>
      <footer className="auth-footer page-shell"><span>Secure sign-in · Your data is encrypted</span><span><Link href="#">Privacy</Link><Link href="#">Terms</Link><Link href="#">Help</Link></span></footer>
    </div>
  );
}
