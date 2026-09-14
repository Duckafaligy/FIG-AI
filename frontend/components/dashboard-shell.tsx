"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  CalendarDays,
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
            <div className="workspace-switch" aria-label="Current project"><span className="workspace-mark">LV</span>LaunchVault.ca</div>
            <div className="workspace-switch" aria-label="Illustrative preview date range"><CalendarDays size={16} aria-hidden="true" /><span>Apr 28 – May 26</span><ChevronDown size={14} aria-hidden="true" /></div>
            <button className="icon-button" aria-label="Notifications"><Bell size={18} /></button>
            <span className="avatar-button" aria-label="Current account: JD" style={{ cursor: "default" }}>JD</span>
            <ChevronDown size={14} aria-hidden="true" />
          </div>
        </header>
        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}

export function DashboardHeader({ eyebrow, title, description, action = "Project settings" }: { eyebrow: string; title: string; description: string; action?: string }) {
  return (
    <div className="dashboard-heading-row">
      <div><span className="dashboard-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p><span className="preview-source"><span />Demo data · LaunchVault.ca</span></div>
      <button className="button button--small"><Plus size={16} />{action}</button>
    </div>
  );
}

export function MetricCard({ label, value, change, detail, icon: Icon, tone = "purple" }: DashboardPage["metrics"][number]) {
  const normalizedChange = change.trim();
  const isNegative = normalizedChange.startsWith("-") || normalizedChange.startsWith("−");
  const isPositive = normalizedChange.startsWith("+");
  const trendColor = isNegative ? "var(--red)" : isPositive ? "var(--green)" : "var(--muted)";
  const trendIcon = isNegative ? "↘" : isPositive ? "↗" : "→";
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-icon"><Icon size={20} /></span>
      <p>{label}</p>
      <strong>{value}</strong>
      <small style={{ color: trendColor }}><span aria-hidden="true">{trendIcon}</span>{change}<em>{detail}</em></small>
    </article>
  );
}

function ChartLegend({ legend }: { legend?: string[] }) {
  return <div className="preview-chart-legend">{legend?.map((label, index) => <span className={`chart-key chart-key--${index + 1}`} key={label}>{label}</span>)}</div>;
}

function PreviewChart({ legend, chart = "trend" }: { legend?: string[]; chart?: DashboardPage["sections"][number]["chart"] }) {
  if (chart === "donut") {
    return <div className="preview-chart preview-chart--donut" aria-label="Illustrative content mix chart"><ChartLegend legend={legend} /><div className="donut-layout"><svg className="preview-donut" viewBox="0 0 120 120"><circle cx="60" cy="60" r="43" fill="none" stroke="#ebe8ff" strokeWidth="16" /><circle cx="60" cy="60" r="43" fill="none" stroke="#6047ff" strokeWidth="16" strokeDasharray="112 270" strokeDashoffset="0" transform="rotate(-90 60 60)" /><circle cx="60" cy="60" r="43" fill="none" stroke="#2f80ed" strokeWidth="16" strokeDasharray="74 270" strokeDashoffset="-121" transform="rotate(-90 60 60)" /><circle cx="60" cy="60" r="43" fill="none" stroke="#20b878" strokeWidth="16" strokeDasharray="51 270" strokeDashoffset="-204" transform="rotate(-90 60 60)" /><text x="60" y="57" textAnchor="middle">1,500</text><text x="60" y="72" textAnchor="middle">items</text></svg><div className="donut-copy"><strong>Library mix</strong><span>Lessons lead the preview, followed by prompts and workflows.</span></div></div></div>;
  }
  if (chart === "bars") {
    const bars = [42, 58, 50, 66, 73, 67, 81, 88, 76, 94, 101, 110];
    return <div className="preview-chart preview-chart--bars" aria-label="Illustrative ranking bar chart"><ChartLegend legend={legend} /><div className="bar-chart">{bars.map((height, index) => <span key={`${height}-${index}`} style={{ height: `${height}px` }}><i /><b /><em /></span>)}</div><div className="chart-axis"><span>Apr 28</span><span>May 5</span><span>May 12</span><span>May 19</span><span>May 26</span></div></div>;
  }
  if (chart === "reliability") {
    return <div className="preview-chart preview-chart--reliability" aria-label="Illustrative automation reliability chart"><ChartLegend legend={legend} /><div className="reliability-bars"><div><span>Content sync</span><i><b style={{ width: "96%" }} /></i><strong>96%</strong></div><div><span>SEO processing</span><i><b style={{ width: "91%" }} /></i><strong>91%</strong></div><div><span>Notification delivery</span><i><b style={{ width: "98%" }} /></i><strong>98%</strong></div><div><span>Review workflow</span><i><b style={{ width: "94%" }} /></i><strong>94%</strong></div></div></div>;
  }
  return (
    <div className="preview-chart" aria-label="Illustrative trend chart">
      <ChartLegend legend={legend} />
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

export function EmptySection({ title, description, icon: Icon, kind, chart, span, legend, rows, columns, steps }: DashboardPage["sections"][number]) {
  const context = kind === "chart" ? "Last 30 days" : kind === "table" ? "LaunchVault.ca" : kind === "flow" ? "Content workflow" : "Needs attention";
  return (
    <section className={`dashboard-panel dashboard-panel--${kind} ${span === "wide" ? "dashboard-panel--wide" : ""}`}>
      <div className="panel-heading"><div><span className="panel-icon"><Icon size={18} /></span><h2>{title}</h2></div><span className="panel-meta">{context}</span></div>
      {kind === "chart" && <><PreviewChart legend={legend} chart={chart} /><p className="panel-description">{description}</p></>}
      {kind === "flow" && <><div className="empty-flow">{steps?.map((step, index) => <div key={step.label}><span>{index + 1}</span><strong>{step.label}</strong><small>{step.copy}</small></div>)}</div><p className="flow-description">{description}</p></>}
      {kind === "table" && <div className="preview-table"><div className="empty-table-head"><span>{columns?.[0]}</span><span>{columns?.[1]}</span><span>{columns?.[2]}</span></div><PreviewRows rows={rows} compact /></div>}
      {kind === "feed" && <PreviewRows rows={rows} />}
    </section>
  );
}
