import { BarChart3, FileText, Home, Search, Sparkles } from "lucide-react";

export function ProductLaptop({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`laptop ${compact ? "laptop--compact" : ""}`} aria-label="FIG dashboard preview">
      <div className="laptop-lid">
        <div className="laptop-camera" />
        <div className="laptop-screen">
          <aside className="mini-sidebar">
            <b>FIG</b>
            <span className="active"><Home size={11} />Overview</span>
            <span><FileText size={11} />Content</span>
            <span><Search size={11} />SEO & GEO</span>
            <span><BarChart3 size={11} />Analytics</span>
          </aside>
          <div className="mini-app">
            <div className="mini-top"><span>Good morning</span><i>+ New content</i></div>
            <div className="mini-kpis">
              {["Total content", "SEO health", "AI visibility", "Organic traffic"].map((label) => (
                <div key={label}><small>{label}</small><strong>—</strong><em>Awaiting data</em></div>
              ))}
            </div>
            <div className="mini-content-grid">
              <div className="mini-chart">
                <div className="mini-panel-title">Content performance</div>
                <div className="mini-chart-empty"><Sparkles size={16} /><span>Connect data to begin</span></div>
              </div>
              <div className="mini-opportunities">
                <div className="mini-panel-title">Next steps</div>
                <span><Search size={11} />Connect your site</span>
                <span><FileText size={11} />Create your first project</span>
                <span><Sparkles size={11} />Run a content audit</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="laptop-base"><span /></div>
    </div>
  );
}
