/**
 * Live workspace data for the dashboard surfaces.
 *
 * The design in `dashboard-pages.ts` stays the source of truth for structure:
 * which sections exist, in what order, with what icons, spans and copy. This
 * module does not redesign anything. It fetches the workspace payload and
 * produces a **plain, serialisable overlay** of values — metric numbers, table
 * rows, stat lists, scores, tabs — keyed by the `area` names the design
 * already sets.
 *
 * Why an overlay and not a whole page object: `DashboardPage.icon` holds a
 * lucide component, and React cannot pass a function from a Server Component
 * to a Client Component. So the split is:
 *
 *     server  →  fetchOverlay()   plain JSON, crosses the boundary fine
 *     client  →  applyOverlay()   merges it into the statically imported page
 *
 * Both halves are pure. If the backend is unreachable, `fetchOverlay` returns
 * `null` and the page renders the static preview exactly as designed.
 */

import {
  api,
  delta,
  fmt,
  type ApiGeoPage,
  type ApiHistoryPage,
  type ApiNotificationsPage,
  type ApiOverviewPage,
  type ApiSeoPage,
} from "./api";
import type { DashboardPage, DashboardRow, DashboardStat, DashboardTone } from "./dashboard-pages";

export type LivePageKey = "overview" | "seo" | "geo" | "notifications" | "history";

/** Everything the overlay can change. All JSON, no functions. */
export type Overlay = {
  /** Keyed by the metric's `label`. */
  metrics: Record<string, { value: string; change: string; detail: string }>;
  /** Keyed by the section's `area`. */
  rows: Record<string, DashboardRow[]>;
  stats: Record<string, DashboardStat[]>;
  scores: Record<string, { value: string; label: string; tone?: DashboardTone }>;
  tabs: Record<string, { label: string; count?: number; active?: boolean }[]>;
  /** The project the data belongs to, for the page description. */
  projectName: string;
};

export type OverlayResult =
  | { live: true; overlay: Overlay; demo: boolean }
  | { live: false; overlay: null; reason: string };

/* ------------------------------------------------------------- helpers */

function blank(projectName = ""): Overlay {
  return { metrics: {}, rows: {}, stats: {}, scores: {}, tabs: {}, projectName };
}

function tone(v: number | null | undefined): DashboardTone | undefined {
  if (v === null || v === undefined) return undefined;
  if (v >= 80) return "green";
  if (v >= 60) return "amber";
  return "red";
}

function metric(o: Overlay, label: string, value: string, change = "", detail = ""): void {
  o.metrics[label] = { value, change, detail };
}

function rows(o: Overlay, area: string, list: DashboardRow[]): void {
  if (list.length) o.rows[area] = list;
}

function stats(o: Overlay, area: string, list: DashboardStat[]): void {
  if (list.length) o.stats[area] = list;
}

/* ------------------------------------------------------------ builders */

function fromOverview(d: ApiOverviewPage): Overlay {
  const o = blank(d.project?.name ?? "");
  const k = d.kpis;

  metric(o, "Total Published Blogs", String(k.published), "", "in this project");
  metric(o, "Posts in Queue", String(k.queue), "", "queued, writing, review");
  metric(o, "Organic Traffic", fmt(k.traffic, { compact: true }), "",
    k.traffic === null ? "needs Search Console" : "last 30 days");
  metric(o, "Avg. Impact Score", fmt(k.impact), "", "latest audit");
  metric(o, "Sync Health", k.sync, "", k.impact === null ? "never audited" : "all systems online");
  metric(o, "AI Search Visibility", fmt(k.ai, { suffix: "%" }), "",
    k.ai === null ? "needs the model crawl" : "across engines");

  rows(o, "overview-impact", d.impact_posts.map((p, i) => ({
    title: p.title,
    meta: p.traffic === null ? "traffic needs Search Console" : `${fmt(p.traffic, { compact: true })} visits`,
    status: fmt(p.impact),
    tone: tone(p.impact),
    rank: i + 1,
  })));

  rows(o, "overview-keywords", d.keywords.map((x, i) => ({
    title: x.kw,
    meta: `position ${x.pos}`,
    status: fmt(x.traffic, { compact: true }),
    tone: x.pos <= 3 ? "green" : x.pos <= 10 ? "blue" : "amber",
    rank: i + 1,
  })));

  rows(o, "overview-opportunities", d.opportunities.map((x, i) => ({
    title: x.topic,
    meta: x.traffic === null ? "estimate needs a keyword source" : "from the latest audit",
    status: x.traffic === null ? "—" : fmt(x.traffic, { compact: true }),
    rank: i + 1,
  })));

  rows(o, "overview-activity", d.activity.map((a) => ({
    title: a.title, meta: a.sub, status: a.ago,
  })));

  rows(o, "overview-library", d.library.map((p) => ({
    title: p.title,
    meta: `${p.published || "not scheduled"}${p.traffic === null ? "" : ` · ${fmt(p.traffic, { compact: true })} visits`}`,
    status: fmt(p.impact),
    tone: tone(p.impact),
    kicker: p.state,
  })));

  rows(o, "overview-health", d.health.map((h) => ({
    title: h.name, meta: h.note, status: h.state, tone: h.ok ? "green" : "amber",
  })));

  stats(o, "overview-funnel", d.funnel.map((f) => ({ label: f.label, value: String(f.n) })));
  if (d.funnel.length) o.scores["overview-funnel"] = { value: String(d.funnel_total), label: "Total" };

  stats(o, "overview-analytics", d.ga.map((g) => ({
    label: g.label, value: g.value ?? "—", change: delta(g.delta ?? null),
  })));

  stats(o, "overview-search-presence", d.presence.map((p) => ({
    label: p.label,
    value: p.value === null || p.value === undefined ? "—" : String(p.value),
    change: delta(p.delta ?? null),
  })));

  return o;
}

