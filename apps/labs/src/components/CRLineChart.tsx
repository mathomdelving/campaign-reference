'use client';

import { memo, useMemo, useState, useEffect } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { chartTheme } from "@/lib/chartTheme";
import { formatCompactCurrency } from "@/utils/formatters";

export interface ChartSeriesConfig {
  key: string;
  label: string;
  color: string;
  strokeWidth?: number;
}

export interface ChartDatum {
  quarter: string;
  timestamp: number;  // Unix timestamp for X-axis positioning
  [key: string]: string | number | Record<string, any>;
}

export interface QuarterlyTick {
  label: string;
  timestamp: number;
}

export interface CRLineChartProps {
  data: ChartDatum[];
  series?: ChartSeriesConfig[];
  height?: number;
  showLegend?: boolean;
  yAxisFormatter?: (value: number) => string;
  quarterlyTicks?: QuarterlyTick[]; // Quarterly tick labels with timestamps
}

const DEFAULT_SERIES: ChartSeriesConfig[] = [
  { key: "dem", label: "Democrats", color: chartTheme.series.dem },
  { key: "gop", label: "Republicans", color: chartTheme.series.gop },
  { key: "ind", label: "Independents", color: chartTheme.series.ind },
];

function getLastName(fullName: string): string {
  // Handle format: "LAST, FIRST MIDDLE" or "First Last"
  const parts = fullName.split(",");

  if (parts.length >= 2) {
    // Format is "LAST, FIRST" - take the part before comma
    const lastName = parts[0].trim();
    return properCase(lastName);
  }

  // Format is "First Last" - take the last word
  const words = fullName.trim().split(" ");
  const lastName = words[words.length - 1];
  return properCase(lastName);
}

