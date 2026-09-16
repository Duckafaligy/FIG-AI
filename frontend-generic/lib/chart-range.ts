export type ChartRange = "1" | "3" | "7" | "30";

export const chartRanges: { value: ChartRange; label: string }[] = [
  { value: "1", label: "Last 1 day" },
  { value: "3", label: "Last 3 days" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" }
];

// Every range filters the same illustrative reporting period, ending May 25.
export function chartSamples(range: ChartRange) {
  if (range === "1") {
    return [0, 4, 8, 12, 16, 20, 23].map((hour) => {
      const label = `${String(hour).padStart(2, "0")}:00`;
      return { label, tooltipLabel: `May 25, 2025 · ${label}`, sampleIndex: 28 + hour / 23 };
    });
  }

  const count = Number(range);
  return Array.from({ length: count }, (_, index) => {
    const sampleIndex = 30 - count + index;
    const date = new Date(Date.UTC(2025, 3, 26 + sampleIndex));
    const label = new Intl.DateTimeFormat("en-CA", { month: "short", day: "numeric", timeZone: "UTC" }).format(date);
    return { label, tooltipLabel: `${label}, 2025`, sampleIndex };
  });
}

export function chartHitArea(index: number, count: number, width = 700) {
  const spacing = width / Math.max(1, count - 1);
  const left = Math.max(0, index * spacing - spacing / 2);
  const right = Math.min(width, index * spacing + spacing / 2);
  return { x: left, width: right - left };
}
