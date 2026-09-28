import Link from "next/link";
import type { ApiAnalyticsPage } from "@/lib/api";
import { FigLineChart } from "./fig-line-chart";
import styles from "./project-page.module.css";

const LAYER_LABEL: Record<string, string> = { craft: "Craft", structure: "Structure", search: "Search", answers: "Answers" };
const fmtDay = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

type PageFinding = { check: string; layer: string; summary: string };

/** One tag per layer, in layer order, so a page with a dozen findings stays one line. */
function byLayer(findings: PageFinding[]): [string, PageFinding[]][] {
  const groups = new Map<string, PageFinding[]>();
  for (const f of findings) groups.set(f.layer, [...(groups.get(f.layer) ?? []), f]);
  const order = Object.keys(LAYER_LABEL);
  return [...groups].sort(([a], [b]) => (order.indexOf(a) + 1 || 99) - (order.indexOf(b) + 1 || 99));
}

/** One project's Google Analytics next to what FIG found on each landing
 *  page (Paper 2c.4). Unknown stays a dash; nothing is estimated
 *  (app/pages.py:analytics). */
export function ProjectAnalytics({ data }: { data: ApiAnalyticsPage }) {
  const project = data.project;
  const settings = project ? `/projects/${encodeURIComponent(project.hostname)}/settings` : "/projects";
  const sessions = data.detail ? data.kpis?.find((k) => k.label === "Sessions")?.value : null;
  const head = <header className={styles.head}><div>
    <span className={styles.eyebrow}>{project?.name ?? "Project"} · Analytics</span>
    <h1>{sessions ? `${sessions} sessions in the last 30 days.` : "Analytics"}</h1>
    <p>From Google Analytics 4{data.property ? `, ${data.property}` : ""}. Last 30 days against the 30 before.</p>
  </div></header>;

  if (!data.detail) {
    const [title, body, action] = !data.connected
      ? ["Google Analytics isn’t connected", "Connect it and this page shows sessions per day, the pages people land on and where they come from, next to what FIG found on each page.", "Connect Google Analytics"]
      : !data.property
        ? ["Choose this project’s Analytics property", "Google Analytics is connected, but no property is picked for this project yet, so there’s nothing to read.", "Choose a property"]
        : ["Google Analytics didn’t answer", "The report request failed, so nothing is shown rather than an estimate. Reconnecting usually fixes an expired token.", "Check the connection"];
    return <div className={styles.page}>{head}
      <div className={styles.banner} role="status"><div><strong>{title}</strong><span>{body}</span></div><Link className={styles.bannerAction} href={settings}>{action}</Link></div>
    </div>;
  }

  const { pages, channels, scanned, days, current, previous } = data.detail;
  const top = Math.max(1, ...channels.map((c) => c.sessions));
  return <div className={styles.page}>{head}
    <div className={styles.kpis}>
      {(data.kpis ?? []).map((k) => <div key={k.label} className={styles.kpi}>
        <span>{k.label}</span>
        <strong>{k.value ?? "—"}</strong>
        <small className={k.delta === null ? "" : (k.label === "Bounce rate" ? k.delta <= 0 : k.delta >= 0) ? styles.goodText : styles.warnText}>
          {k.delta === null ? "No earlier period" : `${k.delta > 0 ? "+" : ""}${k.delta}% vs the 30 days before`}
        </small>
      </div>)}
    </div>

    <section className={styles.card} aria-labelledby="sessions-title">
      <div className={styles.cardHead}><div><h2 id="sessions-title">Sessions per day</h2><p>Last 30 days, with the 30 before as a dashed line.</p></div></div>
      {current.some((v) => v > 0) || previous.some((v) => v > 0)
        ? <FigLineChart shared labels={days.map(fmtDay)} series={[
            { name: "30 days before", colour: "#4a5243", values: previous, dashed: true },
            { name: "Last 30 days", colour: "#14c86b", values: current },
          ]} />
        : <p className={styles.empty}>No sessions recorded in the last 60 days.</p>}
    </section>

    <div className={styles.splitWide}>
      <section className={styles.card} aria-labelledby="pages-title">
        <div className={styles.cardHead}><div><h2 id="pages-title">Busiest pages, with what FIG found on them</h2>
          <p>Fix what people land on first. Sessions from Analytics{scanned ? ", findings from the latest scan." : "; run a scan to see findings per page."}</p></div></div>
        {pages.length ? <table className={styles.table}>
          <thead><tr><th>Landing page</th><th>Sessions</th><th>Engaged</th><th>Findings</th></tr></thead>
          <tbody>{pages.map((p) => <tr key={p.path}>
            <td className={styles.pathCell}>{p.path}</td><td>{p.sessions.toLocaleString()}</td><td>{p.engaged}%</td>
            <td>{!scanned ? "—" : p.findings.length ? <span className={styles.tagRow}>{byLayer(p.findings).map(([layer, list]) =>
              <span key={layer} className={`${styles.layerTag} ${styles[layer] ?? ""}`} title={list.map((f) => f.summary).join("\n")}>{LAYER_LABEL[layer] ?? layer} {list.length}</span>)}</span> : "0"}</td>
          </tr>)}</tbody>
        </table> : <p className={styles.empty}>No landing pages recorded in the last 30 days.</p>}
      </section>
      <section className={styles.card} aria-labelledby="channels-title">
        <div className={styles.cardHead}><div><h2 id="channels-title">Where visits come from</h2><p>Sessions by default channel group.</p></div></div>
        {channels.length ? <ul className={styles.channels}>{channels.map((c) => <li key={c.name}>
          <div><span>{c.name}</span><b>{c.sessions.toLocaleString()} · {c.share}%</b></div>
          <i><em style={{ width: `${(c.sessions / top) * 100}%` }} /></i>
        </li>)}</ul> : <p className={styles.empty}>No sessions in the last 30 days.</p>}
      </section>
    </div>
  </div>;
}
