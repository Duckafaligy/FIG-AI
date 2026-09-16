"use client";

/**
 * The dashboard surfaces, rendered from live workspace data.
 *
 * Same output as `DashboardPage`, with the values overlaid. It stays a client
 * component because `MetricCard` and `DashboardSection` take lucide icon
 * components as props, and a function cannot cross the server/client boundary
 * — so the static page (icons included) is imported here, and only plain JSON
 * arrives from the server as `overlay`.
 *
 * Pass `overlay={null}` and it renders the static preview untouched.
 */

import { applyOverlay, type Overlay } from "@/lib/live";
import { dashboardPages } from "@/lib/dashboard-pages";
import { DashboardHeader, EmptySection, MetricCard } from "./dashboard-shell";

export function LiveDashboardPage({
  page,
  overlay,
}: {
  page: keyof typeof dashboardPages;
  overlay: Overlay | null;
}) {
  const data = applyOverlay(dashboardPages[page], overlay);

  return (
    <div className={`dashboard-page dashboard-page--${data.layout}`}>
      <DashboardHeader
        eyebrow={data.eyebrow}
        title={data.title}
        description={data.description}
        action={data.action}
      />
      <div className={`metric-grid metric-grid--${data.layout}`}>
        {data.metrics.map((metric) => (
          <MetricCard {...metric} key={metric.label} />
        ))}
      </div>
      <div className={`dashboard-grid dashboard-grid--${data.layout}`}>
        {data.sections.map((section) => (
          <EmptySection {...section} key={section.title} />
        ))}
      </div>
    </div>
  );
}
