"use client";
import { useEffect, useState } from "react";
import { Pause, Play } from "lucide-react";
import Link from "next/link";
import { Check } from "lucide-react";
import { actions } from "@/lib/api";
import { PLANS, planContact } from "@/lib/plans";
import { REFUND_WINDOW_DAYS, TRIAL_DAYS } from "@/lib/legal";

type Audience = "Business" | "Education";
type Status = "idle" | "loading" | "signed_out" | "error";

const INCLUDED = [
  "All 21 checks across craft, structure, search and answers",
  "A reason and a concrete fix for every finding",
  "Scan history, so you can re-scan and compare",
  "Report links that stay private until you share them",
  "Content briefs, saved drafts and a review queue",
  "Read-only Google Analytics and Search Console",
  "Approved title and heading fixes on connected WordPress sites",
];

const money = (n: number, cents = false) => `$${cents ? n.toFixed(2) : Math.round(n)}`;
const METRICS = [
  { name: "Monthly price", note: "What you pay each month, in USD before tax.", value: (p: Plan) => p.price!, format: (n: number) => money(n) },
  { name: "Scans per month", note: "Your monthly allowance, shared across all your projects.", value: (p: Plan) => p.scans!, format: String },
  { name: "Active projects", note: "Websites you can track at the same time.", value: (p: Plan) => p.projects!, format: String },
  { name: "Scans per project", note: "Monthly scans if you spread them evenly across every project.", value: (p: Plan) => p.scans! / p.projects!, format: (n: number) => String(Math.round(n)) },
  { name: "Cost per scan", note: "Monthly price divided by included scans. Lower is better.", value: (p: Plan) => p.price! / p.scans!, format: (n: number) => money(n, true) },
  { name: "Cost per project", note: "Monthly price divided by active projects. Lower is better.", value: (p: Plan) => p.price! / p.projects!, format: (n: number) => money(n, true) },
];
const ROTATE_MS = 4000;
const RESUME_MS = 5000;
type Plan = (typeof PLANS)[number];

function Switch<T extends string | number>({ label, options, value, onChange, format, tone }: {
  label: string; options: readonly T[]; value: T; onChange: (v: T) => void; format?: (v: T) => string; tone: "dark" | "light";
}) {
  return (
    <div className={`pn-switch pn-switch--${tone}`} role="group" aria-label={label}>
      {options.map(o => (
        <button key={String(o)} type="button" aria-pressed={o === value} onClick={() => onChange(o)}>
          {format ? format(o) : String(o)}
        </button>
      ))}
    </div>
  );
}

