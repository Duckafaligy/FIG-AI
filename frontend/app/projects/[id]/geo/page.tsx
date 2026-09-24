import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { fetchOverlay } from "@/lib/live";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { overlay } = await fetchOverlay("geo", id);
  return <LiveDashboardPage page="geo" overlay={overlay} />;
}
