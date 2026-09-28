import Link from "next/link";
import type { ApiNotice, ApiProjectHistory, ApiProjectNotifications } from "@/lib/api";
import styles from "./project-page.module.css";

const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];
const TONE: Record<string, string> = { green: "#14c86b", amber: "#d9a441", red: "#e0674f", blue: "#8fb8f0", violet: "#c9b6f5" };

function Notice({ n, loud }: { n: ApiNotice; loud?: boolean }) {
  return <li className={loud ? styles.noticeLoud : styles.notice} style={loud ? { borderLeftColor: TONE[n.tone] } : undefined}>
    <i style={{ background: TONE[n.tone] ?? "#6f7869" }} aria-hidden="true" />
    <div><strong>{n.title}</strong>{n.ago && <small>{n.ago}</small>}<p>{n.sub}</p></div>
    {n.action && <Link className={loud ? styles.primarySmall : styles.ghost} href={n.href}>{n.action}</Link>}
  </li>;
}

/** Project notifications (Paper 2c.7): what needs a person, then what happened. In-app only. */
export function ProjectNotifications({ data }: { data: ApiProjectNotifications }) {
  const needs = data.needs ?? [], recent = data.recent ?? [];
  const project = data.project!;
  return <div className={styles.page}>
    <header className={styles.head}><div>
      <span className={styles.eyebrow}>{project.name} · Notifications</span>
      <h1>{needs.length === 0 ? "Nothing needs you right now." : needs.length === 1 ? `One thing needs you: ${needs[0].title.toLowerCase()}.` : `${WORDS[needs.length] ?? needs.length} things need you.`}</h1>
      <p>Everything that happened on {project.hostname}. These show here in the app; email alerts aren’t sent yet.</p>
    </div></header>
    {needs.length > 0 && <section aria-labelledby="needs-title">
      <h2 id="needs-title" className={styles.sectionLabel}>Needs you</h2>
      <ul className={styles.notices}>{needs.map((n, i) => <Notice key={i} n={n} loud />)}</ul>
    </section>}
    <section aria-labelledby="recent-title">
      <h2 id="recent-title" className={styles.sectionLabel}>Recent</h2>
      {recent.length ? <ul className={styles.notices}>{recent.map((n, i) => <Notice key={i} n={n} />)}</ul>
        : <p className={styles.emptyCard}>Nothing has happened on this project yet. Scans, published changes and posts show up here.</p>}
    </section>
  </div>;
}

/** Project history (Paper 2c.8): the score scan by scan, and a log of what changed. */
export function ProjectHistory({ data }: { data: ApiProjectHistory }) {
  const project = data.project!;
  const series = data.series ?? [], log = data.log ?? [];
  const w = 1000, h = 140, pad = 30;
  const scores = series.map((p) => p.score);
  const lo = Math.max(0, Math.min(...scores, 100) - 8), hi = Math.min(100, Math.max(...scores, 0) + 8);
  const x = (i: number) => series.length < 2 ? w / 2 : pad + (i * (w - pad * 2)) / (series.length - 1);
  const y = (v: number) => h - 22 - ((v - lo) / Math.max(1, hi - lo)) * (h - 44);
  return <div className={styles.page}>
    <header className={styles.head}><div>
      <span className={styles.eyebrow}>{project.name} · History</span>
      <h1>{data.headline}</h1>
      <p>Scans, changes and content on {project.hostname}, newest first. Kept after a change is reverted.</p>
    </div></header>
    {series.length > 1 && <section className={styles.card} aria-labelledby="score-title">
      <div className={styles.cardHead}><div><h2 id="score-title">Impact score, scan by scan</h2><p>One point per finished scan.</p></div></div>
      <svg className={styles.scoreChart} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Scores: ${series.map((p) => `${p.date} ${p.score}`).join(", ")}`}>
        {lo < 80 && hi > 80 && <><line x1="0" x2={w} y1={y(80)} y2={y(80)} className={styles.scoreLine} /><text x={w} y={y(80) - 6} textAnchor="end" className={styles.scoreNote}>80 and up reads clean</text></>}
        {series.length > 1 && <polyline points={series.map((p, i) => `${x(i)},${y(p.score)}`).join(" ")} fill="none" stroke="#14c86b" strokeWidth="2" />}
        {series.map((p, i) => <g key={i}>
          <circle cx={x(i)} cy={y(p.score)} r={i === series.length - 1 ? 5 : 4} fill="#14c86b" />
          <text x={x(i)} y={y(p.score) - 12} textAnchor="middle" className={styles.scoreValue}>{p.score}</text>
          <text x={x(i)} y={h - 4} textAnchor="middle" className={styles.scoreDate}>{p.date.replace(/, \d{4}$/, "")}</text>
        </g>)}
      </svg>
    </section>}
    <section className={styles.card} aria-labelledby="log-title">
      <div className={styles.cardHead}><div><h2 id="log-title">Everything that changed</h2>
        <p>{Object.entries(data.counts ?? {}).map(([k, v]) => `${v} ${k === "Content" ? `content item${v === 1 ? "" : "s"}` : `${k.toLowerCase()}${v === 1 ? "" : "s"}`}`).join(" · ")}</p></div></div>
      {log.length ? <ul className={styles.log}>{log.map((e, i) => <li key={i}>
        <time>{e.when}</time>
        <span><i style={{ background: TONE[e.tone] ?? "#6f7869" }} aria-hidden="true" />{e.kind}</span>
        <p>{e.text}</p>
      </li>)}</ul> : <p className={styles.empty}>Nothing recorded yet.</p>}
    </section>
  </div>;
}
