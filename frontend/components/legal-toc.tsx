"use client";
import { useEffect, useState } from "react";

/** "On this page" list that marks the section being read. */
export function LegalToc({ sections, className }: { sections: { id: string; title: string }[]; className?: string }) {
  const [active, setActive] = useState(sections[0]?.id);

  useEffect(() => {
    const els = sections.map(s => document.getElementById(s.id)).filter((e): e is HTMLElement => !!e);
    const pick = () => {
      // At the very bottom the last (often short) section can't reach the top, so it wins outright.
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) { setActive(els[els.length - 1]?.id); return; }
      let current = els[0]?.id;
      for (const el of els) if (el.getBoundingClientRect().top <= 140) current = el.id;
      setActive(current);
    };
    // Measured a frame later: after a jump (End key), scroll position settles after the observer fires.
    let frame = 0;
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(pick); };
    const io = new IntersectionObserver(schedule, { threshold: [0, 0.25, 0.5, 0.75, 1] });
    els.forEach(el => io.observe(el));
    // Reaching the bottom rarely changes a section's visibility, but the footer does come into view.
    const footer = document.querySelector("footer");
    if (footer) io.observe(footer);
    // A smooth jump (End key) can finish after the observer's last callback; scrollend fires once when it settles.
    window.addEventListener("scrollend", schedule);
    pick();
    return () => { io.disconnect(); cancelAnimationFrame(frame); window.removeEventListener("scrollend", schedule); };
  }, [sections]);

  return (
    <ol className={className}>
      {sections.map(s => (
        <li key={s.id}>
          <a href={`#${s.id}`} aria-current={active === s.id ? "location" : undefined} onClick={() => setActive(s.id)}>{s.title}</a>
        </li>
      ))}
    </ol>
  );
}
