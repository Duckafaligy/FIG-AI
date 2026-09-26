import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { OPERATOR } from "@/lib/legal";
import { Brand } from "./brand";
const columns = [
  { title: "Product", links: [["Free scan", "/#scan"], ["Pricing", "/pricing"], ["Workspace", "/projects"], ["Integrations", "/#integrations"]] },
  { title: "Resources", links: [["Scan library", "/library"], ["Questions", "/#faq"], ["About our crawler", "/bot"]] },
  { title: "Legal", links: [["Privacy policy", "/privacy"], ["Terms & Conditions", "/terms"], ["Refunds", "/refunds"]] },
];
export function Footer() {
  return <footer className="fig-launch-footer"><div className="page-shell fig-footer-main"><div className="fig-footer-brand"><Brand /><h2>A clearer<br />next move.</h2><p>See what makes your site read as generic, and how to fix it.</p><a href={`mailto:${OPERATOR.email}`}>Contact FIG <ArrowUpRight size={14} /></a></div><nav className="fig-footer-links" aria-label="Footer navigation">{columns.map(column => <div key={column.title}><h3>{column.title}</h3>{column.links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}</div>)}</nav></div><div className="page-shell fig-footer-bottom"><span>© {new Date().getFullYear()} FIG. All rights reserved.</span></div></footer>;
}
