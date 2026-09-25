import Image from "next/image";
import { ArrowUpRight, BriefcaseBusiness, GraduationCap } from "lucide-react";
import { PLANS, planContact } from "@/lib/plans";
import styles from "./pricing-visuals.module.css";
import { PricingBudgetChart } from "./pricing-budget-chart";

const fitRows = [
  { label: "Who it’s for", values: ["Business owners", "Businesses focused on ongoing improvement", "Organizations with a tailored scope", "Students & independent learners", "Registered schools & classrooms"] },
  { label: "Suggested focus", values: ["Understand your site and prioritize fixes", "Make review and improvement part of your routine", "Discuss your website portfolio and workflow", "Learn design, structure, search, and content fundamentals", "Explore website analysis as a learning activity"] },
  { label: "Example use case", values: ["Review your business homepage before a refresh", "Re-check pages as your website evolves", "Plan an approach across organizational websites", "Analyze your own project and explain your design decisions", "Discuss page patterns using examples students choose to share"] },
];
const capabilities = [
  ["Website analysis", "Craft, structure, search, and answer-readiness checks", "Locates patterns in public HTML and explains what to improve."],
  ["Finding explanations", "Evidence, context, and a suggested fix", "Signals to evaluate—not proof of AI authorship or guaranteed results."],
  ["Content library", "Saved drafts, rule-based scoring, and review stages", "Automatic article generation and new-post publishing are not available yet."],
  ["WordPress changes", "Supported title and heading fixes", "Requires a connected site and approval; supported changes can be reverted."],
  ["Analytics context", "Read-only Analytics and Search Console connections", "Requires your authorized Google properties; no invented traffic or ranking data."],
  ["Re-checking your work", "On-demand re-scans and stored history", "Helps you review changes; scheduled daily monitoring is not active."],
];

export function PricingPhotography() {
  return <div className={`page-shell ${styles.photos}`}>
    <a href="#business" className={styles.photo}>
      <Image src="https://images.unsplash.com/photo-1758873268745-dd2cf0d677b5?auto=format&fit=crop&w=1100&q=85" alt="A team collaborating at a computer" fill sizes="(max-width: 700px) 100vw, 60vw" />
      <span className={styles.photoTag}><BriefcaseBusiness size={16} />For business</span>
      <div><span>Turn insight into your next move.</span><strong>Build a website you’re proud of.<ArrowUpRight size={25} /></strong></div>
    </a>
    <a href="#education" className={styles.photo}>
      <Image src="https://images.unsplash.com/photo-1758876021859-bd2371d8f0a2?auto=format&fit=crop&w=900&q=85" alt="A person learning and working on a laptop" fill sizes="(max-width: 700px) 100vw, 40vw" />
      <span className={styles.photoTag}><GraduationCap size={18} />For education</span>
      <div><span>A little curiosity goes a long way.</span><strong>Learn by looking closer.<ArrowUpRight size={25} /></strong></div>
    </a>
  </div>;
}

