import { PLANS, planContact } from "@/lib/plans";
export function PlanCatalogue() {
  return <div className="fig-plan-catalogue">{["Business", "Education"].map(audience => <section className="fig-plan-group" key={audience} id={audience.toLowerCase()}>
    <div className="fig-plan-group-heading"><span className="section-kicker">{audience}</span><h2>{audience === "Business" ? "Build a better business website" : "Learn by understanding real websites"}</h2><p>{audience === "Business" ? "Plans for owners and organizations." : "Plans for independent learners and registered schools."}</p></div>
    <div className={`fig-plan-cards fig-plan-cards--${audience.toLowerCase()}`}>{PLANS.filter(p => p.audience === audience).map(plan => <article className={`fig-plan-card ${plan.name === "Premium" ? "fig-plan-card--accent" : ""}`} key={plan.name}>
      <h3>{plan.name}</h3><p>{plan.description}</p><div className="fig-plan-price">{plan.price === null ? <strong>Contact Us</strong> : <><strong>${plan.price}</strong><span>USD / month</span></>}</div>
      <a className={plan.name === "Premium" ? "button" : "secondary-button"} href={planContact(plan.name)}>{plan.price === null ? "Contact Us" : `Enquire about ${plan.name}`}</a>
    </article>)}</div>
  </section>)}<p className="pricing-disclaimer">Monthly prices in USD, excluding applicable taxes. Contact us to confirm plan inclusions and arrange a subscription.</p></div>;
}
