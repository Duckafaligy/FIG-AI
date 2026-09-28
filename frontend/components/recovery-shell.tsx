import type { ReactNode } from "react";
import { AuthFooter } from "@/components/auth-footer";
import { PublicNav } from "@/components/public-nav";
import styles from "./recovery-shell.module.css";

/** Chrome for the two password-recovery pages: the sign-in header, one centred card. */
export function RecoveryShell({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <div className="auth-simple neon-home">
      <PublicNav />
      <main className={`page-shell ${styles.main}`}>
        <div className={`auth-simple-card recovery-card${wide ? " recovery-card--wide" : ""}`}>{children}</div>
      </main>
      <AuthFooter />
    </div>
  );
}
