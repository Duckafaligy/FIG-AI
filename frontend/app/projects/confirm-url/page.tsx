import type { Metadata } from "next";
import { ConfirmUrlForm } from "@/components/confirm-url-form";
import { RecoveryShell } from "@/components/recovery-shell";

export const metadata: Metadata = {
  title: "Confirm your site's URL — FIG",
  robots: { index: false },
};

export default function ConfirmUrlPage() {
  return <RecoveryShell><ConfirmUrlForm /></RecoveryShell>;
}
