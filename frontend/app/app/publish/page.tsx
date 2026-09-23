import { PublishQueue } from "@/components/publish-queue";

export default async function PublishPage({ searchParams }: { searchParams: Promise<{ project?: string }> }) {
  const { project } = await searchParams;
  return <PublishQueue projectId={project} />;
}
