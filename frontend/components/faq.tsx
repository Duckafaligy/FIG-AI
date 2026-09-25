"use client";

import { ChevronDown } from "lucide-react";
import { useId, useState } from "react";

export type FaqItem = { question: string; answer: string };

export function Faq({ items, columns = false }: { items: FaqItem[]; columns?: boolean }) {
  const [open, setOpen] = useState<number | null>(null);
  const id = useId();

  return (
    <div className={`faq-list ${columns ? "faq-list--columns" : ""}`}>
      {items.map((item, index) => {
        const expanded = open === index;
        const answerId = `${id}-answer-${index}`;
        return (
          <article className={`faq-item ${expanded ? "is-open" : ""}`} key={item.question}>
            <button className="faq-question" onClick={() => setOpen(expanded ? null : index)} aria-expanded={expanded} aria-controls={answerId}>
              <span>{item.question}</span><ChevronDown className="faq-chevron" size={18} aria-hidden="true" />
            </button>
            <div className="faq-answer" id={answerId} aria-hidden={!expanded}><p>{item.answer}</p></div>
          </article>
        );
      })}
    </div>
  );
}