function fromSeo(d: ApiSeoPage): Overlay {
  const o = blank(d.project?.name ?? "");
  const k = d.kpis;

  metric(o, "Posts in Queue", String(k.queue), "", "queued, writing, review");
  metric(o, "Published This Month", String(k.published), "", "in this project");
  metric(o, "Avg. SEO Score", fmt(k.seo), "", "across scored drafts");
  metric(o, "Avg. Impact Score", fmt(k.impact), "", "latest audit");
  metric(o, "Organic Click Growth", k.clicks === null ? "—" : delta(k.clicks), "",
    k.clicks === null ? "needs Search Console" : "vs. previous month");
  metric(o, "Keywords in Top 10", fmt(k.top10), "",
    k.top10 === null ? "needs Search Console" : "from last month");

  o.tabs["seo-review"] = [
    { label: `In Queue (${d.counts.queue})`, count: d.counts.queue, active: d.tab === "queue" },
    { label: `In Review (${d.counts.review})`, count: d.counts.review, active: d.tab === "review" },
    { label: `Approved (${d.counts.approved})`, count: d.counts.approved, active: d.tab === "approved" },
  ];

  rows(o, "seo-review", d.rows.map((r) => ({
    title: r.title,
    meta: `${r.topic} · ${r.keywords}`,
    status: fmt(r.seo),
    tone: tone(r.seo),
    kicker: r.state,
    action: "Preview",
  })));

  rows(o, "seo-impact", d.impact.map((p, i) => ({
    title: p.title,
    meta: p.traffic === null ? "traffic needs Search Console" : `${fmt(p.traffic, { compact: true })} visits`,
    status: fmt(p.impact),
    tone: tone(p.impact),
    rank: i + 1,
  })));

  rows(o, "seo-opportunities", d.optimize.map((x) => ({
    title: x.topic,
    meta: x.traffic === null ? "from the latest audit" : `~${fmt(x.traffic, { compact: true })} est. traffic`,
    status: "Medium",
    tone: "amber",
  })));

  rows(o, "seo-links", d.linking.map((l) => ({
    title: l.from, meta: `→ ${l.to}`, status: l.anchor,
  })));

  rows(o, "seo-library", d.library.map((p) => ({
    title: p.title, meta: p.published || "not scheduled",
    status: fmt(p.impact), tone: tone(p.impact), kicker: p.state,
  })));

  if (d.health.value !== null) {
    o.scores["seo-health"] = {
      value: String(d.health.value),
      label: d.health.value >= 80 ? "Excellent" : d.health.value >= 70 ? "Good" : "Needs work",
      tone: tone(d.health.value),
    };
  }
  stats(o, "seo-health", d.health_rows.map((r) => ({ label: r.label, value: fmt(r.value) })));

  stats(o, "seo-clusters", d.clusters.parts.map((p) => ({ label: p.name, value: String(p.value) })));
  if (d.clusters.parts.length) {
    o.scores["seo-clusters"] = { value: fmt(d.clusters.total), label: "Keywords" };
  }

  return o;
}

