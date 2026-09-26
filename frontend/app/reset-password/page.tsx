import type { Metadata } from "next";
import { ResetPasswordForm } from "@/components/recovery-form";
import { RecoveryShell } from "@/components/recovery-shell";

export const metadata: Metadata = {
  title: "Choose a new password - FIG",
  robots: { index: false },
  // Recovery links carry credentials in the URL; never send them on as a Referer.
  referrer: "no-referrer",
};

export default function ResetPasswordPage() {
  return <RecoveryShell><ResetPasswordForm /></RecoveryShell>;
}
