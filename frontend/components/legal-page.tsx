import type { ReactNode } from "react";
import Link from "next/link";
import { PublicNav } from "@/components/public-nav";
import { LAST_UPDATED, OPERATOR, legalIsDraft } from "@/lib/legal";
import { LegalToc } from "./legal-toc";
import styles from "./legal-page.module.css";

export type LegalSection = { id: string; title: string; body: ReactNode };

const RELATED = [
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms of Service" },
  { href: "/refunds", label: "Refunds & cancellation" },
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
  // Left column (title + contents) stays pinned under the nav; only the right column's text scrolls.
  // The page ends with a slim footer inside the text column, so nothing below can push the left column up.
  return (
    <div className="public-page neon-home legal-page">
      <PublicNav />
      <div className={`page-shell ${styles.shell}`}>
        <aside className={styles.side}>
          <header className={styles.head}>
            <span className={styles.kicker}>Legal</span>
            <h1>{title}</h1>
            <p className={styles.updated}>Last updated {LAST_UPDATED}</p>
          </header>
          <nav className={styles.toc} aria-label="On this page">
            <strong>On this page</strong>
            <LegalToc sections={sections.map(({ id, title }) => ({ id, title }))} />
            <div className={styles.related}>
              {RELATED.filter((r) => r.href !== path).map((r) => <Link key={r.href} href={r.href}>{r.label}</Link>)}
            </div>
          </nav>
        </aside>

        <main className={styles.content}>
          {legalIsDraft && (
            <p className={styles.draft} role="note">
              <strong>Draft.</strong> The operator&rsquo;s name and contact details on this page are still to be filled in, so it is not yet a finished, binding document.
            </p>
          )}
          <article className={styles.body}>
            <div className={styles.intro}>{intro}</div>
            {sections.map((s) => (
              <section key={s.id} id={s.id} aria-labelledby={`${s.id}-h`}>
                <h2 id={`${s.id}-h`}>{s.title}</h2>
                {s.body}
              </section>
            ))}
            <div data-legal-end aria-hidden="true" />
          </article>
          <footer className={styles.foot}>
            <span>© {new Date().getFullYear()} FIG. All rights reserved.</span>
            <span><Link href="/">Home</Link><Link href="/pricing">Pricing</Link><a href={`mailto:${OPERATOR.email}`}>Contact</a></span>
          </footer>
        </main>
      </div>
    </div>
  );
}
