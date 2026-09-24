import { PublishQueue } from "@/components/publish-queue";

export default async function PublishPage({ params }: { params: Promise<{ hostname: string }> }) {
  const { hostname } = await params;
  return <PublishQueue projectId={hostname} />;
}
