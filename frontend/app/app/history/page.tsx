import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { fetchOverlay } from "@/lib/live";

export default async function Page() {
  const { overlay } = await fetchOverlay("history");
  return <LiveDashboardPage page="history" overlay={overlay} />;
}
