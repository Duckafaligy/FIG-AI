"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { Reveal } from "./reveal";

const faqs = [
  {
    q: "Is this an AI detector?",
    a: "No. We don't classify whether a page was 'made by AI.' We check for specific, known design patterns — rounded-2xl on everything, numbered eyebrow labels, default color palettes — that tend to appear when AI tools are used without deliberate design choices. The distinction matters: we're flagging patterns, not making accusations.",
  },
  {
    q: "Do I need to own the site I'm checking?",
    a: "Not for one-off checks. Anyone can paste any public URL and get a scan — it's the same as viewing the page source. Ownership verification (via DNS TXT record or meta tag) is only required if you want to set up recurring daily monitoring on a specific domain.",
  },
  {
    q: "What does it actually check?",
    a: "Six categories: component styling (uniform rounding/shadows), layout structure (centered-section templates), color palette (proximity to known AI defaults), typography hierarchy (flat font sizing), copy patterns (generic headline verbs), and icon usage (overused defaults). All checks are deterministic — no AI model is involved in the detection step.",
  },
  {
    q: "Is my URL or code stored?",
    a: "Scan results are cached per domain (not per user) to avoid redundant scraping. We don't store the full HTML of your page. Cached results expire after 7 days for free-tier checks. Verified-domain monitoring history is retained while your subscription is active.",
  },
  {
    q: "Is this free?",
    a: "The first three checks require no account at all. After that, a free account gets you weekly-refresh scans on any URL. Paid plans start at $9/month and add daily monitoring, on-demand re-checks, and domain verification for your own projects.",
  },
];

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className="section">
      <div className="container-page">
        <Reveal>
          <h2 className="text-section text-foreground">Questions</h2>
        </Reveal>

        <div className="mt-10 max-w-[820px] border-b border-t border-border">
          {faqs.map((f, i) => {
            const isOpen = open === i;
            return (
              <div
                key={f.q}
                className={i > 0 ? "border-t border-border" : undefined}
              >
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between gap-4 py-5 text-left"
                >
                  <span className="text-[18px] font-semibold text-foreground">
                    {f.q}
                  </span>
                  <motion.span
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="shrink-0"
                  >
                    <ChevronDown className="h-5 w-5 text-muted" />
                  </motion.span>
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="text-body max-w-[680px] pb-5 text-muted">
                        {f.a}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
