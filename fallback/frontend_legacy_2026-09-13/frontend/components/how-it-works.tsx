import { Link2, Filter, Lightbulb } from "lucide-react";
import { Reveal } from "./reveal";

const steps = [
  {
    Icon: Link2,
    title: "Paste any public URL",
    body: "No install, no snippet, no account. We fetch the page the way a visitor would.",
  },
  {
    Icon: Filter,
    title: "Rules engine flags specific tells",
    body: "Deterministic checks over markup, computed styles, and copy. No model guessing.",
  },
  {
    Icon: Lightbulb,
    title: "Read the explanation, apply the fix",
    body: "Each flag names the pattern, says why it reads as generated, and gives you the change.",
  },
];

// No numbered labels, no step counters, no eyebrow text — the reading order
// carries the sequence on its own.
export function HowItWorks() {
  return (
    <section id="how-it-works" className="section scroll-mt-24">
      <div className="container-page">
        <Reveal>
          <h2 className="text-section text-foreground">How it works</h2>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-12 md:grid-cols-3 md:gap-8">
          {steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.08}>
              <div>
                <div className="flex items-center gap-2.5">
                  <s.Icon
                    className="h-5 w-5 shrink-0 text-muted"
                    strokeWidth={1.75}
                  />
                  <h3 className="text-[18px] font-semibold text-foreground">
                    {s.title}
                  </h3>
                </div>
                <p className="text-body mt-3 max-w-[320px] text-muted">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
