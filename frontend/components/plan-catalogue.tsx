import { PLANS, planContact } from "@/lib/plans";
import { ArrowUpRight, BriefcaseBusiness, GraduationCap, Sprout, Layers3, Building2, BookOpen, School } from "lucide-react";
const icons = [Sprout, Layers3, Building2, BookOpen, School];
export function PlanCatalogue() {
  return <div className="fig-plan-catalogue">{["Business", "Education"].map(audience => <section className="fig-plan-group" key={audience} id={audience.toLowerCase()}>
    <div className={`fig-plan-group-heading fig-plan-banner fig-plan-banner--${audience.toLowerCase()}`}><span className="fig-plan-banner-icon">{audience === "Business" ? <BriefcaseBusiness size={28} /> : <GraduationCap size={30} />}</span><div><span className="section-kicker">{audience === "Business" ? "01 / Business" : "02 / Education"}</span><h2>{audience === "Business" ? "A clearer path to a better website." : "Big ideas start with understanding."}</h2><p>{audience === "Business" ? "For the people building a business, not just a website." : "For curious minds, independent learners, and entire classrooms."}</p></div><span className="fig-plan-banner-note">{audience === "Business" ? "Build with confidence" : "Keep asking why"}</span></div>
    <div className={`fig-plan-cards fig-plan-cards--${audience.toLowerCase()}`}>{PLANS.filter(p => p.audience === audience).map(plan => <article className={`fig-plan-card ${plan.name === "Premium" ? "fig-plan-card--accent" : ""}`} key={plan.name}>
      <div className="fig-plan-card-top"><span className="fig-plan-symbol">{(() => { const Icon = icons[PLANS.indexOf(plan)]; return <Icon size={23} />; })()}</span><span>{plan.name === "Premium" ? "For your next chapter" : plan.price === null ? "Let’s talk" : "Monthly plan"}</span></div><h3>{plan.name}</h3><p>{plan.description}</p><div className="fig-plan-price">{plan.price === null ? <strong>Contact Us</strong> : <><strong>${plan.price}</strong><span>USD / month</span></>}</div>
      <a className={plan.name === "Premium" ? "button" : "secondary-button"} href={planContact(plan.name)}>{plan.price === null ? "Contact Us" : `Enquire about ${plan.name}`}<ArrowUpRight size={16} /></a>
      <span className="fig-plan-card-note">{plan.price === null ? "A conversation about your requirements." : "Confirm your plan with our team."}</span>
    </article>)}</div>
  </section>)}<p className="pricing-disclaimer">Monthly prices in USD, excluding applicable taxes. Contact us to confirm plan inclusions and arrange a subscription.</p></div>;
}
