/**
 * Structured data for crawlers and answer engines: one `<script type="application/ld+json">`.
 * The payload is always our own static data, and `<` is escaped so a stray
 * "</script>" in a string can never end the tag early.
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\u003c") }} />;
}

/** A FAQPage block built from the exact questions and answers shown on the page. */
export function faqJsonLd(items: ReadonlyArray<{ question: string; answer: string }>) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };
}
