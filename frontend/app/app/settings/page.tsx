import { Check, CircleDashed, CreditCard, KeyRound, Link2, ShieldCheck, Users } from "lucide-react";
import { DashboardHeader } from "@/components/dashboard-shell";

const services = [
  { name: "Supabase", detail: "Workspace database", status: "Ready to verify", tone: "blue" },
  { name: "OpenAI", detail: "Content generation", status: "Ready to verify", tone: "green" },
  { name: "Anthropic", detail: "Content assistance", status: "Ready to verify", tone: "purple" },
  { name: "Stripe", detail: "Plans and billing", status: "Backend pending", tone: "amber" }
] as const;

export default function SettingsPage() {
  return (
    <>
      <DashboardHeader eyebrow="LaunchVault.ca · Settings" title="Settings & workspace configuration" description="The single-project workspace for LaunchVault's AI learning library." />
      <div className="settings-grid">
        <section className="dashboard-panel settings-profile"><div className="panel-heading"><div><span className="panel-icon"><Users size={18} /></span><h2>Workspace profile</h2></div><span className="panel-meta">Single project</span></div><div className="workspace-profile"><span className="workspace-logo">LV</span><div><strong>LaunchVault.ca</strong><p>Plain-English AI lessons, prompts, courses, and workflows.</p></div><span className="status-pill status-pill--purple">Preview</span></div></section>
        <section className="dashboard-panel"><div className="panel-heading"><div><span className="panel-icon"><CreditCard size={18} /></span><h2>Billing & usage</h2></div><span className="panel-meta">Preview</span></div><div className="settings-empty"><CreditCard /><strong>Creator plan design</strong><p>LaunchVault pricing can be represented here once Stripe products and entitlements are connected.</p><button className="secondary-button">View billing setup</button></div></section>
        <section className="dashboard-panel settings-services"><div className="panel-heading"><div><span className="panel-icon"><Link2 size={18} /></span><h2>API connections</h2></div><span className="panel-meta">Configuration</span></div><div className="service-list">{services.map((service) => <div key={service.name}><span className={`service-mark service-mark--${service.tone}`}>{service.name.slice(0, 2)}</span><div><strong>{service.name}</strong><small>{service.detail}</small></div><span className={`status-pill status-pill--${service.tone}`}><CircleDashed size={12} />{service.status}</span><button aria-label={`Configure ${service.name}`}><KeyRound size={16} /></button></div>)}</div></section>
        <section className="dashboard-panel"><div className="panel-heading"><div><span className="panel-icon"><ShieldCheck size={18} /></span><h2>Security & access</h2></div><span className="panel-meta">Preview</span></div><div className="settings-list"><span><Check size={15} />Single LaunchVault workspace</span><span><Check size={15} />Role-aware project structure</span><span><CircleDashed size={15} />Authentication connection pending</span></div></section>
      </div>
    </>
  );
}
