import Image from "next/image";
import { ArrowUpRight, BriefcaseBusiness, GraduationCap } from "lucide-react";
import { PLANS, planContact } from "@/lib/plans";
import styles from "./pricing-visuals.module.css";

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
  const monthly = PLANS.filter(plan => plan.price !== null).sort((a, b) => a.price! - b.price!);
  return <section className={`page-shell ${styles.comparison}`} aria-labelledby="comparison-title">
    <div className={styles.heading}><span>THE BIG PICTURE</span><h2 id="comparison-title">Your options, side by side.</h2><p>A clear view of who each plan is for and what it costs.</p></div>
    <div className={styles.overview}>
      <div className={styles.chart}>
        <div className={styles.chartHeading}><h3>Monthly plans at a glance</h3><span>USD / month</span></div>
        <div className={styles.bars} role="img" aria-label="Monthly price comparison: Education 19 dollars, Standard 49 dollars, Premium 99 dollars.">
          {monthly.map(plan => <div className={styles.barRow} key={plan.name}><span>{plan.name}</span><div className={styles.track}><div className={`${styles.bar} ${plan.audience === "Education" ? styles.green : ""}`} style={{ width: `${plan.price! / 99 * 100}%` }} /></div><strong>${plan.price}</strong></div>)}
        </div><p className={styles.chartNote}>Price comparison only. Plans serve different needs; price is not a measure of performance. Taxes excluded.</p>
      </div>
      <aside className={styles.custom}><span className={styles.customIcon}><BriefcaseBusiness size={23} /><GraduationCap size={23} /></span><span className={styles.eyebrow}>ORGANIZATIONS & SCHOOLS</span><h3>Not every team<br />fits a price tag.</h3><p>Talk to us about Enterprise or School Registered. Start with your goals, your people, and what you need from FIG.</p><a href={planContact("Enterprise or School Registered")}>Let’s talk<ArrowUpRight size={17} /></a></aside>
    </div>
    <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Plan comparison table; scroll horizontally on smaller screens">
      <table className={styles.table}><caption>Compare FIG Business and Education plans</caption><thead><tr><th scope="col">At a glance</th>{PLANS.map(p => <th scope="col" key={p.name}><small>{p.audience}</small>{p.name}</th>)}</tr></thead><tbody>
        <tr><th scope="row">Monthly price</th>{PLANS.map(p => <td key={p.name} className={styles.tablePrice}>{p.price === null ? "Contact Us" : `$${p.price} USD`}</td>)}</tr>
        <tr><th scope="row">Designed for</th>{PLANS.map(p => <td key={p.name}>{p.description.replace(/^For /, "")}</td>)}</tr>
        <tr><th scope="row">Plan category</th>{PLANS.map(p => <td key={p.name}><span className={p.audience === "Education" ? styles.eduPill : styles.bizPill}>{p.audience}</span></td>)}</tr>
        <tr><th scope="row">Next step</th>{PLANS.map(p => <td key={p.name}><a href={planContact(p.name)} aria-label={`Ask about ${p.name}`}>Ask about this plan <ArrowUpRight size={13} /></a></td>)}</tr>
      </tbody></table>
    </div><p className={styles.tableNote}>Detailed feature inclusions and usage limits are confirmed with our team before purchase.</p>
  </section>;
}
