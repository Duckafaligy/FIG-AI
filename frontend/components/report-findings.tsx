"use client";
import { useMemo, useState, type ReactNode } from "react";
import { ArrowRight, BadgeCheck, ChevronRight, CircleCheck, Rocket, ShieldCheck, Sparkles, Star, TrendingUp, Wand2, X, Zap, type LucideIcon } from "lucide-react";

export type Finding = {
  check: string; title?: string | null; layer: string; layer_label: string; severity: "low" | "medium" | "high";
  summary: string; why: string; fix: string; evidence: string[]; page: string | null;
};
type Group = Finding & { pages: string[]; perPage: { page: string; summary: string }[]; allEvidence: string[] };

const LAYERS = [["all", "All"], ["craft", "Craft"], ["structure", "Structure"], ["search", "Search"], ["answers", "Answers"]] as const;
const RANK = { high: 0, medium: 1, low: 2 };
const THIN_PAGE_WORDS = 120; // app/rules/checks.py

const pathOf =(url: string | null) => {
  if (!url) return "Whole site";
  try { const p = new URL(url).pathname; return p === "" ? "/" : p; } catch { return url; }
};

const ICONS: Record<string, LucideIcon> = {
  sparkles: Sparkles, "arrow-right": ArrowRight, arrowright: ArrowRight, zap: Zap, bolt: Zap, "lightning-bolt": Zap,
  rocket: Rocket, "shield-check": ShieldCheck, shieldcheck: ShieldCheck, star: Star, "trending-up": TrendingUp, trendingup: TrendingUp,
  wand: Wand2, "wand-2": Wand2, wand2: Wand2, "chevron-right": ChevronRight, chevronright: ChevronRight,
  "check-circle": CircleCheck, checkcircle: CircleCheck, "circle-check": CircleCheck, circlecheck: CircleCheck,
  "circle-check-big": BadgeCheck, circlecheckbig: BadgeCheck,
};

const Code = ({ children }: { children: string }) => <pre className="rv-code">{children}</pre>;
const Missing = ({ label }: { label: string }) => <div className="rv-missing"><X size={16} aria-hidden="true" />{label}</div>;

