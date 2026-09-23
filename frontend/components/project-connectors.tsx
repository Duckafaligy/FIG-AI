"use client";

import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { BarChart3, Check, CircleDashed, Github, Globe2, LayoutTemplate, Layers, LockKeyhole, Search, ShoppingBag } from "lucide-react";
import { actions, apiUrl, type ApiSettingsPage } from "@/lib/api";
import { IntegrationLogo } from "@/components/integration-logo";

type Service = { name: string; detail: string; icon: React.ComponentType<{ size?: number }> };

// Only the two groups that are genuinely per-project (every Integration row
// is owned by one site_id in the database) -- account-wide services
// (Supabase, Anthropic, Stripe, Webhooks) live in Settings, not here.
const GROUPS: { title: string; description: string; services: Service[] }[] = [
  {
    title: "Publishing & repositories",
    description: "Connect this project's CMS or source repository. Available fixes depend on the platform and permissions you grant.",
    services: [
      { name: "WordPress", detail: "Publishing destination", icon: Globe2 },
      { name: "Shopify", detail: "Publishing destination", icon: ShoppingBag },
      { name: "Webflow", detail: "Publishing destination", icon: Layers },
      { name: "Wix", detail: "Publishing destination", icon: LayoutTemplate },
      { name: "GitHub", detail: "Self-hosted / Git-deployed sites", icon: Github },
    ],
  },
  {
    title: "Analytics & search",
    description: "Read-only connections for this project's traffic and search data.",
    services: [
      { name: "Google Analytics", detail: "Traffic and conversions", icon: BarChart3 },
      { name: "Google Search Console", detail: "Queries and indexing", icon: Search },
    ],
  },
];

function IntegrationDialog({ title, busy = false, onClose, children }: { title: string; busy?: boolean; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close(); }, []);
  return <dialog ref={ref} className="settings-connect-dialog" aria-labelledby={titleId} aria-busy={busy} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}>
    <header><div><span>Site connection</span><h2 id={titleId}>{title}</h2></div><button type="button" aria-label="Close connection dialog" disabled={busy} onClick={onClose}>×</button></header>
    {children}
  </dialog>;
}

