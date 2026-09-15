import Link from "next/link";
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
      <div className="page-shell footer-grid">
        <div className="footer-brand">
          <Brand />
          <p>Content that gets you found.</p>
          <span>© 2026 FIG. All rights reserved.</span>
        </div>
        {columns.map((column) => (
          <div className="footer-column" key={column.title}>
            <strong>{column.title}</strong>
            {column.links.map((link) => <Link href={link.href} key={link.label}>{link.label}</Link>)}
          </div>
        ))}
        <div className="footer-newsletter">
          <strong>Get product updates</strong>
          <p>Occasional notes on search, AI visibility, and FIG.</p>
          <form action="/signup" method="get">
            <input aria-label="Email address" name="email" type="email" placeholder="you@company.com" />
            <button className="button button--small" type="submit">Join preview</button>
          </form>
          <small>Opens the FIG signup preview.</small>
        </div>
      </div>
    </footer>
  );
}
