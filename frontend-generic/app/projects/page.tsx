"use client";

import { useMemo, useRef, useState, type CSSProperties } from "react";
import Link from "next/link";
import { WorkspaceTrendChart } from "@/components/visibility-chart";
import calendarStyles from "./projects-calendar.module.css";
import { chartRanges as trendRanges, type ChartRange } from "@/lib/chart-range";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Zap,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
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

type CalendarEvent = {
  id: string;
  date: string;
  title: string;
  time: string;
  status: "Draft" | "Review" | "Scheduled" | "Published";
  type: string;
  template: string;
};

const calendarEvents: CalendarEvent[] = [
  { id: "seo-checklist", date: "2025-05-01", title: "SEO checklist for practical AI lessons", time: "9:30 AM", status: "Published", type: "Guide", template: "Long-form guide" },
  { id: "prompt-library", date: "2025-05-05", title: "Prompt library: work smarter with AI", time: "10:00 AM", status: "Scheduled", type: "Resource", template: "Resource library" },
  { id: "prompt-writing", date: "2025-05-06", title: "Prompt writing workshop", time: "1:00 PM", status: "Review", type: "Lesson", template: "Course lesson" },
  { id: "ai-agents", date: "2025-05-08", title: "AI agents: a practical guide", time: "11:30 AM", status: "Draft", type: "Guide", template: "Editorial guide" },
  { id: "rag-explainer", date: "2025-05-12", title: "RAG explained without jargon", time: "9:00 AM", status: "Scheduled", type: "Explainer", template: "Article" },
  { id: "workflow", date: "2025-05-15", title: "Build an AI workflow in one afternoon", time: "2:00 PM", status: "Review", type: "Tutorial", template: "Step-by-step tutorial" },
  { id: "newsletter", date: "2025-05-19", title: "Weekly learning roundup", time: "8:30 AM", status: "Published", type: "Newsletter", template: "Email digest" },
  { id: "learn-ai", date: "2025-05-21", title: "Learn AI in 5 Minutes a Day", time: "10:00 AM", status: "Published", type: "Guide", template: "Demo workspace guide" },
  { id: "course-update", date: "2025-05-21", title: "Course update: prompt-writing basics", time: "3:00 PM", status: "Scheduled", type: "Lesson", template: "Course lesson" },
  { id: "comparison", date: "2025-05-23", title: "AI tools comparison for beginners", time: "12:00 PM", status: "Draft", type: "Comparison", template: "Comparison page" },
  { id: "weekly-roundup", date: "2025-05-27", title: "What to learn next: May roundup", time: "9:00 AM", status: "Review", type: "Newsletter", template: "Email digest" },
  { id: "ai-planning", date: "2025-05-29", title: "Planning an AI study routine", time: "11:00 AM", status: "Scheduled", type: "Guide", template: "Demo workspace guide" }
];

function dateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function getCalendarDays(month: Date) {
  const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
  const start = new Date(month.getFullYear(), month.getMonth(), 1 - firstDay.getDay());
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

function formatMonth(date: Date) {
  return new Intl.DateTimeFormat("en-CA", { month: "long", year: "numeric" }).format(date);
}

function formatLongDate(date: Date) {
  return new Intl.DateTimeFormat("en-CA", { weekday: "long", month: "long", day: "numeric" }).format(date);
}

export default function ProjectsPage() {
  const [query, setQuery] = useState("");
  const [view, setView] = useState("grid");
  const [sort, setSort] = useState("default");
  const [trendRange, setTrendRange] = useState<ChartRange>("30");
  const [calendarMonth, setCalendarMonth] = useState(() => new Date(2025, 4, 1));
  const [selectedCalendarDate, setSelectedCalendarDate] = useState("2025-05-21");
  const projectDialog = useRef<HTMLDialogElement>(null);
  const matchesProject = "demo-workspace.example ai education prompts practical tools".includes(query.toLowerCase().trim());
  const calendarDays = useMemo(() => getCalendarDays(calendarMonth), [calendarMonth]);
  const monthOptions = Array.from({ length: 12 }, (_, month) => ({
    value: `${calendarMonth.getFullYear()}-${month}`,
    date: new Date(calendarMonth.getFullYear(), month, 1)
  }));
  const selectedDate = useMemo(() => new Date(`${selectedCalendarDate}T12:00:00`), [selectedCalendarDate]);
  const selectedEvents = useMemo(() => calendarEvents.filter((event) => event.date === selectedCalendarDate), [selectedCalendarDate]);
  const activeTrendRange = trendRanges.find((range) => range.value === trendRange) ?? trendRanges[3];

  const changeCalendarMonth = (next: Date) => {
    setCalendarMonth(next);
    setSelectedCalendarDate(dateKey(next));
  };

  const selectCalendarMonth = (value: string) => {
    const [year, month] = value.split("-").map(Number);
    changeCalendarMonth(new Date(year, month, 1));
  };
  return (
    <main className="projects-page">
      <header className="projects-topbar">
        <Link className="projects-brand" href="/projects"><span><Zap size={15} fill="currentColor" /></span><strong>Demo workspace</strong></Link>
        <div className="projects-search"><Search size={16} /><input aria-label="Search projects" placeholder="Search projects, domains, or content…" value={query} onChange={(event) => setQuery(event.target.value)} /><kbd>⌘ K</kbd></div>
        <div className="projects-top-actions">
          <div className="projects-workspace"><span>DW</span>Demo workspace</div>
          <div className="projects-date"><CalendarDays size={15} />May 12, 2025 – May 25, 2025</div>
          <button className="button button--small" type="button" onClick={() => projectDialog.current?.showModal()}><Plus size={15} />New project</button>
          <Link className="projects-icon-button" href="/app/notifications" aria-label="Notifications"><Bell size={17} /></Link>
          <Link className="projects-avatar" href="/app/settings" aria-label="Account settings">JD</Link>
        </div>
      </header>

      <div className="projects-canvas">
        <div className="projects-heading">
          <div><span>Projects</span><h1>All Projects Dashboard</h1><p>Manage and monitor your content workspace in one place.</p></div>
          <span className="projects-demo-badge"><i />Illustrative workspace data</span>
        </div>

        <div className="projects-section-heading">
          <div><h2>Your projects</h2><span>1 project</span></div>
          <div className="projects-view-actions"><label><Search size={14} /><input aria-label="Filter projects" placeholder="Search projects…" value={query} onChange={(event) => setQuery(event.target.value)} /></label><button className={view === "grid" ? "active" : ""} type="button" onClick={() => setView("grid")} aria-pressed={view === "grid"}><LayoutGrid size={14} />Grid</button><button className={view === "list" ? "active" : ""} type="button" onClick={() => setView("list")} aria-pressed={view === "list"}><List size={14} />List</button><span className="projects-sort-note">1 project</span></div>
        </div>

        <section className={`projects-card-grid projects-card-grid--${view}`} aria-label="Project list">
          {matchesProject ? <Link href="/app" className="project-card project-card--selected">
            <span className="project-card-check"><CheckCircle2 size={17} /></span>
            <div className="project-card-heading"><span className="project-logo"><Zap size={20} fill="currentColor" /></span><div><strong>Demo workspace</strong><small>AI education, prompts &amp; practical tools</small><em>demo-workspace.example</em></div><MoreVertical size={17} /></div>
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
            <div className="projects-panel-heading">
              <div><BarChart3 size={17} /><strong>Workspace Performance Trend</strong></div>
              <label className={calendarStyles.trendRangeSelect}>
                <span className={calendarStyles.visuallyHidden}>Select performance chart timeframe</span>
                <select value={trendRange} aria-label="Select performance chart timeframe" onChange={(event) => setTrendRange(event.target.value as ChartRange)}>
                  {trendRanges.map((range) => <option key={range.value} value={range.value}>{range.label}</option>)}
                </select>
                <ChevronDown size={13} aria-hidden="true" />
              </label>
            </div>
            <p className={calendarStyles.trendRangeNote} aria-live="polite">Showing illustrative performance activity from the {activeTrendRange.label.toLowerCase()}.</p>
            <WorkspaceTrendChart range={trendRange} />
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
            <div className="projects-distribution"><div className="projects-ring projects-ring--single"><strong>1</strong><span>Project</span></div><div><span><i />Demo workspace <b>100%</b></span><small>Only one project is configured.</small></div></div>
          </section>

          <section className="projects-panel projects-panel--activity">
            <div className="projects-panel-heading"><div><Clock3 size={17} /><strong>Recent Workspace Activity</strong></div><Link href="/app/history">View all<ArrowRight size={12} /></Link></div>
            <div className="projects-feed">{activity.map(([title,detail,time],index)=><article key={title}><span>{index+1}</span><div><strong>{title}</strong><small>{detail}</small></div><time>{time}</time></article>)}</div>
          </section>

          <section className="projects-panel projects-panel--performance">
            <div className="projects-panel-heading"><div><BarChart3 size={17} /><strong>All Projects Performance</strong></div><label><Search size={13}/><input aria-label="Search performance" placeholder="Search projects…"/></label></div>
            <div className="projects-table projects-table--performance"><div><span>Project</span><span>Status</span><span>Published</span><span>Traffic</span><span>Impressions</span><span>Impact</span><span>Updated</span></div><div><strong>Demo workspace</strong><em>Active preview</em><span>28</span><span>4.2K</span><span>42.7K</span><b>84</b><span>May 25, 2025</span></div></div>
          </section>

          <section className="projects-panel projects-panel--opportunities">
            <div className="projects-panel-heading"><div><Sparkles size={17} /><strong>Top Opportunities</strong></div><Link href="/app/seo">View all<ArrowRight size={12}/></Link></div>
            <div className="projects-feed projects-feed--opportunities">{opportunities.map(([title,detail,priority],index)=><article key={title}><span>{index+1}</span><div><strong>{title}</strong><small>{detail}</small></div><em>{priority}</em></article>)}</div>
          </section>

          <section className={`projects-panel projects-panel--calendar ${calendarStyles.calendarPanel}`}>
            <div className={`${"projects-panel-heading"} ${calendarStyles.calendarHeading}`}>
              <div><CalendarDays size={17}/><strong>Content Calendar</strong><span className={calendarStyles.calendarWorkspace}>Demo workspace</span></div>
              <div className={calendarStyles.calendarControls}>
                <button type="button" className={calendarStyles.calendarIconButton} aria-label="Previous month" onClick={() => changeCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1))}><ChevronLeft size={15}/></button>
                <label className={calendarStyles.monthSelect}>
                  <span className={calendarStyles.visuallyHidden}>Select calendar month</span>
                  <select value={`${calendarMonth.getFullYear()}-${calendarMonth.getMonth()}`} aria-label="Select content calendar month" onChange={(event) => selectCalendarMonth(event.target.value)}>
                    {monthOptions.map((option) => <option key={option.value} value={option.value}>{formatMonth(option.date)}</option>)}
                  </select>
                  <ChevronDown size={13} aria-hidden="true" />
                </label>
                <button type="button" className={calendarStyles.calendarIconButton} aria-label="Next month" onClick={() => changeCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1))}><ChevronRight size={15}/></button>
              </div>
            </div>
            <div className={calendarStyles.calendarLayout}>
              <div className={calendarStyles.calendarGrid} role="group" aria-label={`${formatMonth(calendarMonth)} content calendar`}>
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((weekday) => <span key={weekday} className={calendarStyles.weekday}>{weekday}</span>)}
                {calendarDays.map((day) => {
                  const key = dateKey(day);
                  const dayEvents = calendarEvents.filter((event) => event.date === key);
                  const isCurrentMonth = day.getMonth() === calendarMonth.getMonth();
                  const isSelected = key === selectedCalendarDate;
                  const isToday = key === "2025-05-21";
                  return <button key={key} type="button" className={`${calendarStyles.calendarDay} ${!isCurrentMonth ? calendarStyles.mutedDay : ""} ${isSelected ? calendarStyles.selectedDay : ""}`} onClick={() => { setSelectedCalendarDate(key); if (!isCurrentMonth) setCalendarMonth(new Date(day.getFullYear(), day.getMonth(), 1)); }} aria-pressed={isSelected} aria-label={`${formatLongDate(day)}, ${day.getFullYear()}${dayEvents.length ? `, ${dayEvents.length} content item${dayEvents.length > 1 ? "s" : ""}` : ""}`}>
                    <span className={`${calendarStyles.dayNumber} ${isToday ? calendarStyles.todayNumber : ""}`}>{day.getDate()}</span>
                    <span className={calendarStyles.dayEvents}>
                      {dayEvents.slice(0, 2).map((event) => <span className={`${calendarStyles.eventChip} ${calendarStyles[`status${event.status}`]}`} key={event.id}>{event.title}</span>)}
                      {dayEvents.length > 2 && <span className={calendarStyles.moreEvents}>+{dayEvents.length - 2} more</span>}
                    </span>
                  </button>;
                })}
              </div>
              <aside className={calendarStyles.calendarAgenda} aria-live="polite">
                <div className={calendarStyles.agendaHeading}><span>Selected day</span><strong>{formatLongDate(selectedDate)}</strong></div>
                {selectedEvents.length > 0 ? <div className={calendarStyles.agendaList}>{selectedEvents.map((event) => <article key={event.id} className={calendarStyles.agendaItem}>
                  <span className={`${calendarStyles.agendaStatus} ${calendarStyles[`status${event.status}`]}`}>{event.status}</span>
                  <strong>{event.title}</strong>
                  <small>{event.time} · {event.type}</small>
                  <em>{event.template}</em>
                </article>)}</div> : <div className={calendarStyles.agendaEmpty}><CalendarDays size={18}/><strong>Nothing scheduled</strong><span>Select a highlighted date to review the sample publishing plan.</span></div>}
                <div className={calendarStyles.agendaFooter}><span>Workspace</span><strong>Demo workspace</strong></div>
              </aside>
            </div>
          </section>

          <section className="projects-panel projects-panel--automation">
            <div className="projects-panel-heading"><div><Zap size={17}/><strong>Automation Summary</strong></div><span className="projects-panel-status"><i/>Preview</span></div>
            <div className="projects-automation"><span>Content sync <b>Backend pending</b></span><span>AI suggestions <b>Preview data</b></span><span>SEO optimization <b>Ready to connect</b></span><span>Analytics sync <b>Optional</b></span></div>
          </section>
        </div>
      </div>
      <dialog ref={projectDialog} className="preview-info-dialog" aria-labelledby="project-dialog-title"><div><h2 id="project-dialog-title">Your workspace</h2><button type="button" aria-label="Close" onClick={() => projectDialog.current?.close()}>×</button></div><p>This preview includes one project: Demo workspace. You can explore its content, analytics, SEO, and GEO workspace now.</p><Link className="button" href="/app">Open Demo workspace <ArrowRight size={16} /></Link></dialog>
    </main>
  );
}
