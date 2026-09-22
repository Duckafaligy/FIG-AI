"use client";
import { useState } from "react";
import { PLANS } from "@/lib/plans";
import styles from "./pricing-visuals.module.css";

export function PricingBudgetChart() {
  const [months, setMonths] = useState(1);
  const plans = PLANS.filter(p => p.price !== null).sort((a, b) => a.price! - b.price!);
  const ceiling = 100 * months;
  return <div className={styles.chart}>
    <div className={styles.chartHeading}><h3>Plan your investment</h3><span>USD · before tax</span></div>
    <p className={styles.chartSubtitle}>Compare the cost over your own timeline.</p>
    <div className={styles.periods} aria-label="Budget period">{[1, 3, 6, 12].map(n => <button key={n} type="button" aria-pressed={months === n} onClick={() => setMonths(n)}>{n} {n === 1 ? "month" : "months"}</button>)}</div>
    <div className={styles.axis} aria-hidden="true"><span>$0</span><span>${ceiling / 2}</span><span>${ceiling.toLocaleString()}</span></div>
    <div className={styles.bars}>
      {plans.map(plan => <div className={styles.barRow} key={plan.name}><span>{plan.name}</span><div className={styles.track}><div className={`${styles.bar} ${plan.audience === "Education" ? styles.green : ""}`} style={{ width: `${plan.price! / 100 * 100}%` }} /></div><strong>${(plan.price! * months).toLocaleString()}</strong></div>)}
    </div>
    <div className={styles.budgetSummary} aria-live="polite"><strong>{months === 1 ? "Monthly cost" : `${months}-month budget`}</strong><span>{plans.map(plan => `${plan.name} $${(plan.price! * months).toLocaleString()}`).join(" · ")}</span></div>
    <p className={styles.chartNote}>Calculated from monthly prices—not an annual subscription, discount, or checkout quote. Enterprise and School Registered are quoted separately.</p>
  </div>;
}
