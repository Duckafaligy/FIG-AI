"use client";
import Link from "next/link";
import { applyOverlay, type Overlay } from "@/lib/live";
import { dashboardPages } from "@/lib/dashboard-pages";
import { LiveTrendChart, MetricCard, useDashboardSearch } from "./dashboard-shell";
import { ServiceUnavailable } from "./service-unavailable";

export function LiveDashboardPage({ page, overlay }: { page: keyof typeof dashboardPages; overlay: Overlay | null }) {
  const search = useDashboardSearch().trim().toLowerCase();
  if (!overlay) return <ServiceUnavailable />;
  const data = applyOverlay(dashboardPages[page], overlay);
  return <div className={`dashboard-page dashboard-page--${data.layout}`}>
    <div className="dashboard-heading-row"><div><span className="dashboard-eyebrow">{data.eyebrow}</span><h1>{data.title}</h1><p>{overlay.projectName || "Your workspace"} · Data from your connected services</p></div><Link className="button" href="/app/library">Open library</Link></div>
    <div className={`metric-grid metric-grid--${data.layout}`}>{data.metrics.map(metric => <MetricCard {...metric} key={metric.label} />)}</div>
    <div className={`dashboard-grid dashboard-grid--${data.layout}`}>
      {data.sections.map(section => {
        section = { ...section, rows: section.rows?.filter(row => !search || [row.title, row.meta, row.status].join(" ").toLowerCase().includes(search)) };
        const Icon = section.icon;
        const hasRows = Boolean(section.rows?.length);
        const hasStats = Boolean(section.stats?.length);
        const spanClass = section.span === "wide" ? "dashboard-panel--wide" : section.span ? `dashboard-panel--span-${section.span}` : "";
        return <section key={section.title} className={`dashboard-panel dashboard-panel--${section.kind} dashboard-panel--${section.variant ?? "standard"} ${section.area ? `dashboard-panel--${section.area}` : ""} ${spanClass}`}>
          <div className="panel-heading"><div><span className="panel-icon"><Icon size={18} /></span><h2>{section.title}</h2></div></div>
          {section.liveChart ? <LiveTrendChart data={section.liveChart} /> : <>
            {section.score && <p><strong>{section.score.value}</strong> {section.score.label}</p>}
            {hasStats && <div className="summary-stat-grid">{section.stats!.map(stat => <article className="summary-stat" key={stat.label}><span>{stat.label}</span><strong>{stat.value}</strong>{stat.change && <small>{stat.change}</small>}</article>)}</div>}
            {hasRows && <div className="live-record-list">{section.rows!.map((row, index) => <article key={index}><div><strong>{row.title}</strong>{row.meta && <p>{row.meta}</p>}{row.kicker && <small>{row.kicker}</small>}</div><span>{row.status}</span></article>)}</div>}
            {!hasRows && !hasStats && !section.score && <div className="feed-empty">No recorded data for this section yet.</div>}
          </>}
        </section>;
      })}
    </div>
  </div>;
}
