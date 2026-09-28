import styles from "./fig-line-chart.module.css";

type Series = { name: string; colour: string; values: number[]; dashed?: boolean };

/** A plain day-by-day line chart. By default each series is scaled to its own
 *  peak so clicks and impressions can share one frame; `shared` puts every
 *  series on one scale, for comparing like with like (this month vs last). */
export function FigLineChart({ series, labels, height = 200, shared = false }: { series: Series[]; labels: string[]; height?: number; shared?: boolean }) {
  const w = 1000, h = height;
  const n = Math.max(...series.map((s) => s.values.length), 2);
  const x = (i: number) => (i / (n - 1)) * w;
  const sharedPeak = Math.max(1, ...series.flatMap((s) => s.values));
  const ticks = [0, Math.floor((n - 1) / 3), Math.floor(((n - 1) * 2) / 3), n - 1];
  return <figure className={styles.figure}>
    <figcaption className={styles.legend}>{series.map((s) =>
      <span key={s.name}><i style={{ background: s.colour }} className={s.dashed ? styles.dashed : ""} />{s.name}</span>)}</figcaption>
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className={styles.svg} role="img"
      aria-label={series.map((s) => `${s.name}: ${s.values.reduce((a, b) => a + b, 0).toLocaleString()} in total`).join("; ")}>
      {[0, .25, .5, .75, 1].map((f) => <line key={f} x1="0" x2={w} y1={f * (h - 2) + 1} y2={f * (h - 2) + 1} className={styles.grid} />)}
      {series.map((s) => {
        const peak = shared ? sharedPeak : Math.max(...s.values, 1);
        const pts = s.values.map((v, i) => `${x(i).toFixed(1)},${(h - 6 - (v / peak) * (h - 16)).toFixed(1)}`).join(" ");
        return <polyline key={s.name} points={pts} fill="none" stroke={s.colour} strokeWidth="2" strokeDasharray={s.dashed ? "6 5" : undefined} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />;
      })}
    </svg>
    <div className={styles.axis}>{ticks.map((t, i) => <span key={i}>{labels[t] ?? ""}</span>)}</div>
  </figure>;
}
