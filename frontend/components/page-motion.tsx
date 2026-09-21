"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

/** Progressive enhancement: content stays visible without JavaScript or motion. */
export function PageMotion() {
  const pathname = usePathname();
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const animations = new Set<Animation>();
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        if (media.matches) continue;
        const animation = entry.target.animate(
          [{ opacity: .65, transform: "translateY(12px)" }, { opacity: 1, transform: "translateY(0)" }],
          { duration: 420, easing: "cubic-bezier(.2,.72,.2,1)" }
        );
        animations.add(animation);
        animation.onfinish = () => animations.delete(animation);
      }
    }, { threshold: .08 });
    document.querySelectorAll("main > section, .home-section, .home-audience-grid article, .footer-top, .dashboard-heading-row").forEach((element) => observer.observe(element));
    const reduce = () => { if (media.matches) animations.forEach((animation) => animation.cancel()); };
    media.addEventListener("change", reduce);
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        const input = document.querySelector<HTMLInputElement>(".projects-search input, .dashboard-search input");
        if (input) { event.preventDefault(); input.focus(); input.select(); }
      }
    };
    document.addEventListener("keydown", shortcut);
    return () => { observer.disconnect(); animations.forEach((animation) => animation.cancel()); media.removeEventListener("change", reduce); document.removeEventListener("keydown", shortcut); };
  }, [pathname]);
  return null;
}
