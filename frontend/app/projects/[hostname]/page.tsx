import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { fetchOverlay } from "@/lib/live";

export default async function Page({ params }: { params: Promise<{ hostname: string }> }) {
  const { hostname } = await params;
  const { overlay } = await fetchOverlay("overview", hostname);
  return <LiveDashboardPage page="overview" overlay={overlay} />;
}
