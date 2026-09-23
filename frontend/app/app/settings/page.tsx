"use client";

import { ServiceUnavailable } from "@/components/service-unavailable";

import { useEffect, useState, type ComponentType, type KeyboardEvent } from "react";
import {
  BadgeCheck,
  Bell,
  BrainCircuit,
  Check,
  CheckCheck,
  ChevronRight,
  CircleDashed,
  Copy,
  CreditCard,
  FileText,
  Globe2,
  KeyRound,
  Link2,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Users,
  Webhook
} from "lucide-react";
import { DashboardHeader } from "@/components/dashboard-shell";
import { AccountControls } from "@/components/account-controls";
import { PreviewInfo } from "@/components/preview-info";
import { actions, api, fmt, type ApiSettingsPage } from "@/lib/api";

type Icon = ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
type TabId = "workspace" | "team" | "billing" | "security" | "notifications" | "defaults" | "webhooks";

const members = [
  ["JD", "Jordan Davis", "Owner", "All workspace permissions", "Active", "2 hours ago"],
  ["MC", "Maya Chen", "Admin", "Projects, settings, billing", "Active", "4 hours ago"],
  ["PS", "Priya Shah", "Content manager", "Create, edit, publish", "Active", "Yesterday"],
  ["DR", "Daniel Reyes", "SEO specialist", "SEO, GEO, analytics", "Active", "3 hours ago"],
  ["EP", "Emma Patel", "Analyst", "View analytics and reports", "Active", "6 hours ago"]
];

const usage = [["Content drafts", "126 / 500", "25%"], ["API credits", "48.2K / 100K", "48%"], ["AI generations", "312K / 1M", "31%"], ["Team seats", "5 / 10", "50%"]];

const allTabs: { id: TabId; label: string; description: string; icon: Icon }[] = [
  { id: "workspace", label: "Workspace", description: "Profile, plan, and workspace summary", icon: Settings2 },
  { id: "team", label: "Team & roles", description: "People, access, and permissions", icon: Users },
  { id: "billing", label: "Billing & usage", description: "Plan and account usage", icon: CreditCard },
  { id: "security", label: "Security", description: "Authentication and access controls", icon: ShieldCheck },
  { id: "notifications", label: "Notifications", description: "Delivery and alert preferences", icon: Bell },
  { id: "defaults", label: "Content defaults", description: "Writing and output preferences", icon: SlidersHorizontal },
  { id: "webhooks", label: "Webhooks", description: "Event delivery configuration", icon: Webhook }
];

function LocalToggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return <div className="settings-toggle-row"><div><strong>{label}</strong><span>{description}</span></div><button type="button" className={`settings-switch${checked ? " is-on" : ""}`} aria-label={`${checked ? "Disable" : "Enable"} ${label} in local preview`} aria-pressed={checked} onClick={onChange}><i /></button></div>;
}

function UsageCards({ rows }: { rows: { label: string; value: string; percent: string }[] }) {
  return <div className="settings-usage-cards">{rows.map(({ label, value, percent }) => <article key={label}><div><span>{label}</span><strong>{value}</strong></div><small>{percent} of allowance</small><i><b style={{ width: percent }} /></i></article>)}</div>;
}

function usagePercent(used: number | null, cap: number): string {
  if (used === null || cap <= 0) return "0%";
  return `${Math.min(100, Math.round((used / cap) * 100))}%`;
}

