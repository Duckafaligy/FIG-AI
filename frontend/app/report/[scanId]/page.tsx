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

            <section className={`page-shell ${styles.findings}`}>
              <div className={styles.findingsHead}>
                <h2>What stood out</h2>
                <p>Each pattern with where it appeared, why it reads as generic, and a concrete fix.</p>
              </div>
              {result.findings.length === 0
                ? <p className={styles.clean}>No flags on this read. Nothing here matched a known generic pattern.</p>
                : <ReportFindings findings={result.findings} />}
              <p className={styles.note}>These are patterns commonly associated with generic or templated sites, checked by fixed rules against the public HTML. They are not proof of how a page was made, and a site can be excellent while tripping several of them.</p>
            </section>

            <section className={`page-shell ${styles.cta}`}>
              <div>
                <h2>{isSample ? "See your own site like this." : "Check your own site."}</h2>
                <p>The same free read, up to six public pages, no account needed.</p>
              </div>
              <Link className="button" href="/#scan">Run a free scan <ArrowUpRight size={16} /></Link>
            </section>
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
