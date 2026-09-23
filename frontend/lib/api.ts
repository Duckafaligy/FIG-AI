/**
 * Client for the FIG workspace API (`/api`, served by the FastAPI backend).
 *
 * The backend authenticates with its own signed HttpOnly session cookie, so
 * requests have to carry it two different ways depending on where they run:
 *
 *   - In a Server Component there is no ambient browser cookie jar, so the
 *     incoming request's cookies are read with `await cookies()` (async in
 *     Next 16) and forwarded as a header. This ONLY works if that cookie
 *     belongs to this app's own domain -- browsers never attach a cookie to
 *     a request aimed at a different domain than the one that issued it, no
 *     matter what SameSite says. Locally that's true by accident (frontend
 *     and backend are both "localhost", just different ports, which counts
 *     as same-site). Deployed for real, frontend and backend live on two
 *     genuinely different domains, so this only stays true if the browser
 *     never talks to the backend's domain directly -- see SERVER_BASE below.
 *   - In the browser, requests use the same-origin proxy and include cookies.
 *     Cross-domain requests are not a production authentication option.
 *
 * Nothing here throws on a failed request. Every call returns a result object,
 * so callers can show a real unavailable/error state. Live pages must never
 * substitute preview records for failed requests.
 *
 * NEXT_PUBLIC_DEMO_MODE=1 makes that fallback a guarantee instead of an
 * accident of network conditions: apiServer/apiClient short-circuit before
 * ever touching the network, so a demo deployment can never show real data
 * regardless of what NEXT_PUBLIC_API_URL happens to be set to (or reach).
 * Meant for a separate Vercel project pointed at this same frontend
 * directory -- one codebase, a demo URL that's structurally incapable of
 * connecting to anything, and a live URL that's unaffected by this at all.
 */

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "1";
const DEMO_BLOCKED: ApiErr = { ok: false, status: 0, error: "demo mode: no backend calls are made" };

