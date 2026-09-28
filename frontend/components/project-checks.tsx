import Link from "next/link";
import type { ApiLayerCheck } from "@/lib/api";
import styles from "./project-page.module.css";

const PLATFORM_LABEL: Record<string, string> = { wordpress: "WordPress", shopify: "Shopify", webflow: "Webflow", wix: "Wix", github: "GitHub PR" };

function where(c: ApiLayerCheck, pagesScanned: number | null | undefined) {
  if (c.state === "unchecked") return "Not run on the latest scan";
  if (c.state === "pass") return pagesScanned ? `Passed on all ${pagesScanned} pages` : "Passed";
  if (c.site_wide) return "Site-wide";
  const shown = c.pages.slice(0, 3).join(", ");
  return `${c.pages.length} page${c.pages.length === 1 ? "" : "s"}: ${shown}${c.pages.length > 3 ? ", …" : ""}`;
}

/** Every check in a set of layers, flagged ones first with their fix, then
 *  anything this scan didn't run, then passes. Shared by SEO and GEO. */
export function LayerChecks({ checks, pagesScanned, platform, publishHref }: {
  checks: ApiLayerCheck[]; pagesScanned?: number | null; platform?: string | null; publishHref: string;
}) {
  return <ul className={styles.checks}>{checks.map((c) => <li key={c.title}>
    <div className={styles.checkRow}>
      <div><strong>{c.title}</strong><span>{where(c, pagesScanned)}</span></div>
      <span className={`${styles.state} ${c.state === "flag" ? styles.stateFlag : c.state === "pass" ? styles.statePass : styles.stateUnchecked}`}>
        {c.state === "flag" ? "Found" : c.state === "pass" ? "Passing" : "—"}
      </span>
    </div>
    {c.state === "flag" && (c.fix || c.summary) && <div className={styles.fixBox}>
      <div className={styles.fixText}>{c.summary && <p>{c.summary}</p>}{c.fix && <p className={styles.fixLine}>Fix: {c.fix}</p>}</div>
      {c.fixable && platform
        ? <Link className={styles.primarySmall} href={publishHref}>Queue fix · {PLATFORM_LABEL[platform] ?? platform}</Link>
        : <span className={styles.advice}>Advice only</span>}
    </div>}
  </li>)}</ul>;
}
