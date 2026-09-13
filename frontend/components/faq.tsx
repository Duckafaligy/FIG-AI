"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

export type FaqItem = { question: string; answer: string };

export function Faq({ items }: { items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="faq-list">
      {items.map((item, index) => (
        <div className={`faq-item ${open === index ? "is-open" : ""}`} key={item.question}>
          <button onClick={() => setOpen(open === index ? null : index)} aria-expanded={open === index}>
            {item.question}<ChevronDown size={18} />
          </button>
          <div className="faq-answer"><p>{item.answer}</p></div>
        </div>
      ))}
    </div>
  );
}
