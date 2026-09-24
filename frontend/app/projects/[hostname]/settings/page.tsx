"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ProjectConnectors } from "@/components/project-connectors";
import { AnalyticsPropertyPicker } from "@/components/analytics-property-picker";
import { ServiceUnavailable } from "@/components/service-unavailable";
import { api, type ApiProjectSettingsPage } from "@/lib/api";

export default function ProjectSettingsPage() {
  const { hostname } = useParams<{ hostname: string }>();
  const [live, setLive] = useState<ApiProjectSettingsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const load = useCallback(() => api.projectSettings(hostname).then((result) => {
    if (result.ok) { setLive(result.data); setLoadError(""); }
    else setLoadError(result.error);
    setLoading(false);
  }), [hostname]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  if (loading) return <p role="status">Loading settings…</p>;
  if (!live) return <ServiceUnavailable message={loadError} />;

  if (!live.project) {
    return <>
      <div className="dashboard-heading-row">
        <div><span className="dashboard-eyebrow">Settings</span><h1>Project settings</h1><p>Connect a project's CMS, repository, and analytics.</p></div>
      </div>
      <section className="settings-surface settings-integration-empty">
        <strong>Add a project to connect a platform</strong>
        <p>CMS and analytics connections belong to a project. Create or select one first.</p>
        <Link href="/projects" className="settings-row-action">Go to projects</Link>
      </section>
    </>;
  }

  return <>
    <div className="dashboard-heading-row">
      <div><span className="dashboard-eyebrow">Settings</span><h1>{live.project.hostname}</h1><p>Connect this project's CMS, repository, and analytics. Workspace-wide settings (billing, team, profile) live off the all-projects screen.</p></div>
    </div>
    {loadError && <p className="form-message" role="alert">{loadError}</p>}
    <ProjectConnectors projectId={live.project.id} apis={live.apis} onChanged={load} />
    <AnalyticsPropertyPicker key={live.project.id} projectId={live.project.id} />
  </>;
}
