import styles from "./pricing-visuals.module.css";

const layers = [
  { title: "Craft", subtitle: "Does it feel considered?", copy: "Find repeated card treatments, generic marketing phrases, familiar default palettes, and flat typography. Each flag explains a pattern—not who made the page.", examples: "Visual repetition · Copy specificity · Typography" },
  { title: "Structure", subtitle: "Does the page make sense?", copy: "Check the H1, skipped heading levels, thin content, and section ordering. See where the underlying page structure could be clearer for the people reading it.", examples: "Heading hierarchy · Content depth · Page order" },
  { title: "Search", subtitle: "Are the basics in place?", copy: "Review titles, descriptions, canonicals, language attributes, image alt text, and internal-link signals. Fix concrete omissions instead of chasing an unexplained SEO score.", examples: "Metadata · Canonicals · Descriptive images" },
  { title: "Answers", subtitle: "Is your content easy to understand?", copy: "Look for structured data, answerable questions, and specific supporting details. These are content-readiness signals, not a promise of search rankings or AI citations.", examples: "Structured data · Questions · Specific details" },
];
export function PricingProductDetail() {
  return <section className={`page-shell ${styles.productDetail}`} aria-labelledby="product-detail-title">
    <div className={styles.heading}><span>WHAT FIG ACTUALLY LOOKS AT</span><h2 id="product-detail-title">More than a number.<br />A reason. A location. A next step.</h2><p>Four perspectives on your website, grounded in the page’s HTML and content.</p></div>
    <div className={styles.layerGrid}>{layers.map((layer, i) => <article key={layer.title} className={styles.layer}><span className={styles.layerLabel}>{layer.title}</span><h3>{layer.subtitle}</h3><p>{layer.copy}</p><small>{layer.examples}</small></article>)}</div>
    <div className={styles.workflowDetail}><div><span className={styles.eyebrow}>FROM FINDING TO FOLLOW-THROUGH</span><h3>Understand it.<br />Improve it.<br />Check it again.</h3><p>A practical workflow for your own website—not a tool for accusing someone else of using AI.</p></div><ol>
      <li><strong>Read the evidence</strong><p>Open the affected page, understand the flagged pattern, and review the suggested fix. The scanner reads public HTML; JavaScript-only content can be incomplete.</p></li>
      <li><strong>Choose the next action</strong><p>Make your own changes, or review supported title and heading fixes for a connected WordPress site. Those changes require approval and can be reverted.</p></li>
      <li><strong>Give missing content a home</strong><p>Turn content gaps into briefs. Save drafts in the library, check them against nine writing rules, and move them through review. Automatic drafting and new-post publishing are not available yet.</p></li>
      <li><strong>Re-scan and add context</strong><p>Re-check after an edit. Connect read-only Google Analytics and Search Console to bring your own traffic and query data alongside the findings.</p></li>
    </ol></div>
    <div className={styles.learningNote}><strong>For education: learning stays personal.</strong><p>Study patterns, understand the explanation, and apply what you learn to your own work. FIG is not a plagiarism detector or an automated grading system. School discussions should preserve student choice over sharing results.</p></div>
    <p className={styles.tableNote}>These describe current product capabilities, not a promise that every feature is included in every plan. Plan-specific allowances are confirmed before purchase.</p>
  </section>;
}
