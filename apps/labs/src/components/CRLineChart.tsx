'use client';

import { memo, useMemo } from "react";
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
  const resolvedSeries = useMemo(() => {
    return series.filter((item) => hasValues(data, item.key));
  }, [data, series]);

  const activeSeries = useMemo(() => {
    if (resolvedSeries.length > 0) return resolvedSeries;
    return series;
  }, [resolvedSeries, series]);

  return (
    <div className="h-full w-full rounded-2xl border border-rb-border bg-rb-white p-3 sm:p-6">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 16, right: 8, bottom: 12, left: 4 }}
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
            }}
            tickFormatter={yAxisFormatter}
          />
          <Tooltip content={<TooltipContent />} />
          {showLegend && (
            <Legend
              formatter={(value) => {
                const match = activeSeries.find((item) => item.key === value);
                return match?.label ?? value;
              }}
              verticalAlign="top"
              align="right"
              iconType="plainline"
              wrapperStyle={{
                paddingBottom: 12,
                fontSize: 12,
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