function properCase(value: string): string {
  // Handle hyphenated names and capitalize each word properly
  return value
    .toLowerCase()
    .split(/(\s+|-)/g) // Split on spaces and hyphens but keep delimiters
    .map((word) => {
      if (word === " " || word === "-") return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join("");
}

function getPartyBadgeColor(party: string | null | undefined): string {
  if (!party) return "#6B7280"; // gray-500
  const normalized = party.toUpperCase();
  if (normalized === "DEM" || normalized === "DEMOCRAT") return "#3B82F6"; // blue-500
  if (normalized === "REP" || normalized === "GOP" || normalized === "REPUBLICAN") return "#EF4444"; // red-500
  return "#6B7280"; // gray-500 for independents/others
}

function normalizePartyLabel(party: string | null | undefined): string {
  if (!party) return "";
  const normalized = party.toUpperCase();
  if (normalized === "DEMOCRAT" || normalized === "DEM") return "DEM";
  if (normalized === "REPUBLICAN" || normalized === "REP" || normalized === "GOP") return "GOP";
  return party; // Return original for independents/others
}

function TooltipContent({
  active,
  label,
  payload,
  chartData,
  seriesConfig,
}: {
  active?: boolean;
  label?: string | number;
  payload?: Array<{ name: string; value: number; color: string }>;
  chartData?: ChartDatum[];
  seriesConfig?: ChartSeriesConfig[];
}) {
  if (!active || !payload || payload.length === 0) return null;

  const sorted = [...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  // If label is a timestamp (number), look up the quarter label from chartData
  let displayLabel = String(label);
  if (typeof label === 'number' && chartData) {
    const datum = chartData.find(d => d.timestamp === label);
    if (datum && datum.quarter) {
      displayLabel = datum.quarter;
    }
  }

  // Look up the current datum to get per-datapoint metadata
  const currentDatum = typeof label === 'number' && chartData
    ? chartData.find(d => d.timestamp === label)
    : null;

  // Create a map from series label to series key for metadata lookup
  const labelToKeyMap = new Map<string, string>();
  seriesConfig?.forEach(config => {
    labelToKeyMap.set(config.label, config.key);
  });

  return (
    <div className="rounded border border-gray-200 bg-white p-3 text-xs shadow-sm">
      <p className="mb-2 font-medium text-[#2B2F36]">{displayLabel}</p>
      <div className="space-y-2">
        {sorted.map((entry) => {
          // Look up metadata for this specific data point
          const seriesKey = labelToKeyMap.get(entry.name);
          const metadataKey = seriesKey ? `${seriesKey}_meta` : null;
          const metadata = (metadataKey && currentDatum && currentDatum[metadataKey]) as
            | { committeeId?: string | null; party?: string | null }
            | undefined;

          return (
            <div key={entry.name} className="space-y-0.5">
              <div className="font-semibold" style={{ color: entry.color }}>
                {entry.name}
              </div>
              {(metadata?.committeeId || metadata?.party) && (
                <div className="flex items-center gap-1.5 text-[10px] text-gray-600">
                  {metadata.committeeId && (
                    <span className="font-mono">{metadata.committeeId}</span>
                  )}
                  {metadata.committeeId && metadata.party && (
                    <span>•</span>
                  )}
                  {metadata.party && (
                    <span
                      className="px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide"
                      style={{
                        backgroundColor: getPartyBadgeColor(metadata.party) + '20',
                        color: getPartyBadgeColor(metadata.party)
                      }}
                    >
                      {normalizePartyLabel(metadata.party)}
                    </span>
                  )}
                </div>
              )}
              <div className="font-mono text-[#2B2F36] font-semibold">
                {formatCompactCurrency(entry.value)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function hasValues(data: ChartDatum[], key: string) {
  return data.some((datum) => {
    const value = datum[key];
    return typeof value === "number" && value !== 0;
  });
}

function CRLineChartComponent({
  data,
  height = 360,
  showLegend = true,
  yAxisFormatter = formatCompactCurrency,
  series = DEFAULT_SERIES,
  quarterlyTicks,
}: CRLineChartProps) {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const resolvedSeries = useMemo(() => {
    return series.filter((item) => hasValues(data, item.key));
  }, [data, series]);

  const activeSeries = useMemo(() => {
    if (resolvedSeries.length > 0) return resolvedSeries;
    return series;
  }, [resolvedSeries, series]);

  // Mobile-optimized Y-axis formatter (remove decimals)
  const mobileYAxisFormatter = useMemo(() => {
    if (!isMobile) return yAxisFormatter;

    return (value: number) => {
      if (!value) return "$0";
      if (Math.abs(value) >= 1_000_000) {
        return `$${Math.round(value / 1_000_000)}M`;
      }
      if (Math.abs(value) >= 1_000) {
        return `$${Math.round(value / 1_000)}K`;
      }
      return `$${Math.round(value)}`;
    };
  }, [isMobile, yAxisFormatter]);

  // Legend formatter: show last names on mobile, full names on desktop
  const legendFormatter = useMemo(() => {
    return (value: string) => {
      const match = activeSeries.find((item) => item.key === value);
      const label = match?.label ?? value;

      // On mobile, extract last name only
      if (isMobile && label) {
        return getLastName(label);
      }

      return label;
    };
  }, [activeSeries, isMobile]);

  // Calculate Y-axis ticks dynamically to exclude the bottom (0) tick on mobile
  const yAxisTicks = useMemo(() => {
    if (!isMobile || data.length === 0) return undefined; // Let recharts auto-calculate for desktop

    // Find max value across all series
    let maxValue = 0;
    data.forEach((datum) => {
      activeSeries.forEach((series) => {
        const value = datum[series.key];
        if (typeof value === "number" && value > maxValue) {
          maxValue = value;
        }
      });
    });

    if (maxValue === 0) return undefined;

    // Generate 5 ticks excluding 0, evenly spaced from the max
    const tickCount = 5;
    const ticks: number[] = [];
    for (let i = 1; i <= tickCount; i++) {
      ticks.push((maxValue * i) / tickCount);
    }

    return ticks;
  }, [isMobile, data, activeSeries]);

  // Create tick formatter for quarterly labels
  const xAxisTickFormatter = useMemo(() => {
    if (!quarterlyTicks) return undefined;

    // Create a map of timestamps to labels
    const tickMap = new Map<number, string>();
    quarterlyTicks.forEach(tick => {
      tickMap.set(tick.timestamp, tick.label);
    });

    return (value: number) => tickMap.get(value) || "";
  }, [quarterlyTicks]);

  // Extract tick timestamps for X-axis
  const xAxisTicks = useMemo(() => {
    return quarterlyTicks?.map(t => t.timestamp);
  }, [quarterlyTicks]);

  return (
    <div className="h-full w-full rounded-2xl border border-rb-border bg-rb-white p-3 sm:p-6">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={isMobile
            ? { top: 16, right: 8, bottom: 12, left: 6 }
            : { top: 16, right: 8, bottom: 12, left: 8 }
          }
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#B0B0B0" opacity={0.4} />
          <XAxis
            type="number"
            dataKey="timestamp"
            domain={['dataMin', 'dataMax']}
            stroke="#2B2F36"
            tickLine={false}
            axisLine={{ stroke: "#E4E4E7" }}
            tick={{
              fill: "#2B2F36",
              fontSize: chartTheme.labelFontSize,
              fontFamily: chartTheme.labelFontFamily,
            }}
            ticks={xAxisTicks}
            tickFormatter={xAxisTickFormatter}
          />
          <YAxis
            stroke="#2B2F36"
            tickLine={false}
            axisLine={{ stroke: "#E4E4E7" }}
            tick={
              isMobile
                ? {
                    fill: "#2B2F36",
                    fontSize: chartTheme.labelFontSize,
                    fontFamily: chartTheme.labelFontFamily,
                    angle: -45,
                    textAnchor: "end",
                  } as any
                : {
                    fill: "#2B2F36",
                    fontSize: chartTheme.labelFontSize,
                    fontFamily: chartTheme.labelFontFamily,
                  }
            }
            tickFormatter={mobileYAxisFormatter}
            width={isMobile ? 50 : 50}
            ticks={yAxisTicks}
            domain={isMobile && yAxisTicks ? [0, "dataMax"] : undefined}
          />
          <Tooltip content={<TooltipContent chartData={data} seriesConfig={activeSeries} />} />
          {showLegend && (
            <Legend
              formatter={legendFormatter}
              verticalAlign="top"
              align="right"
              iconType="plainline"
              wrapperStyle={{
                paddingBottom: 12,
                fontSize: isMobile ? 11 : 12,
                color: "#2B2F36",
              }}
            />
          )}

          {activeSeries.map((config) => (
            <Line
              key={config.key}
              type="linear"
              dataKey={config.key}
              name={config.label}
              stroke={config.color}
              strokeWidth={config.strokeWidth ?? chartTheme.linePrimaryWidth}
              dot={false}
              activeDot={{
                r: 5,
                fill: config.color,
                stroke: "rgba(255,255,255,0.35)",
                strokeWidth: 2,
              }}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export const CRLineChart = memo(CRLineChartComponent);
