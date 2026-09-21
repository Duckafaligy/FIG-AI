import Link from "next/link";
import { ArrowUpRight, Scale } from "lucide-react";
import { TRIAL_DAYS } from "@/lib/legal";
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
          <h2>See what makes your site read as generic, and how to fix it.</h2>
          <p>FIG checks the design, structure, search basics and answer-readiness of your public pages, and tells you where each finding is and what to change.</p>
          <div className="footer-intro-note"><Scale size={14} /><span>A self-check tool. Findings are <b>signals, never verdicts</b>.</span></div>
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
          <span className="footer-eyebrow">Get started</span>
          <strong>Try it on your own site.</strong>
          <p>Run a free scan with no account, or create an account for a {TRIAL_DAYS}-day trial with no card.</p>
          <form action="/signup" method="get">
            <input aria-label="Email address" name="email" type="email" required placeholder="you@company.com" />
            <button className="button button--small" type="submit">Create account <ArrowUpRight size={14} /></button>
          </form>
          <small>Continues to sign-up with your email filled in. Nothing is sent to you.</small>
        </div>
      </div>
      <div className="page-shell footer-bottom"><span>© 2026 FIG. All rights reserved.</span><div><Link href="/projects">Explore demo</Link><Link href="/pricing">Pricing</Link><Link href="/signin">Sign in</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/refunds">Refunds</Link><Link href="/bot">FIGBot</Link></div><span>Made for practical, discoverable content.</span></div>
    </footer>
  );
}
