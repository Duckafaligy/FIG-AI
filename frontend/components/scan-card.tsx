"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

export type Confidence = "high" | "medium" | "low";

/**
 * Category tag pill — monospace, accent text on a 15%-accent field.
 * The single accent-tinted surface allowed, and deliberately tiny.
 */
export function CategoryTag({ children }: { children: ReactNode }) {
  return (
    <span
      className="text-monolabel inline-flex items-center rounded-md px-2 py-1 font-mono font-medium"
      style={{ background: "rgba(224, 90, 51, 0.15)", color: "var(--accent)" }}
    >
      {children}
    </span>
  );
}

const barColor: Record<Confidence, string> = {
  high: "var(--accent)",
  medium: "var(--amber)",
  low: "var(--text-muted)",
};

/**
 * Thin confidence bar. When `animated`, its width grows from 0 to its
 * final value on scroll-in over 800ms — the one bold moment on the page.
 */
export function ConfidenceBar({
  level,
  value,
  animated = false,
  height = 3,
}: {
  level: Confidence;
  value: number; // 0..1
  animated?: boolean;
  height?: number;
}) {
  const width = `${Math.round(value * 100)}%`;
  return (
    <div
      className="w-full overflow-hidden rounded-full"
      style={{ height, background: "rgba(255, 255, 255, 0.06)" }}
    >
      {animated ? (
        <motion.div
          className="h-full rounded-full"
          style={{ background: barColor[level] }}
          initial={{ width: 0 }}
          whileInView={{ width }}
          viewport={{ once: true, amount: 0.6 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      ) : (
        <div
          className="h-full rounded-full"
          style={{ background: barColor[level], width }}
        />
      )}
    </div>
  );
}

const flags: {
  category: string;
  level: Confidence;
  label: string;
  desc: string;
  value: number;
}[] = [
  {
    category: "components",
    level: "high",
    label: "high confidence",
    desc: "Uniform rounded-2xl + shadow-lg applied to 8 elements",
    value: 0.9,
  },
  {
    category: "layout",
    level: "medium",
    label: "medium confidence",
    desc: "Three centered max-w-4xl sections, identical structure",
    value: 0.58,
  },
  {
    category: "copy",
    level: "low",
    label: "low confidence",
    desc: "Headline verb 'Elevate' paired with a 'Get Started' CTA",
    value: 0.34,
  },
];

/**
 * Compact scan-result mockup used in the hero. This IS the product demo,
 * not decoration — every value is realistic.
 */
export function ScanCard() {
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      {/* header */}
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 shrink-0 rounded-[2px] bg-accent" />
        <span className="text-monolabel font-mono text-foreground">
          cs-final-project.vercel.app
        </span>
        <span className="text-monolabel ml-auto font-mono text-muted">
          6 flags found
        </span>
      </div>

      {/* score */}
      <div className="mt-5 flex items-baseline gap-4">
        <span className="text-[48px] font-semibold leading-none text-accent">
          6
        </span>
        <div>
          <div className="text-sub font-semibold text-foreground">
            Six patterns worth changing
          </div>
          <div className="text-small text-muted">
            2 high confidence, 2 medium, 2 low
          </div>
        </div>
      </div>

      {/* flag rows */}
      <div className="mt-6 space-y-4">
        {flags.map((f) => (
          <div key={f.category}>
            <div className="flex items-center gap-2">
              <CategoryTag>{f.category}</CategoryTag>
              <span className="text-monolabel font-mono text-muted">
                {f.label}
              </span>
            </div>
            <p className="mt-2 text-[15px] text-foreground">{f.desc}</p>
            <div className="mt-2">
              <ConfidenceBar level={f.level} value={f.value} />
            </div>
          </div>
        ))}
      </div>

      {/* footer */}
      <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
        <span className="text-monolabel font-mono text-muted">
          scan complete · 1.4s
        </span>
        <span className="text-monolabel font-mono text-accent">full report</span>
      </div>
    </div>
  );
}