export function PricingComparison() {
  return <section className={`page-shell ${styles.comparison}`} aria-labelledby="comparison-title">
    <div className={`${styles.heading} ${styles.comparisonHeading}`}><span>THE BIG PICTURE</span><h2 id="comparison-title">Find your fit.<br />Know your investment.</h2><p>Building a business or exploring your next idea? Compare the costs, find your starting point, and see how FIG fits the way you work.</p></div>
    <div className={styles.overview}>
      <PricingBudgetChart />
      <aside className={styles.custom}><span className={styles.customIcon}><BriefcaseBusiness size={23} /><GraduationCap size={23} /></span><span className={styles.eyebrow}>ORGANIZATIONS & SCHOOLS</span><h3>Start with your needs.<br />Build the right scope.</h3><p>Enterprise and School Registered begin with a conversation, not an automatic checkout.</p><dl className={styles.enquiryList}><div><dt>Enterprise</dt><dd>Tell us about your websites, who will use FIG, and how you review and make changes.</dd></div><div><dt>School Registered</dt><dd>Share your learning goals, expected group size, and how students would choose to share their work.</dd></div><div><dt>What we’ll clarify</dt><dd>Plan inclusions, usage allowances, access requirements, and pricing before you commit.</dd></div></dl><a href={planContact("Enterprise or School Registered")}>Discuss your requirements<ArrowUpRight size={17} /></a></aside>
    </div>
    <p className={styles.scrollHint}>Scroll sideways to compare all five plans <span aria-hidden="true">↔</span></p>
    <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Plan comparison table; scroll horizontally on smaller screens">
      <table className={`${styles.table} ${styles.planTable}`}><caption>One view. Every option.<span className={styles.captionNote}>Compare Business and Education plans</span></caption><thead><tr><th scope="col">At a glance<small>Your plan, your starting point.</small></th>{PLANS.map(p => <th scope="col" key={p.name} className={p.audience === "Education" ? styles.educationColumn : styles.businessColumn}><small>{p.audience}</small>{p.name}<a className={styles.planHeaderLink} href={planContact(p.name)} aria-label={`Discuss ${p.name}`}>Let’s talk <ArrowUpRight size={13} /></a></th>)}</tr></thead><tbody>
        <tr><th scope="row">Monthly price</th>{PLANS.map(p => <td key={p.name} className={styles.tablePrice}>{p.price === null ? "Contact Us" : `$${p.price} USD`}</td>)}</tr>
        <tr><th scope="row">12-month budget<small className={styles.rowHint}>Monthly rate × 12; not annual billing</small></th>{PLANS.map(p => <td key={p.name}>{p.price === null ? "Quoted to your scope" : `$${(p.price * 12).toLocaleString()} USD`}</td>)}</tr>
        <tr className={styles.groupRow}><th colSpan={6}>Find your fit · suggested uses, not different feature entitlements</th></tr>
        {fitRows.map(row => <tr key={row.label}><th scope="row">{row.label}</th>{row.values.map((value, i) => <td key={PLANS[i].name}>{value}</td>)}</tr>)}
        <tr><th scope="row">Plan category</th>{PLANS.map(p => <td key={p.name}><span className={p.audience === "Education" ? styles.eduPill : styles.bizPill}>{p.audience}</span></td>)}</tr>
        <tr className={styles.groupRow}><th colSpan={6}>Before subscribing</th></tr>
        <tr><th scope="row">Sites, scans & usage</th><td colSpan={5}>Plan-specific limits have not been finalized. Confirm the number of sites, scans, and any usage allowances with our team.</td></tr>
        <tr><th scope="row">Members & support</th><td colSpan={5}>Seat counts, support commitments, and organization access are agreed before purchase. No unlimited seats or service-level guarantee is implied.</td></tr>
        <tr><th scope="row">Next step</th>{PLANS.map(p => <td key={p.name}><a href={planContact(p.name)} aria-label={`Ask about ${p.name}`}>Ask about this plan <ArrowUpRight size={13} /></a></td>)}</tr>
      </tbody></table>
    </div><p className={styles.tableNote}>All amounts exclude applicable taxes. The use cases above describe fit, not a promised feature list — Standard and Premium include the same FIG checks; the difference is how much of your workflow you run through it.</p>
    <div className={styles.capabilityHeading}><span className={styles.eyebrow}>UNDERSTAND THE PRODUCT</span><h3>What’s built—and what it means for you.</h3><p>Current capabilities across FIG. Availability within each commercial plan is confirmed before purchase.</p></div>
    <p className={`${styles.scrollHint} ${styles.capabilityScrollHint}`}>Scroll sideways for requirements and details <span aria-hidden="true">↔</span></p>
    <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Current FIG capabilities"><table className={`${styles.table} ${styles.capabilityTable}`}><caption>Current product capabilities</caption><thead><tr><th scope="col">Area</th><th scope="col">What you can work with</th><th scope="col">Requirements & boundaries</th></tr></thead><tbody>{capabilities.map(([name, feature, detail]) => <tr key={name}><th scope="row">{name}</th><td>{feature}</td><td>{detail}</td></tr>)}</tbody></table></div>
  </section>;
}
