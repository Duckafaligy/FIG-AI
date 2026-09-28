import Link from "next/link";
import type { ApiProjectSeo } from "@/lib/api";
import { FigLineChart } from "./fig-line-chart";
import { LayerChecks } from "./project-checks";
import styles from "./project-page.module.css";

const fmtDay = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

/** One project's SEO (Paper 2c.2): Search Console traffic when it's connected
 *  and readable, never estimated, next to the search and structure checks. */
export function ProjectSeo({ data }: { data: ApiProjectSeo }) {
  const project = data.project!;
  const base = `/projects/${encodeURIComponent(project.hostname)}`;
  const t = data.traffic ?? null;
  const gsc = data.search_console!;
  const checks = data.checks ?? [];
  const flagged = checks.filter((c) => c.state === "flag").length;
  const score = data.scores ? [data.scores.search, data.scores.structure].filter((v): v is number => v !== null) : [];

  return <div className={styles.page}>
    <header className={styles.head}>
      <div>
        <span className={styles.eyebrow}>{project.name} · SEO</span>
        <h1>{data.headline}</h1>
        <p>{data.sub}</p>
      </div>
    </header>

    {!gsc.readable && <div className={styles.banner} role="status">
      <div>
        <strong>{gsc.connected ? "Search Console needs reconnecting" : "Search Console isn’t connected"}</strong>
        <span>{gsc.connected
          ? "Google didn’t return data for this site. Nothing is shown in its place and nothing is estimated."
          : "Connect it to see clicks, impressions and the queries people search. The checks below work without it."}</span>
      </div>
      <Link className={styles.bannerAction} href={`${base}/settings`}>{gsc.connected ? "Reconnect" : "Connect"}</Link>
    </div>}

    <div className={styles.kpis}>
      <div className={styles.kpi}><span>Clicks</span><strong>{t ? t.clicks.toLocaleString() : "—"}</strong><small>Last 28 days, from Search Console</small></div>
      <div className={styles.kpi}><span>Impressions</span><strong>{t ? t.impressions.toLocaleString() : "—"}</strong><small>Times the site showed in results</small></div>
      <div className={styles.kpi}><span>Click-through rate</span><strong>{t?.ctr != null ? `${t.ctr}%` : "—"}</strong><small>Clicks ÷ impressions</small></div>
      <div className={styles.kpi}><span>Checks with findings</span><strong>{data.pages_scanned == null ? "—" : `${flagged} of ${checks.length}`}</strong><small>{data.pages_scanned == null ? "Run a scan first" : `Across ${data.pages_scanned} scanned pages`}</small></div>
    </div>

    {t && t.daily.length > 1 && <section className={styles.card} aria-labelledby="traffic-title">
      <div className={styles.cardHead}><div><h2 id="traffic-title">Clicks and impressions</h2><p>One point per day from Search Console. Its data runs a few days behind.</p></div></div>
      <FigLineChart labels={t.daily.map((d) => fmtDay(d.date))} series={[
        { name: "Clicks", colour: "#14c86b", values: t.daily.map((d) => d.clicks) },
        { name: "Impressions", colour: "#8fb8f0", values: t.daily.map((d) => d.impressions) },
      ]} />
    </section>}

    <div className={styles.halves}>
      <section className={styles.card} aria-labelledby="queries-title">
        <div className={styles.cardHead}><div><h2 id="queries-title">Top queries</h2><p>What people searched before clicking through, last 28 days.</p></div></div>
        {t?.queries.length
          ? <table className={styles.table}><thead><tr><th>Query</th><th>Clicks</th><th>Impr.</th><th>Position</th></tr></thead>
            <tbody>{t.queries.map((q) => <tr key={q.query}><td>{q.query}</td><td>{q.clicks.toLocaleString()}</td><td>{q.impressions.toLocaleString()}</td><td>{q.position}</td></tr>)}</tbody></table>
          : <p className={styles.empty}>{t ? "No queries recorded in the last 28 days." : "Queries come from Search Console."}</p>}
      </section>
      <section className={styles.card} aria-labelledby="checks-title">
        <div className={styles.cardHead}>
          <div><h2 id="checks-title">Search and structure checks</h2><p>{checks.length} checks from the latest scan. Found ones first, with the fix.</p></div>
          {score.length > 0 && <span className={styles.scoreTag}>{Math.round(score.reduce((a, b) => a + b, 0) / score.length)}</span>}
        </div>
        <LayerChecks checks={checks} pagesScanned={data.pages_scanned} platform={data.platform} publishHref={`${base}/publish`} />
      </section>
    </div>
  </div>;
}
