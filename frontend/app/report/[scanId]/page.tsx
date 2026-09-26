import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, CircleAlert, Loader } from "lucide-react";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { ReportFindings, type Finding } from "@/components/report-findings";
import sample from "@/lib/sample-report.json";
import styles from "./report.module.css";

/**
 * Public per-scan report: no auth, no session. Renders GET /scan/{scan_id}
 * (app/public.py:public_read_result). /report/sample renders
 * lib/sample-report.json instead, generated from the real rules engine by
 * scripts/make_sample_report.py, so the design can be seen without a scan.
 *
 * Copy stays probabilistic on purpose (CLAUDE.md's "ONE rule"): "commonly
 * associated with", never "this IS AI-written".
 */

type ScanResult =
  | { scan_id: string; hostname: string; status: "queued" | "running"; error?: null }
  | { scan_id: string; hostname: string; status: "failed"; error: string | null }
  | {
      scan_id: string; hostname: string; status: "done"; pages: number; score: number | null;
      verdict: "clean" | "check" | "fix" | null; finished_at: string | null;
      layers: { craft: number | null; structure: number | null; search: number | null; answers: number | null };
      findings: Finding[];
    };

const LAYERS = [
  ["craft", "Craft", "How it reads"], ["structure", "Structure", "What sits where"],
  ["search", "Search", "What a crawler reaches"], ["answers", "Answers", "What a model can quote"],
] as const;
const VERDICT: Record<string, { label: string; description: string }> = {
  clean: { label: "Clean", description: "Few patterns here are commonly associated with generic or templated output." },
  check: { label: "Worth a check", description: "A handful of patterns here are commonly associated with generic or templated output. Never a certainty; worth a human look." },
  fix: { label: "Worth fixing", description: "Several patterns here are commonly associated with generic or templated output. Never a certainty; worth a human look." },
};
const pathOf = (url: string | null) => {
  if (!url) return "Whole site";
  try { return new URL(url).pathname || "/"; } catch { return url; }
};
const tone = (n: number) => (n >= 80 ? "good" : n >= 55 ? "mid" : "low");