/** The "found" and "better" visuals for a pattern. Only draws what the evidence actually supports. */
function compare(g: Group, host: string): { now: ReactNode; better: ReactNode } | null {
  const ev = g.allEvidence;
  const firstPath = g.pages[0] === "Whole site" ? "/" : g.pages[0];
  switch (g.check) {
    case "default_color_palette": {
      const hexes = ev.map(e => e.match(/#[0-9a-f]{6}/i)?.[0]).filter((h): h is string => !!h);
      if (!hexes.length) return null;
      return {
        now: <div className="rv-swatches">{hexes.map(h => <span key={h}><i style={{ background: h }} />{h.toUpperCase()}<small>library default</small></span>)}</div>,
        better: <div className="rv-swatches"><span><i className="rv-swatch-own" />Your colour<small>one accent, chosen for you</small></span><span><i style={{ background: "#f3f5ef" }} />Neutral</span><span><i style={{ background: "#111310" }} />Neutral</span></div>,
      };
    }
    case "component_uniformity":
      return {
        now: <div className="rv-cards rv-cards--same" aria-hidden="true">{[0, 1, 2, 3].map(i => <b key={i} />)}</div>,
        better: <div className="rv-cards rv-cards--varied" aria-hidden="true"><b /><b /><b /><b /></div>,
      };
    case "numbered_eyebrows":
      return {
        now: <div className="rv-eyebrows">{(ev.length ? ev : ["01", "02", "03"]).slice(0, 3).map(n => <div key={n}><small>{n}</small><b /></div>)}</div>,
        better: <div className="rv-eyebrows">{[0, 1, 2].map(i => <div key={i}><b /></div>)}</div>,
      };
    case "flat_typography": {
      const m = ev[0]?.match(/<(h\d)>\s*x(\d+)/i);
      const level = m?.[1] ?? "h3", n = Math.min(Number(m?.[2] ?? 6), 9);
      return {
        now: <div className="rv-heads">{Array.from({ length: n }, (_, i) => <div key={i}><small>{level}</small><b style={{ width: "62%" }} /></div>)}</div>,
        better: <div className="rv-heads">{[["h1", 92, 0], ["h2", 74, 1], ["h3", 56, 2], ["h3", 56, 2], ["h2", 74, 1], ["h3", 56, 2]].map(([t, w, d], i) => <div key={i} style={{ paddingLeft: `${Number(d) * 14}px` }}><small>{t}</small><b style={{ width: `${w}%` }} /></div>)}</div>,
      };
    }
    case "overused_icons":
      return {
        now: <div className="rv-icons">{ev.map(e => { const name = e.split(" ")[0].toLowerCase(); const Icon = ICONS[name]; return <span key={e}>{Icon ? <Icon size={20} aria-hidden="true" /> : null}<small>{name}</small></span>; })}</div>,
        better: <div className="rv-plain">An icon only where it says something specific; otherwise let the words carry it.</div>,
      };
    case "generic_copy": {
      const phrases = [...new Set(ev.map(e => e.replace(/^"|"$/g, "")))].filter(p => p.length < 90).slice(0, 3);
      return {
        now: <ul className="rv-quotes">{phrases.map(p => <li key={p}>&ldquo;{p}&rdquo;</li>)}</ul>,
        better: <ul className="rv-quotes rv-quotes--good"><li>What it is, who it&rsquo;s for, and a concrete detail only you could say.</li></ul>,
      };
    }
    case "section_order": {
      const flow = ev[0]?.split(/\s*→\s*/).filter(Boolean) ?? [];
      const p = flow.findIndex(s => /pric/i.test(s)), f = flow.findIndex(s => /feature|how it works|benefit/i.test(s));
      if (p < 0 || f < 0 || p > f) return null;
      const fixed = [...flow]; const [moved] = fixed.splice(p, 1); fixed.splice(f, 0, moved);
      const Flow = ({ items, good }: { items: string[]; good: boolean }) => <div className="rv-flow">{items.map((s, i) => <span key={s + i} className={/pric/i.test(s) ? (good ? "is-good" : "is-bad") : ""}>{s}</span>)}</div>;
      return { now: <Flow items={flow} good={false} />, better: <Flow items={fixed} good /> };
    }
    case "thin_page": {
      const rows = g.perPage.map(x => ({ page: x.page, words: Number(x.summary.match(/(\d+)\s+words/)?.[1] ?? NaN) })).filter(r => !Number.isNaN(r.words));
      if (!rows.length) return null;
      const max = Math.max(THIN_PAGE_WORDS * 1.4, ...rows.map(r => r.words));
      const Bars = ({ items }: { items: { page: string; words: number }[] }) => (
        <div className="rv-bars">{items.map(r => (
          <div key={r.page}><code>{r.page}</code><span className="rv-bar"><i style={{ width: `${(r.words / max) * 100}%` }} className={r.words >= THIN_PAGE_WORDS ? "is-good" : "is-bad"} /><em style={{ left: `${(THIN_PAGE_WORDS / max) * 100}%` }} /></span><b>{r.words}</b></div>
        ))}<p>Line: {THIN_PAGE_WORDS}-word minimum</p></div>
      );
      return { now: <Bars items={rows} />, better: <Bars items={rows.map(r => ({ ...r, words: Math.max(r.words, THIN_PAGE_WORDS) }))} /> };
    }
    case "missing_alt": {
      const m = g.summary.match(/(\d+) of (\d+)/); const total = Math.min(Number(m?.[2] ?? 4), 6);
      return {
        now: <div className="rv-imgs">{Array.from({ length: total }, (_, i) => <span key={i} className="is-bad"><X size={14} aria-hidden="true" />no alt</span>)}</div>,
        better: <div className="rv-imgs">{Array.from({ length: total }, (_, i) => <span key={i} className="is-good"><CircleCheck size={14} aria-hidden="true" />described</span>)}</div>,
      };
    }
    case "missing_meta_description":
      return {
        now: <div className="rv-serp"><small>{host}{firstPath}</small><b>{host}</b><p className="is-bad">No description. Search engines guess from whatever text they find first.</p></div>,
        better: <div className="rv-serp"><small>{host}{firstPath}</small><b>{host}</b><p>One clear sentence on what this page offers and who it&rsquo;s for.</p></div>,
      };
    case "missing_h1": return { now: <Missing label="No <h1> on the page" />, better: <Code>{"<h1>What this page is about</h1>"}</Code> };
    case "missing_canonical": return { now: <Missing label="No canonical link" />, better: <Code>{`<link rel="canonical" href="https://${host}${firstPath}">`}</Code> };
    case "missing_lang": return { now: <Missing label="<html> has no lang" />, better: <Code>{'<html lang="en">'}</Code> };
    case "no_structured_data": return { now: <Missing label="No JSON-LD" />, better: <Code>{`<script type="application/ld+json">\n{ "@context": "https://schema.org",\n  "@type": "Organization",\n  "name": "…", "url": "https://${host}" }\n</script>`}</Code> };
    case "missing_llms_txt": return { now: <Missing label={`${host}/llms.txt not found`} />, better: <Code>{`# ${host}\n> One sentence on what the site is.\n\n## Pages\n- [Pricing](https://${host}/pricing)`}</Code> };
    default:
      return ev.length ? { now: <div className="rv-chips">{ev.slice(0, 6).map(e => <code key={e}>{e}</code>)}</div>, better: null } : null;
  }
}

/** Findings grouped by check, each shown as "found" next to "better", filterable by layer. */
export function ReportFindings({ findings, host }: { findings: Finding[]; host: string }) {
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
        {shown.map(g => {
          const c = compare(g, host);
          return (
            <li key={g.check} className="rf-card">
              <div className="rf-head">
                <span className={`rf-sev rf-sev--${g.severity}`}>{g.severity === "high" ? "High" : g.severity === "medium" ? "Medium" : "Low"}</span>
                <span className="rf-layer">{g.layer_label}</span>
                <span className="rf-pagelist">{g.pages.map(p => <code key={p}>{p}</code>)}</span>
              </div>
              <h3>{g.pages.length > 1 ? (g.title ?? g.summary) : g.summary}</h3>
              <div className={`rv-compare${c?.better ? "" : " rv-compare--single"}`}>
                <div className="rv-side rv-side--now"><span className="rv-tag">Found</span>{c?.now ?? <p className="rv-plain">{g.summary}</p>}</div>
                <div className="rv-side rv-side--better">
                  <span className="rv-tag">Better</span>
                  {c?.better}
                  <p className="rv-fix">{g.fix}</p>
                </div>
              </div>
              <p className="rf-why">{g.why}</p>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
