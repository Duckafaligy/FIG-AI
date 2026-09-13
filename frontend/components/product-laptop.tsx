import { BarChart3, FileText, Home, Search, Sparkles } from "lucide-react";

export function ProductLaptop({ compact = false }: { compact?: boolean }) {
  const metrics = [
    ["Published lessons", "1,500", "+12"],
    ["SEO health", "82", "+4 pts"],
    ["AI visibility", "42%", "+8%"],
    ["Organic traffic", "18.4K", "+18.7%"]
  ];

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
            <div className="mini-top"><span>LaunchVault.ca</span><i>+ New content</i></div>
            <div className="mini-kpis">
              {metrics.map(([label, value, detail]) => (
                <div key={label}><small>{label}</small><strong>{value}</strong><em>{detail}</em></div>
              ))}
            </div>
            <div className="mini-content-grid">
              <div className="mini-chart">
                <div className="mini-panel-title">Content performance</div>
                <div className="mini-chart-preview"><svg viewBox="0 0 160 64" preserveAspectRatio="none"><path d="M0 52 C20 49 27 40 43 44 S70 26 88 31 S118 17 135 23 S151 9 160 12" fill="none" stroke="#6448ff" strokeWidth="3" /><path d="M0 59 C19 57 28 53 43 54 S70 42 88 45 S118 32 135 36 S151 23 160 27" fill="none" stroke="#2f80ed" strokeWidth="2.5" /></svg><span>Preview trend</span></div>
              </div>
              <div className="mini-opportunities">
                <div className="mini-panel-title">Next steps</div>
                <span><Search size={11} />Review AI agents guide</span>
                <span><FileText size={11} />Refresh RAG explainer</span>
                <span><Sparkles size={11} />Publish prompt playbook</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="laptop-base"><span /></div>
    </div>
  );
}
