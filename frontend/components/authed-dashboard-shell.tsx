import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { api } from "@/lib/api";
import { ServiceUnavailable } from "@/components/service-unavailable";

// Shared by every route that needs the real dashboard chrome (sidebar +
// topbar) around a signed-in page -- currently /projects/[id]/* and
// /projects/settings. One implementation so the auth gate can't drift
// between them.
export async function AuthedDashboardShell({ children, params }: { children: React.ReactNode; params?: Promise<{ hostname?: string }> }) {
  const hostname = (await params)?.hostname;
  const me = await api.me();
  if (!me.ok) return <ServiceUnavailable />;
  if (!me.data.signed_in) {
    redirect("/signin");
  }
  if (me.data.dev_no_auth) return <ServiceUnavailable message="Live workspaces require authenticated sessions. Disable FIG_DEV_NO_AUTH on the backend." />;
  if (me.data.account.needs_plan) redirect("/choose-plan");
  // The sidebar's project card and badges. A failed fetch leaves them out
  // rather than blocking the page.
  const chrome = hostname ? await api.projectChrome(decodeURIComponent(hostname)) : null;
  return <DashboardShell workspaceName={me.data.account.name} chrome={chrome?.ok ? chrome.data : null}>{children}</DashboardShell>;
}
