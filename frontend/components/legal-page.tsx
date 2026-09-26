import type { ReactNode } from "react";
import Link from "next/link";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { LAST_UPDATED, legalIsDraft } from "@/lib/legal";
import styles from "./legal-page.module.css";

export type LegalSection = { id: string; title: string; body: ReactNode };

const RELATED = [
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms of Service" },
  { href: "/refunds", label: "Refunds & cancellation" },
  { href: "/bot", label: "About FIGBot" },
];

export function LegalTable({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className={styles.tableWrap}>
      <table>
        <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

export function Callout({ children }: { children: ReactNode }) {
  return <div className={styles.callout}>{children}</div>;
}

/**
 * One layout for every legal page, so they read as a set and a change to the
 * chrome happens once. Server component: nothing here needs the browser.
 */
export function LegalPage({ title, intro, sections, path }: { title: string; intro: ReactNode; sections: LegalSection[]; path: string }) {
  return (
    <div className="public-page neon-home">
      <PublicNav />
      <main className={`page-shell ${styles.main}`}>
        <header className={styles.head}>
          <span className={styles.kicker}>Legal</span>
          <h1>{title}</h1>
          <p className={styles.updated}>Last updated {LAST_UPDATED}</p>
        </header>

        {legalIsDraft && (
          <p className={styles.draft} role="note">
            <strong>Draft.</strong> The operator&rsquo;s name and contact details on this page are still to be filled in, so it is not yet a finished, binding document.
          </p>
        )}

        <div className={styles.layout}>
          <nav className={styles.toc} aria-label="On this page">
            <strong>On this page</strong>
            <ol>{sections.map((s) => <li key={s.id}><a href={`#${s.id}`}>{s.title}</a></li>)}</ol>
            <div className={styles.related}>
              {RELATED.filter((r) => r.href !== path).map((r) => <Link key={r.href} href={r.href}>{r.label}</Link>)}
            </div>
          </nav>

          <article className={styles.body}>
            <div className={styles.intro}>{intro}</div>
            {sections.map((s) => (
              <section key={s.id} id={s.id} aria-labelledby={`${s.id}-h`}>
                <h2 id={`${s.id}-h`}>{s.title}</h2>
                {s.body}
              </section>
            ))}
          </article>
        </div>
      </main>
      <Footer />
    </div>
  );
}
