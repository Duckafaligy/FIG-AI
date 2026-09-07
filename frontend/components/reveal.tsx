"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * Global scroll entrance: opacity 0 -> 1, translateY 12px -> 0, once.
 * Intentionally subtle (12px, not 30px+). Stagger siblings by passing
 * an incremental `delay` (0.08 per sibling).
 */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1], delay }}
    >
      {children}
    </motion.div>
  );
}
