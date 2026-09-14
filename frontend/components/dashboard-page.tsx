"use client";

import { dashboardPages } from "@/lib/dashboard-pages";
import { DashboardHeader, EmptySection, MetricCard } from "./dashboard-shell";

export function DashboardPage({ page }: { page: keyof typeof dashboardPages }) {
  const data = dashboardPages[page];
  return (
    <>
      <DashboardHeader eyebrow={data.eyebrow} title={data.title} description={data.description} action={data.action} />
      <div className="metric-grid">{data.metrics.map((metric) => <MetricCard {...metric} key={metric.label} />)}</div>
      <div className="dashboard-grid">
        {data.sections.map((section) => <EmptySection {...section} key={section.title} />)}
      </div>
    </>
  );
}
