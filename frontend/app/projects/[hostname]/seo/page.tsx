import { ProjectSeo } from "@/components/project-seo";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { api } from "@/lib/api";

export default async function Page({ params }: { params: Promise<{ hostname: string }> }) {
  const { hostname } = await params;
  const result = await api.projectSeo(decodeURIComponent(hostname));
  if (!result.ok || !result.data.project) return <ServiceUnavailable message={result.ok ? "This project couldn't be found." : result.error} />;
  return <ProjectSeo data={result.data} />;
}
