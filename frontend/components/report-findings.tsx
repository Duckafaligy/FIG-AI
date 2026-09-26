"use client";
import { useMemo, useState } from "react";

export type Finding = {
  check: string; title?: string | null; layer: string; layer_label: string; severity: "low" | "medium" | "high";
  summary: string; why: string; fix: string; evidence: string[]; page: string | null;
};
type Group = Finding & { pages: string[]; perPage: { page: string; summary: string }[]; allEvidence: string[] };

const LAYERS = [["all", "All"], ["craft", "Craft"], ["structure", "Structure"], ["search", "Search"], ["answers", "Answers"]] as const;
const RANK = { high: 0, medium: 1, low: 2 };

const pathOf = (url: string | null) => {
  if (!url) return "Whole site";
  try { const p = new URL(url).pathname; return p === "" ? "/" : p; } catch { return url; }
};

/** Findings grouped by check (one card per pattern, with every page it appeared on), filterable by layer. */
export function ReportFindings({ findings }: { findings: Finding[] }) {
  const [layer, setLayer] = useState<string>("all");
  const groups = useMemo(() => {
    const by = new Map<string, Group>();
    for (const f of findings) {
      const g = by.get(f.check) ?? { ...f, pages: [], perPage: [], allEvidence: [] };
      const p = pathOf(f.page);
      if (!g.pages.includes(p)) { g.pages.push(p); g.perPage.push({ page: p, summary: f.summary }); }
      for (const e of f.evidence) if (e && !g.allEvidence.includes(e)) g.allEvidence.push(e);
      if (RANK[f.severity] < RANK[g.severity]) g.severity = f.severity;
      by.set(f.check, g);
    }
    return [...by.values()].sort((a, b) => RANK[a.severity] - RANK[b.severity] || b.pages.length - a.pages.length);
  }, [findings]);
  const shown = layer === "all" ? groups : groups.filter(g => g.layer === layer);
  const count = (l: string) => (l === "all" ? groups.length : groups.filter(g => g.layer === l).length);

  return (
    <div className="rf">
      <div className="rf-tabs" role="group" aria-label="Filter by layer">
        {LAYERS.map(([id, label]) => (
          <button key={id} type="button" aria-pressed={layer === id} onClick={() => setLayer(id)} disabled={count(id) === 0}>
            {label}<span>{count(id)}</span>
          </button>
        ))}
      </div>
      <ol className="rf-list">
        {shown.map(g => (
          <li key={g.check} className={`rf-card rf-card--${g.severity}`}>
            <div className="rf-meta">
              <span className={`rf-sev rf-sev--${g.severity}`}>{g.severity === "high" ? "High" : g.severity === "medium" ? "Medium" : "Low"}</span>
              <span>{g.layer_label}</span>
              <span>{g.pages.length === 1 ? g.pages[0] : `On ${g.pages.length} pages`}</span>
            </div>
            <h3>{g.pages.length > 1 ? (g.title ?? g.summary) : g.summary}</h3>
            <p className="rf-why">{g.why}</p>
            {(g.pages.length > 1 || g.allEvidence.length > 0) && (
              <dl className="rf-where">
                {g.pages.length > 1 && <div><dt>Where</dt><dd className="rf-pages">{g.perPage.map(x => <span key={x.page}><code>{x.page}</code>{x.summary}</span>)}</dd></div>}
                {g.allEvidence.length > 0 && <div><dt>Found</dt><dd>{g.allEvidence.slice(0, 6).map(e => <code key={e}>{e}</code>)}{g.allEvidence.length > 6 && <em>+{g.allEvidence.length - 6} more</em>}</dd></div>}
              </dl>
            )}
            <div className="rf-fix"><strong>How to fix</strong><p>{g.fix}</p></div>
          </li>
        ))}
      </ol>
    </div>
  );
}