function fromGeo(d: ApiGeoPage): Overlay {
  const o = blank(d.project?.name ?? "");
  const k = d.kpis;

  metric(o, "AI Queries Tracked", fmt(k.queries), "",
    k.queries === null ? "needs the model crawl" : "from last month");
  metric(o, "Answer Inclusion Rate", fmt(k.inclusion, { suffix: "%" }), "",
    k.inclusion === null ? "needs the model crawl" : "from last month");
  metric(o, "Citation Rate", fmt(k.citation, { suffix: "%" }), "",
    k.citation === null ? "needs the model crawl" : "from last month");
  metric(o, "Avg GEO Impact Score", fmt(k.impact), "", "from the answers layer");
  metric(o, "Prompt Coverage", fmt(k.coverage, { suffix: "%" }), "",
    k.coverage === null ? "needs the model crawl" : "from last month");
  metric(o, "Source Trust Score", fmt(k.trust), "",
    k.trust === null ? "needs the model crawl" : "from last month");

  rows(o, "geo-content", d.rows.map((r) => ({
    title: r.title,
    meta: `${r.type} · ${r.prompts === null ? "prompts need the crawl" : `${r.prompts} prompts`}`,
    status: fmt(r.score),
    tone: tone(r.score),
    kicker: r.updated,
    action: "Preview",
  })));

  rows(o, "geo-mentions", d.mentions.map((m, i) => ({
    title: m.title, meta: "AI mentions", status: String(m.value), rank: i + 1,
  })));

  rows(o, "geo-citations", d.citations.map((c, i) => ({
    title: c.title, meta: "potential reach",
    status: fmt(c.value, { compact: true }), rank: i + 1,
  })));

  rows(o, "geo-prompts", d.clusters.map((c, i) => ({
    title: c.title, meta: "inclusion rate", status: c.value, tone: "green", rank: i + 1,
  })));

  rows(o, "geo-snippets", d.snippets.map((s, i) => ({
    title: s.query,
    meta: `${s.source} · ${s.seen}`,
    status: s.quality,
    tone: s.quality === "Excellent" ? "green" : s.quality === "Fair" ? "amber" : "blue",
    rank: i + 1,
  })));

  stats(o, "geo-sources", d.breakdown.parts.map((p) => ({ label: p.name, value: `${p.pct}%` })));
  if (d.breakdown.parts.length) {
    o.scores["geo-sources"] = { value: fmt(d.breakdown.total, { compact: true }), label: "Citations" };
  }

  return o;
}

function fromNotifications(d: ApiNotificationsPage): Overlay {
  const o = blank(d.project?.name ?? "");
  const k = d.kpis;

  metric(o, "Unread Alerts", String(k.unread), "", "needing a person");
  metric(o, "Approval Needed", String(k.approvals), "", "changes waiting");
  metric(o, "Failed Automations", String(k.automations), "", "failed jobs");
  metric(o, "Failed Syncs", String(k.syncs), "", "failed audits");
  metric(o, "Scheduled Today", String(k.scheduled), "", "posts with a date");
  metric(o, "Reminder Status", k.status, "", "all systems active");

  rows(o, "notifications-feed", d.feed.map((f) => ({
    title: f.title,
    meta: f.sub,
    status: f.ago,
    tone: f.tone === "r" ? "red" : f.tone === "a" ? "amber" : "blue",
    action: f.action,
  })));

  rows(o, "notifications-automation", d.alerts.map((a) => ({
    title: a.title, meta: a.ago, status: "High", tone: "red",
  })));

  rows(o, "notifications-scheduled", d.reminders.map((r) => ({
    title: r.title, meta: r.when, status: r.tag, tone: "blue",
  })));

  rows(o, "notifications-approvals", d.approvals.map((a) => ({
    title: a.title, meta: `${a.type} · ${a.ago}`, status: a.level,
    tone: a.level === "High" ? "red" : "amber",
  })));

  rows(o, "notifications-failures", d.failed.map((f) => ({
    title: f.name, meta: `${f.type} · ${f.ago}`, status: f.state, tone: "red",
  })));

  rows(o, "notifications-channels", d.channels.map((c) => ({
    title: c.name,
    meta: c.value === null ? "no transport wired up" : "delivery rate",
    status: fmt(c.value, { suffix: "%" }),
    tone: c.value === null ? undefined : c.value >= 95 ? "green" : "amber",
  })));

  rows(o, "notifications-rules", d.rules.map((r) => ({
    title: r.name, meta: r.sub, status: r.on ? "On" : "Off",
    tone: r.on ? "green" : undefined,
  })));

  rows(o, "notifications-resolved", d.resolved.map((r) => ({
    title: r.issue, meta: `${r.type} · ${r.at} · ${r.by}`, status: r.note,
  })));

  if (d.reliability.value !== null) {
    o.scores["notifications-reliability"] = {
      value: `${d.reliability.value}%`, label: "Reliable", tone: "green",
    };
  }
  stats(o, "notifications-reliability", d.rel_rows.map((r) => ({
    label: r.label, value: String(r.value),
  })));

  return o;
}

