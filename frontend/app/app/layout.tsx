import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { api } from "@/lib/api";
import { ServiceUnavailable } from "@/components/service-unavailable";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const me = await api.me();
  if (!me.ok) return <ServiceUnavailable />;
  if (!me.data.signed_in) {
    redirect("/signin");
  }
  if (me.data.dev_no_auth) return <ServiceUnavailable message="Live workspaces require authenticated sessions. Disable FIG_DEV_NO_AUTH on the backend." />;
  return <DashboardShell workspaceName={me.data.account.name}>{children}</DashboardShell>;
}
