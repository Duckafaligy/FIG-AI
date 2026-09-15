import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bell,
  BrainCircuit,
  Check,
  CircleDashed,
  CreditCard,
  Database,
  FileText,
  KeyRound,
  Link2,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Users,
  Webhook
} from "lucide-react";
import { DashboardHeader } from "@/components/dashboard-shell";
import { PreviewInfo } from "@/components/preview-info";

type Service = {
  name: string;
  detail: string;
  permission: string;
  status: string;
  tone: "blue" | "green" | "purple" | "amber";
  icon: LucideIcon;
};

const members = [
  ["JD", "Jordan Davis", "Owner", "All permissions", "Active", "2 hours ago"],
  ["MC", "Maya Chen", "Admin", "Projects, settings, billing", "Active", "4 hours ago"],
  ["PS", "Priya Shah", "Content manager", "Create, edit, publish", "Active", "Yesterday"],
  ["DR", "Daniel Reyes", "SEO specialist", "SEO, GEO, analytics", "Active", "3 hours ago"],
  ["EP", "Emma Patel", "Analyst", "Analytics and reports", "Active", "6 hours ago"]
];

const services: Service[] = [
  { name: "Supabase", detail: "Workspace database", permission: "Read / write", status: "Ready to verify", tone: "blue", icon: Database },
  { name: "OpenAI", detail: "Content generation", permission: "Read / write", status: "Ready to verify", tone: "green", icon: BrainCircuit },
  { name: "Anthropic", detail: "Content assistance", permission: "Read / write", status: "Ready to verify", tone: "purple", icon: BrainCircuit },
  { name: "Stripe", detail: "Plans and billing", permission: "Billing", status: "Backend pending", tone: "amber", icon: CreditCard },
  { name: "Shopify", detail: "Publishing destination", permission: "Not connected", status: "Optional", tone: "green", icon: ShoppingBag },
  { name: "Google Analytics", detail: "Traffic and conversions", permission: "Read", status: "Optional", tone: "amber", icon: BarChart3 },
  { name: "Search Console", detail: "Queries and indexing", permission: "Read", status: "Optional", tone: "blue", icon: Search },
  { name: "Webhooks", detail: "Workspace events", permission: "Send / receive", status: "Backend pending", tone: "purple", icon: Webhook }
];

const usage = [
  ["Content drafts", "126 / 500", "25%"],
  ["API credits", "48.2K / 100K", "48%"],
  ["AI generations", "312K / 1M", "31%"],
  ["Team seats", "5 / 10", "50%"]
];