async function fetchScan(scanId: string): Promise<ScanResult | null> {
  if (scanId === "sample") return sample as ScanResult;
  // Server-side, straight to the backend (see lib/api.ts SERVER_BASE); never runs in a browser.
  const base = (process.env.FIG_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
  try {
    const res = await fetch(`${base}/scan/${encodeURIComponent(scanId)}`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    return res.ok ? ((await res.json()) as ScanResult) : null;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ scanId: string }> }): Promise<Metadata> {
  const { scanId } = await params;
  const result = await fetchScan(scanId);
  if (!result) return { title: "Report not found - FIG" };
  if (scanId === "sample") return { title: "Sample report - FIG", description: "What a FIG self-check report looks like, with illustrative data." };
  const title = result.status === "done" ? `${result.hostname}: self-check report - FIG` : `${result.hostname}: scan in progress - FIG`;
  const description = result.status === "done"
    ? `Scored ${result.score ?? "-"}/100. ${VERDICT[result.verdict ?? ""]?.description ?? ""}`
    : "A free self-check scan from FIG, looking for patterns commonly associated with generic output.";
  return { title, description, openGraph: { title, description } };
}

function ScoreDial({ score }: { score: number }) {
  const size = 168, stroke = 10, r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const dash = (Math.max(0, Math.min(100, score)) / 100) * c;
  return (
    <div className={`${styles.dial} ${styles[`tone_${tone(score)}`]}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Score ${score} out of 100`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1d2119" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="currentColor" strokeWidth={stroke}
          strokeDasharray={`${dash} ${c}`} strokeLinecap="butt" transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div className={styles.dialText}><strong>{score}</strong><span>out of 100</span></div>
    </div>
  );
}

/** Overview charts, all computed from the findings list: severity mix and a page × layer map. */
function Charts({ findings, score }: { findings: Finding[]; score: number | null }) {
  const checks = new Map<string, Finding["severity"]>();
  for (const f of findings) {
    const prev = checks.get(f.check);
    if (!prev || (f.severity === "high") || (f.severity === "medium" && prev === "low")) checks.set(f.check, f.severity);
  }
  const sev = { high: 0, medium: 0, low: 0 };
  checks.forEach(s => { sev[s] += 1; });
  const total = checks.size;
  const pages = [...new Set(findings.map(f => pathOf(f.page)))];
  const cell = (p: string, l: string) => findings.filter(f => pathOf(f.page) === p && f.layer === l).length;
  const max = Math.max(1, ...pages.flatMap(p => LAYERS.map(([l]) => cell(p, l))));

  return (
    <section className={`page-shell ${styles.charts}`}>
      {score !== null && (
        <div className={`${styles.chart} ${styles.bandChart}`}>
          <h2>Where the score sits</h2>
          <div className={styles.bands} aria-label={`Score ${score} on bands: worth fixing under 55, worth a check 55 to 79, clean 80 and up`} role="img">
            <span className={styles.bandLow} style={{ flexBasis: "55%" }}>Worth fixing</span>
            <span className={styles.bandMid} style={{ flexBasis: "25%" }}>Worth a check</span>
            <span className={styles.bandGood} style={{ flexBasis: "20%" }}>Clean</span>
            <i style={{ left: `${score}%` }}><b>{score}</b></i>
          </div>
          <div className={styles.bandScale} aria-hidden="true"><span>0</span><span style={{ left: "55%" }}>55</span><span style={{ left: "80%" }}>80</span><span style={{ left: "100%" }}>100</span></div>
        </div>
      )}
      <div className={styles.chart}>
        <h2>By severity</h2>
        <div className={styles.stack} role="img" aria-label={`${sev.high} high, ${sev.medium} medium, ${sev.low} low`}>
          {(["high", "medium", "low"] as const).map(s => sev[s] > 0 && <span key={s} className={styles[`sev_${s}`]} style={{ flexGrow: sev[s] }} />)}
        </div>
        <ul className={styles.legend}>
          {(["high", "medium", "low"] as const).map(s => <li key={s}><i className={styles[`sev_${s}`]} /><b>{sev[s]}</b>{s[0].toUpperCase() + s.slice(1)}</li>)}
        </ul>
        <p className={styles.chartNote}>{total} distinct pattern{total === 1 ? "" : "s"}</p>
      </div>
      <div className={`${styles.chart} ${styles.mapChart}`}>
        <h2>Where they are</h2>
        <table className={styles.heat}>
          <thead><tr><th scope="col"><span className="sr-only">Page</span></th>{LAYERS.map(([l, label]) => <th key={l} scope="col">{label}</th>)}</tr></thead>
          <tbody>
            {pages.map(p => (
              <tr key={p}>
                <th scope="row"><code>{p}</code></th>
                {LAYERS.map(([l]) => { const n = cell(p, l); return <td key={l} style={{ ["--a" as string]: n ? 0.18 + (n / max) * 0.62 : 0 }}>{n || ""}</td>; })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function State({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className={styles.state}><h1>{title}</h1>{children}</section>;
}

export default async function ReportPage({ params }: { params: Promise<{ scanId: string }> }) {
  const { scanId } = await params;
  const result = await fetchScan(scanId);
  const isSample = scanId === "sample";

  return (
    <div className="public-page neon-home">
      <PublicNav />
      <main className={styles.main}>
        {!result ? (
          <State title="Report not found">
            <p>This link doesn&apos;t match a scan FIG has a record of. It may have expired, or the link may be mistyped.</p>
            <Link className="button" href="/#scan">Run a free scan <ArrowUpRight size={16} /></Link>
          </State>
        ) : result.status === "failed" ? (
          <State title={result.hostname}>
            <p className={styles.stateBad}><CircleAlert size={18} aria-hidden="true" /> This scan couldn&apos;t finish: {result.error || "an unexpected error"}.</p>
            <Link className="button" href="/#scan">Try another scan <ArrowUpRight size={16} /></Link>
          </State>
        ) : result.status !== "done" ? (
          <State title={result.hostname}>
            <p><Loader size={18} aria-hidden="true" className={styles.spin} /> Still scanning. This page fills in once it finishes; refresh in a moment.</p>
          </State>
        ) : (
          <>
            <section className={styles.hero}>
              <div className={`page-shell ${styles.heroGrid}`}>
                <div className={styles.heroCopy}>
                  <div className={styles.labels}>
                    <span>Self-check report</span>
                    {isSample && <span className={styles.sampleTag}>Sample, illustrative data</span>}
                  </div>
                  <h1>{result.hostname}</h1>
                  <p className={styles.meta}>
                    {result.pages} page{result.pages === 1 ? "" : "s"} read
                    {result.finished_at && <> &middot; scanned {new Date(result.finished_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}</>}
                  </p>
                  <div className={styles.verdict}>
                    <strong>{VERDICT[result.verdict ?? ""]?.label ?? "Scored"}</strong>
                    <p>{VERDICT[result.verdict ?? ""]?.description ?? "A probabilistic, educational read, never a certainty."}</p>
                  </div>
                </div>
                <div className={styles.scorePanel}>
                  {result.score !== null && <ScoreDial score={result.score} />}
                  <dl className={styles.layers}>
                    {LAYERS.map(([key, label, sub]) => {
                      const v = result.layers[key];
                      return (
                        <div key={key}>
                          <dt>{label}<small>{sub}</small></dt>
                          <dd>
                            <span className={styles.track} aria-hidden="true"><span className={`${styles.fill} ${v !== null ? styles[`tone_${tone(v)}`] : ""}`} style={{ transform: `scaleX(${(v ?? 0) / 100})` }} /></span>
                            <b>{v ?? "-"}</b>
                          </dd>
                        </div>
                      );
                    })}
                  </dl>
                </div>
              </div>
            </section>

            {result.findings.length > 0 && <Charts findings={result.findings} score={result.score} />}

            <section className={`page-shell ${styles.findings}`}>
              <div className={styles.findingsHead}>
                <h2>Found, and better</h2>
                <p>What the scan saw on the left, what it could look like on the right.</p>
              </div>
              {result.findings.length === 0
                ? <p className={styles.clean}>No flags on this read. Nothing here matched a known generic pattern.</p>
                : <ReportFindings findings={result.findings} host={result.hostname} />}
              <p className={styles.note}>These are patterns commonly associated with generic or templated sites, checked by fixed rules against the public HTML. They are not proof of how a page was made, and a site can be excellent while tripping several of them.</p>
            </section>
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