export function ProjectConnectors({ projectId, apis, onChanged }: {
  projectId: string;
  apis: ApiSettingsPage["apis"];
  onChanged: () => void | Promise<void>;
}) {
  const liveApi = (name: string) => apis.find((a) => a.name === name);

  const [wpFormOpen, setWpFormOpen] = useState(false);
  const [wpBusy, setWpBusy] = useState(false);
  const [wpError, setWpError] = useState("");
  const submitWordPress = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const siteUrl = String(form.get("site-url") ?? "").trim();
    const username = String(form.get("username") ?? "").trim();
    const appPassword = String(form.get("app-password") ?? "").trim();
    setWpBusy(true);
    setWpError("");
    const result = await actions.connectIntegration(projectId, "wordpress", siteUrl, `${username}:${appPassword}`);
    setWpBusy(false);
    if (!result.ok) { setWpError(result.error); return; }
    if (!result.data.connected) { setWpError(result.data.error ?? "couldn't connect"); return; }
    setWpFormOpen(false);
    await onChanged();
  };

  const [shopifyFormOpen, setShopifyFormOpen] = useState(false);
  const [shopifyShop, setShopifyShop] = useState("");
  const submitShopify = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const raw = shopifyShop.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
    const shop = raw.includes(".") ? raw : `${raw}.myshopify.com`;
    window.location.href = apiUrl(`/oauth/shopify/start?site_id=${projectId}&shop=${encodeURIComponent(shop)}`);
  };

  const [githubFormOpen, setGithubFormOpen] = useState(false);
  const [githubRepo, setGithubRepo] = useState("");
  const submitGithub = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const raw = githubRepo.trim().replace(/^https?:\/\/(www\.)?github\.com\//, "").replace(/\/$/, "");
    window.location.href = apiUrl(`/oauth/github/start?site_id=${projectId}&repo=${encodeURIComponent(raw)}`);
  };

  return (
    <div className="settings-tab-stack settings-integrations-panel">
      {GROUPS.map(group => (
        <section className="settings-surface" key={group.title}>
          <div className="settings-integration-group" aria-label={group.title}>
            <h4>{group.title}</h4>
            <p>{group.description}</p>
            <div className="settings-integration-list">
              {group.services.map((service) => {
                const ServiceIcon = service.icon;
                const isGoogleAnalytics = service.name === "Google Analytics";
                const isGoogleSearchConsole = service.name === "Google Search Console";
                const isWordPress = service.name === "WordPress";
                const isShopify = service.name === "Shopify";
                const isWebflow = service.name === "Webflow";
                const isWix = service.name === "Wix";
                const isGithub = service.name === "GitHub";
                const remote = liveApi(service.name);
                const statusText = remote?.state || "Unavailable";
                const tone = remote?.ok ? "green" : "neutral";
                return (
                  <article key={service.name}>
                    <span className="settings-service-icon settings-integration-brand"><IntegrationLogo name={service.name} /></span>
                    <div className="settings-integration-identity">
                      <strong>{service.name}</strong>
                      <small>{remote?.account || "Account information unavailable"}</small>
                      <small>Connected since: {remote?.since && remote.since !== "—" ? remote.since : "Unavailable"}</small>
                    </div>
                    <span className="settings-service-permission"><small>Access</small>{remote?.perms || "Unavailable"}</span>
                    <b className={`settings-status settings-status--${tone}`}>{remote?.ok ? <Check size={12} /> : <CircleDashed size={12} />}{statusText}</b>
                    {(isGoogleAnalytics || isGoogleSearchConsole) ? (
                      <a className="settings-row-action button button--small" href={apiUrl(`/oauth/google/start?site_id=${projectId}`)}>{remote?.ok ? "Reconnect" : "Connect"}</a>
                    ) : isWordPress ? (
                      <button type="button" className="settings-row-action button button--small" onClick={() => setWpFormOpen((open) => !open)}>{remote?.ok ? "Reconnect" : "Connect"}</button>
                    ) : isShopify ? (
                      <button type="button" className="settings-row-action button button--small" onClick={() => setShopifyFormOpen((open) => !open)}>{remote?.ok ? "Reconnect" : "Connect"}</button>
                    ) : isWebflow ? (
                      <a className="settings-row-action button button--small" href={apiUrl(`/oauth/webflow/start?site_id=${projectId}`)}>{remote?.ok ? "Reconnect" : "Connect"}</a>
                    ) : isWix ? (
                      <a className="settings-row-action button button--small" href={apiUrl(`/oauth/wix/start?site_id=${projectId}`)}>{remote?.ok ? "Reconnect" : "Connect"}</a>
                    ) : isGithub ? (
                      <button type="button" className="settings-row-action button button--small" onClick={() => setGithubFormOpen((open) => !open)}>{remote?.ok ? "Reconnect" : "Connect"}</button>
                    ) : <ServiceIcon size={14} />}
                  </article>
                );
              })}
            </div>
          </div>
        </section>
      ))}

      {wpFormOpen && (
        <IntegrationDialog title="Connect WordPress" busy={wpBusy} onClose={() => { setWpFormOpen(false); setWpError(""); }}>
          <form onSubmit={submitWordPress} className="settings-connect-form">
            <div className="auth-fields">
              <label className="auth-field" htmlFor="wp-site-url"><span>Site URL</span><input id="wp-site-url" name="site-url" required placeholder="https://yoursite.com" /></label>
              <label className="auth-field" htmlFor="wp-username"><span>Username</span><input id="wp-username" name="username" required placeholder="your WordPress username" /></label>
              <label className="auth-field" htmlFor="wp-app-password"><span>Application password</span><input id="wp-app-password" name="app-password" type="password" autoComplete="off" required placeholder="Your WordPress application password" /></label>
            </div>
            <p>Use an Application Password, not your login password. Generate one in WordPress under Users → Profile → Application Passwords. FIG tests the connection before saving it.</p>
            {wpError && <p className="form-message" role="alert">{wpError}</p>}
            <div className="settings-connect-actions">
              <button className="button button--small" type="submit" disabled={wpBusy}>{wpBusy ? "Connecting…" : "Connect WordPress"}</button>
              <button className="secondary-button" type="button" onClick={() => setWpFormOpen(false)} disabled={wpBusy}>Cancel</button>
            </div>
          </form>
        </IntegrationDialog>
      )}
      {shopifyFormOpen && (
        <IntegrationDialog title="Connect Shopify" onClose={() => setShopifyFormOpen(false)}>
          <form onSubmit={submitShopify} className="settings-connect-form">
            <label className="auth-field" htmlFor="shopify-store"><span>Store</span><input id="shopify-store" required placeholder="your-store or your-store.myshopify.com" value={shopifyShop} onChange={(event) => setShopifyShop(event.target.value)} /></label>
            <p>Use your store's myshopify.com domain. You'll continue to Shopify to review the requested access and approve the connection. Supported fixes require your approval in FIG.</p>
            <div className="settings-connect-actions">
              <button className="button button--small" type="submit">Continue to Shopify</button>
              <button className="secondary-button" type="button" onClick={() => setShopifyFormOpen(false)}>Cancel</button>
            </div>
          </form>
        </IntegrationDialog>
      )}
      {githubFormOpen && (
        <IntegrationDialog title="Connect GitHub" onClose={() => setGithubFormOpen(false)}>
          <form onSubmit={submitGithub} className="settings-connect-form">
            <label className="auth-field" htmlFor="github-repo"><span>Repository</span><input id="github-repo" required placeholder="owner/repo or a github.com URL" value={githubRepo} onChange={(event) => setGithubRepo(event.target.value)} /></label>
            <p>Continue to GitHub to authorize access. Supported fixes open pull requests for your review rather than changing your default branch directly.</p>
            <p className="settings-connect-warning">GitHub's OAuth repo permission can cover all repositories your account can access—not only the repository entered here. Review the consent screen before continuing.</p>
            <div className="settings-connect-actions">
              <button className="button button--small" type="submit">Continue to GitHub</button>
              <button className="secondary-button" type="button" onClick={() => setGithubFormOpen(false)}>Cancel</button>
            </div>
          </form>
        </IntegrationDialog>
      )}

      <section className="settings-surface settings-integration-note">
        <LockKeyhole size={19} />
        <div><strong>You review access before connecting</strong><p>OAuth authorization happens on the provider's site. WordPress uses an Application Password sent to FIG's backend for verification and encrypted storage. Reconnect repeats authorization; connection status is not a last-sync report.</p></div>
      </section>
    </div>
  );
}
