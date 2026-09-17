import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { fetchOverlay } from "@/lib/live";

export default async function Page() {
  const { overlay } = await fetchOverlay("seo");
  return <LiveDashboardPage page="seo" overlay={overlay} />;
}
