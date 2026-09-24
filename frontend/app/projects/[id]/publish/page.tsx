import { PublishQueue } from "@/components/publish-queue";

export default async function PublishPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PublishQueue projectId={id} />;
}
