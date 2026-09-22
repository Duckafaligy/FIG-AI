import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { OPERATOR } from "@/lib/legal";
import { Brand } from "./brand";
const columns = [
  { title: "Product", links: [["Website analysis", "/#scan"], ["Features", "/#features"], ["Scan library", "/library"], ["Workspace", "/projects"]] },
  { title: "Plans", links: [["Business", "/pricing#business"], ["Education", "/pricing#education"], ["All pricing", "/pricing"], ["Create account", "/signup"]] },
  { title: "Resources", links: [["How it works", "/#workflow"], ["Questions", "/#faq"], ["About FIGBot", "/bot"], ["Sign in", "/signin"]] },
];
export function Footer() {
  return <footer className="fig-launch-footer"><div className="page-shell fig-footer-main"><div className="fig-footer-brand"><Brand /><h2>Better websites start<br />with understanding.</h2><p>Website analysis for business owners, students, and everyone who wants to build better.</p><a href={`mailto:${OPERATOR.email}`}>Contact FIG <ArrowUpRight size={14} /></a></div><nav className="fig-footer-links" aria-label="Footer navigation">{columns.map(column => <div key={column.title}><h3>{column.title}</h3>{column.links.map(([label, href]) => <Link key={label} href={href}>{label}</Link>)}</div>)}</nav></div><div className="page-shell fig-footer-bottom"><span>© {new Date().getFullYear()} FIG. All rights reserved.</span><div><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><Link href="/refunds">Refunds</Link></div><span>Findings are signals, not verdicts.</span></div></footer>;
}
