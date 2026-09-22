import type { ReactNode } from "react";
import { PublicNav } from "@/components/public-nav";
import styles from "./recovery-shell.module.css";

/** Chrome for the two password-recovery pages: the sign-in header, one centred card. */
export function RecoveryShell({ children }: { children: ReactNode }) {
  return (
    <div className="auth-page">
      <PublicNav />
      <main className={`page-shell ${styles.main}`}>
        <div className="auth-card">{children}</div>
      </main>
    </div>
  );
}
