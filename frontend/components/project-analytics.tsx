"use client";
import Link from "next/link";
import { BarChart3, Clock, MousePointerClick, Users } from "lucide-react";
import type { ApiAnalyticsPage } from "@/lib/api";
import { LiveTrendChart, MetricCard } from "./dashboard-shell";
import styles from "./project-analytics.module.css";

const ICONS = { Sessions: Users, "Avg. engagement time": Clock, "Bounce rate": MousePointerClick, "Engaged sessions": BarChart3 };
const LAYER_LABEL: Record<string, string> = { craft: "Craft", structure: "Structure", search: "Search", answers: "Answers" };

type PageFinding = { check: string; layer: string; summary: string };

/** One chip per layer, in layer order, so a page with twelve findings stays one line. */
function byLayer(findings: PageFinding[]): [string, PageFinding[]][] {
  const groups = new Map<string, PageFinding[]>();
  for (const f of findings) groups.set(f.layer, [...(groups.get(f.layer) ?? []), f]);
  const order = Object.keys(LAYER_LABEL);
  return [...groups].sort(([a], [b]) => (order.indexOf(a) + 1 || 99) - (order.indexOf(b) + 1 || 99));
}

/** One project's Google Analytics next to what FIG found on each landing
 *  page. Unknown stays a dash; nothing is estimated (app/pages.py:analytics). */
export function ProjectAnalytics({ data }: { data: ApiAnalyticsPage }) {
  const project = data.project;
  const settings = project ? `/projects/${encodeURIComponent(project.hostname)}/settings` : "/projects";
  const sessions = data.detail ? data.kpis?.find((k) => k.label === "Sessions")?.value : null;
  const heading = <div className="dashboard-heading-row"><div>
    <span className="dashboard-eyebrow">Analytics</span>
    <h1>{sessions ? `${sessions} sessions in the last 30 days` : "Analytics"}</h1>
    <p>{project?.name ?? "This project"} · Google Analytics 4{data.property ? ` · ${data.property}` : ""}</p>
  </div></div>;

  if (!data.detail) {
    const [title, body, action] = !data.connected
      ? ["Google Analytics isn’t connected", "Connect it and this page shows sessions per day, the pages people land on, and where they come from, next to what FIG found on each page.", "Connect Google Analytics"]
      : !data.property
        ? ["Choose this project’s Analytics property", "Google Analytics is connected, but no property is picked for this project yet, so there’s nothing to read.", "Choose a property"]
        : ["Google Analytics didn’t answer", "The report request failed, so nothing is shown rather than an estimate. Reconnecting usually fixes an expired token.", "Check the connection"];
    return <div className="dashboard-page">{heading}
      <section className={`dashboard-panel ${styles.empty}`}><h2>{title}</h2><p>{body}</p><Link className="button" href={settings}>{action}</Link></section>
    </div>;
  }

  const { chart, pages, channels, scanned } = data.detail;
  const top = Math.max(1, ...channels.map((c) => c.sessions));
  return <div className="dashboard-page">{heading}
    <div className={`metric-grid ${styles.metrics}`}>
      {(data.kpis ?? []).map((k) => <MetricCard key={k.label} label={k.label} value={k.value ?? "—"}
        change={k.delta === null ? "—" : `${k.delta > 0 ? "+" : ""}${k.delta}%`} detail="vs the 30 days before"
        icon={ICONS[k.label as keyof typeof ICONS] ?? BarChart3} tone="green" lowerIsBetter={k.label === "Bounce rate"} />)}
    </div>
    <div className="dashboard-grid">
      <section className={`dashboard-panel ${styles.full}`}>
        <div className="panel-heading"><div><span className="panel-icon"><BarChart3 size={18} /></span><h2>Sessions per day</h2></div></div>
        {chart.lines.length ? <LiveTrendChart data={chart} /> : <div className="feed-empty">No sessions recorded in the last 60 days.</div>}
      </section>
      <section className={`dashboard-panel ${styles.wide}`}>
        <div className="panel-heading"><div><h2>Busiest pages, with what FIG found on them</h2></div></div>
        <p className={styles.note}>Fix what people land on first. Sessions from Analytics{scanned ? ", findings from the latest scan." : "; run a scan to see findings per page."}</p>
        {pages.length ? <table className={styles.table}>
          <thead><tr><th>Landing page</th><th>Sessions</th><th>Engaged</th><th>Findings</th></tr></thead>
          <tbody>{pages.map((p) => <tr key={p.path}>
            <td className={styles.path}>{p.path}</td><td>{p.sessions.toLocaleString()}</td><td>{p.engaged}%</td>
            <td>{!scanned ? "—" : p.findings.length ? <span className={styles.chips}>{byLayer(p.findings).map(([layer, list]) =>
              <span key={layer} className={`${styles.chip} ${styles[layer] ?? ""}`} title={list.map((f) => f.summary).join("\n")}>{LAYER_LABEL[layer] ?? layer} {list.length}</span>)}</span> : "0"}</td>
          </tr>)}</tbody>
        </table> : <div className="feed-empty">No landing pages recorded in the last 30 days.</div>}
      </section>
      <section className={`dashboard-panel ${styles.side}`}>
        <div className="panel-heading"><div><h2>Where visits come from</h2></div></div>
        {channels.length ? <ul className={styles.channels}>{channels.map((c) => <li key={c.name}>
          <div><span>{c.name}</span><b>{c.sessions.toLocaleString()} · {c.share}%</b></div>
          <i><em style={{ width: `${(c.sessions / top) * 100}%` }} /></i>
        </li>)}</ul> : <div className="feed-empty">No sessions in the last 30 days.</div>}
      </section>
    </div>
  </div>;
}
