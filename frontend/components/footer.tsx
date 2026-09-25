import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { OPERATOR } from "@/lib/legal";
import { Brand } from "./brand";
const columns = [
  { title: "Product", links: [["Overview", "/#scan"], ["Workspace", "/projects"], ["Pricing", "/pricing"], ["Integrations", "/#integrations"]] },
  { title: "Company", links: [["About", "/bot"], ["Contact", `mailto:${OPERATOR.email}`], ["Changelog", "/library"], ["Careers", `mailto:${OPERATOR.email}`]] },
  { title: "Resources", links: [["Scan library", "/library"], ["Guides", "/library"], ["Help center", "/#faq"], ["Status", "/projects"]] },
  { title: "Legal", links: [["Privacy policy", "/privacy"], ["Terms", "/terms"], ["Cookie policy", "/privacy"], ["Refunds", "/refunds"]] },
];
export function Footer() {
  return <footer className="fig-launch-footer"><div className="page-shell fig-footer-main"><div className="fig-footer-brand"><Brand /><h2>A clearer<br />next move.</h2><p>Content intelligence for teams who build on the web.</p><a href={`mailto:${OPERATOR.email}`}>Contact FIG <ArrowUpRight size={14} /></a></div><nav className="fig-footer-links" aria-label="Footer navigation">{columns.map(column => <div key={column.title}><h3>{column.title}</h3>{column.links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}</div>)}</nav></div><div className="page-shell fig-footer-bottom"><span>© {new Date().getFullYear()} FIG. All rights reserved.</span><div><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/refunds">Refunds</Link></div><span>Build with context.</span></div></footer>;
}
