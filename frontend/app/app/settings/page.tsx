import { Check, CircleDashed, CreditCard, KeyRound, Link2, ShieldCheck, Users } from "lucide-react";
import { DashboardHeader } from "@/components/dashboard-shell";

const services = ["Supabase", "OpenAI", "Anthropic", "Stripe"];

export default function SettingsPage() {
  return (
    <>
      <DashboardHeader eyebrow="Settings" title="Settings & workspace configuration" description="Manage your workspace, people, connected services, and product preferences." />
      <div className="settings-grid">
        <section className="dashboard-panel settings-profile"><div className="panel-heading"><div><span className="panel-icon"><Users size={18} /></span><h2>Workspace profile</h2></div><button>Edit profile</button></div><div className="workspace-profile"><span className="workspace-logo">F</span><div><strong>My workspace</strong><p>Add your company details to personalize FIG.</p></div><span className="status-pill">Setup needed</span></div></section>
        <section className="dashboard-panel"><div className="panel-heading"><div><span className="panel-icon"><CreditCard size={18} /></span><h2>Billing & usage</h2></div><button>Manage</button></div><div className="settings-empty"><CircleDashed /><strong>No active plan</strong><p>Stripe billing details will appear here after backend connection.</p><button className="secondary-button">Choose a plan</button></div></section>
        <section className="dashboard-panel settings-services"><div className="panel-heading"><div><span className="panel-icon"><Link2 size={18} /></span><h2>API connections</h2></div><button>Connect service</button></div><div className="service-list">{services.map((service) => <div key={service}><span className="service-mark">{service.slice(0, 2)}</span><div><strong>{service}</strong><small>Backend configuration</small></div><span className="status-pill status-pill--muted"><CircleDashed size={12} />Not verified</span><button aria-label={`Configure ${service}`}><KeyRound size={16} /></button></div>)}</div></section>
        <section className="dashboard-panel"><div className="panel-heading"><div><span className="panel-icon"><ShieldCheck size={18} /></span><h2>Security & access</h2></div><button>Manage</button></div><div className="settings-list"><span><Check size={15} />Secure session design</span><span><Check size={15} />Role-aware workspace structure</span><span><CircleDashed size={15} />Authentication connection pending</span></div></section>
      </div>
    </>
  );
}
