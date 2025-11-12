'use client';

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";
import { formatCompactCurrency } from "@/utils/formatters";

const METRIC_CONFIG = {
  totalRaised: { key: "totalReceipts", label: "Total Raised", color: "#5B8AEF" },
  totalDisbursed: { key: "totalDisbursements", label: "Total Spent", color: "#E06A6A" },
  cashOnHand: { key: "cashOnHand", label: "Cash on Hand", color: "#21C36F" },
} as const;

type MetricKey = keyof typeof METRIC_CONFIG;

interface RaceChartProps {
  data: LeaderboardCandidate[];
  metrics: MetricToggles;
}

export function RaceChart({ data, metrics }: RaceChartProps) {
  const chartData = useMemo(() => {
    // Determine which metrics to include in sorting
    const visibleMetrics = (Object.keys(metrics) as MetricKey[]).filter(
      (metric) => metrics[metric]
    );

    // Priority order for sorting: totalRaised > totalDisbursed > cashOnHand
    const metricPriority: MetricKey[] = ['totalRaised', 'totalDisbursed', 'cashOnHand'];

    // Get the highest priority metric from selected metrics
    const getSortMetric = (): MetricKey => {
      if (visibleMetrics.length === 0) {
        return 'totalRaised'; // Default
      }

      // Find the highest priority metric that is selected
      for (const metric of metricPriority) {
        if (visibleMetrics.includes(metric)) {
          return metric;
        }
      }

      return visibleMetrics[0]; // Fallback
    };

    const sortMetric = getSortMetric();
    const sortKey = METRIC_CONFIG[sortMetric].key as keyof LeaderboardCandidate;

    const sorted = [...data]
      .sort((a, b) => {
        const aValue = (a[sortKey] as number) ?? 0;
        const bValue = (b[sortKey] as number) ?? 0;
        return bValue - aValue;
      })
      .slice(0, 20);

    return sorted.map((candidate) => ({
      name: candidate.name,
      shortName: getLastName(candidate.name),
      totalReceipts: candidate.totalReceipts ?? 0,
      totalDisbursements: candidate.totalDisbursements ?? 0,
      cashOnHand: candidate.cashOnHand ?? 0,
    }));
  }, [data, metrics]);

  const visibleMetrics = (Object.keys(metrics) as MetricKey[]).filter(
    (metric) => metrics[metric]
  );

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl border border-rb-border bg-rb-white p-12 text-center text-sm text-rb-grey shadow-sm">
        Chart will appear once data loads.
      </div>
    );
  }

  return (
    <div className="h-[540px] w-full rounded-2xl border border-rb-border bg-rb-white p-6 shadow-sm">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 24, right: 32, bottom: 80, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#B0B0B0" opacity={0.4} />
          <XAxis
            dataKey="shortName"
            axisLine={{ stroke: "#E4E4E7" }}
            tickLine={false}
            tick={{ fill: "#2B2F36", fontSize: 12 }}
            interval={0}
            height={70}
            angle={45}
            textAnchor="start"
          />
          <YAxis
            tickFormatter={(value) => formatCompactCurrency(value)}
            axisLine={{ stroke: "#E4E4E7" }}
            tickLine={false}
            tick={{ fill: "#2B2F36", fontSize: 12 }}
          />
          <Tooltip
            cursor={{ fill: "rgba(20, 40, 85, 0.08)" }}
            contentStyle={{
              backgroundColor: "#FFFFFF",
              border: "1px solid #E5E7EB",
              borderRadius: 12,
              color: "#2B2F36",
              boxShadow: "0 10px 30px rgba(20,40,85,0.1)",
            }}
            labelStyle={{ color: "#142855", fontWeight: 600 }}
            labelFormatter={(label: string) => {
              // Find the full name from chartData
              const candidate = chartData.find(c => c.shortName === label);
              return formatFullName(candidate?.name ?? label);
            }}
            formatter={(value: number, name: string) => {
              const metricEntry = Object.values(METRIC_CONFIG).find(
                (entry) => entry.key === name
              );
              return [formatCompactCurrency(value), metricEntry?.label ?? name];
            }}
          />
          <Legend
            verticalAlign="top"
            wrapperStyle={{ color: "#2B2F36", paddingBottom: 12 }}
          />
          {visibleMetrics.map((metric) => {
            const { key, label, color } = METRIC_CONFIG[metric];
            return (
              <Bar
                key={metric}
                dataKey={key}
                name={label}
                fill={color}
                radius={[6, 6, 0, 0]}
              />
            );
          })}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function formatFullName(name: string) {
  const parts = name.split(",");

  // If there's a comma, format is "LAST, FIRST MIDDLE"
  if (parts.length >= 2) {
    const lastName = properCase(parts[0].trim());
    const firstMiddle = parts[1].trim().split(" ");
    const firstName = properCase(firstMiddle[0] || "");

    // Get middle initial if exists
    const middlePart = firstMiddle.slice(1).join(" ");
    const middleInitial = middlePart ? ` ${properCase(middlePart.charAt(0))}.` : "";

    return `${firstName}${middleInitial} ${lastName}`;
  }

  // If no comma, assume already formatted
  return properCase(name);
}

function getLastName(name: string) {
  const parts = name.split(",");

  // If there's a comma, the last name is before it (format: "LAST, FIRST")
  if (parts.length >= 2) {
    const lastName = parts[0].trim();
    return properCase(lastName);
  }

  // If no comma, assume format is "First Last" and take the last word
  const words = name.trim().split(" ");
  const lastName = words[words.length - 1];
  return properCase(lastName);
}

function properCase(value: string) {
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
