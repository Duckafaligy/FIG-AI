import type { Metadata } from "next";
import { RecoveryShell } from "@/components/recovery-shell";
import { RepoPicker } from "@/components/repo-picker";

export const metadata: Metadata = {
  title: "Import a repository - FIG",
  robots: { index: false },
};

export default function PickRepoPage() {
  return <RecoveryShell wide><RepoPicker /></RecoveryShell>;
}