const tabs = allTabs.filter(tab => ["workspace", "team", "billing"].includes(tab.id));

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("workspace");
  const [settings, setSettings] = useState({ twoFactor: false, email: true, project: true, system: false, browser: true, approval: true, publish: false });
  const [defaultsSaved, setDefaultsSaved] = useState(false);
  useEffect(() => {
    if (activeTab !== "defaults") return;
    try {
      const saved = JSON.parse(sessionStorage.getItem("fig-content-defaults") ?? "{}");
      document.querySelectorAll<HTMLSelectElement>(".settings-defaults-form select").forEach((field) => {
        if (typeof saved[field.name] === "string" && Array.from(field.options).some(option => option.value === saved[field.name])) field.value = saved[field.name];
      });
    } catch { /* Storage is optional; fields still work without it. */ }
  }, [activeTab]);
  const [live, setLive] = useState<ApiSettingsPage | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [sharingBusy, setSharingBusy] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  const loadSettings = () => api.settings().then((result) => {
    if (result.ok) setLive(result.data);
    return result;
  });
  useEffect(() => {
    let cancelled = false;
    api.settings().then((result) => {
      if (cancelled) return;
      setLoading(false);
      if (result.ok && !result.data.demo) setLive(result.data);
      else setLoadError(result.ok ? "This account contains seeded demo data. Use a real workspace to continue." : "Unable to load account settings. Please sign in or retry.");
    });
    return () => {
      cancelled = true;
    };
  }, []);
  const liveProjectId = live?.project?.id ?? null;

  const toggleSharing = async () => {
    if (!liveProjectId || !live) return;
    setSharingBusy(true);
    const result = await actions.shareProject(liveProjectId, !live.sharing.public);
    if (!result.ok) { setSharingBusy(false); setLoadError(result.error); return; }
    await loadSettings();
    setSharingBusy(false);
  };
  const copyReportLink = () => {
    if (!live?.sharing.report_url) return;
    navigator.clipboard?.writeText(live.sharing.report_url).then(() => {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    });
  };
  const [billingBusy, setBillingBusy] = useState<"checkout" | "portal" | null>(null);
  const [billingError, setBillingError] = useState("");
  const goToCheckout = async () => {
    setBillingBusy("checkout");
    setBillingError("");
    const result = await actions.startCheckout();
    if (!result.ok) {
      setBillingError(result.error);
      setBillingBusy(null);
      return;
    }
    window.location.href = result.data.url;
  };
  const goToPortal = async () => {
    setBillingBusy("portal");
    setBillingError("");
    const result = await actions.startPortal();
    if (!result.ok) {
      setBillingError(result.error);
      setBillingBusy(null);
      return;
    }
    window.location.href = result.data.url;
  };
  const usageRows = live
    ? live.usage.map((u) => ({
        label: u.label,
        value: `${fmt(u.used)} / ${fmt(u.cap)}`,
        percent: usagePercent(u.used, u.cap ?? 0),
      }))
    : usage.map(([label, value, percent]) => ({ label, value, percent }));
  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];
  const ActiveIcon = active.icon;
  const flip = (key: keyof typeof settings) => setSettings((current) => ({ ...current, [key]: !current[key] }));
  const tabId = (tab: TabId) => `settings-tab-${tab}`;
  const panelId = (tab: TabId) => `settings-panel-${tab}`;
  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const nextIndex = event.key === "ArrowRight" ? (index + 1) % tabs.length
      : event.key === "ArrowLeft" ? (index + tabs.length - 1) % tabs.length
        : event.key === "Home" ? 0
          : event.key === "End" ? tabs.length - 1
            : null;
    if (nextIndex === null) return;
    event.preventDefault();
    const nextTab = tabs[nextIndex];
    setActiveTab(nextTab.id);
    event.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`#${tabId(nextTab.id)}`)?.focus();
  };

  if (loading) return <p role="status">Loading settings…</p>;
  if (!live) return <ServiceUnavailable message={loadError} />;
  return <>
    <DashboardHeader eyebrow="Settings" title="Settings & workspace configuration" description="Manage workspace details, team access, integrations, and content preferences." action="Edit profile" />
    {loadError && <p className="form-message" role="alert">{loadError}</p>}
    <div className="settings-tabbed-workbench">
      <aside className="settings-tab-sidebar" aria-label="Settings sections">
        <div className="settings-sidebar-workspace"><span className="settings-workspace-mark">{live ? live.initials : "LV"}</span><div><strong>{live ? live.profile.name : "LaunchVault.ca"}</strong><small>{live ? "Connected workspace" : "Frontend preview"}</small></div><ChevronRight size={15} /></div>
        <nav role="tablist" aria-label="Workspace settings">
          {tabs.map((tab, index) => { const TabIcon = tab.icon; const selected = tab.id === activeTab; return <button type="button" key={tab.id} id={tabId(tab.id)} role="tab" aria-controls={panelId(tab.id)} aria-selected={selected} tabIndex={selected ? 0 : -1} className={selected ? "is-active" : ""} onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => handleTabKeyDown(event, index)}><TabIcon size={17} /><span>{tab.label}</span></button>; })}
        </nav>
        <div className="settings-sidebar-note"><CircleDashed size={15} /><span><strong>Connected workspace</strong>Supported actions are saved by the backend. Unavailable controls are identified explicitly.</span></div>
      </aside>

      <section className="settings-tab-content" role="tabpanel" id={panelId(activeTab)} aria-labelledby={tabId(activeTab)}>
        <header className="settings-tab-header"><span className="settings-tab-icon"><ActiveIcon size={19} /></span><div><h2>{active.label}</h2><p>{active.description}</p></div><span className="settings-demo-chip"><span />{live ? live.profile.name : "LaunchVault.ca demo"}</span></header>

        {activeTab === "workspace" && <div className="settings-tab-stack">
          <section className="settings-surface settings-workspace-surface"><div className="settings-surface-heading"><div><h3>Workspace profile</h3><p>{live ? "The account behind this workspace." : "The core details shown throughout this frontend preview."}</p></div><PreviewInfo className="settings-link-button" label="Edit profile" message="Workspace editing isn't wired up yet. No change is sent to Supabase or any connected service." /></div><div className="settings-workspace-profile"><span className="settings-profile-logo">{live ? live.initials : "LV"}</span><div><strong>{live ? live.profile.name : "LaunchVault.ca"}</strong>{!live && <p>Plain-English AI lessons, prompts, courses, and practical workflows.</p>}<span><BadgeCheck size={13} />{live ? (live.profile.kind === "Direct" ? "Direct workspace" : live.profile.kind) : "Preview workspace"}</span></div></div><div className="settings-fact-grid"><article><span>Workspace ID</span><strong>{live ? live.profile.slug : "lv_workspace_01"}</strong></article><article><span>Owner</span><strong>{live ? (live.seats[0]?.email ?? "—") : "Jordan Davis"}</strong></article><article><span>Industry</span><strong>{live ? "—" : "Education & technology"}</strong></article><article><span>Timezone</span><strong>{live ? "—" : "Eastern Time"}</strong></article><article><span>Website</span><strong>{live ? (live.project?.hostname ?? "—") : "launchvault.ca"}</strong></article><article><span>Created</span><strong>{live ? live.profile.created : "Sep 13, 2026"}</strong></article></div></section>
          <div className="settings-two-column"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Workspace at a glance</h3><p>{live ? "Real counters for this workspace." : "Sample counters for this one project."}</p></div></div><div className="settings-glance-grid"><article><Users size={18} /><strong>{live ? live.counts.members : 5}</strong><span>Team members</span></article><article><Link2 size={18} /><strong>{live ? live.counts.services : 8}</strong><span>Services connected</span></article><article><FileText size={18} /><strong>{live ? live.counts.projects : 1500}</strong><span>{live ? "Projects" : "Library items"}</span></article><article><BrainCircuit size={18} /><strong>{live ? live.counts.published : 50}</strong><span>{live ? "Published posts" : "Topics"}</span></article></div></section><section className="settings-surface settings-plan-surface"><div className="settings-surface-heading"><div><h3>Current plan</h3><p>{live ? (live.plan.state === "Trial" ? `${live.plan.days} day${live.plan.days === 1 ? "" : "s"} left in trial.` : "Billed per site.") : "Billing is not connected."}</p></div>{live ? (
              <button type="button" className="settings-link-button" onClick={live.plan.subscribed ? goToPortal : goToCheckout} disabled={billingBusy !== null}>
                {billingBusy ? "Redirecting…" : live.plan.subscribed ? "Manage billing" : "Subscribe"}
              </button>
            ) : (
              <PreviewInfo className="settings-link-button" label="Manage billing" message="Stripe checkout and the customer portal aren't wired up from this page yet." />
            )}</div><strong className="settings-plan-name">{live ? live.plan.name : "Pro"} <span>{live ? live.plan.state.toLowerCase() : "preview"}</span></strong><div className="settings-plan-price">{live ? live.plan.price : "$79"} <small>/ {live ? live.plan.unit : "month"}</small></div><p>{live ? "Real trial/plan state for this account." : "Team workflow, writing tools, and analytics shown as a product preview."}</p>{billingError && <p className="form-message" role="alert">{billingError}</p>}</section></div>

          <section className="settings-surface">
            <div className="settings-surface-heading">
              <div><h3>Public report link</h3><p>{live ? "Share your latest audit with anyone, no sign-in required." : "Sharing needs a real connected workspace."}</p></div>
              {live && <Globe2 size={19} aria-hidden="true" />}
            </div>
            {!live ? (
              <p style={{ opacity: 0.7, fontSize: 14 }}>This preview has no real scan to share. Sign in and run an audit to enable this.</p>
            ) : !live.sharing.can_share ? (
              <p style={{ opacity: 0.7, fontSize: 14 }}>Run your first audit to get a report worth sharing.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="settings-toggle-row">
                  <div><strong>{live.sharing.public ? "Report is public" : "Report is private"}</strong><span>{live.sharing.public ? "Anyone with the link can view your latest audit." : "Only your workspace can see this audit."}</span></div>
                  <button type="button" className={`settings-switch${live.sharing.public ? " is-on" : ""}`} aria-label={live.sharing.public ? "Make report private" : "Make report public"} aria-pressed={live.sharing.public} onClick={toggleSharing} disabled={sharingBusy}><i /></button>
                </div>
                {live.sharing.public && live.sharing.report_url && (
                  <div className="settings-fact-grid" style={{ gridTemplateColumns: "1fr auto" }}>
                    <article style={{ overflow: "hidden" }}><span>Report URL</span><strong style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}>{live.sharing.report_url}</strong></article>
                    <button type="button" className="button button--small" onClick={copyReportLink}>{copiedLink ? <CheckCheck size={15} /> : <Copy size={15} />}{copiedLink ? "Copied" : "Copy link"}</button>
                  </div>
                )}
              </div>
            )}
          </section>
          {live && <AccountControls currentName={live.profile.name} email={live.profile.email} />}
        </div>}

        {activeTab === "team" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>People & roles</h3><p>{live ? "Everyone signed in to this workspace." : "Sample workspace members with the permissions their roles would carry."}</p></div><PreviewInfo className="button button--small" label="Invite member" message="Team invitations aren't wired up yet. No invitation has been sent." /></div><div className="settings-member-table" role="table" aria-label="Workspace team members"><div className="settings-member-head" role="row"><span>Person</span><span>Role</span><span>Permissions</span><span>Status</span><span>Last active</span><span /></div>{(live ? live.seats.map((s) => [s.initials, s.name, s.role, s.perms, "Active", s.active] as const) : members).map(([initials, name, role, permissions, status, activeAt]) => <div className="settings-member-row" role="row" key={name}><span className="settings-person"><i>{initials}</i><strong>{name}</strong></span><span><b className="settings-role-chip">{role}</b></span><span>{permissions}</span><span><b className="settings-status settings-status--green">{status}</b></span><span>{activeAt}</span><span><PreviewInfo className="settings-row-action" label="Manage" message={`Role changes and access removal for ${name} aren't wired up yet.`} /></span></div>)}</div></section><section className="settings-surface settings-team-note"><Users size={19} /><div><strong>Roles are previewed, not enforced</strong><p>Role changes and invitations aren't wired up yet. {live ? "Names and emails above are real." : "These names and roles are local demo content only."}</p></div></section></div>}

        {activeTab === "billing" && <div className="settings-tab-stack"><section className="settings-surface settings-billing-feature"><div><span className="settings-kicker">{live ? "Billing" : "Billing preview"}</span><h3>{live ? `${live.plan.name} plan for ${live.profile.name}` : "Pro plan for LaunchVault.ca"}</h3><p>{live ? `Billed ${live.plan.unit}. Monthly total: ${live.plan.monthly}.` : "Use the workspace freely as a visual prototype. Stripe billing, metering, and plan enforcement are not connected yet."}</p>{live ? (
          <button type="button" className="settings-link-button" onClick={live.plan.subscribed ? goToPortal : goToCheckout} disabled={billingBusy !== null}>
            {billingBusy ? "Redirecting…" : live.plan.subscribed ? "View billing details & invoices" : "Subscribe"}
          </button>
        ) : (
          <PreviewInfo className="settings-link-button" label="View billing details" message="The Stripe customer portal isn't linked from this page yet — see app/billing.py." />
        )}{billingError && <p className="form-message" role="alert">{billingError}</p>}</div><div><strong>{live ? live.plan.price : "$79"}</strong><span>/ {live ? live.plan.unit : "month"}</span><small>{live ? live.plan.state : "Illustrative plan price"}</small></div></section><section className="settings-surface"><div className="settings-surface-heading"><div><h3>{live ? "Usage" : "Monthly usage"}</h3><p>{live ? "Real counts for this workspace." : "Representative demo values, not live account metering."}</p></div>{!live && <span className="settings-demo-chip"><span />Illustrative</span>}</div><UsageCards rows={usageRows} /></section><section className="settings-surface settings-plan-includes"><h3>{live ? "Included in this plan" : "Included in the preview plan"}</h3><div>{(live ? live.plan.features : ["Up to 10 team members", "Five connected projects", "AI writing workflows", "Advanced analytics views", "Priority support"]).map((item) => <span key={item}><Check size={15} />{item}</span>)}</div></section></div>}

        {activeTab === "security" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Sign-in & access</h3><p>Security controls are shown as local settings for the eventual workspace backend.</p></div><span className="settings-demo-chip"><span />No auth provider connected</span></div><div className="settings-toggle-list"><LocalToggle label="Two-factor authentication" description="Require an additional verification step for workspace sign-in." checked={settings.twoFactor} onChange={() => flip("twoFactor")} /><LocalToggle label="Session notifications" description="Show a local alert when a new browser session begins." checked={settings.browser} onChange={() => flip("browser")} /></div></section><div className="settings-two-column"><section className="settings-surface"><h3>Access options</h3><div className="settings-option-cards"><article><KeyRound size={18} /><div><strong>Single sign-on</strong><span>Enterprise setup option</span></div><b>Not configured</b></article><article><Users size={18} /><div><strong>Active sessions</strong><span>One illustrative local session</span></div><b>Preview</b></article></div></section><section className="settings-surface settings-security-tip"><ShieldCheck size={20} /><div><h3>Keep keys out of the UI</h3><p>Use secure server-side environment configuration for Supabase, OpenAI, Anthropic, Stripe, and CMS credentials.</p></div></section></div></div>}

        {activeTab === "notifications" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Notification preferences</h3><p>Toggle sample preferences to see how the final settings interaction should feel.</p></div><span className="settings-demo-chip"><span />Changes reset on reload</span></div><div className="settings-toggle-list"><LocalToggle label="Email product updates" description="Product changes, release notes, and workspace notices." checked={settings.email} onChange={() => flip("email")} /><LocalToggle label="Project activity" description="Reviews, approvals, content movement, and comments." checked={settings.project} onChange={() => flip("project")} /><LocalToggle label="System updates" description="Maintenance, connection state, and workflow availability." checked={settings.system} onChange={() => flip("system")} /><LocalToggle label="Approval reminders" description="Follow up on content that is still waiting for a decision." checked={settings.approval} onChange={() => flip("approval")} /><LocalToggle label="Publishing alerts" description="Receive a preview alert when a content item is ready to ship." checked={settings.publish} onChange={() => flip("publish")} /></div></section><section className="settings-surface settings-notification-note"><Bell size={18} /><div><strong>Nothing is delivered from the demo</strong><p>These controls only update local visual state and do not email, notify, or subscribe anybody.</p></div></section></div>}

        {activeTab === "defaults" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Content defaults</h3><p>Starting preferences for an editor or future generation workflow.</p></div><PreviewInfo className="settings-link-button" label="How defaults work" message="These fields are locally interactive presentation controls. Saving content defaults, selecting models, and using them in a generation workflow requires the backend connection phase." /></div><div className="settings-defaults-form"><label><span>Brand voice</span><select name="content-default-1" onChange={() => setDefaultsSaved(false)} defaultValue="Professional & friendly"><option>Professional & friendly</option><option>Direct & practical</option><option>Warm & educational</option></select></label><label><span>Target audience</span><select name="content-default-2" onChange={() => setDefaultsSaved(false)} defaultValue="Learners and operators"><option>Learners and operators</option><option>Marketing teams</option><option>Technical teams</option></select></label><label><span>Default tone</span><select name="content-default-3" onChange={() => setDefaultsSaved(false)} defaultValue="Informative"><option>Informative</option><option>Conversational</option><option>Concise</option></select></label><label><span>Language</span><select name="content-default-4" onChange={() => setDefaultsSaved(false)} defaultValue="English (US)"><option>English (US)</option><option>English (Canada)</option><option>French (Canada)</option></select></label><label><span>AI model</span><select name="content-default-5" onChange={() => setDefaultsSaved(false)} defaultValue="Choose in backend"><option>Choose in backend</option><option>OpenAI content model</option><option>Anthropic content model</option></select></label><label><span>Post format</span><select name="content-default-6" onChange={() => setDefaultsSaved(false)} defaultValue="Auto-select"><option>Auto-select</option><option>Guide</option><option>Article with FAQ</option></select></label></div><div className="settings-defaults-footer"><span><CircleDashed size={13} />{defaultsSaved ? "Saved locally for this browser session." : "Preview preferences only"}</span><button type="button" className="button button--small" onClick={(event) => { const section = event.currentTarget.closest("section"); const values = Object.fromEntries(Array.from(section?.querySelectorAll("select") ?? []).map((field) => [field.name, field.value])); try { sessionStorage.setItem("fig-content-defaults", JSON.stringify(values)); setDefaultsSaved(true); } catch { setDefaultsSaved(false); } }}>Save local preview</button></div></section></div>}

        {activeTab === "webhooks" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Webhook delivery</h3><p>{live ? "Real delivery counts — outbound webhooks aren't sent yet, so these stay at zero." : "Prepare the event layer your integrations will use once the backend is online."}</p></div><PreviewInfo className="button button--small" label="Add endpoint" message="Outbound webhook delivery isn't built yet — see app/webapp.py." /></div><div className="settings-webhook-stats"><article><strong>{live ? live.webhooks.active : 0}</strong><span>Active endpoints</span></article><article><strong>{live ? fmt(live.webhooks.delivered) : "—"}</strong><span>Events delivered</span></article><article><strong>Pending</strong><span>Signing secret</span></article></div><div className="settings-webhook-empty"><Webhook size={22} /><div><strong>No webhook endpoints configured</strong><p>When available, events such as <code>content.published</code>, <code>review.requested</code>, and <code>project.updated</code> will appear here with a delivery history.</p></div><PreviewInfo className="settings-link-button" label="View example" message="Outbound webhook delivery isn't built yet, so there's no example to show." /></div></section></div>}
      </section>
    </div>
  </>;
}
