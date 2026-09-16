"use client";

import { useState, type ComponentType } from "react";
import {
  BadgeCheck,
  BarChart3,
  Bell,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleDashed,
  CreditCard,
  Database,
  FileText,
  KeyRound,
  Link2,
  LockKeyhole,
  PlugZap,
  Search,
  Settings2,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Users,
  Webhook
} from "lucide-react";
import { DashboardHeader } from "@/components/dashboard-shell";
import { PreviewInfo } from "@/components/preview-info";

type Icon = ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
type TabId = "workspace" | "team" | "integrations" | "billing" | "security" | "notifications" | "defaults" | "webhooks";
type Service = { name: string; detail: string; permission: string; status: string; tone: "blue" | "green" | "purple" | "amber"; icon: Icon };

const members = [
  ["JD", "Jordan Davis", "Owner", "All workspace permissions", "Active", "2 hours ago"],
  ["MC", "Maya Chen", "Admin", "Projects, settings, billing", "Active", "4 hours ago"],
  ["PS", "Priya Shah", "Content manager", "Create, edit, publish", "Active", "Yesterday"],
  ["DR", "Daniel Reyes", "SEO specialist", "SEO, GEO, analytics", "Active", "3 hours ago"],
  ["EP", "Emma Patel", "Analyst", "View analytics and reports", "Active", "6 hours ago"]
];

const services: Service[] = [
  { name: "Supabase", detail: "Workspace database", permission: "Read / write", status: "Ready to configure", tone: "blue", icon: Database },
  { name: "OpenAI", detail: "Content generation", permission: "Read / write", status: "Ready to configure", tone: "green", icon: BrainCircuit },
  { name: "Anthropic", detail: "Content assistance", permission: "Read / write", status: "Ready to configure", tone: "purple", icon: BrainCircuit },
  { name: "Stripe", detail: "Plans and billing", permission: "Billing", status: "Backend pending", tone: "amber", icon: CreditCard },
  { name: "Shopify", detail: "Publishing destination", permission: "Not connected", status: "Optional", tone: "green", icon: ShoppingBag },
  { name: "Google Analytics", detail: "Traffic and conversions", permission: "Read", status: "Optional", tone: "amber", icon: BarChart3 },
  { name: "Search Console", detail: "Queries and indexing", permission: "Read", status: "Optional", tone: "blue", icon: Search },
  { name: "Webhooks", detail: "Workspace events", permission: "Send / receive", status: "Backend pending", tone: "purple", icon: Webhook }
];

const usage = [["Content drafts", "126 / 500", "25%"], ["API credits", "48.2K / 100K", "48%"], ["AI generations", "312K / 1M", "31%"], ["Team seats", "5 / 10", "50%"]];

const tabs: { id: TabId; label: string; description: string; icon: Icon }[] = [
  { id: "workspace", label: "Workspace", description: "Profile, plan, and workspace summary", icon: Settings2 },
  { id: "team", label: "Team & roles", description: "People, access, and permissions", icon: Users },
  { id: "integrations", label: "Integrations", description: "Services and connection preparation", icon: PlugZap },
  { id: "billing", label: "Billing & usage", description: "Preview plan and product usage", icon: CreditCard },
  { id: "security", label: "Security", description: "Authentication and access controls", icon: ShieldCheck },
  { id: "notifications", label: "Notifications", description: "Delivery and alert preferences", icon: Bell },
  { id: "defaults", label: "Content defaults", description: "Writing and output preferences", icon: SlidersHorizontal },
  { id: "webhooks", label: "Webhooks", description: "Event delivery configuration", icon: Webhook }
];

function LocalToggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return <div className="settings-toggle-row"><div><strong>{label}</strong><span>{description}</span></div><button type="button" className={`settings-switch${checked ? " is-on" : ""}`} aria-label={`${checked ? "Disable" : "Enable"} ${label} in local preview`} aria-pressed={checked} onClick={onChange}><i /></button></div>;
}

