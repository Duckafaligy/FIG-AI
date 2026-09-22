"use client";
import { useState } from "react";
import { PLANS } from "@/lib/plans";
import styles from "./pricing-visuals.module.css";

export function PricingBudgetChart() {
  const [months, setMonths] = useState(1);
  const plans = PLANS.filter(p => p.price !== null).sort((a, b) => a.price! - b.price!);
  const ceiling = 100 * months;
  return <div className={styles.chart}>
    <div className={styles.chartHeading}><h3>A clear view of your budget.</h3><span>USD · before tax</span></div>
    <p className={styles.chartSubtitle}>Choose a timeline. See what each monthly plan adds up to.</p>
    <div className={styles.periods} aria-label="Budget period">{[1, 3, 6, 12].map(n => <button key={n} type="button" aria-pressed={months === n} onClick={() => setMonths(n)}>{n} {n === 1 ? "month" : "months"}</button>)}</div>
    <div className={styles.axis} aria-hidden="true"><span>$0</span><span>${ceiling / 2}</span><span>${ceiling.toLocaleString()}</span></div>
    <div className={styles.bars}>
      {plans.map(plan => <div className={styles.barRow} key={plan.name}><span>{plan.name}<small>${plan.price}/mo</small></span><div className={styles.track} aria-hidden="true"><div className={`${styles.bar} ${plan.audience === "Education" ? styles.green : plan.name === "Standard" ? styles.standardBar : ""}`} style={{ width: `${plan.price!}%` }} /></div><strong key={`${plan.name}-${months}`} className={styles.budgetValue}>${(plan.price! * months).toLocaleString()}</strong></div>)}
    </div>
    <div className={styles.budgetSummary} aria-live="polite"><strong>{months === 1 ? "One month. Three starting points." : `Your ${months}-month outlook.`}</strong><span>{plans.map(plan => `${plan.name} $${(plan.price! * months).toLocaleString()}`).join(" · ")}</span></div>
    <p className={styles.chartNote}>Calculated from monthly prices—not an annual subscription, discount, or checkout quote. Enterprise and School Registered are quoted separately.</p>
  </div>;
}