// The browser's own base. Empty by default (relative paths), so every
// browser request stays on this app's own origin and next.config.mjs's
// rewrite proxies it to the real backend server-side -- required so the
// session cookie the backend sets ends up belonging to THIS domain (see the
// docstring above). Local dev sets NEXT_PUBLIC_API_URL explicitly, which
// opts back into calling the backend directly -- fine there, since
// localhost:3001/localhost:8000 are already same-site.
// Production must use the same-origin proxy: cross-domain cookies cannot
// authenticate Server Components, even when browser fetches include them.
const CLIENT_BASE = process.env.NODE_ENV === "production"
  ? ""
  : (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

// Server Components call the backend directly -- a plain server-to-server
// request, never subject to a browser's SameSite/CORS rules, so it doesn't
// need the proxy. FIG_BACKEND_URL is server-only (no NEXT_PUBLIC_ prefix)
// and is also what the rewrite above proxies to, so the two stay in sync.
const SERVER_BASE = (process.env.FIG_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export type ApiOk<T> = { ok: true; data: T };
export type ApiErr = { ok: false; status: number; error: string };
export type ApiResult<T> = ApiOk<T> | ApiErr;

export function apiUrl(path: string): string {
  return `${CLIENT_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function serverUrl(path: string): string {
  return `${SERVER_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function failed(status: number, error: string): ApiErr {
  return { ok: false, status, error };
}

/** Shared response handling, so every caller reports failure the same way. */
async function unwrap<T>(res: Response): Promise<ApiResult<T>> {
  if (!res.ok) {
    let detail = res.statusText || `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // a non-JSON error body is fine; the status line is enough
    }
    return failed(res.status, detail);
  }
  try {
    return { ok: true, data: (await res.json()) as T };
  } catch (err) {
    return failed(res.status, `response was not JSON: ${String(err)}`);
  }
}

/**
 * Fetch from a Server Component, forwarding the caller's session cookie.
 *
 * `cache: "no-store"` is explicit: workspace data is per-request and must not
 * be shared between viewers. Next 16 does not cache fetches by default, but
 * saying so keeps it true if a `use cache` boundary is added above.
 */
export async function apiServer<T>(path: string): Promise<ApiResult<T>> {
  if (DEMO_MODE) return DEMO_BLOCKED as ApiResult<T>;
  // Deliberately not wrapped in try/catch: calling `cookies()` is what tells
  // Next this route reads the request and can't be prerendered. Swallowing
  // that here silently made every page using apiServer eligible for static
  // caching again -- including the /app auth gate, which then never re-ran
  // per request. Let it throw; Next catches its own bailout above us.
  const { cookies } = await import("next/headers");
  const jar = await cookies();
  const cookieHeader = jar
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  try {
    const res = await fetch(serverUrl(path), {
      signal: AbortSignal.timeout(15000),
      cache: "no-store",
      headers: cookieHeader ? { cookie: cookieHeader } : undefined,
    });
    return unwrap<T>(res);
  } catch (err) {
    return failed(0, `the API is not reachable at ${SERVER_BASE} (${String(err)})`);
  }
}

/** Fetch from the browser. */
export async function apiClient<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  if (DEMO_MODE) return DEMO_BLOCKED as ApiResult<T>;
  try {
    const res = await fetch(apiUrl(path), {
      signal: AbortSignal.timeout(30000),
      ...init,
      cache: "no-store",
      credentials: "include",
      headers: {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...(init?.headers ?? {}),
      },
    });
    return unwrap<T>(res);
  } catch (err) {
    return failed(0, `the API is not reachable at ${CLIENT_BASE || "(same origin, proxied)"} (${String(err)})`);
  }
}

/** POST/PATCH/DELETE from the browser. */
export function apiSend<T>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  body?: unknown
): Promise<ApiResult<T>> {
  return apiClient<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/* ---------------------------------------------------------------- payloads */
/* Only the fields the frontend reads. The backend sends more; these are the
   parts it is safe to depend on. `null` means "not knowable yet" — an
   unconnected integration — and renders as an em dash, which is different
   from a real zero. */

export type Nullable<T> = T | null;

export type ApiProject = { id: string; hostname: string; name: string };

export type ApiChrome = {
  account: {
    id: string;
    name: string;
    slug: string;
    kind: string;
    white_label: boolean;
    on_trial: boolean;
    trial_days_left: number;
  };
  page: string;
  projects: ApiProject[];
  project: Nullable<ApiProject>;
  alerts: number;
  range_label: string;
  initials: string;
  demo?: boolean;
};

export type ApiMe =
  | { signed_in: false; dev_no_auth: boolean }
  | {
      signed_in: true;
      dev_no_auth: boolean;
      user: Nullable<{ id: string; email: string }>;
      account: {
        id: string;
        name: string;
        slug: string;
        kind: string;
        on_trial: boolean;
        trial_days_left: number;
        projects: number;
      };
    };

export type ApiChartLine = {
  name: string;
  colour: string;
  path: string;
  area: string;
  points: { x: number; y: number; v: number }[];
};

export type ApiChart = {
  w: number;
  h: number;
  pad_l: number;
  uid: number;
  ticks: { y: number; label: string }[];
  xlabels: { x: number; label: string }[];
  lines: ApiChartLine[];
  max: number;
};

export type ApiDonut = {
  size: number;
  stroke: number;
  c: number;
  r: number;
  circ: number;
  total: number;
  label: string;
  empty: boolean;
  parts: { name: string; value: number; colour: string; pct: number; dash: number; offset: number }[];
};

export type ApiGauge = {
  size: number;
  stroke: number;
  c: number;
  r: number;
  circ: number;
  dash: number;
  value: Nullable<number>;
  suffix: string;
  tone: string;
  fs: number;
};

export type ApiProjectsPage = ApiChrome & {
  cards: {
    id: string;
    name: string;
    tagline: string;
    hostname: string;
    tone: string;
    initial: string;
    state: string;
    published: number;
    impact: Nullable<number>;
  }[];
  kpis: {
    projects: number;
    published: number;
    traffic: Nullable<number>;
    impressions: Nullable<number>;
    impact: Nullable<number>;
    synced: string;
  };
  trend: ApiChart;
  seo_health: ApiGauge;
  seo_rows: { label: string; value: Nullable<number> }[];
  geo_health: ApiGauge;
  geo_rows: { label: string; value: Nullable<number>; delta: Nullable<number>; colour: string }[];
  top: { title: string; sub: string; traffic: Nullable<number>; impressions: Nullable<number>; impact: Nullable<number> }[];
  dist: ApiDonut;
  activity: { icon: string; tone: string; title: string; sub: string; ago: string }[];
  table: {
    id: string;
    name: string;
    state: string;
    published: number;
    traffic: Nullable<number>;
    impressions: Nullable<number>;
    impact: Nullable<number>;
    updated: string;
  }[];
  opportunities: { title: string; sub: string; level: string }[];
  calendar: { dow: string; label: string; count: number; today: boolean; posts: { site: string; title: string }[] }[];
  automation: { icon: string; name: string; detail: string; state: string; note: string }[];
};

export type ApiOverviewPage = ApiChrome & {
  kpis: {
    published: number;
    queue: number;
    traffic: Nullable<number>;
    impact: Nullable<number>;
    sync: string;
    ai: Nullable<number>;
  };
  trend: ApiChart;
  ga: { value: Nullable<string>; label: string; delta?: Nullable<number> }[];
  presence: { icon: string; label: string; value: Nullable<string | number>; delta?: Nullable<number> }[];
  impact_posts: { title: string; traffic: Nullable<number>; impact: Nullable<number> }[];
  funnel: { label: string; n: number; colour: string }[];
  funnel_total: number;
  funnel_donut: ApiDonut;
  activity: { icon: string; tone: string; title: string; sub: string; ago: string }[];
  keywords: { kw: string; pos: number; traffic: number }[];
  opportunities: { topic: string; traffic: Nullable<number> }[];
  library: {
    id: string;
    title: string;
    state: string;
    published: string;
    traffic: Nullable<number>;
    impact: Nullable<number>;
  }[];
  health: { icon: string; name: string; state: string; ok: boolean; note: string }[];
};

export type ApiSeoPage = ApiChrome & {
  kpis: {
    queue: number;
    published: number;
    seo: Nullable<number>;
    impact: Nullable<number>;
    clicks: Nullable<number>;
    top10: Nullable<number>;
  };
  tab: string;
  counts: { queue: number; review: number; approved: number };
  rows: {
    id: string;
    title: string;
    topic: string;
    keywords: string;
    seo: Nullable<number>;
    impact: Nullable<number>;
    state: string;
  }[];
  impact: { title: string; traffic: Nullable<number>; impact: Nullable<number> }[];
  optimize: { topic: string; traffic: Nullable<number> }[];
  linking: { from: string; to: string; anchor: string }[];
  library: { id: string; title: string; state: string; published: string; impact: Nullable<number> }[];
  clusters: ApiDonut;
  keywords_total: Nullable<number>;
  health: ApiGauge;
  health_rows: { label: string; value: Nullable<number> }[];
};

export type ApiGeoPage = ApiChrome & {
  kpis: {
    queries: Nullable<number>;
    inclusion: Nullable<number>;
    citation: Nullable<number>;
    impact: Nullable<number>;
    coverage: Nullable<number>;
    trust: Nullable<number>;
  };
  platforms: ApiChart;
  rows: { id: string; title: string; type: string; prompts: Nullable<number>; score: Nullable<number>; updated: string }[];
  mentions: { title: string; value: number }[];
  citations: { title: string; value: number }[];
  clusters: { title: string; value: string }[];
  snippets: { query: string; quality: string; source: string; seen: string }[];
  breakdown: ApiDonut;
};

export type ApiNotificationsPage = ApiChrome & {
  kpis: {
    unread: number;
    approvals: number;
    automations: number;
    syncs: number;
    scheduled: number;
    status: string;
  };
  feed: { kind: string; tone: string; title: string; sub: string; ago: string; action: string; href: string }[];
  counts: { approval: number; automation: number; sync: number; reminder: number };
  total: number;
  over_time: ApiChart;
  reliability: ApiGauge;
  rel_rows: { label: string; value: number; colour: string }[];
  alerts: { title: string; ago: string }[];
  reminders: { title: string; when: string; tag: string }[];
  approvals: { title: string; type: string; ago: string; level: string }[];
  failed: { name: string; type: string; ago: string; state: string }[];
  channels: { icon: string; name: string; value: Nullable<number> }[];
  rules: { icon: string; name: string; sub: string; on: boolean }[];
  resolved: { issue: string; type: string; at: string; by: string; note: string }[];
};

export type ApiHistoryPage = ApiChrome & {
  kpis: {
    total: number;
    published: number;
    updates: number;
    syncs: number;
    automation: number;
    failed: number;
  };
  trend: ApiChart;
  cats: ApiDonut;
  cat_rows: { name: string; value: number; colour: string }[];
  stream: { icon: string; tone: string; title: string; sub: string; ago: string; state: string }[];
  log: { when: string; type: string; desc: string; content: string; actor: string; initials: string; state: string }[];
  actors: { name: string; initials: string; value: number; pct: number }[];
  areas: { title: string; value: number; value2?: string }[];
  edited: { title: string; value: number }[];
  publishes: { title: string; sub?: string; value: string }[];
  reverts: { title: string; value: string }[];
};

export type ApiSettingsPage = ApiChrome & {
  sharing: { public: boolean; can_share: boolean; report_url: Nullable<string> };
  profile: { name: string; slug: string; kind: string; created: string; email: string; white_label: boolean };
  counts: { members: number; services: number; projects: number; published: number };
  seats: { name: string; email: string; role: string; perms: string; active: string; initials: string }[];
  plan: { name: string; price: string; unit: string; state: string; days: number; monthly: string; features: string[]; subscribed: boolean };
  usage: { label: string; used: Nullable<number>; cap: Nullable<number> }[];
  apis: { name: string; account: string; state: string; ok: boolean; perms: string; since: string }[];
  keys: { label: string; prefix: string; created: string; used: string }[];
  security: { name: string; sub: string; state: string; ok: boolean }[];
  prefs: { name: string; sub: string; on: boolean }[];
  defaults: { label: string; value: string }[];
  limits: { label: string; used: Nullable<number>; cap: Nullable<number> }[];
  webhooks: { active: number; delivered: Nullable<number>; rate: Nullable<number> };
};

export type ApiProjectSettingsPage = ApiChrome & {
  apis: ApiSettingsPage["apis"];
};

export type ApiChangeRow = {
  id: string; site_id: string; hostname: string; client: Nullable<string>;
  page: Nullable<string>; kind: string; title: string; detail: Nullable<string>;
  state: "proposed" | "approved" | "published" | "failed" | "rejected" | "reverted";
  error: Nullable<string>; platform: Nullable<string>; can_publish: boolean; at: string;
};
export type ApiChangesPage = {
  rows: ApiChangeRow[];
  counts: Record<string, number>;
  connected: number;
  sites: number;
};

/* ------------------------------------------------------------------ calls */

export const api = {
  me: () => apiServer<ApiMe>("/api/me"),
  // projects(), settings() and projectSettings() are called from Client
  // Components (app/projects/page.tsx, app/projects/settings/page.tsx,
  // app/app/settings/page.tsx -- all "use client", fetching in a
  // useEffect), never from a Server Component. apiServer needs
  // next/headers, which does not exist in the browser -- calling it from
  // client-side code throws, so `live` state on these pages was never
  // actually populated. apiClient is the correct fetch for these; every
  // other entry below runs inside a real Server Component and keeps
  // apiServer.
  projects: () => apiClient<ApiProjectsPage>("/api/projects"),
  overview: (project = "") =>
    apiServer<ApiOverviewPage>(`/api/overview${project ? `?project=${encodeURIComponent(project)}` : ""}`),
  seo: (project = "", tab = "queue") =>
    apiServer<ApiSeoPage>(
      `/api/seo?tab=${encodeURIComponent(tab)}${project ? `&project=${encodeURIComponent(project)}` : ""}`
    ),
  geo: (project = "") =>
    apiServer<ApiGeoPage>(`/api/geo${project ? `?project=${encodeURIComponent(project)}` : ""}`),
  notifications: () => apiServer<ApiNotificationsPage>("/api/notifications"),
  history: () => apiServer<ApiHistoryPage>("/api/history"),
  // Account-wide only (workspace profile, team, billing, ...) -- reached
  // from /projects' account menu, not from the per-project dashboard sidebar.
  settings: () => apiClient<ApiSettingsPage>("/api/settings"),
  // /app/settings' real data: one project's own connectors, scoped the same
  // way overview()/seo()/geo() are -- empty defaults to the account's first
  // site (same as those three), a real id 404s if it isn't yours.
  projectSettings: (project = "") =>
    apiClient<ApiProjectSettingsPage>(`/api/project-settings${project ? `?project=${encodeURIComponent(project)}` : ""}`),
  // Client-fetched like projects()/settings() -- this page is its own
  // bespoke route, not one of the five overlay-driven LivePageKey pages.
  // `project` scopes to one site's own changes; omitted, this is the
  // account-wide /app/publish queue.
  changes: (project = "") =>
    apiClient<ApiChangesPage>(`/api/changes${project ? `?project=${encodeURIComponent(project)}` : ""}`),
};

/* ------------------------------------------------- browser-side mutations */

export const actions = {
  signIn: (accessToken: string, workspaceName?: string) =>
    apiSend<{ ok: true; email: string }>("/api/session", "POST", {
      access_token: accessToken,
      workspace_name: workspaceName ?? "",
    }),
  signOut: () => apiSend<{ ok: true }>("/api/logout", "POST"),
  /** Ends every FIG session for the person this Supabase token belongs to. Called by the reset-password page. */
  revokeSessions: (accessToken: string) =>
    apiSend<{ ok: true }>("/api/session/revoke", "POST", { access_token: accessToken }),
  renameWorkspace: (name: string) =>
    apiSend<{ ok: true; profile: { name: string; slug: string } }>("/api/settings/profile", "PATCH", { name }),
  /** Deletes the workspace and everything in it. `confirm` must be the account email. */
  deleteAccount: (confirm: string) =>
    apiSend<{ deleted: true; sites: number; subscription_cancelled: boolean; sign_in_record_deleted: boolean }>(
      "/api/account/delete", "POST", { confirm }),
  addProject: (hostname: string, name?: string) =>
    apiSend<{ id: string; hostname: string; scan_id: string }>("/api/projects", "POST", { hostname, name }),
  removeProject: (id: string) => apiSend<{ ok: true }>(`/api/projects/${id}`, "DELETE"),
  auditProject: (id: string) => apiSend<{ ok: true; scan_id: string }>(`/api/projects/${id}/audit`, "POST"),
  shareProject: (id: string, isPublic: boolean) =>
    apiSend<{ ok: true; public: boolean; report_url: string | null }>(`/api/projects/${id}/share`, "POST", { public: isPublic }),
  connectIntegration: (projectId: string, platform: string, endpoint: string, credential: string) =>
    apiSend<{ id: string; platform: string; connected: boolean; hint: string | null; error: string | null }>(
      "/api/integrations", "POST", { project_id: projectId, platform, endpoint, credential }),
  startCheckout: () => apiSend<{ url: string; quantity: number; trial_days: number }>("/api/billing/checkout", "POST"),
  startPortal: () => apiSend<{ url: string }>("/api/billing/portal", "POST"),
  auditAll: () => apiSend<{ ok: true; queued: number }>("/api/audit-all", "POST"),
  proposeBriefs: () => apiSend<{ ok: true; briefs: number }>("/api/content/propose", "POST"),
  moveContent: (id: string, to: string) => apiSend<unknown>(`/api/content/${id}/move`, "POST", { to }),
  saveContent: (id: string, body: string) => apiSend<unknown>(`/api/content/${id}`, "PATCH", { body }),
  proposeChanges: (project = "") =>
    apiSend<{ ok: true; changes: number }>(
      `/api/changes/propose${project ? `?project=${encodeURIComponent(project)}` : ""}`, "POST"),
  changeAction: (id: string, action: "approve" | "reject" | "publish" | "revert") =>
    apiSend<unknown>(`/api/changes/${id}/${action}`, "POST"),
};

/** A one-way, per-browser id for the free scan's rate limit -- not identity,
 * just lets the backend tell "this browser's 3rd scan today" from a fresh
 * one. Regenerated if localStorage is unavailable (private browsing, etc.),
 * which only means that visit gets its own bucket rather than persisting. */
function freeScanDeviceId(): string {
  try {
    const key = "fig_free_scan_device";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const id = crypto.randomUUID();
    localStorage.setItem(key, id);
    return id;
  } catch {
    return crypto.randomUUID();
  }
}

export type PublicScanStart = { scan_id: string; hostname: string; status: string; poll: string; cached?: boolean };
export type PublicScanStatus =
  | { scan_id: string; hostname: string; status: "queued" | "running"; error?: null }
  | { scan_id: string; hostname: string; status: "failed"; error: string | null }
  | { scan_id: string; hostname: string; status: "done"; [key: string]: unknown };

/** The free, unauthenticated scan -- app/public.py, no session cookie involved. */
export const publicScan = {
  start: (url: string, share = true) =>
    apiSend<PublicScanStart>("/scan", "POST", { url, device_id: freeScanDeviceId(), share }),
  status: (scanId: string) => apiClient<PublicScanStatus>(`/scan/${scanId}`),
  library: (limit = 30) =>
    apiClient<{ library: unknown[]; total_sites: number }>(`/scan/library?limit=${limit}`),
};

/** Format a nullable number the way the backend intends: null is unknown. */
export function fmt(value: Nullable<number>, opts?: { suffix?: string; compact?: boolean }): string {
  if (value === null || value === undefined) return "—";
  const suffix = opts?.suffix ?? "";
  if (opts?.compact) {
    if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1).replace(/\.0$/, "")}M${suffix}`;
    if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1).replace(/\.0$/, "")}K${suffix}`;
  }
  return `${value.toLocaleString("en-US")}${suffix}`;
}

/** "+12.4%" / "-3%" / "" — the change string the metric cards expect. */
export function delta(value: Nullable<number>, suffix = "%"): string {
  if (value === null || value === undefined || value === 0) return "";
  return `${value > 0 ? "+" : ""}${value}${suffix}`;
}