export function PricingNeon() {
  const [audience, setAudience] = useState<Audience>("Business");
  const [status, setStatus] = useState<Record<string, Status>>({});
  const [message, setMessage] = useState<Record<string, string>>({});

  useEffect(() => {
    if (window.location.hash === "#education") setAudience("Education");
  }, []);

  async function subscribe(name: string) {
    setStatus(s => ({ ...s, [name]: "loading" }));
    const result = await actions.startCheckout(name.toLowerCase());
    if (result.ok) { window.location.href = result.data.url; return; }
    setStatus(s => ({ ...s, [name]: result.status === 401 ? "signed_out" : "error" }));
    setMessage(m => ({ ...m, [name]: result.error }));
  }

  const plans = PLANS.filter(p => p.audience === audience);
  const selfServe = PLANS.filter(p => p.price !== null).sort((a, b) => a.price! - b.price!);

  return (
    <>
      <section className="pn-hero">
        <div className="page-shell pn-hero-grid">
          <div>
            <h1>Simple monthly plans.</h1>
            <p>Every plan runs all 21 checks. Self-serve plans differ in projects tracked and scans per month.</p>
            <Switch label="Plans for" tone="dark" options={["Business", "Education"] as const} value={audience} onChange={setAudience} />
          </div>
          <dl className="pn-facts">
            <div><dt>From</dt><dd>$19 / month</dd></div>
            <div><dt>Free trial</dt><dd>{TRIAL_DAYS} days, no card</dd></div>
            <div><dt>Refund</dt><dd>{REFUND_WINDOW_DAYS} days on your first payment</dd></div>
          </dl>
        </div>
      </section>

      <section className="pn-plans" id={audience.toLowerCase()}>
        <div className={`page-shell pn-plan-grid pn-plan-grid--${plans.length}`}>
          {plans.map(plan => {
            const st = status[plan.name] ?? "idle";
            const featured = plan.name === "Premium";
            return (
              <article key={plan.name} className={`pn-card${featured ? " pn-card--featured" : ""}`}>
                <div className="pn-card-top">
                  <h2>{plan.name}</h2>
                  {featured && <span>Most scans</span>}
                </div>
                <p className="pn-price">
                  {plan.price === null ? <strong>Custom</strong> : <><strong>${plan.price}</strong><span>USD / month</span></>}
                </p>
                <p className="pn-desc">{plan.description}</p>
                <dl className="pn-limits">
                  <div><dt>{plan.projects ?? "Scoped"}</dt><dd>{plan.projects === 1 ? "active project" : "active projects"}</dd></div>
                  <div><dt>{plan.scans ?? "Scoped"}</dt><dd>scans per month</dd></div>
                </dl>
                {plan.price !== null ? <>
                  <button type="button" className={featured ? "button" : "secondary-button"} disabled={st === "loading"} onClick={() => subscribe(plan.name)}>
                    {st === "loading" ? "Opening checkout..." : `Choose ${plan.name}`}
                  </button>
                  <p className="pn-note" aria-live="polite">
                    {st === "signed_out" ? <><Link href="/signup">Create an account</Link> or <Link href="/signin">sign in</Link> first.</>
                      : st === "error" ? (message[plan.name] || "Checkout didn't open. Try again.")
                      : "Cancel anytime in Settings, Billing."}
                  </p>
                </> : <>
                  <a className="secondary-button" href={planContact(plan.name)}>Contact us</a>
                  <p className="pn-note">Limits and terms agreed with you.</p>
                </>}
              </article>
            );
          })}
        </div>
        <p className="page-shell pn-fine">Prices in USD, before tax. A scan is one audit of one website. Unused scans reset each billing period and never roll over, with no overage charges.</p>
      </section>

      <section className="pn-included">
        <div className="page-shell pn-included-grid">
          <h2>In every plan.</h2>
          <div>
            <ul>{INCLUDED.map(item => <li key={item}><Check size={16} />{item}</li>)}</ul>
            <p>Not available yet: scheduled monitoring, automatic publishing and full article writing.</p>
          </div>
        </div>
      </section>

      <PlanChart plans={selfServe} />
    </>
  );
}

function PlanChart({ plans }: { plans: Plan[] }) {
  const [index, setIndex] = useState(0);
  const [delay, setDelay] = useState(ROTATE_MS);
  const [stopped, setStopped] = useState(false);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  const running = !reduced && !stopped;
  useEffect(() => {
    if (!running) return;
    const t = setTimeout(() => { setIndex(i => (i + 1) % METRICS.length); setDelay(ROTATE_MS); }, delay);
    return () => clearTimeout(t);
  }, [running, index, delay]);

  const pick = (i: number) => { setIndex(i); setDelay(RESUME_MS); };
  const m = METRICS[index];
  const ceiling = Math.max(...plans.map(m.value));

  return (
    <section className="pn-cost">
      <div className="page-shell pn-cost-grid">
        <div className="pn-cost-copy">
          <h2>What each plan gives you.</h2>
          <p>{m.note}</p>
          <div className="pn-metrics" role="group" aria-label="Compare plans by">
            {METRICS.map((x, i) => (
              <button key={x.name} type="button" aria-pressed={i === index} onClick={() => pick(i)}>
                {x.name}
                {i === index && running && <i key={`${index}-${delay}`} style={{ animationDuration: `${delay}ms` }} aria-hidden="true" />}
              </button>
            ))}
          </div>
          {!reduced && (
            <button type="button" className="pn-rotate" aria-pressed={stopped} onClick={() => { setStopped(s => !s); setDelay(RESUME_MS); }}>
              {stopped ? <><Play size={14} /> Play</> : <><Pause size={14} /> Pause</>}
            </button>
          )}
        </div>
        <div className="pn-columns">
          {plans.map(plan => {
            const r = m.value(plan) / ceiling;
            return (
              <div className="pn-col" key={plan.name} style={{ "--r": r } as React.CSSProperties}>
                <div className="pn-col-plot">
                  <strong>{m.format(m.value(plan))}</strong>
                  <div className={`pn-col-bar pn-col-bar--${plan.name.toLowerCase()}`} aria-hidden="true" />
                </div>
                <span>{plan.name}<small>${plan.price} / month</small></span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
