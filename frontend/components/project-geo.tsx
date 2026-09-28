import { Check, X } from "lucide-react";
import type { ApiProjectGeo } from "@/lib/api";
import { LayerChecks } from "./project-checks";
import styles from "./project-page.module.css";


const ENGINES = ["ChatGPT", "Perplexity", "Claude", "Google AI"];

/** One project's GEO (Paper 2c.3): what answer engines can read and quote.
 *  Citation tracking isn't built, so its panel says so instead of estimating. */
export function ProjectGeo({ data }: { data: ApiProjectGeo }) {
  const project = data.project!;
  const base = `/projects/${encodeURIComponent(project.hostname)}`;
  const crawlers = data.crawlers ?? [];
  const allowed = crawlers.filter((c) => c.allowed).length;

  return <div className={styles.page}>
    <header className={styles.head}>
      <div>
        <span className={styles.eyebrow}>{project.name} · GEO</span>
        <h1>{data.headline}</h1>
        <p>What answer engines like ChatGPT and Perplexity need to read the site and quote it.</p>
      </div>
    </header>

    <div className={styles.kpis}>
      <div className={styles.kpi}><span>Answers score</span><strong>{data.score ?? "—"}</strong><small>Layer score from the latest scan</small></div>
      <div className={styles.kpi}><span>AI crawlers allowed</span><strong>{data.site_checked ? `${allowed} of ${crawlers.length}` : "—"}</strong><small>From robots.txt</small></div>
      <div className={styles.kpi}><span>llms.txt</span><strong className={data.llms_txt === false ? styles.warnText : ""}>{data.llms_txt === null || data.llms_txt === undefined ? "—" : data.llms_txt ? "Found" : "Missing"}</strong><small>Checked at the site root</small></div>
      <div className={styles.kpi}><span>Pages with JSON-LD</span><strong>{data.jsonld_pages == null ? "—" : `${data.jsonld_pages} of ${data.pages_scanned}`}</strong><small>Structured data a model can read</small></div>
    </div>

    <section className={styles.card} aria-labelledby="crawlers-title">
      <div className={styles.cardHead}><div><h2 id="crawlers-title">Who can read the site</h2>
        <p>{data.site_checked ? "Read from robots.txt at the latest scan. Blocking one of these means that engine can’t quote you, however good the page is." : "The latest scan didn’t read robots.txt for these. Run a scan to check."}</p></div></div>
      <ul className={styles.crawlers}>{crawlers.map((c) => <li key={c.token}>
        <div><code>{c.token}</code><span title={c.owner}>{c.owner}</span></div>
        {c.allowed === null ? <em className={styles.stateUnchecked}>—</em>
          : c.allowed ? <em className={styles.statePass}><Check size={13} aria-hidden="true" />Allowed</em>
          : <em className={styles.stateBlocked}><X size={13} aria-hidden="true" />Blocked</em>}
      </li>)}</ul>
    </section>

    <div className={styles.halves}>
      <section className={styles.card} aria-labelledby="answer-title">
        <div className={styles.cardHead}><div><h2 id="answer-title">Answer checks</h2><p>Run on every page, and once for the whole site.</p></div>{data.score != null && <span className={styles.scoreTag}>{data.score}</span>}</div>
        <LayerChecks checks={data.checks ?? []} pagesScanned={data.pages_scanned} platform={data.platform} publishHref={`${base}/publish`} />
      </section>
      <section className={`${styles.card} ${styles.dashed}`} aria-labelledby="citation-title">
        <div className={styles.cardHead}><div><h2 id="citation-title">Is anyone quoting {project.name}?</h2><p>Whether AI answer engines actually cite this site when people ask about it.</p></div><span className={styles.pill}>Not built yet</span></div>
        <div className={styles.engines}>{ENGINES.map((e) => <div key={e}><span>{e}</span><strong>—</strong></div>)}</div>
        <p className={styles.bodyText}>Answering this means asking each engine real questions every week, for every project, and paying for each one. That’s a separate decision, so these stay blank instead of showing an estimate.</p>
        <p className={styles.mutedText}>What FIG checks for free is on this page: whether the engines are allowed in, and whether the pages give them something clear to quote.</p>
      </section>
    </div>
  </div>;
}
