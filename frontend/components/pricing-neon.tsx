"use client";
import { useEffect, useState } from "react";
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

const PERIODS = [1, 3, 6, 12];

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
  const [months, setMonths] = useState(1);
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
  const ceiling = Math.max(...selfServe.map(p => p.price!)) * months;

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

      <section className="pn-cost">
        <div className="page-shell pn-cost-grid">
          <div className="pn-cost-copy">
            <h2>What it adds up to.</h2>
            <p>Monthly price times the months you pick. No annual discount, no contract.</p>
            <Switch label="Period" tone="light" options={PERIODS} value={months} onChange={setMonths} format={n => n === 1 ? "1 month" : `${n} months`} />
          </div>
          <div className="pn-bars" aria-live="polite">
            {selfServe.map(plan => (
              <div className="pn-bar-row" key={plan.name}>
                <span>{plan.name}<small>${plan.price} / month</small></span>
                <div className="pn-bar-track" aria-hidden="true">
                  <div className={`pn-bar-fill pn-bar-fill--${plan.name.toLowerCase()}`} style={{ transform: `scaleX(${plan.price! * months / ceiling})` }} />
                </div>
                <strong>${(plan.price! * months).toLocaleString("en-US")}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
