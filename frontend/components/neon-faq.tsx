"use client";

import { useId, useState } from "react";
import { OPERATOR } from "@/lib/legal";
import type { FaqItem } from "./faq";

export function NeonFaq({ title, items }: { title: string; items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(0);
  const id = useId();
  return (
    <section className="nfaq" id="faq">
      <div className="page-shell nfaq-grid">
        <div className="nfaq-intro">
          <h2>{title}</h2>
          <p>Something else on your mind? <a href={`mailto:${OPERATOR.email}`}>Email us</a>.</p>
        </div>
        <div className="nfaq-list">
          {items.map((item, i) => {
            const expanded = open === i;
            return (
              <div className={`nfaq-item${expanded ? " is-open" : ""}`} key={item.question}>
                <h3>
                  <button type="button" aria-expanded={expanded} aria-controls={`${id}-${i}`} onClick={() => setOpen(expanded ? null : i)}>
                    <span>{item.question}</span>
                    <i aria-hidden="true"><b /><b /></i>
                  </button>
                </h3>
                <div className="nfaq-answer" id={`${id}-${i}`} role="region" aria-hidden={!expanded} inert={!expanded}>
                  <div><p>{item.answer}</p></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
