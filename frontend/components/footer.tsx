import Link from "next/link";
import { ArrowUpRight, Sparkles } from "lucide-react";
import { Brand } from "./brand";

const columns = [
  { title: "Product", links: [{ label: "Features", href: "/#features" }, { label: "Integrations", href: "/#integrations" }, { label: "Pricing", href: "/pricing" }, { label: "Demo", href: "/projects" }] },
  { title: "Resources", links: [{ label: "Workflow", href: "/#workflow" }, { label: "GEO workspace", href: "/app/geo" }, { label: "SEO workspace", href: "/app/seo" }, { label: "FAQ", href: "/#faq" }] },
  { title: "Company", links: [{ label: "For teams", href: "/#teams" }, { label: "Create an account", href: "/signup" }, { label: "Sign in", href: "/signin" }, { label: "Help", href: "/#faq" }] },
  { title: "Workspace", links: [{ label: "Overview", href: "/app" }, { label: "Notifications", href: "/app/notifications" }, { label: "History", href: "/app/history" }, { label: "Settings", href: "/app/settings" }] }
];

export function Footer() {
  return (
    <footer className="footer">
      <div className="page-shell footer-top">
        <div className="footer-intro">
          <Brand />
          <h2>Clearer content operations, from the first brief to the final review.</h2>
          <p>FIG brings planning, SEO, GEO, collaboration, and publishing into one calm workspace for teams building visible, useful content.</p>
          <div className="footer-intro-note"><Sparkles size={14} /><span>Frontend preview for <b>LaunchVault.ca</b> · illustrative data only</span></div>
        </div>
        <div className="footer-navigation">
          {columns.map((column) => (
            <div className="footer-column" key={column.title}>
              <strong>{column.title}</strong>
              {column.links.map((link) => <Link href={link.href} key={link.label}>{link.label}</Link>)}
            </div>
          ))}
        </div>
        <div className="footer-newsletter">
          <span className="footer-eyebrow">Keep in the loop</span>
          <strong>Product notes, without the noise.</strong>
          <p>Occasional previews of FIG’s search, AI visibility, and content workflow work.</p>
          <form action="/signup" method="get">
            <input aria-label="Email address" name="email" type="email" required placeholder="you@company.com" />
            <button className="button button--small" type="submit">Get preview <ArrowUpRight size={14} /></button>
          </form>
          <small>Continues to signup with your email filled in. Does not subscribe you.</small>
        </div>
      </div>
      <div className="page-shell footer-bottom"><span>© 2026 FIG. All rights reserved.</span><div><Link href="/projects">Explore demo</Link><Link href="/pricing">Pricing</Link><Link href="/signin">Sign in</Link><Link href="/#faq">Help</Link></div><span>Made for practical, discoverable content.</span></div>
    </footer>
  );
}
