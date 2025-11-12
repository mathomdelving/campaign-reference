export type PartySeriesKey = "dem" | "gop" | "ind" | "neutral";

export const chartTheme = {
  bg: "#0E1117",
  gridColor: "#B0B0B0",
  axisColor: "#2B2F36",
  annotationColor: "#707C91",
  labelFontFamily: "Inter, system-ui, sans-serif",
  labelFontSize: 12,
  linePrimaryWidth: 2.5,
  lineSecondaryWidth: 1.5,
  areaOpacity: 0.08,
  hoverShadow: "drop-shadow(0 0 18px rgba(255, 255, 255, 0.18))",
  series: {
    dem: "#5B8AEF",
    gop: "#E06A6A",
    ind: "#F4B400",
    neutral: "#7F8FA4",
    up: "#21C36F",
    down: "#E94C49",
  } satisfies Record<string, string>,
} as const;

export type ChartTheme = typeof chartTheme;

// Distinct color palette for multi-entity charts (avoiding partisan blue/red)
export const CHART_COLOR_PALETTE = [
  '#10B981', // Emerald green
  '#F59E0B', // Amber/gold
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#EC4899', // Pink (magenta, not red)
  '#84CC16', // Lime green
  '#F97316', // Orange
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#A855F7', // Violet
] as const;

/**
 * Get a color from the palette based on index (cycles through palette)
 */
export function getChartColor(index: number): string {
  return CHART_COLOR_PALETTE[index % CHART_COLOR_PALETTE.length];
}
