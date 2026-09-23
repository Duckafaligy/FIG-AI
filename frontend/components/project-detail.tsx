"use client";

import Link from "next/link";
import { ArrowRight, Bot, Globe2, MessageSquareText, Search } from "lucide-react";
import { ProjectConnectors } from "@/components/project-connectors";
import { PublishQueue } from "@/components/publish-queue";
import type { ApiOverviewPage } from "@/lib/api";

export function ProjectDetail({ projectId, overview }: { projectId: string; overview: ApiOverviewPage }) {
  const hostname = overview.project?.hostname ?? "This project";
  return (
    <div className="project-detail">
      <header className="dashboard-heading-row">
        <div>
          <span className="dashboard-eyebrow">Projects / {hostname}</span>
          <h1>{hostname}</h1>
          <p>Everything for this one project — its scan results, its connectors, and its pending fixes — in one place.</p>
        </div>
        <Link href="/projects" className="secondary-button">← All projects</Link>
      </header>

      <div className="project-detail-kpis">
        <article><span>Published posts</span><strong>{overview.kpis.published}</strong></article>
        <article><span>In the content queue</span><strong>{overview.kpis.queue}</strong></article>
        <article><span>Answers-layer score</span><strong>{overview.kpis.impact ?? "—"}</strong></article>
      </div>

      <div className="project-detail-links">
        <Link href={`/app?project=${encodeURIComponent(projectId)}`}><Globe2 size={15} />Full dashboard<ArrowRight size={12} /></Link>
        <Link href={`/app/seo?project=${encodeURIComponent(projectId)}`}><Search size={15} />SEO findings<ArrowRight size={12} /></Link>
        <Link href={`/app/geo?project=${encodeURIComponent(projectId)}`}><MessageSquareText size={15} />GEO / AI visibility<ArrowRight size={12} /></Link>
        <Link href={`/app/history?project=${encodeURIComponent(projectId)}`}><Bot size={15} />History<ArrowRight size={12} /></Link>
      </div>

      <section className="project-detail-section">
        <h2>Connectors</h2>
        <ProjectConnectors projectId={projectId} />
      </section>

      <section className="project-detail-section">
        <h2>Publish queue</h2>
        <PublishQueue projectId={projectId} embedded />
      </section>
    </div>
  );
}
