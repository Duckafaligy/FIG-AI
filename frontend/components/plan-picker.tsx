"use client";

import { ArrowRight, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { actions, apiClient, type ApiMe } from "@/lib/api";
import { PLANS, monthly, planContact } from "@/lib/plans";
import styles from "./plan-picker.module.css";

const POLL_MS = 2000;
const POLL_LIMIT = 30; // about a minute for Stripe's webhook to land

/**
 * The paywall. The workspace is paid-only (2026-09-27): an account with no
 * plan gets 402 from /api and is sent here. After Stripe checkout the browser
 * usually arrives before the webhook that grants the plan, so with
 * ?checkout=done this polls /api/me until the plan shows up.
 */
export function PlanPicker() {
  const [state, setState] = useState<"loading" | "choose" | "confirming" | "slow">("loading");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const returning = params.get("checkout");
    if (returning === "cancelled") setNotice("Checkout was cancelled. Nothing was charged.");
    let tries = 0;
    let timer: ReturnType<typeof setTimeout>;
    const check = async () => {
      const me = await apiClient<ApiMe>("/api/me");
      if (me.ok && !me.data.signed_in) { window.location.replace("/signin"); return; }
      if (me.ok && me.data.signed_in && !me.data.account.needs_plan) { window.location.replace("/projects"); return; }
      if (returning === "done") {
        tries += 1;
        if (tries >= POLL_LIMIT) { setState("slow"); return; }
        setState("confirming");
        timer = setTimeout(check, POLL_MS);
        return;
      }
      setState("choose");
    };
    check();
    return () => clearTimeout(timer);
  }, []);

  const choose = async (plan: string) => {
    setBusy(plan);
    setError("");
    const result = await actions.startCheckout(plan);
    if (!result.ok) { setBusy(""); setError(result.error); return; }
    window.location.href = result.data.url;
  };

  if (state === "loading") return <p className={styles.status}>Loading your workspace…</p>;
  if (state === "confirming") return <div className={styles.status}><h1>Confirming your payment…</h1><p>This usually takes a few seconds. You’ll go straight to your workspace.</p></div>;
  if (state === "slow") return (
    <div className={styles.status}>
      <h1>Your payment is still being confirmed.</h1>
      <p>Stripe hasn’t told us yet. Refresh in a minute; if it still doesn’t open, contact us and we’ll sort it out. You won’t be charged twice.</p>
      <button className="button" type="button" onClick={() => window.location.reload()}>Check again</button>
    </div>
  );

  const selfServe = PLANS.filter((p) => p.price !== null);
  const contact = PLANS.filter((p) => p.price === null);
  return (
    <>
      <header className={styles.head}>
        <span className={styles.eyebrow}>One step left</span>
        <h1>Choose a plan to open your workspace.</h1>
        <p>Every plan runs all 21 checks; plans differ in how many projects you track and how many scans you run a month. Cancel any time, and your first payment has a 14-day refund.</p>
        {notice && <p className={styles.notice}>{notice}</p>}
        {error && <p className="form-message" role="alert">{error}</p>}
      </header>
      <div className={styles.grid}>
        {selfServe.map((plan) => {
          const key = plan.name.toLowerCase();
          const featured = key === "premium";
          return (
            <article key={plan.name} className={`${styles.card}${featured ? ` ${styles.featured}` : ""}`}>
              <div className={styles.top}>
                <span className={styles.audience}>{plan.audience}</span>
                <h2>{plan.name}</h2>
                <p className={styles.price}><strong>${monthly(plan)}</strong> / month</p>
                <p className={styles.desc}>{plan.description}</p>
              </div>
              <ul className={styles.limits}>
                <li><Check size={14} aria-hidden />{plan.projects} project{plan.projects === 1 ? "" : "s"}</li>
                <li><Check size={14} aria-hidden />{plan.scans} scans a month</li>
              </ul>
              <button className={featured ? "button" : "secondary-button"} type="button" disabled={!!busy} onClick={() => choose(key)}>
                {busy === key ? "Opening checkout…" : <>Choose {plan.name}<ArrowRight size={15} aria-hidden /></>}
              </button>
            </article>
          );
        })}
      </div>
      <div className={styles.contact}>
        {contact.map((plan) => (
          <a key={plan.name} href={planContact(plan.name)}>
            <strong>{plan.name}</strong><span>from ${monthly(plan)} / month · {plan.projects} projects · talk to us</span>
          </a>
        ))}
      </div>
      <p className={styles.free}>Just looking? The <a href="/#scan">free one-off scan</a> works on any site with no plan.</p>
    </>
  );
}
