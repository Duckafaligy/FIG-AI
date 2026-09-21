import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Library as LibraryIcon } from "lucide-react";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import styles from "./library.module.css";

/**
 * The public library — every free scan, browsable. Reads
 * `app/public.py:scan_library`, deduplicated one row per site (unlike
 * `/reads/recent`'s raw per-visit log). A site's domain shows by default
 * (2026-09-20 product decision, see that endpoint's docstring): `/scan`
 * only ever reads a site's own already-public homepage, never a student's
 * own private in-progress project. A read can still be kept anonymous by
 * whoever ran it (`share: false`), and shows here as "an anonymous site."
 *
 * Verdict copy stays probabilistic on purpose (CLAUDE.md's "ONE rule") —
 * never "this IS AI-written," always "commonly associated with."
 */

type LibraryEntry = {
  scan_id: string;
  site: string | null;
  shared: boolean;
  pages: number | null;
  score: number | null;
  verdict: "clean" | "check" | "fix" | null;
  top_check: string | null;
  top_layer: string | null;
  at: string | null;
};

type LibraryResponse = { library: LibraryEntry[]; total_sites: number };

const VERDICT_LABEL: Record<string, string> = { clean: "Clean", check: "Worth a check", fix: "Worth fixing" };

async function fetchLibrary(): Promise<LibraryResponse | null> {
  const base = (process.env.FIG_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
  try {
    const res = await fetch(`${base}/scan/library?limit=48`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    if (!res.ok) return null;
    return (await res.json()) as LibraryResponse;
  } catch {
    return null;
  }
}

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Scan library — FIG",
    description: "Every free FIG scan, browsable: which patterns turned up, on which sites, and how they scored.",
  };
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export default async function LibraryPage() {
  const data = await fetchLibrary();
  const entries = data?.library ?? [];

  return (
    <div className="public-page">
      <PublicNav />
      <main className={styles.main}>
        <div className="page-shell">
          <header className={styles.hero}>
            <span className="eyebrow"><LibraryIcon size={13} />Public library</span>
            <h1>Every free scan, in one place</h1>
            <p>
              {data ? `${data.total_sites} site${data.total_sites === 1 ? "" : "s"} scanned so far.` : "Recent free scans."}{" "}
              Run your own — no account needed.
            </p>
          </header>

          {entries.length === 0 ? (
            <section className={styles.empty}>
              <p>{data ? "No public scans yet." : "The scan library is unavailable. Please try again shortly."}</p>
              <Link className="button" href="/">{data ? "Run the first one" : "Back to home"}<ArrowRight size={16} /></Link>
            </section>
          ) : (
            <div className={styles.grid}>
              {entries.map((entry) => (
                <Link key={entry.scan_id} href={`/report/${entry.scan_id}`} className={styles.card}>
                  <div className={styles.cardHead}>
                    <strong>{entry.site ?? "an anonymous site"}</strong>
                    {entry.verdict && (
                      <span className={`${styles.verdict} ${styles[`verdict${entry.verdict[0].toUpperCase()}${entry.verdict.slice(1)}`] ?? ""}`}>
                        {VERDICT_LABEL[entry.verdict] ?? entry.verdict}
                      </span>
                    )}
                  </div>
                  <p className={styles.cardMeta}>
                    {entry.score !== null ? `Scored ${entry.score}` : "Scoring"}
                    {entry.pages !== null ? ` · ${entry.pages} page${entry.pages === 1 ? "" : "s"}` : ""}
                    {entry.at ? ` · ${formatDate(entry.at)}` : ""}
                  </p>
                  {entry.top_check && (
                    <p className={styles.cardTop}>Most notable: {entry.top_layer ? `${entry.top_layer} — ` : ""}{entry.top_check.replace(/_/g, " ")}</p>
                  )}
                </Link>
              ))}
            </div>
          )}

          <section className={styles.cta}>
            <h2>Check your own site</h2>
            <p>This same free read is open to anyone — no account needed.</p>
            <Link className="button" href="/">Run a free scan<ArrowRight size={16} /></Link>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}
