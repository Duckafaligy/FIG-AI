"use client";
import { useEffect } from "react";

// Feeds the pointer position to CSS (--mx/--my) for the grid aura in neon-dark.css.
export function CursorAura() {
  useEffect(() => {
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    const root = document.documentElement.style;
    let frame = 0, x = 0, y = 0;
    const paint = () => { frame = 0; root.setProperty("--mx", `${x}px`); root.setProperty("--my", `${y}px`); };
    const move = (e: PointerEvent) => { x = e.clientX; y = e.clientY; if (!frame) frame = requestAnimationFrame(paint); };
    const hide = () => { x = y = -9999; if (!frame) frame = requestAnimationFrame(paint); };
    window.addEventListener("pointermove", move, { passive: true });
    document.documentElement.addEventListener("pointerleave", hide);
    return () => {
      window.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", hide);
      cancelAnimationFrame(frame);
    };
  }, []);
  return null;
}
