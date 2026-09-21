import { LiveDashboardPage } from "@/components/live-dashboard-page";
import { fetchOverlay } from "@/lib/live";

export default async function Page({ searchParams }: { searchParams: Promise<{ project?: string }> }) {
  const { overlay } = await fetchOverlay("overview", (await searchParams).project ?? "");
  return <LiveDashboardPage page="overview" overlay={overlay} />;
}
