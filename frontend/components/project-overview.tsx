"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, BarChart3, Bot, Search } from "lucide-react";
import { actions, type ApiProjectOverview } from "@/lib/api";
import styles from "./project-page.module.css";

const LAYER_LABEL: Record<string, string> = { craft: "Craft", structure: "Structure", search: "Search", answers: "Answers" };
const PLATFORM_LABEL: Record<string, string> = { wordpress: "WordPress", shopify: "Shopify", webflow: "Webflow", wix: "Wix", github: "GitHub PR" };

function tone(score: number | null) {
  if (score === null) return styles.toneNone;
  return score >= 70 ? styles.toneGood : score >= 50 ? styles.toneMid : styles.toneLow;
}

function Ring({ score }: { score: number | null }) {
  const r = 47, c = 2 * Math.PI * r;
  return <svg className={styles.ring} viewBox="0 0 112 112" role="img" aria-label={score === null ? "No score yet" : `Score ${score} out of 100`}>
    <circle cx="56" cy="56" r={r} className={styles.ringTrack} />
    {score !== null && <circle cx="56" cy="56" r={r} className={`${styles.ringFill} ${tone(score)}`} strokeDasharray={`${(c * score) / 100} ${c}`} transform="rotate(-90 56 56)" />}
    <text x="56" y="65" textAnchor="middle">{score ?? "—"}</text>
  </svg>;
}

/** One project's Overview (Paper 2c.1). Everything shown comes from the
 *  latest scan or a connected service; unknowns are dashes with the reason. */
