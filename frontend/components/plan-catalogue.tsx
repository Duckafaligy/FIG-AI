"use client";
import { useState } from "react";
import Link from "next/link";
import { actions } from "@/lib/api";
import { PLANS, planContact } from "@/lib/plans";
import { ArrowUpRight, BriefcaseBusiness, GraduationCap, Sprout, Layers3, Building2, BookOpen, School } from "lucide-react";
const icons = [Sprout, Layers3, Building2, BookOpen, School];

// The three fixed-price, self-serve plans (Standard/Premium/Education) --
// Enterprise and School Registered stay Contact Us, they have no Stripe
// price to check out at all (PLAN-DECISIONS.md).
type Status = "idle" | "loading" | "signed_out" | "error";

export function PlanCatalogue() {
  const [status, setStatus] = useState<Record<string, Status>>({});
  const [message, setMessage] = useState<Record<string, string>>({});

  async function subscribe(planName: string) {
    const key = planName.toLowerCase();
    setStatus((s) => ({ ...s, [planName]: "loading" }));
    const result = await actions.startCheckout(key);
    if (result.ok) {
      window.location.href = result.data.url;
      return;
    }
    setStatus((s) => ({ ...s, [planName]: result.status === 401 ? "signed_out" : "error" }));
    setMessage((m) => ({ ...m, [planName]: result.error }));
  }

  return <div className="fig-plan-catalogue">{["Business", "Education"].map(audience => <section className="fig-plan-group" key={audience} id={audience.toLowerCase()}>
    <div className={`fig-plan-group-heading fig-plan-banner fig-plan-banner--${audience.toLowerCase()}`}><span className="fig-plan-banner-icon">{audience === "Business" ? <BriefcaseBusiness size={28} /> : <GraduationCap size={30} />}</span><div><span className="section-kicker">{audience}</span><h2>{audience === "Business" ? "A clearer path to a better website." : "Big ideas start with understanding."}</h2><p>{audience === "Business" ? "For the people building a business, not just a website." : "For curious minds, independent learners, and entire classrooms."}</p></div><span className="fig-plan-banner-note">{audience === "Business" ? "Build with confidence" : "Keep asking why"}</span></div>
    <div className={`fig-plan-cards fig-plan-cards--${audience.toLowerCase()}`}>{PLANS.filter(p => p.audience === audience).map(plan => {
      const selfServe = plan.price !== null;
      const st = status[plan.name] ?? "idle";
      return <article className={`fig-plan-card ${plan.name === "Premium" ? "fig-plan-card--accent" : ""}`} key={plan.name}>
        <div className="fig-plan-card-top"><span className="fig-plan-symbol">{(() => { const Icon = icons[PLANS.indexOf(plan)]; return <Icon size={23} />; })()}</span><span>{plan.name === "Premium" ? "For your next chapter" : plan.price === null ? "Let’s talk" : "Monthly plan"}</span></div><h3>{plan.name}</h3><p>{plan.description}</p><div className="fig-plan-price">{plan.price === null ? <strong>Contact Us</strong> : <><strong>${plan.price}</strong><span>USD / month</span></>}</div>
        {selfServe ? <>
          <button type="button" className={plan.name === "Premium" ? "button" : "secondary-button"}
                 disabled={st === "loading"} onClick={() => subscribe(plan.name)}>
            {st === "loading" ? "Opening checkout…" : `Subscribe to ${plan.name}`}<ArrowUpRight size={16} />
          </button>
          {st === "signed_out" && <span className="fig-plan-card-note">
            <Link href="/signup">Create an account</Link> or <Link href="/signin">sign in</Link> first, then subscribe.
          </span>}
          {st === "error" && <span className="fig-plan-card-note">{message[plan.name] || "Couldn't start checkout. Try again."}</span>}
          {st === "idle" && <span className="fig-plan-card-note">Cancel anytime from Settings → Billing.</span>}
        </> : <>
          <a className="secondary-button" href={planContact(plan.name)}>Contact Us<ArrowUpRight size={16} /></a>
          <span className="fig-plan-card-note">A conversation about your requirements.</span>
        </>}
      </article>;
    })}</div>
  </section>)}<p className="pricing-disclaimer">Monthly prices in USD, excluding applicable taxes. Standard, Premium and Education subscribe instantly; Enterprise and School Registered start with a conversation.</p></div>;
}
