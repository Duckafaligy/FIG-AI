"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowLeft,
  Bell,
  BadgeCheck,
  CalendarClock,
  Zap,
  CalendarDays,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Globe2,
  Link2,
  LayoutTemplate,
  Monitor,
  RefreshCw,
  ShieldCheck,
  Upload,
  Eye,
  FileText,
  Check,
  Trash2,
  Download,
  History,
  Home,
  Menu,
  Plus,
  Search,
  Settings,
  Sparkles,
  X
} from "lucide-react";
import { createContext, useContext, useEffect, useId, useRef, useState, type CSSProperties } from "react";
import type { DashboardPage, DashboardRow } from "@/lib/dashboard-pages";
import { chartHitArea, chartRanges, chartSamples, type ChartRange } from "@/lib/chart-range";
import { ContentTemplatePreview } from "./content-template-preview";

const DashboardSearchContext = createContext("");

const nav = [
  { href: "/app", label: "Overview", icon: Home },
  { href: "/app/seo", label: "SEO", icon: Search },
  { href: "/app/geo", label: "GEO", icon: Globe2 },
  { href: "/app/notifications", label: "Notifications", icon: Bell },
  { href: "/app/history", label: "History", icon: History },
  { href: "/app/settings", label: "Settings", icon: Settings }
];

