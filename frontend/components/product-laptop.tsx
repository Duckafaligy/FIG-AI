import { BarChart3, FileText, Home, Library, Search, Settings2, Quote } from "lucide-react";

type LaptopVariant = "overview" | "queue" | "library";

const views: Record<LaptopVariant, {
  title: string;
  eyebrow: string;
  subtitle: string;
  primaryAction: string;
  metrics: [string, string, string][];
  panelTitle: string;
  rows: [string, string, string][];
  actions: string[];
}> = {
  overview: {
    title: "Good morning",
    eyebrow: "Overview",
    subtitle: "Here is what is happening with LaunchVault.ca.",
    primaryAction: "+ New content",
    metrics: [["Total content", "248", "+12%"], ["Avg. SEO score", "78", "+6 pts"], ["AI visibility", "4.3K", "+24%"], ["Organic traffic", "92K", "+18%"]],
    panelTitle: "Content performance",
    rows: [],
    actions: ["Improve for AI results", "Add internal links", "Update older content"]
  },
  queue: {
    title: "SEO Content Queue",
    eyebrow: "Content",
    subtitle: "Manage and review LaunchVault.ca drafts before publishing.",
    primaryAction: "+ New post",
    metrics: [["Posts in queue", "12", "+3"], ["Published this month", "28", "+27%"], ["Avg. SEO score", "84", "+6 pts"], ["Organic traffic", "4.2K", "+18.7%"], ["Keywords", "312", "+28%"]],
    panelTitle: "Posts for review",
    rows: [["AI agents: a plain-English guide", "In progress", "92"], ["RAG without jargon", "Queued", "88"], ["Prompting checklist", "Review", "84"], ["Build your first AI workflow", "Scheduled", "86"], ["Choosing the right AI tools", "Review", "82"], ["A practical guide to AI search", "Queued", "90"]],
    actions: ["Add internal links", "Review keyword brief", "Schedule this week"]
  },
  library: {
    title: "LaunchVault library",
    eyebrow: "Library",
    subtitle: "Browse guides, prompts, courses, and workflow blueprints.",
    primaryAction: "+ New lesson",
    metrics: [["Lessons", "1,500", "+12"], ["Topics", "50", "+3"], ["Saved prompts", "312", "+28"], ["Weekly readers", "4.2K", "+18%"]],
    panelTitle: "Recent content",
    rows: [["Learn AI in 5 Minutes", "Guide", "Live"], ["Build a Newsletter Agent", "Blueprint", "New"], ["Advanced Prompt Engineering", "Course", "60%"], ["A Practical Guide to AI Search", "Guide", "Live"], ["Your First Automation", "Blueprint", "Live"]],
    actions: ["Continue a course", "Open prompt lab", "Browse workflows"]
  }
};

const keywords = ["ai agents", "retrieval augmented generation", "prompt engineering", "ai workflows", "best ai tools", "ai search"];
const recentContent = [
  ["AI agents: a plain-English guide", "Published", "1.2K", "92"],
  ["RAG without jargon", "Published", "980", "88"],
  ["Build your first AI workflow", "Scheduled", "—", "86"]
];

export function ProductLaptop({ compact = false, variant = "overview" }: { compact?: boolean; variant?: LaptopVariant }) {
  const view = views[variant];

  return (
    <div className={`laptop laptop--${variant} ${compact ? "laptop--compact" : ""}`} aria-label={`FIG ${view.title} sample dashboard`}>
      <div className="laptop-lid">
        <div className="laptop-camera" />
        <div className="laptop-screen">
          <aside className="mini-sidebar">
            <b>FIG</b>
            <span className={variant === "overview" ? "active" : ""}><Home size={11} />Overview</span>
            <span className={variant === "queue" ? "active" : ""}><FileText size={11} />Content</span>
            <span><Search size={11} />Optimize</span>
            <span><BarChart3 size={11} />Analytics</span>
            <span className={variant === "library" ? "active" : ""}><Library size={11} />Library</span>
            <span><Settings2 size={11} />Settings</span>
          </aside>
          <div className="mini-app">
            <div className="mini-top">
              <span className="mini-search"><Search size={9} />Search content, projects, or insights...</span>
              <span className="mini-project"><b>LV</b>LaunchVault.ca</span>
              <i>{view.primaryAction}</i>
            </div>
            <div className="mini-page-heading"><small>{view.eyebrow}</small><strong>{view.title}</strong><span>{view.subtitle}</span></div>
            <div className="mini-kpis">
              {view.metrics.map(([label, value, detail]) => <div key={label}><small>{label}</small><strong>{value}</strong><em>{detail}</em></div>)}
            </div>
            <div className={`mini-content-grid${variant === "queue" ? " mini-content-grid--queue" : ""}`}>
              <div className="mini-chart">
                <div className="mini-panel-title">{view.panelTitle}</div>
                {variant === "overview" ? <><div className="mini-chart-legend"><span>Organic traffic</span><span>AI visibility</span></div><div className="mini-chart-preview"><svg viewBox="0 0 160 64" preserveAspectRatio="none"><path d="M0 52 C20 49 27 40 43 44 S70 26 88 31 S118 17 135 23 S151 9 160 12" fill="none" stroke="#6448ff" strokeWidth="3" /><path d="M0 59 C19 57 28 53 43 54 S70 42 88 45 S118 32 135 36 S151 23 160 27" fill="none" stroke="#2f80ed" strokeWidth="2.5" /></svg></div><div className="mini-chart-axis"><span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span></div></> : <><div className="mini-tabs"><span className="active">All</span><span>Queued</span><span>In progress</span><span>Review</span><span>Scheduled</span><span>Published</span></div><div className="mini-review-table"><div className="mini-review-head"><span>Content</span><span>Status</span><span>Score</span>{variant === "queue" && <><span>Target keyword</span><span>Scheduled</span></>}</div>{view.rows.map(([title, meta, score], index) => <div className="mini-review-row" key={title}><span><FileText size={9} /><b>{title}</b></span><em className={`mini-status mini-status--${meta.toLowerCase().replaceAll(" ", "-")}`}>{meta}</em><strong>{score}</strong>{variant === "queue" && <><small>{keywords[index]}</small><small>May {19 + index}, 2025</small></>}</div>)}</div></>}
              </div>
              {variant !== "queue" && <div className="mini-opportunities">
                <div className="mini-panel-title">{variant === "library" ? "Continue learning" : "Next steps"}</div>
                {view.actions.map((action, index) => <span key={action}>{index === 0 ? <Search size={11} /> : index === 1 ? <FileText size={11} /> : <Quote size={11} />}{action}</span>)}
                <div className="mini-health"><b>Workspace health</b><strong>● Healthy</strong><small>LaunchVault.ca</small></div>
              </div>}
            </div>
            {variant === "overview" && <div className="mini-recent-panel"><div className="mini-panel-title">Recent content <span>View all →</span></div>{recentContent.map(([title, status, traffic, score]) => <div className="mini-recent-row" key={title}><FileText size={9} /><b>{title}</b><em>{status}</em><span>{traffic} views</span><strong>{score}</strong></div>)}</div>}
            <div className="mini-screen-footer"><span>LaunchVault.ca</span><span>Sample data</span><span>Demo workspace</span></div>
          </div>
        </div>
      </div>
      <div className="laptop-base"><span /></div>
    </div>
  );
}