export default function SettingsPage() {
  return (
    <>
      <DashboardHeader eyebrow="Settings" title="Settings & workspace configuration" description="Manage the LaunchVault.ca workspace, members, connected services, and product defaults." action="Edit profile" />
      <div className="settings-dashboard-grid">
        <section className="dashboard-panel settings-profile-card">
          <div className="panel-heading"><div><span className="panel-icon"><Users size={18} /></span><h2>Workspace profile</h2></div><PreviewInfo className="panel-action" label="Edit profile" message="LaunchVault.ca is the sample workspace for this preview. Editing the workspace name, website, industry, and timezone will become available when workspace storage is connected. No profile changes have been saved." /></div>
          <div className="workspace-profile workspace-profile--detailed"><span className="workspace-logo">LV</span><div><div className="workspace-title-line"><strong>LaunchVault.ca</strong><span className="status-pill status-pill--green">Preview workspace</span></div><p>Plain-English AI lessons, prompts, courses, and practical workflows.</p></div></div>
          <div className="profile-facts"><div><span>Workspace ID</span><strong>lv_workspace_01</strong></div><div><span>Owner</span><strong>Jordan Davis</strong></div><div><span>Industry</span><strong>Education & technology</strong></div><div><span>Timezone</span><strong>Eastern Time</strong></div><div><span>Website</span><strong>launchvault.ca</strong></div><div><span>Created</span><strong>Sep 13, 2026</strong></div></div>
        </section>

        <section className="dashboard-panel settings-overview-card">
          <div className="panel-heading"><div><span className="panel-icon"><BarChart3 size={18} /></span><h2>Workspace overview</h2></div><span className="panel-meta">Demo data</span></div>
          <div className="settings-overview-stats"><div><Users /><strong>5</strong><span>Team members</span></div><div><Link2 /><strong>8</strong><span>Services listed</span></div><div><FileText /><strong>1,500</strong><span>Library items</span></div><div><BrainCircuit /><strong>50</strong><span>Topics</span></div></div>
        </section>

        <section className="dashboard-panel settings-members-card">
          <div className="panel-heading"><div><span className="panel-icon"><Users size={18} /></span><h2>Seats & roles</h2></div><PreviewInfo className="button button--small" label="Invite member" message="The members shown here are sample profiles. Invitations and role assignments will be available once authentication and team access are connected. No invitation has been sent." /></div>
          <div className="settings-table settings-members-table"><div className="settings-table-head"><span>User</span><span>Role</span><span>Permissions</span><span>Status</span><span>Last active</span><span>Actions</span></div>{members.map(([initials, name, role, permissions, status, active]) => <div className="settings-table-row" key={name}><span className="member-cell"><i>{initials}</i><strong>{name}</strong></span><span><b className="role-chip">{role}</b></span><span>{permissions}</span><span><b className="status-pill status-pill--green">{status}</b></span><span>{active}</span><span title={`Manage ${name}`}><PreviewInfo className="panel-action" label="Manage" message={`${name} is a sample ${role.toLowerCase()} profile with these example permissions: ${permissions}. Changing a role, revoking access, or removing a member will require the connected team service. This preview does not change anyone’s access.`} /></span></div>)}</div>
        </section>

        <section className="dashboard-panel settings-billing-card">
          <div className="panel-heading"><div><span className="panel-icon"><CreditCard size={18} /></span><h2>Billing & usage</h2></div><PreviewInfo className="panel-action" label="Manage billing" message="The Pro plan and usage figures are illustrative. Stripe billing has not been connected in this preview, so there is no active subscription or payment method to manage here. No checkout session or charge has been created." /></div>
          <div className="billing-layout"><div className="billing-plan"><span>Current plan</span><strong>Pro preview</strong><b>$79 <small>/ month</small></b><em>Billing connection pending</em></div><ul><li><Check />Up to 10 team members</li><li><Check />Five connected projects</li><li><Check />Full AI integrations</li><li><Check />Advanced analytics</li><li><Check />Priority support</li></ul></div>
        </section>

        <section className="dashboard-panel settings-usage-card">
          <div className="panel-heading"><div><span className="panel-icon"><BarChart3 size={18} /></span><h2>Monthly usage</h2></div><span className="panel-meta">Illustrative</span></div>
          <div className="usage-grid">{usage.map(([label, value, percent]) => <div key={label}><strong>{value}</strong><span>{label}</span><i><b style={{ width: percent }} /></i><small>{percent}</small></div>)}</div>
        </section>

        <section className="dashboard-panel settings-connections-card">
          <div className="panel-heading"><div><span className="panel-icon"><Link2 size={18} /></span><h2>API connections</h2></div><PreviewInfo className="button button--small" label="Connect service" message="Choose a service from the table to see its intended role. Connecting accounts, storing credentials, and verifying permissions will be available during the integration phase. This preview does not accept API keys or authorize external accounts." /></div>
          <div className="settings-table settings-connections-table"><div className="settings-table-head"><span>Service</span><span>Workspace purpose</span><span>Status</span><span>Permissions</span><span>Environment</span><span>Actions</span></div>{services.map((service) => { const Icon = service.icon; return <div className="settings-table-row" key={service.name}><span className="service-cell"><i className={`service-mark service-mark--${service.tone}`}><Icon size={17} /></i><strong>{service.name}</strong></span><span>{service.detail}</span><span><b className={`status-pill status-pill--${service.tone}`}><CircleDashed size={11} />{service.status}</b></span><span>{service.permission}</span><span>Frontend preview</span><span title={`Configure ${service.name}`}><PreviewInfo className="panel-action" label="Setup" message={`${service.name} is listed for ${service.detail.toLowerCase()}. Its current preview status is “${service.status}.” Configuration and connection tests are not available yet; no credentials, permissions, or live connection have been verified by this page.`} /></span></div>; })}</div>
        </section>

        <section className="dashboard-panel settings-compact-card"><div className="panel-heading"><div><span className="panel-icon"><ShieldCheck size={18} /></span><h2>Security & access</h2></div><PreviewInfo className="panel-action" label="Manage" message="Two-factor authentication, single sign-on, and session management will be configured through the connected authentication service. The session shown here is illustrative, and this preview has not enabled or changed any security setting." /></div><div className="settings-option-list"><span><ShieldCheck /><div><strong>Two-factor authentication</strong><small>Ready for backend configuration</small></div><b className="status-pill status-pill--blue">Planned</b></span><span><KeyRound /><div><strong>Single sign-on</strong><small>Enterprise workspace option</small></div><b className="status-pill">Not configured</b></span><span><Users /><div><strong>Active sessions</strong><small>One illustrative session</small></div><b className="status-pill status-pill--green">Healthy</b></span></div></section>
        <section className="dashboard-panel settings-compact-card"><div className="panel-heading"><div><span className="panel-icon"><Bell size={18} /></span><h2>Notification preferences</h2></div><PreviewInfo className="panel-action" label="Manage" message="These are example preferences for email, project activity, and system updates. Saving delivery preferences will be available when notification services are connected. This preview does not send email or change notification subscriptions." /></div><div className="settings-option-list"><span><Bell /><div><strong>Email notifications</strong><small>Product updates and approvals</small></div><b className="status-pill status-pill--green">Enabled</b></span><span><Users /><div><strong>Project activity</strong><small>Posts, approvals, and comments</small></div><b className="status-pill status-pill--green">Enabled</b></span><span><BrainCircuit /><div><strong>System updates</strong><small>Maintenance and new features</small></div><b className="status-pill status-pill--blue">Planned</b></span></div></section>
        <section className="dashboard-panel settings-compact-card"><div className="panel-heading"><div><span className="panel-icon"><SlidersHorizontal size={18} /></span><h2>Content defaults</h2></div><PreviewInfo className="panel-action" label="Edit defaults" message="The brand voice, audience, tone, language, and post format shown are sample defaults for LaunchVault.ca. Saved defaults and model selection will become available when the workspace and content-generation services are connected." /></div><div className="content-defaults"><label>Brand voice<span>Professional & friendly</span></label><label>Target audience<span>General</span></label><label>Default tone<span>Informative</span></label><label>Language<span>English</span></label><label>AI model<span>Selected in backend</span></label><label>Post format<span>Auto-select</span></label></div></section>

        <section className="dashboard-panel settings-limits-card"><div className="panel-heading"><div><span className="panel-icon"><BarChart3 size={18} /></span><h2>Rate limits / API usage</h2></div><span className="panel-meta">Illustrative</span></div><div className="usage-grid usage-grid--wide">{usage.map(([label, value, percent]) => <div key={label}><strong>{value}</strong><span>{label}</span><i><b style={{ width: percent }} /></i><small>{percent}</small></div>)}</div></section>
        <section className="dashboard-panel settings-webhooks-card"><div className="panel-heading"><div><span className="panel-icon"><Webhook size={18} /></span><h2>Webhooks</h2></div><PreviewInfo className="panel-action" label="Manage" message="No webhook endpoints are connected. Endpoint configuration, signing secrets, event subscriptions, and delivery history will be available when webhook processing is connected. Opening this preview does not send an event." /></div><div className="webhook-summary"><div><strong>0</strong><span>Active webhooks</span></div><div><strong>—</strong><span>Events delivered</span></div><div><strong>Pending</strong><span>Backend connection</span></div></div><p><CircleDashed size={12} />No webhook events have been connected yet.</p></section>
      </div>
    </>
  );
}
