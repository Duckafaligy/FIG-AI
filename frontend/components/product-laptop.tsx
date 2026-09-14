import { BarChart3, FileText, Home, Search, Sparkles } from "lucide-react";

type LaptopVariant = "overview" | "queue" | "library";

const views: Record<LaptopVariant, {
  title: string;
  metrics: [string, string, string][];
  panelTitle: string;
  rows: [string, string, string][];
  actions: string[];
}> = {
  overview: {
    title: "LaunchVault.ca",
    metrics: [["Published lessons", "1,500", "+12"], ["SEO health", "82", "+4 pts"], ["AI visibility", "42%", "+8%"], ["Organic traffic", "18.4K", "+18.7%"]],
    panelTitle: "Content performance",
    rows: [],
    actions: ["Review AI agents guide", "Refresh RAG explainer", "Publish prompt playbook"]
  },
  queue: {
    title: "SEO Content Queue",
    metrics: [["Posts in queue", "8", "+3"], ["Published this month", "14", "+27%"], ["Avg. SEO score", "82", "+4 pts"], ["Organic traffic", "18.4K", "+18.7%"]],
    panelTitle: "Posts for review",
    rows: [["AI agents guide", "Review", "92"], ["RAG without jargon", "Queued", "88"], ["Prompting checklist", "Draft", "84"]],
    actions: ["Add internal links", "Review keyword brief", "Schedule this week"]
  },
  library: {
    title: "LaunchVault library",
    metrics: [["Lessons", "1,500", "+12"], ["Topics", "50", "+3"], ["Saved prompts", "312", "+28"], ["Weekly readers", "4.2K", "+18%"]],
    panelTitle: "Recent content",
    rows: [["Learn AI in 5 Minutes", "Guide", "Live"], ["Build a Newsletter Agent", "Blueprint", "New"], ["Advanced Prompt Engineering", "Course", "60%"]],
    actions: ["Continue a course", "Open prompt lab", "Browse workflows"]
  }
};

export function ProductLaptop({ compact = false, variant = "overview" }: { compact?: boolean; variant?: LaptopVariant }) {
  const view = views[variant];

  return (
    <div className={`laptop laptop--${variant} ${compact ? "laptop--compact" : ""}`} aria-label={`FIG ${view.title} dashboard preview`}>
      <div className="laptop-lid">
        <div className="laptop-camera" />
        <div className="laptop-screen">
          <aside className="mini-sidebar">
            <b>FIG</b>
            <span className={variant === "overview" ? "active" : ""}><Home size={11} />Overview</span>
            <span className={variant === "queue" || variant === "library" ? "active" : ""}><FileText size={11} />Content</span>
            <span><Search size={11} />SEO & GEO</span>
            <span><BarChart3 size={11} />Analytics</span>
          </aside>
          <div className="mini-app">
            <div className="mini-top"><span>{view.title}</span><i>{variant === "queue" ? "+ New brief" : "+ New content"}</i></div>
            <div className="mini-kpis">
              {view.metrics.map(([label, value, detail]) => <div key={label}><small>{label}</small><strong>{value}</strong><em>{detail}</em></div>)}
            </div>
            <div className="mini-content-grid">
              <div className="mini-chart">
                <div className="mini-panel-title">{view.panelTitle}</div>
                {variant === "overview" ? <div className="mini-chart-preview"><svg viewBox="0 0 160 64" preserveAspectRatio="none"><path d="M0 52 C20 49 27 40 43 44 S70 26 88 31 S118 17 135 23 S151 9 160 12" fill="none" stroke="#6448ff" strokeWidth="3" /><path d="M0 59 C19 57 28 53 43 54 S70 42 88 45 S118 32 135 36 S151 23 160 27" fill="none" stroke="#2f80ed" strokeWidth="2.5" /></svg><span>Preview trend</span></div> : <div className="mini-content-list">{view.rows.map(([title, meta, score]) => <span key={title}><i /><b>{title}</b><em>{meta}</em><strong>{score}</strong></span>)}</div>}
              </div>
              <div className="mini-opportunities">
                <div className="mini-panel-title">{variant === "library" ? "Continue learning" : "Next steps"}</div>
                {view.actions.map((action, index) => <span key={action}>{index === 0 ? <Search size={11} /> : index === 1 ? <FileText size={11} /> : <Sparkles size={11} />}{action}</span>)}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="laptop-base"><span /></div>
    </div>
  );
}
