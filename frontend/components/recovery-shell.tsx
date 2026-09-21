import type { ReactNode } from "react";
import Link from "next/link";
import { Brand } from "@/components/brand";
import styles from "./recovery-shell.module.css";

/** Chrome for the two password-recovery pages: the sign-in header, one centred card. */
export function RecoveryShell({ children }: { children: ReactNode }) {
  return (
    <div className="auth-page">
      <header className="auth-nav page-shell">
        <Brand />
        <nav aria-label="Account navigation">
          <Link href="/signin">Sign in</Link>
          <Link className="button button--small" href="/signup">Sign up</Link>
        </nav>
      </header>
      <main className={`page-shell ${styles.main}`}>
        <div className="auth-card">{children}</div>
      </main>
    </div>
  );
}
