import { ProjectAnalytics } from "@/components/project-analytics";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { api } from "@/lib/api";

export default async function Page({ params }: { params: Promise<{ hostname: string }> }) {
  const { hostname } = await params;
  const result = await api.analytics(hostname);
  if (!result.ok) return <ServiceUnavailable />;
  return <ProjectAnalytics data={result.data} />;
}
