import { Reveal } from "./reveal";

// Same card structure across all six, but the content is deliberately uneven —
// varied description lengths and example specificity, so it never reads
// copy-pasted.
const items = [
  {
    category: "components",
    title: "Uniform rounding + shadow applied broadly",
    example: "rounded-2xl + shadow-lg on 8 of 10 cards",
  },
  {
    category: "layout",
    title: "Centered max-w-4xl sections with no layout variation",
    example:
      "Three consecutive centered sections with an identical column-of-cards structure",
  },
  {
    category: "color",
    title: "Palette within distance threshold of known AI defaults",
    example: "#6D28D9 is within 18 units of a known default violet",
  },
  {
    category: "typography",
    title: "Flat type hierarchy with minimal size differentiation",
    example: "Only one text-size class used across the entire page",
  },
  {
    category: "copy",
    title: "Generic headline verbs and filler CTA text",
    example: "Headline contains 'Elevate your' and the CTA says 'Get Started'",
  },
  {
    category: "icons",
    title: "Overused icon names from the default lucide set",
    example: "Sparkles, ArrowRight, Zap all imported from lucide-react",
  },
];

export function WhatItCatches() {
  return (
    <section id="what-it-catches" className="section scroll-mt-24">
      <div className="container-page">
        <Reveal>
          <h2 className="text-section text-foreground">What it catches</h2>
        </Reveal>
        <Reveal delay={0.06}>
          <p className="text-body mt-4 max-w-[640px] text-muted">
            Six categories of detectable pattern, checked deterministically
            before any model is called.
          </p>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((it, i) => (
            <Reveal key={it.category} delay={(i % 3) * 0.08}>
              <div className="h-full rounded-lg border border-border bg-surface p-6">
                <span className="font-mono text-[13px] text-accent">
                  {it.category}
                </span>
                <p className="text-body mt-3 font-semibold text-foreground">
                  {it.title}
                </p>
                <p className="mt-3 text-[14px] leading-relaxed text-muted">
                  {it.example}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
