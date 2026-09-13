"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  ChevronDown,
  Globe2,
  HelpCircle,
  History,
  Home,
  Menu,
  Plus,
  Search,
  Settings,
  X
} from "lucide-react";
import { useState } from "react";
import { Brand } from "./brand";
import type { DashboardPage } from "@/lib/dashboard-pages";

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
            <button className="workspace-switch"><span className="workspace-mark">LV</span>LaunchVault.ca<ChevronDown size={15} /></button>
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
      <div><span className="dashboard-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p><span className="preview-source"><span />Preview workspace · live sources not connected</span></div>
      <button className="button button--small"><Plus size={16} />Project settings</button>
    </div>
  );
}

export function MetricCard({ label, value, change, detail, icon: Icon, tone = "purple" }: DashboardPage["metrics"][number]) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-icon"><Icon size={20} /></span>
      <p>{label}</p>
      <strong>{value}</strong>
      <small><span>↗</span>{change}<em>{detail}</em></small>
    </article>
  );
}

function PreviewChart({ legend }: { legend?: string[] }) {
  return (
    <div className="preview-chart" aria-label="Illustrative trend chart">
      <div className="preview-chart-legend">{legend?.map((label, index) => <span className={`chart-key chart-key--${index + 1}`} key={label}>{label}</span>)}</div>
      <div className="preview-chart-art">
        <div className="chart-grid-lines" />
        <svg viewBox="0 0 700 190" preserveAspectRatio="none">
          <defs><linearGradient id="chart-wash" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#5b45ef" stopOpacity=".22" /><stop offset="1" stopColor="#5b45ef" stopOpacity="0" /></linearGradient></defs>
          <path d="M0 155 C78 150, 112 126, 178 132 S280 96, 350 111 S465 71, 541 84 S641 35, 700 46 L700 190 L0 190Z" fill="url(#chart-wash)" />
          <path d="M0 155 C78 150, 112 126, 178 132 S280 96, 350 111 S465 71, 541 84 S641 35, 700 46" fill="none" stroke="#6047ff" strokeWidth="3" />
          <path d="M0 166 C78 158, 112 149, 178 151 S280 130, 350 136 S465 111, 541 118 S641 82, 700 92" fill="none" stroke="#2f80ed" strokeWidth="2.5" />
          <path d="M0 173 C78 167, 112 160, 178 166 S280 147, 350 150 S465 131, 541 137 S641 109, 700 116" fill="none" stroke="#20b878" strokeWidth="2.5" />
        </svg>
      </div>
      <div className="chart-axis"><span>Apr 28</span><span>May 5</span><span>May 12</span><span>May 19</span><span>May 26</span></div>
    </div>
  );
}

function PreviewRows({ rows, compact = false }: { rows?: DashboardPage["sections"][number]["rows"]; compact?: boolean }) {
  return <div className={compact ? "preview-table-body" : "preview-feed"}>{rows?.map((row) => <article className="preview-row" key={row.title}><span className={`row-mark row-mark--${row.tone ?? "purple"}`} /><div><strong>{row.title}</strong><small>{row.meta}</small></div><span className={`status-pill status-pill--${row.tone ?? "purple"}`}>{row.status}</span></article>)}</div>;
}

export function EmptySection({ title, description, icon: Icon, kind, legend, rows, columns, steps }: DashboardPage["sections"][number]) {
  return (
    <section className={`dashboard-panel dashboard-panel--${kind}`}>
      <div className="panel-heading"><div><span className="panel-icon"><Icon size={18} /></span><h2>{title}</h2></div><span className="panel-meta">Preview data</span></div>
      {kind === "chart" && <><PreviewChart legend={legend} /><p className="panel-description">{description}</p></>}
      {kind === "flow" && <><div className="empty-flow">{steps?.map((step, index) => <div key={step.label}><span>{index + 1}</span><strong>{step.label}</strong><small>{step.copy}</small></div>)}</div><p className="flow-description">{description}</p></>}
      {kind === "table" && <div className="preview-table"><div className="empty-table-head"><span>{columns?.[0]}</span><span>{columns?.[1]}</span><span>{columns?.[2]}</span></div><PreviewRows rows={rows} compact /></div>}
      {kind === "feed" && <PreviewRows rows={rows} />}
    </section>
  );
}
