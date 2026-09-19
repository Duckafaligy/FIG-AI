import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle2, CircleAlert, TriangleAlert } from "lucide-react";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import styles from "./report.module.css";

/**
 * Public per-scan report — no auth, no session. Reads the same free-tier
 * endpoint `app/public.py:public_read_result` already serves at
 * `GET /scan/{scan_id}`; this page just renders it. CLAUDE.md's roadmap
 * calls this "the growth mechanic," so metadata carries real Open Graph
 * tags for when the link gets pasted somewhere.
 *
 * Verdict copy stays probabilistic on purpose (see CLAUDE.md's "ONE rule")
 * — never "this IS AI-written," always "commonly associated with."
 */

type Finding = {
  check: string;
  layer: string;
  layer_label: string;
  severity: "low" | "medium" | "high";
  summary: string;
  why: string;
  fix: string;
  evidence: string[];
  page: string | null;
};

type ScanResult =
  | { scan_id: string; hostname: string; status: "queued" | "running"; error?: null }
  | { scan_id: string; hostname: string; status: "failed"; error: string | null }
  | {
      scan_id: string;
      hostname: string;
      status: "done";
      pages: number;
      score: number | null;
      verdict: "clean" | "check" | "fix" | null;
      finished_at: string | null;
      layers: { craft: number | null; structure: number | null; search: number | null; answers: number | null };
      findings: Finding[];
    };

const LAYER_LABEL: Record<string, string> = { craft: "Craft", structure: "Structure", search: "Search", answers: "Answers" };
const LAYER_SUB: Record<string, string> = {
  craft: "how it reads", structure: "what sits where",
  search: "what a crawler reaches", answers: "what a model can quote",
};
const SEVERITY_LABEL: Record<string, string> = { high: "High", medium: "Medium", low: "Low" };
const VERDICT_COPY: Record<string, { label: string; description: string }> = {
  clean: { label: "Clean", description: "Few patterns here are commonly associated with generic or AI-generated output." },
  check: { label: "Worth a check", description: "A handful of patterns here are commonly associated with generic or AI-generated output — never a certainty, worth a human look." },
  fix: { label: "Worth fixing", description: "Several patterns here are commonly associated with generic or AI-generated output — never a certainty, worth a human look." },
};

async function fetchScan(scanId: string): Promise<ScanResult | null> {
  // Server-side fetch, same as lib/api.ts's SERVER_BASE: goes straight to the
  // backend rather than through the client-facing proxy, since this never
  // runs in a browser and isn't subject to any cookie/CORS rules. Needs
  // FIG_BACKEND_URL now that NEXT_PUBLIC_API_URL is left empty in production
  // (see next.config.mjs and lib/api.ts for why).
  const base = (process.env.FIG_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
  try {
    const res = await fetch(`${base}/scan/${scanId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as ScanResult;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ scanId: string }> }): Promise<Metadata> {
  const { scanId } = await params;
  const result = await fetchScan(scanId);
  if (!result) return { title: "Report not found — FIG" };
  const title = result.status === "done"
    ? `${result.hostname} — self-check report — FIG`
    : `${result.hostname} — scan in progress — FIG`;
  const description = result.status === "done"
    ? `Scored ${result.score ?? "—"}/100. ${VERDICT_COPY[result.verdict ?? ""]?.description ?? ""}`
    : "A free self-check scan from FIG — checking for patterns that read as generic AI output.";
  return { title, description, openGraph: { title, description } };
}

function ScoreRing({ score }: { score: number }) {
  const size = 132, stroke = 12, r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const dash = (Math.max(0, Math.min(100, score)) / 100) * c;
  const tone = score >= 80 ? "var(--green)" : score >= 55 ? "#c8830a" : "var(--red)";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={styles.ring} role="img" aria-label={`Score ${score} out of 100`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth={stroke} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tone} strokeWidth={stroke}
        strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className={styles.ringLabel}>{score}</text>
    </svg>
  );
}

export default async function ReportPage({ params }: { params: Promise<{ scanId: string }> }) {
  const { scanId } = await params;
  const result = await fetchScan(scanId);

  return (
    <div className="public-page">
      <PublicNav />
      <main className={styles.main}>
        <div className="page-shell">
          {!result ? (
            <section className={styles.state}>
              <h1>Report not found</h1>
              <p>This link doesn&apos;t match a scan FIG has a record of. It may have expired, or the link may be mistyped.</p>
              <Link className="button" href="/">Run a free scan<ArrowRight size={16} /></Link>
            </section>
          ) : result.status === "failed" ? (
            <section className={styles.state}>
              <h1>{result.hostname}</h1>
              <p className={styles.stateBad}><CircleAlert size={18} aria-hidden="true" />This scan couldn&apos;t finish: {result.error || "an unexpected error"}.</p>
              <Link className="button" href="/">Try another scan<ArrowRight size={16} /></Link>
            </section>
          ) : result.status !== "done" ? (
            <section className={styles.state}>
              <h1>{result.hostname}</h1>
              <p><TriangleAlert size={18} aria-hidden="true" /> Still scanning — this link fills in automatically once it finishes. Refresh in a moment.</p>
            </section>
          ) : (
            <>
              <header className={styles.hero}>
                <span className="eyebrow">Self-check report</span>
                <h1>{result.hostname}</h1>
                <p className={styles.sub}>
                  {result.pages} page{result.pages === 1 ? "" : "s"} read
                  {result.finished_at
                    ? ` · scanned ${new Date(result.finished_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}`
                    : ""}
                </p>
                <div className={styles.scoreRow}>
                  {result.score !== null && <ScoreRing score={result.score} />}
                  <div>
                    <strong className={styles.verdictLabel}>{VERDICT_COPY[result.verdict ?? ""]?.label ?? "Scored"}</strong>
                    <p>{VERDICT_COPY[result.verdict ?? ""]?.description ?? "A probabilistic, educational read — never a certainty."}</p>
                  </div>
                </div>
              </header>

              <div className={styles.layerGrid}>
                {(["craft", "structure", "search", "answers"] as const).map((layer) => (
                  <article key={layer} className={styles.layerCard}>
                    <span>{LAYER_LABEL[layer]}</span>
                    <strong>{result.layers[layer] ?? "—"}</strong>
                    <small>{LAYER_SUB[layer]}</small>
                  </article>
                ))}
              </div>

              <section className={styles.findings}>
                <h2>What stood out</h2>
                {result.findings.length === 0 ? (
                  <p className={styles.clean}><CheckCircle2 size={18} aria-hidden="true" />No flags on this read — nothing here matched a known generic pattern.</p>
                ) : (
                  <ul>
                    {result.findings.map((f, i) => (
                      <li key={`${f.check}-${i}`} className={styles.finding}>
                        <div className={styles.findingHead}>
                          <span className={`${styles.severity} ${styles[`severity${f.severity[0].toUpperCase()}${f.severity.slice(1)}`] ?? ""}`}>
                            {SEVERITY_LABEL[f.severity] ?? f.severity}
                          </span>
                          <span className={styles.findingLayer}>{f.layer_label}</span>
                        </div>
                        <h3>{f.summary}</h3>
                        <p>{f.why}</p>
                        <p className={styles.fix}><strong>Fix: </strong>{f.fix}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className={styles.cta}>
                <h2>Check your own site</h2>
                <p>This same free read is open to anyone — no account needed.</p>
                <Link className="button" href="/">Run a free scan<ArrowRight size={16} /></Link>
              </section>
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
