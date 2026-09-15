"use client";

import { useRef, useState, type CSSProperties } from "react";
import Link from "next/link";
import { WorkspaceTrendChart } from "@/components/visibility-chart";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Zap,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  FileText,
  Globe2,
  LayoutGrid,
  List,
  MoreVertical,
  Plus,
  Search,
  Sparkles,
  Target,
  Wifi
} from "lucide-react";

const stats = [
  { label: "Total projects", value: "1", change: "+1 this month", icon: FileText, tone: "purple" },
  { label: "Published posts", value: "28", change: "+15.6%", icon: CheckCircle2, tone: "coral" },
  { label: "Workspace traffic", value: "4.2K", change: "+18.7%", icon: BarChart3, tone: "blue" },
  { label: "Total impressions", value: "42.7K", change: "+24%", icon: Globe2, tone: "violet" },
  { label: "Avg. impact score", value: "84", change: "+6 points", icon: Sparkles, tone: "amber" },
  { label: "Sync health", value: "Preview", change: "Backend pending", icon: Wifi, tone: "green" }
];

const activity = [
  ["Guide published", "Learn AI in 5 Minutes a Day", "2 hours ago"],
  ["GEO keywords improved", "12 sample prompts moved upward", "5 hours ago"],
  ["Content optimized", "Three internal links suggested", "8 hours ago"],
  ["New topic created", "Practical AI workflows", "1 day ago"]
];

const opportunities = [
  ["Expand AI agents topic cluster", "12 related keywords", "High"],
  ["Target prompt-writing searches", "28 sample opportunities", "High"],
  ["Improve internal linking", "14 pages", "Medium"],
  ["Add comparison content", "8 suggested pages", "Medium"]
];

