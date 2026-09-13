"use client";

import Link from "next/link";
import { Brand } from "./brand";

const columns = [
  { title: "Product", links: ["Features", "Integrations", "Pricing", "API"] },
  { title: "Resources", links: ["Guides", "Changelog", "Help center", "Community"] },
  { title: "Company", links: ["About", "Careers", "Contact", "Press"] },
  { title: "Legal", links: ["Privacy", "Terms", "Security", "Status"] }
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
            {column.links.map((link) => <Link href="#" key={link}>{link}</Link>)}
          </div>
        ))}
        <div className="footer-newsletter">
          <strong>Get product updates</strong>
          <p>Occasional notes on search, AI visibility, and FIG.</p>
          <form onSubmit={(event) => event.preventDefault()}>
            <input aria-label="Email address" type="email" placeholder="you@company.com" />
            <button className="button button--small" type="submit">Subscribe</button>
          </form>
        </div>
      </div>
    </footer>
  );
}
