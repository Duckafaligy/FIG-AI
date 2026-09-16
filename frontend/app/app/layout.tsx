import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { api } from "@/lib/api";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const me = await api.me();
  // Only gate when the backend actually answered "not signed in" — if it's
  // unreachable (e.g. this deploy has no backend behind it yet), fall back
  // to the static preview instead of locking every visitor out.
  if (me.ok && !me.data.signed_in && !me.data.dev_no_auth) {
    redirect("/signin");
  }
  return <DashboardShell>{children}</DashboardShell>;
}