function UsageCards() {
  return <div className="settings-usage-cards">{usage.map(([label, value, percent]) => <article key={label}><div><span>{label}</span><strong>{value}</strong></div><small>{percent} of illustrative allowance</small><i><b style={{ width: percent }} /></i></article>)}</div>;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("workspace");
  const [settings, setSettings] = useState({ twoFactor: false, email: true, project: true, system: false, browser: true, approval: true, publish: false });
  const [defaultsSaved, setDefaultsSaved] = useState(false);
  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];
  const ActiveIcon = active.icon;
  const flip = (key: keyof typeof settings) => setSettings((current) => ({ ...current, [key]: !current[key] }));

  return <>
    <DashboardHeader eyebrow="Settings" title="Settings & workspace configuration" description="Manage workspace details, team access, integrations, and content preferences." action="Edit profile" />
    <div className="settings-tabbed-workbench">
      <aside className="settings-tab-sidebar" aria-label="Settings sections">
        <div className="settings-sidebar-workspace"><span className="settings-workspace-mark">LV</span><div><strong>LaunchVault.ca</strong><small>Frontend preview</small></div><ChevronRight size={15} /></div>
        <nav role="tablist" aria-label="Workspace settings">
          {tabs.map((tab) => { const TabIcon = tab.icon; const selected = tab.id === activeTab; return <button type="button" key={tab.id} role="tab" aria-selected={selected} className={selected ? "is-active" : ""} onClick={() => setActiveTab(tab.id)}><TabIcon size={17} /><span>{tab.label}</span>{tab.id === "integrations" && <small>8</small>}</button>; })}
        </nav>
        <div className="settings-sidebar-note"><CircleDashed size={15} /><span><strong>Local preview</strong>No credentials or settings are stored from this page.</span></div>
      </aside>

      <section className="settings-tab-content" role="tabpanel" aria-label={active.label}>
        <header className="settings-tab-header"><span className="settings-tab-icon"><ActiveIcon size={19} /></span><div><h2>{active.label}</h2><p>{active.description}</p></div><span className="settings-demo-chip"><span />LaunchVault.ca demo</span></header>

        {activeTab === "workspace" && <div className="settings-tab-stack">
          <section className="settings-surface settings-workspace-surface"><div className="settings-surface-heading"><div><h3>Workspace profile</h3><p>The core details shown throughout this frontend preview.</p></div><PreviewInfo className="settings-link-button" label="Edit profile" message="Workspace editing is disabled in this frontend preview. No change is sent to LaunchVault.ca, Supabase, or any connected service." /></div><div className="settings-workspace-profile"><span className="settings-profile-logo">LV</span><div><strong>LaunchVault.ca</strong><p>Plain-English AI lessons, prompts, courses, and practical workflows.</p><span><BadgeCheck size={13} />Preview workspace</span></div></div><div className="settings-fact-grid"><article><span>Workspace ID</span><strong>lv_workspace_01</strong></article><article><span>Owner</span><strong>Jordan Davis</strong></article><article><span>Industry</span><strong>Education & technology</strong></article><article><span>Timezone</span><strong>Eastern Time</strong></article><article><span>Website</span><strong>launchvault.ca</strong></article><article><span>Created</span><strong>Sep 13, 2026</strong></article></div></section>
          <div className="settings-two-column"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Workspace at a glance</h3><p>Sample counters for this one project.</p></div></div><div className="settings-glance-grid"><article><Users size={18} /><strong>5</strong><span>Team members</span></article><article><Link2 size={18} /><strong>8</strong><span>Services listed</span></article><article><FileText size={18} /><strong>1,500</strong><span>Library items</span></article><article><BrainCircuit size={18} /><strong>50</strong><span>Topics</span></article></div></section><section className="settings-surface settings-plan-surface"><div className="settings-surface-heading"><div><h3>Current plan</h3><p>Billing is not connected.</p></div><PreviewInfo className="settings-link-button" label="Manage billing" message="Stripe has not been connected. The plan and price are illustrative and no subscription, checkout, or payment method exists in this preview." /></div><strong className="settings-plan-name">Pro <span>preview</span></strong><div className="settings-plan-price">$79 <small>/ month</small></div><p>Team workflow, writing tools, and analytics shown as a product preview.</p></section></div>
        </div>}

        {activeTab === "team" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>People & roles</h3><p>Sample workspace members with the permissions their roles would carry.</p></div><PreviewInfo className="button button--small" label="Invite member" message="Team invitations and role changes are not enabled in this frontend preview. No invitation has been sent." /></div><div className="settings-member-table" role="table" aria-label="LaunchVault team members"><div className="settings-member-head" role="row"><span>Person</span><span>Role</span><span>Permissions</span><span>Status</span><span>Last active</span><span /></div>{members.map(([initials, name, role, permissions, status, activeAt]) => <div className="settings-member-row" role="row" key={name}><span className="settings-person"><i>{initials}</i><strong>{name}</strong></span><span><b className="settings-role-chip">{role}</b></span><span>{permissions}</span><span><b className="settings-status settings-status--green">{status}</b></span><span>{activeAt}</span><span><PreviewInfo className="settings-row-action" label="Manage" message={`${name} is a sample ${role.toLowerCase()} profile. This preview can show intended permissions but cannot change a role, invite a person, or remove access.`} /></span></div>)}</div></section><section className="settings-surface settings-team-note"><Users size={19} /><div><strong>Roles are previewed, not enforced</strong><p>Authentication and workspace authorization will be added with the backend. These names and roles are local demo content only.</p></div></section></div>}

        {activeTab === "integrations" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Connection preparation</h3><p>Services FIG is designed to work with. Statuses are not credential checks.</p></div><PreviewInfo className="button button--small" label="Connect service" message="This frontend does not accept keys, OAuth permissions, or external connection requests. Each listed service is a configuration target for the backend phase." /></div><div className="settings-integration-list">{services.map((service) => { const ServiceIcon = service.icon; return <article key={service.name}><span className={`settings-service-icon settings-service-icon--${service.tone}`}><ServiceIcon size={18} /></span><div><strong>{service.name}</strong><small>{service.detail}</small></div><span className="settings-service-permission">{service.permission}</span><b className={`settings-status settings-status--${service.tone}`}><CircleDashed size={11} />{service.status}</b><PreviewInfo className="settings-row-action" label="Setup" message={`${service.name} is shown for ${service.detail.toLowerCase()}. No credentials, permissions, connected account, or live service status has been verified by this interface.`} /></article>; })}</div></section><section className="settings-surface settings-integration-note"><LockKeyhole size={19} /><div><strong>Credentials belong in the backend</strong><p>When integrations are connected, encrypted configuration and verification should happen server-side—not in this frontend page.</p></div></section></div>}

        {activeTab === "billing" && <div className="settings-tab-stack"><section className="settings-surface settings-billing-feature"><div><span className="settings-kicker">Billing preview</span><h3>Pro plan for LaunchVault.ca</h3><p>Use the workspace freely as a visual prototype. Stripe billing, metering, and plan enforcement are not connected yet.</p><PreviewInfo className="settings-link-button" label="View billing details" message="No Stripe customer, subscription, checkout, invoice, or payment method exists in this frontend preview." /></div><div><strong>$79</strong><span>/ month</span><small>Illustrative plan price</small></div></section><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Monthly usage</h3><p>Representative demo values, not live account metering.</p></div><span className="settings-demo-chip"><span />Illustrative</span></div><UsageCards /></section><section className="settings-surface settings-plan-includes"><h3>Included in the preview plan</h3><div>{["Up to 10 team members", "Five connected projects", "AI writing workflows", "Advanced analytics views", "Priority support"].map((item) => <span key={item}><Check size={15} />{item}</span>)}</div></section></div>}

        {activeTab === "security" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Sign-in & access</h3><p>Security controls are shown as local settings for the eventual workspace backend.</p></div><span className="settings-demo-chip"><span />No auth provider connected</span></div><div className="settings-toggle-list"><LocalToggle label="Two-factor authentication" description="Require an additional verification step for workspace sign-in." checked={settings.twoFactor} onChange={() => flip("twoFactor")} /><LocalToggle label="Session notifications" description="Show a local alert when a new browser session begins." checked={settings.browser} onChange={() => flip("browser")} /></div></section><div className="settings-two-column"><section className="settings-surface"><h3>Access options</h3><div className="settings-option-cards"><article><KeyRound size={18} /><div><strong>Single sign-on</strong><span>Enterprise setup option</span></div><b>Not configured</b></article><article><Users size={18} /><div><strong>Active sessions</strong><span>One illustrative local session</span></div><b>Preview</b></article></div></section><section className="settings-surface settings-security-tip"><ShieldCheck size={20} /><div><h3>Keep keys out of the UI</h3><p>Use secure server-side environment configuration for Supabase, OpenAI, Anthropic, Stripe, and CMS credentials.</p></div></section></div></div>}

        {activeTab === "notifications" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Notification preferences</h3><p>Toggle sample preferences to see how the final settings interaction should feel.</p></div><span className="settings-demo-chip"><span />Changes reset on reload</span></div><div className="settings-toggle-list"><LocalToggle label="Email product updates" description="Product changes, release notes, and workspace notices." checked={settings.email} onChange={() => flip("email")} /><LocalToggle label="Project activity" description="Reviews, approvals, content movement, and comments." checked={settings.project} onChange={() => flip("project")} /><LocalToggle label="System updates" description="Maintenance, connection state, and workflow availability." checked={settings.system} onChange={() => flip("system")} /><LocalToggle label="Approval reminders" description="Follow up on content that is still waiting for a decision." checked={settings.approval} onChange={() => flip("approval")} /><LocalToggle label="Publishing alerts" description="Receive a preview alert when a content item is ready to ship." checked={settings.publish} onChange={() => flip("publish")} /></div></section><section className="settings-surface settings-notification-note"><Bell size={18} /><div><strong>Nothing is delivered from the demo</strong><p>These controls only update local visual state and do not email, notify, or subscribe anybody.</p></div></section></div>}

        {activeTab === "defaults" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Content defaults</h3><p>Starting preferences for an editor or future generation workflow.</p></div><PreviewInfo className="settings-link-button" label="How defaults work" message="These fields are locally interactive presentation controls. Saving content defaults, selecting models, and using them in a generation workflow requires the backend connection phase." /></div><div className="settings-defaults-form"><label><span>Brand voice</span><select defaultValue="Professional & friendly"><option>Professional & friendly</option><option>Direct & practical</option><option>Warm & educational</option></select></label><label><span>Target audience</span><select defaultValue="Learners and operators"><option>Learners and operators</option><option>Marketing teams</option><option>Technical teams</option></select></label><label><span>Default tone</span><select defaultValue="Informative"><option>Informative</option><option>Conversational</option><option>Concise</option></select></label><label><span>Language</span><select defaultValue="English (US)"><option>English (US)</option><option>English (Canada)</option><option>French (Canada)</option></select></label><label><span>AI model</span><select defaultValue="Choose in backend"><option>Choose in backend</option><option>OpenAI content model</option><option>Anthropic content model</option></select></label><label><span>Post format</span><select defaultValue="Auto-select"><option>Auto-select</option><option>Guide</option><option>Article with FAQ</option></select></label></div><div className="settings-defaults-footer"><span><CircleDashed size={13} />{defaultsSaved ? "Saved locally for this browser session." : "Preview preferences only"}</span><button type="button" className="button button--small" onClick={() => setDefaultsSaved(true)}>Save local preview</button></div></section></div>}

        {activeTab === "webhooks" && <div className="settings-tab-stack"><section className="settings-surface"><div className="settings-surface-heading"><div><h3>Webhook delivery</h3><p>Prepare the event layer your integrations will use once the backend is online.</p></div><PreviewInfo className="button button--small" label="Add endpoint" message="No endpoint can be added in this visual preview. Event subscriptions, signing secrets, and delivery logs need the backend webhook service." /></div><div className="settings-webhook-stats"><article><strong>0</strong><span>Active endpoints</span></article><article><strong>—</strong><span>Events delivered</span></article><article><strong>Pending</strong><span>Signing secret</span></article></div><div className="settings-webhook-empty"><Webhook size={22} /><div><strong>No webhook endpoints configured</strong><p>When available, events such as <code>content.published</code>, <code>review.requested</code>, and <code>project.updated</code> will appear here with a delivery history.</p></div><PreviewInfo className="settings-link-button" label="View example" message="Example event delivery will be shown here once a server-side endpoint configuration is available. No event has been sent from this frontend." /></div></section></div>}
      </section>
    </div>
  </>;
}
