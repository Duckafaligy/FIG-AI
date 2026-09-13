"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  ChevronDown,
  Clock3,
  Globe2,
  HelpCircle,
  History,
  Home,
  Menu,
  Plus,
  Search,
  Settings,
  Sparkles,
  X
} from "lucide-react";
import { useState } from "react";
import { Brand } from "./brand";

const nav = [
  { href: "/app", label: "Overview", icon: Home },
  { href: "/app/seo", label: "SEO", icon: Search },
  { href: "/app/geo", label: "GEO", icon: Globe2 },
  { href: "/app/notifications", label: "Notifications", icon: Bell },
  { href: "/app/history", label: "History", icon: History },
  { href: "/app/settings", label: "Settings", icon: Settings }
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <div className="dashboard-shell">
      <button className="dashboard-menu" onClick={() => setOpen(!open)} aria-label="Toggle dashboard navigation">{open ? <X /> : <Menu />}</button>
      <aside className={`dashboard-sidebar ${open ? "is-open" : ""}`}>
        <Brand inverse />
        <nav aria-label="Dashboard navigation">
          {nav.map((item) => {
            const exact = item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
            const Icon = item.icon;
            return <Link className={exact ? "active" : ""} href={item.href} key={item.href} onClick={() => setOpen(false)}><Icon size={18} />{item.label}</Link>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <Link href="#"><HelpCircle size={18} />Help & docs</Link>
          <Link href="/"><Home size={18} />Public site</Link>
        </div>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-search"><Search size={17} /><input aria-label="Search" placeholder="Search projects, content, or insights…" /><kbd>⌘ K</kbd></div>
          <div className="dashboard-top-actions">
            <button className="workspace-switch"><span className="workspace-mark"><Sparkles size={14} /></span>My workspace<ChevronDown size={15} /></button>
            <button className="icon-button" aria-label="Notifications"><Bell size={18} /></button>
            <button className="avatar-button">JD</button>
          </div>
        </header>
        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}

export function DashboardHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="dashboard-heading-row">
      <div><span className="dashboard-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      <button className="button button--small"><Plus size={16} />New project</button>
    </div>
  );
}

export function MetricCard({ label, icon: Icon }: { label: string; icon: typeof Search }) {
  return (
    <article className="metric-card">
      <span className="metric-icon"><Icon size={20} /></span>
      <p>{label}</p>
      <strong>—</strong>
      <small><Clock3 size={12} />No data yet</small>
    </article>
  );
}

function EmptyChart() {
  return (
    <div className="empty-chart-art" aria-hidden="true">
      <div className="chart-grid-lines" />
      <svg viewBox="0 0 700 190" preserveAspectRatio="none"><path d="M0 155 C90 150, 100 125, 180 130 S285 95, 350 112 S480 65, 540 82 S640 35, 700 44" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray="7 9" /></svg>
    </div>
  );
}

export function EmptySection({ title, description, icon: Icon, kind = "feed" }: { title: string; description: string; icon: typeof Search; kind?: "chart" | "table" | "feed" | "flow" }) {
  return (
    <section className={`dashboard-panel dashboard-panel--${kind}`}>
      <div className="panel-heading"><div><span className="panel-icon"><Icon size={18} /></span><h2>{title}</h2></div><button>View details</button></div>
      {kind === "chart" && <EmptyChart />}
      {kind === "flow" && <div className="empty-flow">{["Connect", "Discover", "Review", "Publish"].map((step, index) => <div key={step}><span>{index + 1}</span><strong>{step}</strong></div>)}</div>}
      {kind === "table" && <div className="empty-table"><div className="empty-table-head"><span>Title</span><span>Status</span><span>Updated</span></div><div className="empty-table"><span className="empty-orb"><Icon size={22} /></span><strong>No items yet</strong><p>{description}</p><button className="secondary-button">Get started</button></div></div>}
      {kind === "feed" && <div className="empty-message"><span className="empty-orb"><Icon size={22} /></span><strong>Nothing here yet</strong><p>{description}</p></div>}
      {kind === "chart" && <div className="chart-empty-label"><strong>Waiting for your first data point</strong><span>{description}</span></div>}
      {kind === "flow" && <p className="flow-description">{description}</p>}
    </section>
  );
}
