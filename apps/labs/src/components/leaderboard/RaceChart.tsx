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
    const sorted = [...data]
      .sort((a, b) => (b.totalReceipts ?? 0) - (a.totalReceipts ?? 0))
      .slice(0, 20);

    return sorted.map((candidate) => ({
      name: candidate.name,
      shortName: abbreviateName(candidate.name),
      totalReceipts: candidate.totalReceipts ?? 0,
      totalDisbursements: candidate.totalDisbursements ?? 0,
      cashOnHand: candidate.cashOnHand ?? 0,
    }));
  }, [data]);

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

function abbreviateName(name: string) {
  const parts = name.split(",");
  if (parts.length < 2) return name;
  const lastName = parts[0].trim();
  const firstPart = parts[1].trim().split(" ")[0];
  return `${firstPart.charAt(0)}. ${capitalize(lastName.toLowerCase())}`;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