function fromHistory(d: ApiHistoryPage): Overlay {
  const o = blank(d.project?.name ?? "");
  const k = d.kpis;

  metric(o, "Total Actions This Month", fmt(k.total), "", "all activity types");
  metric(o, "Posts Published", String(k.published), "", "this month");
  metric(o, "Manual Updates", fmt(k.updates), "", "this month");
  metric(o, "API Sync Events", fmt(k.syncs), "", "this month");
  metric(o, "Automation Runs", fmt(k.automation), "", "no scheduler yet");
  metric(o, "Failed Actions", String(k.failed), "", "this month");

  rows(o, "history-stream", d.stream.map((s) => ({
    title: s.title, meta: s.sub, status: s.ago, kicker: s.state,
    tone: s.state === "Success" ? "green" : s.state === "Failed" ? "red" : "amber",
  })));

  rows(o, "history-audit", d.log.map((r) => ({
    title: r.desc,
    meta: `${r.when} · ${r.content} · ${r.actor}`,
    status: r.state,
    tone: r.state === "Success" ? "green" : r.state === "Failed" ? "red" : "amber",
    kicker: r.type,
  })));

  rows(o, "history-actors", d.actors.map((a) => ({
    title: a.name, meta: `${a.value} actions`, status: `${a.pct}%`,
  })));

  rows(o, "history-workareas", d.areas.map((a, i) => ({
    title: a.title, meta: `${a.value} actions`, status: a.value2 ?? String(a.value), rank: i + 1,
  })));

  rows(o, "history-edited", d.edited.map((e, i) => ({
    title: e.title, meta: "revisions", status: String(e.value), rank: i + 1,
  })));

  rows(o, "history-publishing", d.publishes.map((p) => ({
    title: p.title, meta: p.sub ?? "", status: p.value,
    tone: p.value === "Success" ? "green" : "red",
  })));

  rows(o, "history-reverts", d.reverts.map((r, i) => ({
    title: r.title, meta: "content change", status: r.value,
    tone: r.value === "Reverted" ? "amber" : "red", rank: i + 1,
  })));

  stats(o, "history-categories", d.cat_rows.map((c) => ({ label: c.name, value: String(c.value) })));
  if (d.cat_rows.length) {
    o.scores["history-categories"] = { value: fmt(k.total), label: "Total" };
  }

  return o;
}

/* --------------------------------------------------------- server half */

/** Fetch the overlay for one surface. Server-side; forwards the session cookie. */
export async function fetchOverlay(key: LivePageKey, project = ""): Promise<OverlayResult> {
  const res =
    key === "overview" ? await api.overview(project)
    : key === "seo" ? await api.seo(project)
    : key === "geo" ? await api.geo(project)
    : key === "notifications" ? await api.notifications()
    : await api.history();

  if (!res.ok) {
    return { live: false, overlay: null, reason: res.error };
  }

  const d = res.data;
  const overlay =
    key === "overview" ? fromOverview(d as ApiOverviewPage)
    : key === "seo" ? fromSeo(d as ApiSeoPage)
    : key === "geo" ? fromGeo(d as ApiGeoPage)
    : key === "notifications" ? fromNotifications(d as ApiNotificationsPage)
    : fromHistory(d as ApiHistoryPage);

  return { live: true, overlay, demo: Boolean((d as { demo?: boolean }).demo) };
}

/* --------------------------------------------------------- client half */

/**
 * Merge an overlay into the statically designed page. Pure; returns a copy, so
 * the imported module object is never mutated.
 */
export function applyOverlay(page: DashboardPage, overlay: Overlay | null): DashboardPage {
  if (!overlay) return page;

  return {
    ...page,
    description: overlay.projectName
      ? page.description.replace(/Demo workspace/g, overlay.projectName)
      : page.description,
    metrics: page.metrics.map((m) => {
      const next = overlay.metrics[m.label];
      return next ? { ...m, value: next.value, change: next.change, detail: next.detail } : { ...m };
    }),
    sections: page.sections.map((s) => {
      const area = s.area ?? "";
      return {
        ...s,
        rows: overlay.rows[area] ?? s.rows,
        stats: overlay.stats[area] ?? s.stats,
        score: overlay.scores[area] ?? s.score,
        tabs: overlay.tabs[area] ?? s.tabs,
      };
    }),
  };
}