export function ProjectOverview({ data }: { data: ApiProjectOverview }) {
  const [scanState, setScanState] = useState<"" | "busy" | "queued" | string>("");
  const project = data.project!;
  const base = `/projects/${encodeURIComponent(project.hostname)}`;
  const scan = data.scan ?? null;
  const tiles = data.tiles!;
  const change = scan?.score != null && scan.previous != null ? scan.score - scan.previous : null;

  const runScan = async () => {
    setScanState("busy");
    const result = await actions.auditProject(project.id);
    setScanState(result.ok ? "queued" : result.error);
  };

  return <div className={styles.page}>
    <header className={styles.head}>
      <div>
        <span className={styles.eyebrow}>{project.name} · Overview</span>
        <h1>{data.headline}</h1>
        <p>{data.sub}</p>
      </div>
      <div className={styles.headActions}>
        <a className={styles.ghost} href={`https://${project.hostname}`} target="_blank" rel="noreferrer">{project.hostname}<ArrowUpRight size={14} aria-hidden="true" /></a>
        <button type="button" className={styles.primary} disabled={scanState === "busy" || scanState === "queued"} onClick={runScan}>
          {scanState === "busy" ? "Starting…" : scanState === "queued" ? "Scan queued" : "Run a scan"}
        </button>
      </div>
    </header>
    {scanState && scanState !== "busy" && scanState !== "queued" && <p className="form-message" role="alert">{scanState}</p>}

    <section className={styles.band} aria-label="Score">
      <div className={styles.score}>
        <Ring score={scan?.score ?? null} />
        <div>
          <span>Impact score</span>
          <strong>{change === null ? (scan ? "First scan" : "Not scanned yet") : change === 0 ? "No change since last scan" : `${change > 0 ? "Up" : "Down"} ${Math.abs(change)} since last scan`}</strong>
          {scan && <span>{scan.pages} pages read · scanned {scan.ago}</span>}
        </div>
      </div>
      <div className={styles.layers}>
        {(scan?.layers ?? []).map((l) => <div key={l.layer} className={styles.layer}>
          <span>{LAYER_LABEL[l.layer]}</span>
          <i><b className={tone(l.score)} style={{ width: `${l.score ?? 0}%` }} /></i>
          <em>{l.score ?? "—"}</em>
          <small>{l.findings === 0 ? "clean" : `${l.findings} finding${l.findings === 1 ? "" : "s"}`}</small>
        </div>)}
        {!scan && <p className={styles.muted}>Layer scores appear after the first scan.</p>}
      </div>
    </section>

    <div className={styles.tiles}>
      <Link href={`${base}/seo`} className={styles.tile}>
        <div className={styles.tileTop}><span><Search size={15} aria-hidden="true" />SEO</span><small>Open SEO →</small></div>
        <span className={styles.tileLabel}>Search clicks, last 28 days</span>
        <strong>{tiles.seo.clicks === null ? "—" : tiles.seo.clicks.toLocaleString()}</strong>
        <span className={tiles.seo.clicks === null ? styles.noteWarn : styles.note}>{tiles.seo.clicks !== null ? "From Search Console" : tiles.seo.connected ? "Search Console didn’t return data. Reconnect if it keeps happening." : "Connect Search Console to see clicks."}</span>
      </Link>
      <Link href={`${base}/geo`} className={styles.tile}>
        <div className={styles.tileTop}><span><Bot size={15} aria-hidden="true" />GEO</span><small>Open GEO →</small></div>
        <span className={styles.tileLabel}>AI crawlers allowed in robots.txt</span>
        <strong>{tiles.geo.crawlers_allowed === null ? "—" : `${tiles.geo.crawlers_allowed} of ${tiles.geo.crawlers_total}`}</strong>
        <span className={tiles.geo.llms_txt === false ? styles.noteWarn : styles.note}>{tiles.geo.llms_txt === null ? "Run a scan to check robots.txt and llms.txt." : tiles.geo.llms_txt ? "llms.txt found." : "No llms.txt yet."}</span>
      </Link>
      <Link href={`${base}/analytics`} className={styles.tile}>
        <div className={styles.tileTop}><span><BarChart3 size={15} aria-hidden="true" />Analytics</span><small>Open Analytics →</small></div>
        <span className={styles.tileLabel}>Sessions, last 30 days</span>
        <strong>{tiles.analytics?.sessions ?? "—"}</strong>
        <span className={tiles.analytics ? styles.noteGood : styles.noteWarn}>{!tiles.analytics ? "Connect Google Analytics to see sessions." : tiles.analytics.delta === null ? "No earlier period to compare." : `${tiles.analytics.delta > 0 ? "+" : ""}${tiles.analytics.delta}% on the 30 days before`}</span>
      </Link>
    </div>

    <div className={styles.split}>
      <section className={styles.card} aria-labelledby="findings-title">
        <div className={styles.cardHead}>
          <div><h2 id="findings-title">Open findings</h2><p>Most serious first. Each one says where it is, why it matters and how to fix it.</p></div>
        </div>
        {!scan ? <p className={styles.empty}>Run a scan to see findings.</p>
          : !data.findings?.length ? <p className={styles.empty}>Nothing flagged on the latest scan.</p>
          : <ol className={styles.findings}>{data.findings.map((f) => <li key={f.check}>
            <span className={`${styles.layerTag} ${styles[f.layer] ?? ""}`}>{LAYER_LABEL[f.layer] ?? f.layer}</span>
            <div className={styles.findingBody}>
              <div className={styles.findingTitle}><strong>{f.title}</strong><code>{f.pages.length ? f.pages[0] : "whole site"}</code>{f.pages.length > 1 && <small>and {f.pages.length - 1} more page{f.pages.length === 2 ? "" : "s"}</small>}</div>
              {f.why && <p>{f.why}</p>}
              {f.fix && <p className={styles.fix}>Fix: {f.fix}</p>}
            </div>
            {f.fixable && data.platform
              ? <Link className={styles.primarySmall} href={`${base}/publish`}>Queue fix · {PLATFORM_LABEL[data.platform] ?? data.platform}</Link>
              : <span className={styles.advice}>Advice only</span>}
          </li>)}</ol>}
      </section>
      <section className={styles.card} aria-labelledby="activity-title">
        <div className={styles.cardHead}><div><h2 id="activity-title">Recent activity</h2></div></div>
        {data.activity?.length ? <ul className={styles.activity}>{data.activity.map((a, i) => <li key={i}>
          <i className={a.icon === "sync" ? styles.dotGood : styles.dotMuted} aria-hidden="true" />
          <div><strong>{a.title}</strong><span>{a.sub}</span><small>{a.ago}</small></div>
        </li>)}</ul> : <p className={styles.empty}>Nothing yet.</p>}
      </section>
    </div>
  </div>;
}