export default function ProjectsPage() {
  const [query, setQuery] = useState("");
  const [view, setView] = useState("grid");
  const projectDialog = useRef<HTMLDialogElement>(null);
  const matchesProject = "launchvault.ca ai education prompts practical tools".includes(query.toLowerCase().trim());
  return (
    <main className="projects-page">
      <header className="projects-topbar">
        <Link className="projects-brand" href="/projects"><span><Zap size={15} fill="currentColor" /></span><strong>LaunchVault</strong></Link>
        <div className="projects-search"><Search size={16} /><input aria-label="Search projects" placeholder="Search projects, domains, or content…" value={query} onChange={(event) => setQuery(event.target.value)} /><kbd>⌘ K</kbd></div>
        <div className="projects-top-actions">
          <div className="projects-workspace"><span>LV</span>LaunchVault.ca<ChevronDown size={14} /></div>
          <div className="projects-date"><CalendarDays size={15} />May 12, 2025 – May 25, 2025<ChevronDown size={14} /></div>
          <button className="button button--small" type="button" onClick={() => projectDialog.current?.showModal()}><Plus size={15} />New project</button>
          <Link className="projects-icon-button" href="/app/notifications" aria-label="Notifications"><Bell size={17} /></Link>
          <span className="projects-avatar">JD</span>
        </div>
      </header>

      <div className="projects-canvas">
        <div className="projects-heading">
          <div><span>Projects</span><h1>All Projects Dashboard</h1><p>Manage and monitor your content workspace in one place.</p></div>
          <span className="projects-demo-badge"><i />Illustrative workspace data</span>
        </div>

        <div className="projects-section-heading">
          <div><h2>Your projects</h2><span>1 project</span></div>
          <div className="projects-view-actions"><label><Search size={14} /><input aria-label="Filter projects" placeholder="Search projects…" value={query} onChange={(event) => setQuery(event.target.value)} /></label><button className={view === "grid" ? "active" : ""} type="button" onClick={() => setView("grid")} aria-pressed={view === "grid"}><LayoutGrid size={14} />Grid</button><button className={view === "list" ? "active" : ""} type="button" onClick={() => setView("list")} aria-pressed={view === "list"}><List size={14} />List</button><select aria-label="Sort projects"><option>Last updated</option><option>Name A–Z</option></select></div>
        </div>

        <section className={`projects-card-grid projects-card-grid--${view}`} aria-label="Project list">
          {matchesProject ? <Link href="/app" className="project-card project-card--selected">
            <span className="project-card-check"><CheckCircle2 size={17} /></span>
            <div className="project-card-heading"><span className="project-logo"><Zap size={20} fill="currentColor" /></span><div><strong>LaunchVault.ca</strong><small>AI education, prompts &amp; practical tools</small><em>launchvault.ca</em></div><MoreVertical size={17} /></div>
            <span className="project-active"><i />Active preview</span>
            <div className="project-card-stats"><span><strong>28</strong><small>Published posts</small></span><span><strong>84</strong><small>Avg. impact score</small></span></div>
          </Link> : <div className="projects-no-results"><Search size={22} /><strong>No matching projects</strong><button type="button" onClick={() => setQuery("")}>Clear search</button></div>}
          <button className="project-create-card" type="button" onClick={() => projectDialog.current?.showModal()}><span><Plus size={22} /></span><strong>Create new project</strong><small>Add another workspace when you are ready.</small></button>
        </section>

        <section className="projects-stat-grid" aria-label="Workspace summary">
          {stats.map((item) => { const Icon = item.icon; return <article key={item.label} className={`projects-stat projects-stat--${item.tone}`}><span><Icon size={17} /></span><small>{item.label}</small><strong>{item.value}</strong><em>{item.change}</em></article>; })}
        </section>

        <div className="projects-dashboard-grid">
          <section className="projects-panel projects-panel--trend">
            <div className="projects-panel-heading"><div><BarChart3 size={17} /><strong>Workspace Performance Trend</strong></div><button type="button">Last 30 days<ChevronDown size={13} /></button></div>
            <WorkspaceTrendChart />
          </section>

          <section className="projects-panel projects-panel--health">
            <div className="projects-panel-heading"><div><Target size={17} /><strong>Overall SEO Health</strong></div><Link href="/app/seo">View details<ArrowRight size={12} /></Link></div>
            <div className="projects-health-body"><div className="projects-ring" style={{ "--score": "78%" } as CSSProperties}><strong>78</strong><span>Good</span></div><div className="projects-health-list"><span><i />Content quality <b>92</b></span><span><i />Keyword coverage <b>78</b></span><span><i />Internal linking <b>72</b></span><span><i />Technical SEO <b>76</b></span></div></div>
          </section>

          <section className="projects-panel projects-panel--geo">
            <div className="projects-panel-heading"><div><Sparkles size={17} /><strong>GEO Visibility Summary</strong></div><Link href="/app/geo">View details<ArrowRight size={12} /></Link></div>
            <div className="projects-health-body"><div className="projects-ring projects-ring--blue"><strong>62%</strong><span>Visible</span></div><div className="projects-health-list projects-health-list--platforms"><span>Google AI <b>78%</b><em>+12%</em></span><span>ChatGPT <b>56%</b><em>+18%</em></span><span>Perplexity <b>48%</b><em>+20%</em></span><span>Claude <b>42%</b><em>+16%</em></span></div></div>
          </section>

          <section className="projects-panel projects-panel--content">
            <div className="projects-panel-heading"><div><FileText size={17} /><strong>Top Performing Content</strong></div><Link href="/app">View all<ArrowRight size={12} /></Link></div>
            <div className="projects-table projects-table--content"><div><span>#</span><span>Content</span><span>Traffic</span><span>Impact</span></div>{["Learn AI in 5 Minutes a Day","Practical Prompt Writing","AI Agents: A Beginner’s Guide","RAG Explained Without Jargon","Build an AI Workflow"].map((title,index)=><div key={title}><span>{index+1}</span><strong>{title}</strong><span>{["4.2K","2.8K","1.9K","1.4K","980"][index]}</span><em>{[92,88,84,82,78][index]}</em></div>)}</div>
          </section>

          <section className="projects-panel projects-panel--distribution">
            <div className="projects-panel-heading"><div><LayoutGrid size={17} /><strong>Project Distribution</strong></div></div>
            <div className="projects-distribution"><div className="projects-ring projects-ring--single"><strong>1</strong><span>Project</span></div><div><span><i />LaunchVault.ca <b>100%</b></span><small>Only one project is configured.</small></div></div>
          </section>

          <section className="projects-panel projects-panel--activity">
            <div className="projects-panel-heading"><div><Clock3 size={17} /><strong>Recent Workspace Activity</strong></div><Link href="/app/history">View all<ArrowRight size={12} /></Link></div>
            <div className="projects-feed">{activity.map(([title,detail,time],index)=><article key={title}><span>{index+1}</span><div><strong>{title}</strong><small>{detail}</small></div><time>{time}</time></article>)}</div>
          </section>

          <section className="projects-panel projects-panel--performance">
            <div className="projects-panel-heading"><div><BarChart3 size={17} /><strong>All Projects Performance</strong></div><label><Search size={13}/><input aria-label="Search performance" placeholder="Search projects…"/></label></div>
            <div className="projects-table projects-table--performance"><div><span>Project</span><span>Status</span><span>Published</span><span>Traffic</span><span>Impressions</span><span>Impact</span><span>Updated</span></div><div><strong>LaunchVault.ca</strong><em>Active preview</em><span>28</span><span>4.2K</span><span>42.7K</span><b>84</b><span>May 25, 2025</span></div></div>
          </section>

          <section className="projects-panel projects-panel--opportunities">
            <div className="projects-panel-heading"><div><Sparkles size={17} /><strong>Top Opportunities</strong></div><Link href="/app/seo">View all<ArrowRight size={12}/></Link></div>
            <div className="projects-feed projects-feed--opportunities">{opportunities.map(([title,detail,priority],index)=><article key={title}><span>{index+1}</span><div><strong>{title}</strong><small>{detail}</small></div><em>{priority}</em></article>)}</div>
          </section>

          <section className="projects-panel projects-panel--calendar">
            <div className="projects-panel-heading"><div><CalendarDays size={17}/><strong>Content Calendar</strong></div><button type="button">May 2025<ChevronDown size={12}/></button></div>
            <div className="projects-calendar">{["Mon 19","Tue 20","Wed 21","Thu 22","Fri 23"].map((day,index)=><article key={day}><strong>{day}</strong><span>{["AI agents guide","Prompt writing","RAG explainer","AI workflows","Weekly roundup"][index]}</span><small>{index % 2 ? "Review" : "Scheduled"}</small></article>)}</div>
          </section>

          <section className="projects-panel projects-panel--automation">
            <div className="projects-panel-heading"><div><Zap size={17}/><strong>Automation Summary</strong></div><span className="projects-panel-status"><i/>Preview</span></div>
            <div className="projects-automation"><span>Content sync <b>Backend pending</b></span><span>AI suggestions <b>Preview data</b></span><span>SEO optimization <b>Ready to connect</b></span><span>Analytics sync <b>Optional</b></span></div>
          </section>
        </div>
      </div>
      <dialog ref={projectDialog} className="preview-info-dialog" aria-labelledby="project-dialog-title"><div><h2 id="project-dialog-title">Your workspace</h2><button type="button" aria-label="Close" onClick={() => projectDialog.current?.close()}>×</button></div><p>This preview includes one project: LaunchVault.ca. You can explore its content, analytics, SEO, and GEO workspace now.</p><Link className="button" href="/app">Open LaunchVault <ArrowRight size={16} /></Link></dialog>
    </main>
  );
}
