/** Text-only rendering: stored content is never injected as executable HTML. */
export function ArticlePreview({ title, body, category, hostname, mobile }: {
  title: string; body: string; category: string; hostname: string; mobile: boolean;
}) {
  const words = body.trim() ? body.trim().split(/\s+/).length : 0;
  return <section className={`cms-preview-stage ${mobile ? "cms-preview-mobile" : ""}`} aria-label="Article layout preview">
    <p className="cms-preview-disclaimer">Editorial layout · not a live CMS theme preview. Headings, paragraphs, lists, and quotes are supported; other markup is shown as text.</p>
    <div className="cms-article-sheet"><div className="cms-site-masthead"><BookMark />{hostname}<span>Journal</span></div>
      <article className="cms-article"><span className="cms-article-category">{category || "Article"}</span><h1>{title || "Your article title"}</h1><div className="cms-article-meta">{words ? `${words.toLocaleString()} words · ${Math.max(1, Math.ceil(words / 220))} min read` : "Start writing to see your article take shape"}</div>
        {body.trim() ? body.split(/\n\s*\n/).map((block, i) => {
          const lines = block.split("\n");
          if (lines.every(line => /^[-*] /.test(line))) return <ul key={i}>{lines.map((line, j) => <li key={j}>{line.slice(2)}</li>)}</ul>;
          if (lines.every(line => /^\d+\. /.test(line))) return <ol key={i}>{lines.map((line, j) => <li key={j}>{line.replace(/^\d+\. /, "")}</li>)}</ol>;
          return <div key={i}>{lines.map((line, j) => {
            if (/^#{1,2} /.test(line)) return <h2 key={j}>{line.replace(/^#+ /, "")}</h2>;
            if (/^#{3,6} /.test(line)) return <h3 key={j}>{line.replace(/^#+ /, "")}</h3>;
            if (line.startsWith("> ")) return <blockquote key={j}>{line.slice(2)}</blockquote>;
            return <p key={j}>{line}</p>;
          })}</div>;
        }) : <div className="cms-article-placeholder"><p>Your article body will appear here as you write.</p><span /><span /><span /></div>}
      </article><div className="cms-article-end">End of article</div>
    </div>
  </section>;
}
function BookMark() { return <span className="cms-site-mark" aria-hidden="true">J</span>; }
