/**
 * A diagnostics surface: proves the frontend can reach the FIG backend and
 * shows each dashboard page rendered from live data.
 *
 * Not part of the product navigation. It exists so the API wiring can be
 * checked without editing the designed pages, and so a broken connection is
 * legible rather than silent. Delete it once the real pages are wired.
 *
 * Wiring a real page is two lines — see the bottom of this file.
 */

import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { api, apiUrl } from "@/lib/api";
import { fetchOverlay, type LivePageKey } from "@/lib/live";

export const metadata = { title: "Live data check — FIG" };

const KEYS: LivePageKey[] = ["overview", "seo", "geo", "notifications", "history"];

export default async function Page({
  searchParams,
}: {
  // Next 16: searchParams is a Promise in Server Components.
  searchParams: Promise<{ page?: string }>;
}) {
  const { page } = await searchParams;
  const key: LivePageKey = KEYS.includes(page as LivePageKey) ? (page as LivePageKey) : "overview";

  const [me, result] = await Promise.all([api.me(), fetchOverlay(key)]);

  const reachable = me.ok;
  const signedIn = me.ok && me.data.signed_in;
  const devNoAuth = me.ok && me.data.dev_no_auth;
  const workspace = me.ok && me.data.signed_in ? me.data.account.name : "";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <section
        style={{
          border: "1px solid rgba(148,163,184,.28)",
          borderRadius: 14,
          padding: "18px 20px",
          background: reachable ? "rgba(16,185,129,.06)" : "rgba(239,68,68,.06)",
        }}
      >
        <h2 style={{ margin: 0, fontSize: 17, letterSpacing: "-.02em" }}>
          Backend {reachable ? "reachable" : "unreachable"}
        </h2>
        <dl
          style={{
            margin: "14px 0 0",
            display: "grid",
            gridTemplateColumns: "170px 1fr",
            gap: "8px 16px",
            fontSize: 13.5,
          }}
        >
          <dt style={{ opacity: 0.62 }}>API base</dt>
          <dd style={{ margin: 0, fontFamily: "ui-monospace, monospace" }}>{apiUrl("/api")}</dd>

          <dt style={{ opacity: 0.62 }}>Session</dt>
          <dd style={{ margin: 0 }}>
            {!reachable
              ? "— (no connection)"
              : signedIn
                ? `signed in${devNoAuth ? " via FIG_DEV_NO_AUTH" : ""}`
                : "not signed in"}
          </dd>

          <dt style={{ opacity: 0.62 }}>Workspace</dt>
          <dd style={{ margin: 0 }}>{workspace || "—"}</dd>

          <dt style={{ opacity: 0.62 }}>Overlay for “{key}”</dt>
          <dd style={{ margin: 0 }}>
            {result.live
              ? `live${result.demo ? " (seeded demo estate)" : ""} · ` +
                `${Object.keys(result.overlay.metrics).length} metrics, ` +
                `${Object.keys(result.overlay.rows).length} sections`
              : `falling back to the static preview — ${result.reason}`}
          </dd>
        </dl>

        {!reachable && (
          <p style={{ margin: "14px 0 0", fontSize: 13, lineHeight: 1.6, opacity: 0.75 }}>
            Start the backend with <code>uvicorn app.main:app --port 8000</code> from the repo
            root, and set <code>NEXT_PUBLIC_API_URL</code> if it is not on port 8000. With
            <code> FIG_DEV_NO_AUTH=1</code> it resolves to the seeded demo workspace, so there is
            data to look at without a sign-in flow.
          </p>
        )}

        <nav style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
          {KEYS.map((k) => (
            <a
              key={k}
              href={`/app/live?page=${k}`}
              style={{
                padding: "6px 12px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                textDecoration: "none",
                border: "1px solid rgba(148,163,184,.3)",
                background: k === key ? "rgba(99,102,241,.14)" : "transparent",
                color: "inherit",
              }}
            >
              {k}
            </a>
          ))}
        </nav>
      </section>

      {/*
        This is the whole integration. To make a designed page live, its route
        becomes a Server Component that does:

            const { overlay } = await fetchOverlay("seo");
            return <LiveDashboardPage page="seo" overlay={overlay} />;

        instead of `<DashboardPage page="seo" />`. Structure, icons and copy
        all still come from lib/dashboard-pages.ts.
      */}
      <LiveDashboardPage page={key} overlay={result.overlay} />
    </div>
  );
}
