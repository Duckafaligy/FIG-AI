import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/recovery-form";
import { RecoveryShell } from "@/components/recovery-shell";

export const metadata: Metadata = {
  title: "Forgot your password? — FIG",
  robots: { index: false },
};

export default function ForgotPasswordPage() {
  return <RecoveryShell><ForgotPasswordForm /></RecoveryShell>;
}
