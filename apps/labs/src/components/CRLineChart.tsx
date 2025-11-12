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
  [key: string]: string | number;
}

export interface CRLineChartProps {
  data: ChartDatum[];
  series?: ChartSeriesConfig[];
  height?: number;
  showLegend?: boolean;
  yAxisFormatter?: (value: number) => string;
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

function TooltipContent({
  active,
  label,
  payload,
}: {
  active?: boolean;
  label?: string;
  payload?: Array<{ name: string; value: number; color: string }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const sorted = [...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  return (
    <div className="rounded border border-gray-200 bg-white p-3 text-xs shadow-sm">
      <p className="mb-2 font-medium text-[#2B2F36]">{label}</p>
      <div className="space-y-1">
        {sorted.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between gap-2">
            <span className="font-semibold" style={{ color: entry.color }}>
              {entry.name}
            </span>
            <span className="font-mono text-[#2B2F36]">
              {formatCompactCurrency(entry.value)}
            </span>
          </div>
        ))}
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

  return (
    <div className="h-full w-full rounded-2xl border border-rb-border bg-rb-white p-3 sm:p-6">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={isMobile
            ? { top: 16, right: 8, bottom: 12, left: 12 }
            : { top: 16, right: 8, bottom: 12, left: 8 }
          }
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#B0B0B0" opacity={0.4} />
          <XAxis
            dataKey="quarter"
            stroke="#2B2F36"
            tickLine={false}
            axisLine={{ stroke: "#E4E4E7" }}
            tick={{
              fill: "#2B2F36",
              fontSize: chartTheme.labelFontSize,
              fontFamily: chartTheme.labelFontFamily,
            }}
          />
          <YAxis
            stroke="#2B2F36"
            tickLine={false}
            axisLine={{ stroke: "#E4E4E7" }}
            tick={{
              fill: "#2B2F36",
              fontSize: chartTheme.labelFontSize,
              fontFamily: chartTheme.labelFontFamily,
              angle: isMobile ? 45 : 0,
              textAnchor: isMobile ? "start" : "end",
            }}
            tickFormatter={mobileYAxisFormatter}
            width={isMobile ? 50 : 50}
            ticks={yAxisTicks}
            domain={isMobile && yAxisTicks ? [0, "dataMax"] : undefined}
          />
          <Tooltip content={<TooltipContent />} />
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