const searchCopy: Record<string, string> = {
  "/app": "Search LaunchVault content…",
  "/app/seo": "Search posts, keywords, or briefs…",
  "/app/geo": "Search prompts, answers, or sources…",
  "/app/notifications": "Search alerts and activity…",
  "/app/history": "Search actions, content, or people…",
  "/app/settings": "Search settings, APIs, or members…"
};

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  return (
    <DashboardSearchContext.Provider value={search}><div className="dashboard-shell">
      <button className="dashboard-menu" onClick={() => setOpen(!open)} aria-label="Toggle dashboard navigation">{open ? <X /> : <Menu />}</button>
      <aside className={`dashboard-sidebar ${open ? "is-open" : ""}`}>
        <Link className="dashboard-brand" href="/projects" aria-label="LaunchVault projects"><span><Zap size={14} fill="currentColor" /></span><strong>LaunchVault</strong></Link>
        <nav aria-label="Dashboard navigation">
          {nav.map((item) => {
            const exact = item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
            const Icon = item.icon;
            return <Link className={exact ? "active" : ""} href={item.href} key={item.href} onClick={() => setOpen(false)}><Icon size={18} /><span>{item.label}</span>{item.label === "Notifications" && <small className="nav-count">3</small>}</Link>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <Link href="/projects"><ArrowLeft size={18} />Back to dashboard</Link>
        </div>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-search"><Search size={17} /><input aria-label="Search current dashboard" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={searchCopy[pathname] ?? "Search LaunchVault…"} />{search ? <button aria-label="Clear dashboard search" onClick={() => setSearch("")}><X size={13} /></button> : <kbd>Search</kbd>}</div>
          <div className="dashboard-top-actions">
            <div className="workspace-switch" aria-label="Current project"><span className="workspace-mark">LV</span>LaunchVault.ca</div>
            <div className="workspace-switch" aria-label="Illustrative preview date range"><CalendarDays size={16} aria-hidden="true" /><span>May 12, 2025 – May 25, 2025</span><ChevronDown size={14} aria-hidden="true" /></div>
            <Link className="icon-button" href="/app/notifications" aria-label="Notifications"><Bell size={18} /></Link>
            <span className="avatar-button" aria-label="Current account: JD" style={{ cursor: "default" }}>JD</span>
            <ChevronDown size={14} aria-hidden="true" />
          </div>
        </header>
        <main className="dashboard-content">{children}</main>
      </div>
    </div></DashboardSearchContext.Provider>
  );
}

export function DashboardHeader({ eyebrow, title, description, action = "Project settings" }: { eyebrow: string; title: string; description: string; action?: string }) {
  const [showAction, setShowAction] = useState(false);
  const settingsAction = action === "Project settings" || action === "Manage alerts";
  return (
    <div className="dashboard-heading-row">
      <div><span className="dashboard-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p><span className="preview-source"><span />Demo data · LaunchVault.ca</span></div>
      {settingsAction ? <Link className="button button--small" href="/app/settings"><Settings size={16} />{action}</Link> : <button className="button button--small" onClick={() => setShowAction(true)}><Plus size={16} />{action}</button>}
      {showAction && <HeaderActionDialog action={action} onClose={() => setShowAction(false)} />}
    </div>
  );
}

function HeaderActionDialog({ action, onClose }: { action: string; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => { const element = dialog.current; element?.showModal(); return () => element?.close(); }, []);
  const description = action === "Edit profile" ? "LaunchVault.ca is the sample workspace. Profile editing will cover your workspace name, website, industry, and timezone once workspace storage is connected." : action === "Export log" ? "The audit log below contains illustrative activity. Live workspace exports will become available when activity tracking is connected." : action === "Add query" ? "Prompt tracking will let you add the questions your audience asks and follow LaunchVault citations across AI search platforms." : "Create a brief with a topic, audience, and target keywords. The content workflow below lets you preview, review, and organize sample drafts while your workspace is being set up.";
  return <dialog ref={dialog} className="dashboard-detail-dialog" aria-labelledby={id} onCancel={onClose} onClick={(event) => { if (event.target === dialog.current) onClose(); }}><div className="detail-dialog-heading"><div><span>LaunchVault.ca</span><h2 id={id}>{action}</h2></div><button className="detail-close" aria-label="Close action details" onClick={onClose}><X size={19} /></button></div><div className="detail-dialog-body"><p className="detail-summary">{description}</p><p className="detail-demo-note">This workspace currently contains demo content. No live data has been changed.</p></div><div className="detail-dialog-footer"><button className="button button--small" onClick={onClose}>Continue exploring</button><Link className="button button--primary button--small" href="/app/settings" onClick={onClose}>Workspace settings</Link></div></dialog>;
}

export function MetricCard({ label, value, change, detail, icon: Icon, tone = "purple", lowerIsBetter = false }: DashboardPage["metrics"][number]) {
  const normalizedChange = change.trim();
  const isNegative = normalizedChange.startsWith("-") || normalizedChange.startsWith("−");
  const isPositive = normalizedChange.startsWith("+");
  const improves = lowerIsBetter ? isNegative : isPositive;
  const trendColor = isNegative || isPositive ? improves ? "var(--green)" : "var(--red)" : "var(--muted)";
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

function chartColor(label: string, index: number) {
  const palette = ["#6944ff", "#2679ff", "#16b97b", "#ff982b", "#ed487a"];
  if (label === "Errors" || label === "Failed Actions") return "#ef426f";
  if (label === "Approvals") return "#ffa11c";
  if (label === "Reminders" || label === "Organic Traffic" || label === "Publishing") return "#2679ff";
  if (label === "Impressions" || label === "Manual Updates" || label === "Updates") return "#6944ff";
  return palette[index % palette.length];
}

function ChartLegend({ legend }: { legend?: string[] }) {
  return <div className="preview-chart-legend">{legend?.map((label, index) => <span className="chart-key" style={{ "--chart-series-color": chartColor(label, index) } as CSSProperties} key={label}>{label}</span>)}</div>;
}

function ChartRangeSelect({ value, onChange, label }: { value: ChartRange; onChange: (value: ChartRange) => void; label: string }) {
  return <label className="chart-range-select">
    <span className="visually-hidden">Select {label} timeframe</span>
    <select value={value} onChange={(event) => onChange(event.target.value as ChartRange)} aria-label={`Select ${label} timeframe`}>
      {chartRanges.map((range) => <option key={range.value} value={range.value}>{range.label}</option>)}
    </select>
    <ChevronDown size={13} aria-hidden="true" />
  </label>;
}

function PreviewChart({ legend, distribution, chart = "trend", score, range = "30" }: { legend?: string[]; distribution?: number[]; chart?: DashboardPage["sections"][number]["chart"]; score?: DashboardPage["sections"][number]["score"]; range?: ChartRange }) {
  const gradientId = useId();
  const [activeSample, setActiveSample] = useState<{ range: ChartRange; index: number } | null>(null);
  const samples = chartSamples(range);
  const pointCount = samples.length;
  const dates = samples.map((sample) => sample.label);
  const activePoint = activeSample?.range === range && activeSample.index < pointCount ? activeSample.index : null;
  const setActivePoint = (index: number | null) => setActiveSample(index === null ? null : { range, index });
  if (chart === "donut") {
    const labels = legend ?? ["Blog posts", "Guides", "Prompts"];
    const weights = distribution ?? (labels.length === 5 ? [38, 26, 18, 10, 8] : labels.length === 4 ? [38, 26, 22, 14] : [46, 32, 22]);
    return <div className="preview-chart preview-chart--donut" aria-label="Illustrative distribution chart"><div className="donut-layout"><svg className="preview-donut" viewBox="0 0 120 120" role="img" aria-label={`${score?.value ?? "312"} ${score?.label ?? "items"}`}><circle cx="60" cy="60" r="43" fill="none" stroke="#ebe8ff" strokeWidth="16" />{labels.map((label, index) => <circle key={label} cx="60" cy="60" r="43" pathLength="100" fill="none" stroke={chartColor(label, index)} strokeWidth="16" strokeDasharray={`${weights[index] - .4} 100`} strokeDashoffset={-weights.slice(0, index).reduce((a, b) => a + b, 0)} transform="rotate(-90 60 60)" />)}<text x="60" y="57" textAnchor="middle">{score?.value ?? "312"}</text><text x="60" y="72" textAnchor="middle">{score?.label ?? "items"}</text></svg><div className="donut-breakdown">{labels.map((label, index) => <div key={label}><i style={{ background: chartColor(label, index) }} /><span>{label}</span><strong>{weights[index]}%</strong></div>)}</div></div></div>;
  }
  if (chart === "bars") {
    const labels = legend ?? ["Top 3", "Top 4–10", "Top 11–50"];
    const count = pointCount;
    const bars = samples.map(({ sampleIndex: index }) => [Math.round(40 + index * 2.3), Math.round(38 + index * 3.6 + Math.sin(index) * 5), Math.round(60 + index * 5.5 + Math.cos(index) * 6)]);
    return <div className="preview-chart preview-chart--bars" aria-label="Ranking bar chart">
      <ChartLegend legend={labels} />
      <div className="chart-plot-with-scale">
        <div className="chart-y-axis">{[500, 400, 300, 200, 100, 0].map((value) => <span key={value}>{value}</span>)}</div>
        <div className="rankings-bar-plot">
          {bars.map((values, index) => <button key={index} type="button" className="rankings-bar" style={{ height: `${values.reduce((a, b) => a + b, 0) / 5}%` }} onMouseEnter={() => setActivePoint(index)} onMouseLeave={() => setActivePoint(null)} onFocus={() => setActivePoint(index)} onBlur={() => setActivePoint(null)} aria-label={`${samples[index].tooltipLabel}: ${values.map((value, valueIndex) => `${labels[valueIndex]} ${value}`).join(", ")}`}>{values.map((value, valueIndex) => <i key={labels[valueIndex]} style={{ flex: value, background: chartColor(labels[valueIndex], valueIndex) }} />)}</button>)}
          {activePoint !== null && <div className="chart-point-tooltip" style={{ left: `${Math.min(58, activePoint / Math.max(1, count - 1) * 80)}%` }}><strong>{samples[activePoint].tooltipLabel}</strong>{bars[activePoint].map((value, index) => <div key={labels[index]}><i style={{ background: chartColor(labels[index], index) }} /><span>{labels[index]}</span><b>{value}</b></div>)}</div>}
        </div>
      </div>
      <div className="chart-axis chart-axis--scaled"><span>{dates[0]}</span><span>{dates[Math.floor((count - 1) / 2)]}</span><span>{dates[count - 1]}</span></div>
    </div>;
  }
  if (chart === "reliability") {
    return <div className="preview-chart preview-chart--reliability" aria-label="Illustrative automation reliability"><div className="reliability-layout"><svg className="preview-donut" viewBox="0 0 120 120" role="img" aria-label="96 percent reliable"><circle cx="60" cy="60" r="43" fill="none" stroke="#e9edf4" strokeWidth="13" /><circle cx="60" cy="60" r="43" fill="none" stroke="#00bf7a" strokeWidth="13" pathLength="100" strokeDasharray="96 100" transform="rotate(-90 60 60)" /><text x="60" y="57" textAnchor="middle">96%</text><text x="60" y="73" textAnchor="middle">Reliable</text></svg><div className="reliability-metrics">{[{ title: "Successful jobs", value: "187", change: "↑ +12%", color: "#10bb7e" }, { title: "Failed jobs", value: "7", change: "↓ −53%", color: "#f04778" }, { title: "Timeouts", value: "4", change: "↓ −60%", color: "#f8ac24" }, { title: "Sync errors", value: "6", change: "↓ −33%", color: "#8456ff" }].map((item) => <div key={item.title}><i style={{ background: item.color }} /><span>{item.title}</span><strong>{item.value}</strong><small>{item.change}</small></div>)}</div></div></div>;
  }
  const series = (legend ?? ["Organic Traffic", "Impressions", "Impact Score"]).map((label, seriesIndex) => {
    const points = samples.map(({ sampleIndex }, index) => {
      const progress = sampleIndex / 29;
      const x = index / Math.max(1, pointCount - 1) * 700;
      const start = 145 + seriesIndex * 9;
      const growth = Math.max(28, 109 - seriesIndex * 19);
      const y = start - progress * growth + Math.sin(sampleIndex * 1.6 + seriesIndex) * (5 - seriesIndex * .5) + Math.cos(sampleIndex * .7) * 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return { label, color: chartColor(label, seriesIndex), points };
  });
  const scaleMax = legend?.includes("ChatGPT") ? 100 : legend?.includes("Total Alerts") ? 50 : legend?.includes("Publishing") ? 250 : 5000;
  const formatValue = (value: number) => scaleMax === 100 ? `${value}%` : value >= 1000 ? `${value / 1000}K` : `${value}`;
  const pointValues = (point: number) => series.map((item) => ({ label: item.label, color: item.color, value: Math.round((190 - Number(item.points[point].split(",")[1])) / 190 * scaleMax) }));
  return (
    <div className="preview-chart" aria-label="Trend chart">
      <ChartLegend legend={legend} />
      <div className="chart-plot-with-scale"><div className="chart-y-axis">{[1, .8, .6, .4, .2, 0].map((step) => <span key={step}>{formatValue(scaleMax * step)}</span>)}</div><div className="preview-chart-art">
        <div className="chart-grid-lines" />
        <svg viewBox="0 0 700 190" preserveAspectRatio="none" role="group" aria-label={`Illustrative trends for ${series.map((item) => item.label).join(", ")}`}>
          <defs><linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor={series[0].color} stopOpacity=".12" /><stop offset="1" stopColor={series[0].color} stopOpacity="0" /></linearGradient></defs>
          <polygon points={`0,190 ${series[0].points.join(" ")} 700,190`} fill={`url(#${gradientId})`} />
          {series.map((item) => <g key={item.label}><polyline points={item.points.join(" ")} fill="none" stroke={item.color} strokeWidth="2" vectorEffect="non-scaling-stroke" /></g>)}
          {Array.from({ length: pointCount }, (_, index) => <g key={index} tabIndex={0} role="button" aria-label={`${samples[index].tooltipLabel}: ${pointValues(index).map((item) => `${item.label} ${item.value}${scaleMax === 100 ? " percent" : ""}`).join(", ")}`} onFocus={() => setActivePoint(index)} onBlur={() => setActivePoint(null)} onMouseEnter={() => setActivePoint(index)} onMouseLeave={() => setActivePoint(null)} onKeyDown={(event) => { if (event.key === "Escape") setActivePoint(null); }}><rect {...chartHitArea(index, pointCount)} y="0" height="190" fill="transparent" />{activePoint === index && <line x1={index * 700 / Math.max(1, pointCount - 1)} x2={index * 700 / Math.max(1, pointCount - 1)} y1="0" y2="190" stroke="#aeb7d6" strokeDasharray="3 4" vectorEffect="non-scaling-stroke" />}</g>)}
        </svg>
        {series.flatMap((item) => item.points.map((point, index) => { const [x, y] = point.split(",").map(Number); return <span className="chart-dot" aria-hidden="true" key={`${item.label}-${index}`} style={{ left: `${x / 700 * 100}%`, top: `${y / 190 * 100}%`, background: item.color }} />; }))}
        {activePoint !== null && <div className="chart-point-tooltip" style={{ left: `${Math.min(65, activePoint / Math.max(1, pointCount - 1) * 85)}%` }}><strong>{samples[activePoint].tooltipLabel}</strong>{pointValues(activePoint).map((item) => <div key={item.label}><i style={{ background: item.color }} /><span>{item.label}</span><b>{item.value.toLocaleString()}{scaleMax === 100 ? "%" : ""}</b></div>)}</div>}
      </div></div>
      <div className="chart-axis chart-axis--scaled"><span>{dates[0]}</span><span>{dates[Math.floor((pointCount - 1) / 2)]}</span><span>{dates[pointCount - 1]}</span></div>
    </div>
  );
}

function PreviewRows({ rows, compact = false, ranked = false, onPreview }: { rows?: DashboardPage["sections"][number]["rows"]; compact?: boolean; ranked?: boolean; onPreview?: (row: DashboardRow) => void }) {
  return <div className={compact ? "preview-table-body" : "preview-feed"}>{rows?.map((row, index) => <article className="preview-row" key={`${row.title}-${index}`}>
    <span className={`${ranked || row.rank ? "row-rank" : "row-mark"} row-mark--${row.tone ?? "purple"}`}>{ranked || row.rank ? row.rank ?? index + 1 : null}</span>
    <div>{row.kicker && <span className="row-kicker">{row.kicker}</span>}<strong>{row.title}</strong><small>{row.meta}</small></div>
    <div className="row-tail">{onPreview && ["View", "Review", "Resolve"].includes(row.status) ? <button className="feed-action" onClick={() => onPreview(row)}>{row.status}</button> : <span className={`status-pill status-pill--${row.tone ?? "purple"}`}>{row.status}</span>}{row.action && <button className="row-action" onClick={() => onPreview?.(row)}>{row.action}</button>}</div>
  </article>)}</div>;
}

type ContentDialogView = "preview" | "metadata" | "publish";

function contentSlug(title: string) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 68) || "launchvault-content";
}

function DetailDialog({ row, columns, action, onClose, onUpdate, onRemove }: { row: DashboardRow; columns?: string[]; action: string; onClose: () => void; onUpdate: (status: string) => void; onRemove: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [activeView, setActiveView] = useState<ContentDialogView>(action === "Publish" ? "publish" : "preview");
  const [template, setTemplate] = useState("Guides · Learning article");
  const [schedule, setSchedule] = useState("Publish now (demo)");
  const [revision, setRevision] = useState(0);
  const [seoTitle, setSeoTitle] = useState(`${row.title} | LaunchVault`);
  const [descriptionOverride, setDescriptionOverride] = useState<string | null>(null);
  const [slug, setSlug] = useState(contentSlug(row.title));
  const [archiveConfirmation, setArchiveConfirmation] = useState(false);
  const [localNotice, setLocalNotice] = useState("");
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  useEffect(() => {
    setActiveView(action === "Publish" ? "publish" : "preview");
  }, [action]);
  const isActivity = columns?.includes("Date & Time") || action === "Details";
  const cellFor = (heading: string) => {
    const index = columns?.findIndex((column) => column.toLowerCase() === heading.toLowerCase()) ?? -1;
    return index >= 0 ? row.cells?.[index]?.value : undefined;
  };
  const category = cellFor("Topic") ?? row.category ?? "Guides";
  const keyword = cellFor("Target Keywords") ?? (row.meta.replace(/ · .*$/, "") || "learn AI");
  const seoScore = cellFor("SEO Score") ?? (row.status.match(/^\d+$/) ? row.status : "84");
  const impactScore = cellFor("Impact Score") ?? (row.status.match(/^\d+$/) ? row.status : "78");
  const status = cellFor("Status") ?? row.status;
  const pathPrefix = template.startsWith("Blog") ? "blog" : template.startsWith("Resources") ? "resources" : "guides";
  const targetUrl = `launchvault.ca/${pathPrefix}/${slug}`;
  const metaDescription = descriptionOverride ?? `Learn ${keyword} with practical examples, a reusable prompt, and a clear review checklist. Build useful AI skills with LaunchVault.`;
  const reviewChecks = [
    { label: "SEO title within 60 characters", ready: seoTitle.trim().length > 0 && seoTitle.length <= 60 },
    { label: "Description within 160 characters", ready: metaDescription.trim().length > 0 && metaDescription.length <= 160 },
    { label: "Destination slug is valid", ready: /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) },
    { label: "Page template selected", ready: Boolean(template) },
    { label: "Article and FAQ included", ready: true }
  ];
  const regenerate = () => {
    const next = revision + 1;
    setRevision(next);
    setSeoTitle(next % 2 ? `${row.title}: A Practical Guide` : `${row.title} | LaunchVault`);
    setDescriptionOverride(next % 2 ? `Get started with ${keyword}. Follow a worked example, adapt the prompt to your task, and review the result with LaunchVault’s step-by-step guide.` : `Make ${keyword} part of your routine. Explore a practical example, a reusable prompt, and a checklist for clear, accurate results.`);
    setLocalNotice(`Sample version ${next + 1} is ready. The introduction, prompt, and metadata have changed.`);
  };
  const statusLabel = status === "Published" ? "Published" : status === "In Review" ? "Ready for review" : status === "In Queue" ? "Draft" : status;
  const updateAndClose = (nextStatus: string) => {
    onUpdate(nextStatus);
    onClose();
  };
  const tabs: { id: ContentDialogView; label: string; icon: typeof Monitor }[] = [
    { id: "preview", label: "Page preview", icon: Monitor },
    { id: "metadata", label: "SEO & metadata", icon: BadgeCheck },
    { id: "publish", label: "Publish setup", icon: LayoutTemplate }
  ];
  return <dialog className="dashboard-detail-dialog" ref={dialog} aria-labelledby={titleId} onCancel={onClose} onClick={(event) => { if (event.target === dialog.current) onClose(); }}>
    <div className="detail-dialog-heading detail-dialog-heading--rich"><div><span>LaunchVault.ca · CMS template simulation</span><h2 id={titleId}>{isActivity ? "Activity details" : action === "Publish" ? "Publish content" : "Content details"}</h2></div><div className="detail-heading-actions"><span className="detail-demo-badge"><ShieldCheck size={13} />Local demo</span><button className="detail-close" onClick={onClose} aria-label="Close details"><X size={19} /></button></div></div>
    <div className="detail-dialog-body detail-dialog-body--rich">
      <div className="detail-content-title detail-content-title--rich"><span className="detail-document-icon"><FileText size={24} /></span><div><div className="detail-title-line"><h3>{row.title}</h3><span className={`status-pill status-pill--${status === "Published" ? "green" : row.tone ?? "purple"}`}>{statusLabel}</span></div><p>{category} · {keyword}</p></div></div>
      {isActivity ? <>
        {row.cells ? <dl className="detail-facts">{row.cells.map((cell, index) => <div key={`${columns?.[index]}-${index}`}><dt>{columns?.[index] ?? "Detail"}</dt><dd>{cell.value}</dd></div>)}</dl> : <p className="detail-summary">{row.meta}</p>}
        <article className="detail-activity-note"><span><ShieldCheck size={16} />Demo activity record</span><p>This is a presentation-only timeline entry. It does not expose a connected CMS, event stream, or user data.</p></article>
      </> : <>
        <div className="detail-tab-list" role="tablist" aria-label="Content review views">
          {tabs.map((tab, index) => { const Icon = tab.icon; return <button key={tab.id} id={`${titleId}-tab-${tab.id}`} role="tab" aria-controls={`${titleId}-panel-${tab.id}`} aria-selected={activeView === tab.id} tabIndex={activeView === tab.id ? 0 : -1} className={activeView === tab.id ? "active" : ""} onClick={() => setActiveView(tab.id)} onKeyDown={event => {
            const next = event.key === "ArrowRight" ? (index + 1) % tabs.length : event.key === "ArrowLeft" ? (index + tabs.length - 1) % tabs.length : event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : null;
            if (next === null) return;
            event.preventDefault();
            setActiveView(tabs[next].id);
            (event.currentTarget.parentElement?.children[next] as HTMLButtonElement)?.focus();
          }}><Icon size={15} />{tab.label}</button>; })}
        </div>

        {activeView === "preview" && <section className="detail-content-preview" role="tabpanel" id={`${titleId}-panel-preview`} aria-labelledby={`${titleId}-tab-preview`}>
          <div className="detail-preview-toolbar"><span className="detail-browser-dots"><i /><i /><i /></span><span><ShieldCheck size={13} />Template simulation · no CMS connection used</span><button onClick={() => setActiveView("publish")}>Open publish setup <ChevronRight size={14} /></button></div>
          <ContentTemplatePreview title={row.title} category={category} topic={keyword} template={template} revision={revision} id={titleId} />
          <div className="detail-preview-footer"><span><Monitor size={14} />Desktop template · {template}</span><button onClick={() => setActiveView("metadata")}><ExternalLink size={14} />Review search preview</button></div>
        </section>}

        {activeView === "metadata" && <section className="detail-metadata-view" role="tabpanel" id={`${titleId}-panel-metadata`} aria-labelledby={`${titleId}-tab-metadata`}>
          <div className="detail-view-heading"><div><span>Search presentation</span><h4>Metadata ready for review</h4><p>Edit the fields to update the search preview. Changes last while this review is open.</p></div><button className="detail-subtle-button" onClick={regenerate}><RefreshCw size={14} />Regenerate sample</button></div>
          <div className="detail-serp-preview"><span>Google preview · illustrative</span><small>https://{targetUrl}</small><strong>{seoTitle}</strong><p>{metaDescription}</p></div>
          <div className="detail-meta-grid">
            <label><span>SEO title <em className={seoTitle.length > 60 ? "is-over-limit" : ""}>{seoTitle.length} / 60</em></span><input aria-label="SEO title" value={seoTitle} onChange={event => setSeoTitle(event.target.value)} /></label>
            <label><span>URL slug</span><div className="detail-input-prefix"><b>/{pathPrefix}/</b><input aria-label="URL slug" value={slug} onChange={event => setSlug(event.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"))} /></div></label>
            <label className="detail-meta-grid--wide"><span>Meta description <em className={metaDescription.length > 160 ? "is-over-limit" : ""}>{metaDescription.length} / 160</em></span><textarea aria-label="Meta description" value={metaDescription} onChange={event => setDescriptionOverride(event.target.value)} /></label>
          </div>
          <div className="detail-quality-grid"><article><BadgeCheck size={17} /><div><strong>Search intent</strong><span>Informational · sample SEO score</span></div><b>{seoScore}/100</b></article><article><BadgeCheck size={17} /><div><strong>Content impact</strong><span>Learning resource · sample score</span></div><b>{impactScore}/100</b></article><article><BadgeCheck size={17} /><div><strong>Content structure</strong><span>Article with FAQ and review checklist</span></div><b>Preview</b></article><article><BadgeCheck size={17} /><div><strong>Article navigation</strong><span>3 shortcuts to learning sections</span></div><b>3</b></article></div>
        </section>}

        {activeView === "publish" && <section className="detail-publish-view" role="tabpanel" id={`${titleId}-panel-publish`} aria-labelledby={`${titleId}-tab-publish`}>
          <div className="detail-view-heading"><div><span>Destination & delivery</span><h4>Review the final publishing snapshot</h4><p>This is a local template preview only. A CMS destination has not been verified or contacted.</p></div><span className="detail-connection-state"><span />Preview only</span></div>
          <div className="detail-publish-snapshot"><div className="detail-snapshot-cover">LV</div><div><span>{category} · Sample version {revision + 1}</span><h4>{row.title}</h4><p>{metaDescription}</p><button className="detail-subtle-button" onClick={() => setActiveView("preview")}><Monitor size={14} />Review full page</button></div></div>
          <div className="detail-publish-grid">
            <div className="detail-publish-form">
              <label><span>CMS template</span><select aria-label="CMS template" value={template} onChange={event => setTemplate(event.target.value)}><option>Guides · Learning article</option><option>Blog · Article with FAQ</option><option>Resources · Tutorial layout</option></select></label>
              <label><span>Delivery timing</span><select aria-label="Delivery timing" value={schedule} onChange={event => setSchedule(event.target.value)}><option>Publish now (demo)</option><option>Schedule · Tomorrow, 9:00 AM</option><option>Schedule · Next Monday, 10:00 AM</option></select></label>
              <label><span>Destination path</span><div className="detail-readonly-url"><Globe2 size={15} /><span>{targetUrl}</span></div></label>
              <div className="detail-publish-destination"><LayoutTemplate size={18} /><div><strong>LaunchVault content collection</strong><span>{template}</span></div><small>Not verified</small></div>
            </div>
            <aside className="detail-publish-checklist"><div><span>Content review checks</span><b>{reviewChecks.filter(item => item.ready).length} / {reviewChecks.length}</b></div>{reviewChecks.map(item => <p key={item.label} className={item.ready ? "" : "needs-review"}>{item.ready ? <Check size={15} /> : <Eye size={15} />}{item.label}</p>)}</aside>
          </div>
          {archiveConfirmation ? <div className="detail-archive-confirm" role="alert"><div><Trash2 size={17} /><span><strong>Remove this draft from the local demo?</strong><small>The row disappears from this screen only. Reloading restores the sample data.</small></span></div><div><button className="detail-subtle-button" onClick={() => setArchiveConfirmation(false)}>Keep draft</button><button className="button button--small detail-reject" onClick={() => { onRemove(); onClose(); }}>Remove from demo</button></div></div> : <div className="detail-publish-actions"><button className="detail-subtle-button" onClick={regenerate}><RefreshCw size={14} />Regenerate sample</button><button className="detail-subtle-button" onClick={() => setArchiveConfirmation(true)}><Trash2 size={14} />Remove draft</button><button className="detail-subtle-button" onClick={() => { setSchedule("Schedule · Tomorrow, 9:00 AM"); setLocalNotice("A review schedule was prepared in this local preview."); }}><CalendarClock size={14} />Schedule review</button></div>}
        </section>}
      </>}
      {localNotice && <p className="detail-local-notice" role="status"><Check size={14} />{localNotice}</p>}
      <p className="detail-demo-note">Illustrative sample content only. These controls do not read, write, publish, schedule, or remove content in any connected service.</p>
    </div><div className="detail-dialog-footer detail-dialog-footer--rich"><span><ShieldCheck size={14} />Local workspace preview</span><div><button className="button button--small" onClick={onClose}>Close</button>{!isActivity && action === "Reject" && <button className="button button--small detail-reject" onClick={() => updateAndClose("Rejected")}>Reject in demo</button>}{!isActivity && action !== "Reject" && <button className="button button--primary button--small" onClick={() => updateAndClose(schedule.startsWith("Schedule") ? "Scheduled" : "Published")}>{schedule.startsWith("Schedule") ? "Schedule in demo" : "Publish in demo"}</button>}</div></div>
  </dialog>;
}

function DataTable({ title, columns, rows, ranked, area, onPreview }: { title: string; columns?: string[]; rows: DashboardRow[]; ranked: boolean; area?: string; onPreview: (row: DashboardRow, action?: string) => void }) {
  const headings = columns ?? ["Title", "Details", "Status"];
  const hasActions = headings[headings.length - 1] === "Actions";
  return <div className={`dashboard-data-table-wrap ${headings.length > 4 ? "dashboard-data-table-wrap--wide" : ""}`} tabIndex={0} role="region" aria-label={`${title} table`}><table className={`dashboard-data-table ${area ? `dashboard-data-table--${area}` : ""}`}>
    <thead><tr>{ranked && <th scope="col" className="data-rank">#</th>}{headings.map((heading) => <th scope="col" key={heading}>{heading}</th>)}</tr></thead>
    <tbody>{rows.map((row, index) => {
      const cells = row.cells ?? [{ value: row.title }, { value: row.meta }, { value: row.status, kind: "status" as const, tone: row.tone }];
      return <tr key={row.title}>{ranked && <td className="data-rank"><span>{row.rank ?? index + 1}</span></td>}{cells.map((cell, cellIndex) => <td key={`${row.title}-${cellIndex}`} className={`${cellIndex === 0 ? "data-title" : ""} ${cell.kind === "score" ? "data-score" : ""}`}>{cell.kind === "score" || cell.kind === "status" ? <span className={`status-pill status-pill--${cell.tone ?? row.tone ?? "purple"}`}>{cell.value}</span> : cellIndex === 0 && hasActions ? <button className="data-title-button" onClick={() => onPreview(row)}>{cell.value}</button> : cell.value}</td>)}{hasActions && <td className="data-actions"><div><button onClick={() => onPreview(row, row.action === "Details" ? "Details" : "Preview")} aria-label={`${row.action === "Details" ? "Details for" : "Preview"} ${row.title}`}><Eye size={12} /><span>{row.action === "Manage" ? "Manage" : row.action === "Details" ? "Details" : "Preview"}</span></button>{row.action === "Review" && <><button className="data-publish" onClick={() => onPreview(row, "Publish")} aria-label={`Publish ${row.title}`}><Download size={12} /><span>Publish</span></button><button className="data-reject" onClick={() => onPreview(row, "Reject")} aria-label={`Reject ${row.title}`}><Trash2 size={12} /><span>Reject</span></button></>}</div></td>}</tr>;
    })}{rows.length === 0 && <tr><td className="data-empty" colSpan={headings.length + (ranked ? 1 : 0)}><Search size={22} /><strong>No matching content</strong><span>Try another search or filter.</span></td></tr>}</tbody>
  </table></div>;
}

function SummaryGrid({ stats }: { stats?: DashboardPage["sections"][number]["stats"] }) {
  return <div className="summary-stat-grid">{stats?.map((stat) => <article className={`summary-stat summary-stat--${stat.tone ?? "purple"}`} key={stat.label}><span>{stat.label}</span><strong>{stat.value}</strong>{stat.change && <small>{stat.change}</small>}</article>)}</div>;
}

function FunnelPreview({ stats, score }: { stats?: DashboardPage["sections"][number]["stats"]; score?: DashboardPage["sections"][number]["score"] }) {
  return <div className="funnel-preview"><div className="funnel-stages">{stats?.map((stat, index) => <article key={stat.label}><span>{index + 1}</span><p>{stat.label}</p><strong>{stat.value}</strong></article>)}</div><div className="funnel-total"><span>{score?.value}</span><small>{score?.label}</small></div></div>;
}

function AnswerPreview({ rows }: { rows?: DashboardPage["sections"][number]["rows"] }) {
  const [answer, ...sources] = rows ?? [];
  if (!answer) return null;
  return <div className="answer-preview"><div className="answer-query"><Search size={16} /><strong>{answer.title}</strong></div><article className="answer-card"><span className="answer-spark"><Sparkles size={18} /></span><div><span className="row-kicker">{answer.kicker ?? "AI overview"}</span><p>{answer.meta}</p><span className={`status-pill status-pill--${answer.tone ?? "green"}`}>{answer.status}</span></div></article><div className="answer-sources">{sources.map((source, index) => <span key={source.title}><b>{index + 1}</b>{source.title}<small>{source.status}</small></span>)}</div></div>;
}

function HealthPreview({ rows, score }: { rows?: DashboardPage["sections"][number]["rows"]; score?: DashboardPage["sections"][number]["score"] }) {
  return <div className="health-preview"><div className={`health-score health-score--${score?.tone ?? "green"}`}><strong>{score?.value}</strong><span>{score?.label}</span></div><PreviewRows rows={rows} compact /></div>;
}

export function DashboardSection({ area, title, description, icon: Icon, kind, variant = "standard", chart, span, meta, legend, distribution, rows, columns, steps, stats, tabs, score }: DashboardPage["sections"][number]) {
  const globalSearch = useContext(DashboardSearchContext);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [activeTab, setActiveTab] = useState(tabs?.find((tab) => tab.active)?.label ?? "All");
  const [localRows, setLocalRows] = useState(rows ?? []);
  const [selected, setSelected] = useState<{ row: DashboardRow; action: string } | null>(null);
  const [notice, setNotice] = useState("");
  const [chartRange, setChartRange] = useState<ChartRange>("30");
  const matchesTab = (row: DashboardRow, label: string) => /^all/i.test(label) || label === "Unread" || row.status === label || row.category === label;
  const visibleRows = localRows.filter((row) => {
    const content = [row.title, row.meta, row.status, row.category, ...(row.cells?.map((cell) => cell.value) ?? [])].join(" ").toLowerCase();
    return content.includes(query.toLowerCase()) && content.includes(globalSearch.toLowerCase()) && (status === "All statuses" || row.status === status) && matchesTab(row, activeTab);
  });
  const isSearchable = kind === "table" && (variant === "library" || variant === "audit");
  const previewRow = (row: DashboardRow, action = "Preview") => setSelected({ row, action });
  const supportsTimeRange = kind === "chart" && chart !== "donut" && chart !== "reliability";
  const context = meta ?? (kind === "chart" ? "Last 30 days" : kind === "table" ? "View all →" : kind === "flow" ? "How it works" : "LaunchVault.ca");
  const spanClass = span === "wide" ? "dashboard-panel--wide" : span ? `dashboard-panel--span-${span}` : "";
  return (
    <section className={`dashboard-panel dashboard-panel--${kind} dashboard-panel--${variant} ${area ? `dashboard-panel--${area}` : ""} ${spanClass}`}>
      <div className="panel-heading"><div><span className="panel-icon"><Icon size={18} /></span><h2>{title}</h2></div>{supportsTimeRange ? <ChartRangeSelect value={chartRange} onChange={setChartRange} label={title} /> : <span className="panel-meta">{context}</span>}</div>
      {isSearchable && <div className="dashboard-table-tools"><label className="dashboard-table-search"><Search size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={variant === "audit" ? "Search actions, content, or users…" : "Search content…"} aria-label={`Search ${title}`} />{query && <button aria-label={`Clear ${title} search`} onClick={() => setQuery("")}><X size={12} /></button>}</label><label className="dashboard-table-filter"><span className="visually-hidden">Filter {title} by status</span><select value={status} onChange={(event) => setStatus(event.target.value)} aria-label={`Filter ${title} by status`}><option>All statuses</option>{Array.from(new Set(localRows.map((row) => row.status))).map((value) => <option key={value}>{value}</option>)}</select></label><span className="dashboard-table-count">{visibleRows.length} {visibleRows.length === 1 ? "item" : "items"}</span></div>}
      {tabs && <div className="panel-tabs" role="group" aria-label={`Filter ${title}`}>{tabs.map((tab) => <button className={activeTab === tab.label ? "active" : ""} aria-pressed={activeTab === tab.label} onClick={() => setActiveTab(tab.label)} key={tab.label}>{tab.label}<small>{localRows.filter((row) => matchesTab(row, tab.label)).length}</small></button>)}</div>}
      {kind === "chart" && <><PreviewChart legend={legend} distribution={distribution} chart={chart} score={score} range={chartRange} /><p className="panel-description">{description}</p></>}
      {kind === "flow" && <><div className="empty-flow">{steps?.map((step, index) => { const StepIcon = [Link2, FileText, Search, Upload][index % 4]; return <div key={step.label}><span className={`flow-step-icon flow-step-icon--${index}`}><StepIcon size={24} aria-hidden="true" /></span><strong>{step.label}</strong><small>{step.copy}</small></div>; })}</div><p className="flow-description">{description}</p></>}
      {kind === "table" && <><DataTable title={title} columns={columns} rows={visibleRows} ranked={variant === "ranked"} area={area} onPreview={previewRow} /><p className="panel-description">{description}</p></>}
      {kind === "feed" && <><PreviewRows rows={visibleRows} ranked={variant === "ranked"} onPreview={previewRow} />{visibleRows.length === 0 && <div className="feed-empty">No matching activity. Try another filter.</div>}<p className="panel-description">{description}</p></>}
      {kind === "summary" && <><SummaryGrid stats={stats} /><p className="panel-description">{description}</p></>}
      {kind === "funnel" && <><FunnelPreview stats={stats} score={score} /><p className="panel-description">{description}</p></>}
      {kind === "answer" && <><AnswerPreview rows={rows} /><p className="panel-description">{description}</p></>}
      {kind === "health" && <><HealthPreview rows={rows} score={score} /><p className="panel-description">{description}</p></>}
      {notice && <p className="dashboard-local-notice" role="status"><Check size={13} />{notice}</p>}
      {selected && <DetailDialog row={selected.row} columns={columns} action={selected.action} onClose={() => setSelected(null)} onRemove={() => {
        setLocalRows((current) => current.filter((row) => row.title !== selected.row.title));
        setNotice(`${selected.row.title} removed from this local demo.`);
      }} onUpdate={(newStatus) => {
        setLocalRows((current) => current.map((row) => row.title === selected.row.title ? { ...row, status: newStatus, tone: newStatus === "Rejected" ? "red" : "green", cells: row.cells?.map((cell) => cell.kind === "status" ? { ...cell, value: newStatus, tone: newStatus === "Rejected" ? "red" : "green" } : cell) } : row));
        setNotice(`${selected.row.title} marked ${newStatus.toLowerCase()} in this demo.`);
      }} />}
    </section>
  );
}

export const EmptySection = DashboardSection;
