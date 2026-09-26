"use client";
import { useEffect, useRef, useState } from "react";

/** "On this page" list that marks the section being read. */
export function LegalToc({ sections, className }: { sections: { id: string; title: string }[]; className?: string }) {
  const [active, setActive] = useState(sections[0]?.id);
  const list = useRef<HTMLOListElement>(null);

  // If the pinned column is taller than the screen, keep the highlighted item inside its visible part
  // (moves only that column, never the page).
  useEffect(() => {
    const link = list.current?.querySelector<HTMLElement>('a[aria-current="location"]');
    const box = link?.closest("aside");
    if (!link || !box || box.scrollHeight <= box.clientHeight) return;
    const l = link.getBoundingClientRect(), b = box.getBoundingClientRect();
    if (l.top < b.top + 24 || l.bottom > b.bottom - 24) box.scrollTo({ top: box.scrollTop + (l.top - b.top) - b.height / 2, behavior: "smooth" });
  }, [active]);

  useEffect(() => {
    const els = sections.map(s => document.getElementById(s.id)).filter((e): e is HTMLElement => !!e);
    const end = document.querySelector("[data-legal-end]");
    const pick = () => {
      // Only when the end of the text is actually on screen does the last (often short) section win;
      // otherwise it's the last section whose heading has passed under the nav.
      if (end && end.getBoundingClientRect().top <= window.innerHeight) { setActive(els[els.length - 1]?.id); return; }
      let current = els[0]?.id;
      const line = window.innerHeight * 0.35;
      for (const el of els) if (el.getBoundingClientRect().top <= line) current = el.id;
      setActive(current);
    };
    let frame = 0;
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(pick); };
    const io = new IntersectionObserver(schedule, { threshold: [0, 0.25, 0.5, 0.75, 1] });
    els.forEach(el => io.observe(el));
    if (end) io.observe(end);
    window.addEventListener("scrollend", schedule);
    pick();
    return () => { io.disconnect(); cancelAnimationFrame(frame); window.removeEventListener("scrollend", schedule); };
  }, [sections]);

  return (
    <ol ref={list} className={className}>
      {sections.map(s => (
        <li key={s.id}>
          <a href={`#${s.id}`} aria-current={active === s.id ? "location" : undefined} onClick={() => setActive(s.id)}>{s.title}</a>
        </li>
      ))}
    </ol>
  );
}
