"use client";

import { Wrench } from "lucide-react";
import { CategoryTag, ConfidenceBar, type Confidence } from "./scan-card";
import { Reveal } from "./reveal";

const collapsed: { category: string; tell: string; level: Confidence; value: number }[] = [
  {
    category: "layout",
    tell: "Three consecutive centered sections with identical structure",
    level: "medium",
    value: 0.62,
  },
  {
    category: "color",
    tell: "#6D28D9 is within 18 units of a known default violet",
    level: "low",
    value: 0.4,
  },
  {
    category: "copy",
    tell: "Headline opens with 'Elevate your' and the CTA reads 'Get Started'",
    level: "high",
    value: 0.82,
  },
];

export function ExampleOutput() {
  return (
    <section className="section">
      <div className="container-page">
        <Reveal>
          <h2 className="text-section text-foreground">
            What a scan actually looks like
          </h2>
        </Reveal>

        <Reveal delay={0.08}>
          <div className="mt-10 rounded-lg border border-border bg-surface p-6 md:p-8">
            {/* top bar */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border pb-5">
              <span className="h-2 w-2 shrink-0 rounded-[2px] bg-accent" />
              <span className="font-mono text-[13px] text-foreground">
                cs-final-project.vercel.app
              </span>
              <span className="text-monolabel ml-auto font-mono text-muted">
                overall score 61 / 100
              </span>
              <span className="text-monolabel font-mono text-muted">
                · 6 flags
              </span>
            </div>

            {/* one fully expanded flag */}
            <div className="pt-6">
              <div className="flex items-center gap-2">
                <CategoryTag>components</CategoryTag>
                <span className="text-monolabel font-mono text-muted">
                  high confidence
                </span>
              </div>

              <p className="mt-3 text-[17px] font-semibold text-foreground">
                Uniform rounded-2xl + shadow-lg applied to 8 elements
              </p>

              {/* the one bold animation on the page */}
              <div className="mt-3 max-w-[240px]">
                <ConfidenceBar level="high" value={0.86} animated />
              </div>

              <p className="mt-5 max-w-[680px] text-[15px] leading-relaxed text-foreground">
                When every card on a page shares the same heavy rounding and drop
                shadow, it signals that a template or default component library
                was applied without customization. The uniformity itself is the
                tell — hand-built interfaces vary their elevation and rounding
                based on a component&rsquo;s importance and its place in the
                hierarchy. A settings row and a hero panel almost never warrant
                the same treatment.
              </p>

              <div className="mt-5 flex gap-3 rounded-lg border border-border bg-background p-4">
                <Wrench
                  className="mt-0.5 h-4 w-4 shrink-0 text-accent"
                  strokeWidth={1.75}
                />
                <p className="max-w-[640px] text-[15px] leading-relaxed text-foreground">
                  Pick 2–3 intentional radius values — say 4px for inputs, 8px
                  for cards, 0px for full-bleed hero containers — and assign them
                  by component role. Drop{" "}
                  <span className="font-mono text-[13px] text-muted">
                    shadow-lg
                  </span>{" "}
                  entirely and lean on 1px borders for elevation.
                </p>
              </div>
            </div>

            {/* collapsed flags — imply there is more depth */}
            <div className="mt-8 space-y-4 border-t border-border pt-6">
              {collapsed.map((f) => (
                <div
                  key={f.category}
                  className="flex flex-wrap items-center gap-x-3 gap-y-2"
                >
                  <CategoryTag>{f.category}</CategoryTag>
                  <span className="text-[15px] text-foreground">{f.tell}</span>
                  <div className="ml-auto w-[120px]">
                    <ConfidenceBar level={f.level} value={f.value} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
