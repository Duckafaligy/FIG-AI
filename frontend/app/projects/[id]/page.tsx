import { api } from "@/lib/api";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { ProjectDetail } from "@/components/project-detail";

export default async function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await api.overview(id);
  if (!result.ok) {
    return <ServiceUnavailable message={result.status === 404 ? "This project doesn't exist, or isn't yours." : result.error} />;
  }
  return <ProjectDetail projectId={id} overview={result.data} />;
}
