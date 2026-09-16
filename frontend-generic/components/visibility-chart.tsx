"use client";

import { useState } from "react";
import { chartHitArea, chartSamples, type ChartRange } from "@/lib/chart-range";

const months = [
  { label: "Jan", values: [18, 14, 10] },
  { label: "Feb", values: [29, 23, 18] },
  { label: "Mar", values: [42, 38, 27] },
  { label: "Apr", values: [58, 49, 36] },
  { label: "May", values: [67, 59, 42] },
  { label: "Jun", values: [78, 68, 56] }
];
const platforms = ["ChatGPT", "Google AI", "Perplexity"];

export function VisibilityChart() {
  const [selected, setSelected] = useState<number | null>(null);
  return (
    <div className="visibility-bar-chart">
      <div className="visibility-bar-legend">{platforms.map((name, index) => <span key={name}><i className={`visibility-series-${index}`} />{name}</span>)}</div>
      <div className="visibility-bar-plot">
        <div className="visibility-bar-ticks" aria-hidden="true"><span>100%</span><span>75%</span><span>50%</span><span>25%</span><span>0%</span></div>
        <div className="visibility-bar-groups">
          {months.map((month, index) => (
            <button key={month.label} className={`visibility-bar-group${selected === index ? " is-selected" : ""}`} type="button" aria-label={`${month.label}: ${platforms.map((name, i) => `${name} ${month.values[i]}%`).join(", ")}`} onMouseEnter={() => setSelected(index)} onMouseLeave={() => setSelected(null)} onFocus={() => setSelected(index)} onBlur={() => setSelected(null)} onClick={() => setSelected(index)}>
              <span className="visibility-bars" aria-hidden="true">{month.values.map((value, i) => <i key={i} className={`visibility-series-${i}`} style={{ height: `${value}%` }} />)}</span>
              <span className="visibility-month">{month.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="visibility-chart-readout" aria-live="polite">{selected === null ? "Answer inclusion rate · hover or select a month" : `${months[selected].label} · ${platforms.map((name, i) => `${name} ${months[selected].values[i]}%`).join(" · ")}`}</div>
    </div>
  );
}

const workspaceSeries = [
  { label: "Organic traffic", color: "#287bf1", end: 342 },
  { label: "Impressions", color: "#7551f8", end: 415 },
  { label: "Published posts", color: "#18b47c", end: 275 }
];

export function WorkspaceTrendChart({ range = "30" }: { range?: ChartRange }) {
  const [activePoint, setActivePoint] = useState<{ range: ChartRange; index: number } | null>(null);
  const samples = chartSamples(range);
  const pointCount = samples.length;
  const active = activePoint?.range === range && activePoint.index < pointCount ? activePoint.index : null;
  const setActive = (index: number | null) => setActivePoint(index === null ? null : { range, index });
  const points = workspaceSeries.map(series => samples.map(({ sampleIndex }) => Math.round(100 + (series.end - 100) * sampleIndex / 29 + Math.sin(sampleIndex * 1.2) * 10)));
  const x = (index: number) => index / Math.max(1, pointCount - 1) * 700;
  const y = (value: number) => 220 - value / 500 * 220;
  return <div className="workspace-trend">
    <div className="workspace-trend-legend">{workspaceSeries.map(series => <span key={series.label}><i style={{ background: series.color }} />{series.label}</span>)}<small>Growth index · Apr 26 = 100{range === "1" ? " · May 25 hourly" : ""}</small></div>
    <div className="workspace-trend-grid"><div className="workspace-trend-scale">{[500, 400, 300, 200, 100, 0].map(value => <span key={value}>{value}</span>)}</div><div className="workspace-trend-plot">
      <svg viewBox="0 0 700 220" preserveAspectRatio="none" role="group" aria-label="Illustrative indexed growth of traffic, impressions, and published posts">
        {[0, 100, 200, 300, 400, 500].map(value => <line key={value} x1="0" x2="700" y1={y(value)} y2={y(value)} stroke="#e9eef7" />)}
        {workspaceSeries.map((series, seriesIndex) => <g key={series.label}><polyline points={points[seriesIndex].map((value, index) => `${x(index)},${y(value)}`).join(" ")} fill="none" stroke={series.color} strokeWidth="2.3" vectorEffect="non-scaling-stroke" /></g>)}
        {points[0].map((_, index) => <g key={index} tabIndex={0} role="button" aria-label={`${samples[index].tooltipLabel}: ${workspaceSeries.map((series, seriesIndex) => `${series.label} ${points[seriesIndex][index]}`).join(", ")}`} onMouseEnter={() => setActive(index)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(index)} onBlur={() => setActive(null)} onKeyDown={(event) => { if (event.key === "Escape") setActive(null); }}><rect {...chartHitArea(index, pointCount)} y="0" height="220" fill="transparent" />{active === index && <line x1={x(index)} x2={x(index)} y1="0" y2="220" stroke="#a5aed2" strokeDasharray="4 4" />}</g>)}
      </svg>
      {workspaceSeries.flatMap((series, seriesIndex) => points[seriesIndex].map((value, index) => <span key={`${series.label}-${index}`} className="workspace-trend-dot" aria-hidden="true" style={{ left: `${x(index) / 700 * 100}%`, top: `${y(value) / 220 * 100}%`, background: series.color }} />))}
      {active !== null && <div className="workspace-trend-tooltip" style={{ left: `${Math.min(65, active / Math.max(1, pointCount - 1) * 85)}%` }}><strong>{samples[active].tooltipLabel}</strong>{workspaceSeries.map((series, index) => <span key={series.label}><i style={{ background: series.color }} />{series.label}<b>{points[index][active]}</b></span>)}</div>}
    </div></div>
    <div className="workspace-trend-dates"><span>{samples[0].label}</span><span>{samples[Math.floor((pointCount - 1) / 2)].label}</span><span>{samples[pointCount - 1].label}</span></div>
  </div>;
}
