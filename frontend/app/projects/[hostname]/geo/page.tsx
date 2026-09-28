import { ProjectGeo } from "@/components/project-geo";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { api } from "@/lib/api";

export default async function Page({ params }: { params: Promise<{ hostname: string }> }) {
  const { hostname } = await params;
  const result = await api.projectGeo(decodeURIComponent(hostname));
  if (!result.ok || !result.data.project) return <ServiceUnavailable message={result.ok ? "This project couldn't be found." : result.error} />;
  return <ProjectGeo data={result.data} />;
}
