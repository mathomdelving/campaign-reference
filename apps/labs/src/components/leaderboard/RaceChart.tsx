'use client';

import { useMemo, useState, useEffect } from "react";
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
import { formatCompactCurrency, formatCurrency } from "@/utils/formatters";

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

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; dataKey: string; payload: any }>;
  label?: string;
  chartData: any[];
}

function CustomTooltip({ active, payload, label, chartData }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0 || !label) return null;

  // Find the candidate from chartData using the label (shortName)
  const candidate = chartData.find((c) => c.shortName === label);
  if (!candidate) return null;

  // Get total value across all metrics shown
  const totalValue = payload.reduce((sum, entry) => sum + (entry.value ?? 0), 0);

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E5E7EB',
        borderRadius: '12px',
        boxShadow: '0 10px 30px rgba(20,40,85,0.1)',
        padding: '12px 16px',
        minWidth: '220px',
      }}
    >
      <div style={{ fontWeight: 600, color: '#111827', marginBottom: '4px' }}>
        {formatFullName(candidate.name)}
      </div>
      <div
        style={{
          fontSize: '12px',
          color: '#9CA3AF',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '8px',
        }}
      >
        <span>{candidate.candidate_id}</span>
        <span>•</span>
        <span style={{ color: getPartyColor(candidate.party), fontWeight: 500 }}>
          {formatPartyLabel(candidate.party)}
        </span>
        <span>•</span>
        <span>{formatDistrictLabel(candidate.office, candidate.state, candidate.district)}</span>
      </div>
      <div style={{ fontSize: '13px', color: '#111827' }}>
        {payload.map((entry, index) => {
          const metricConfig = Object.values(METRIC_CONFIG).find(
            (config) => config.key === entry.dataKey
          );
          return (
            <div key={index} style={{ marginBottom: index < payload.length - 1 ? '4px' : 0 }}>
              <strong>{metricConfig?.label}: </strong>
              {formatCurrency(entry.value)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatPartyLabel(party?: string | null): string {
  if (!party) return "N/A";
  const normalized = party.toLowerCase();
  if (normalized.includes("dem")) return "DEM";
  if (normalized.includes("rep")) return "GOP";
  if (normalized.includes("ind")) return "IND";
  return party;
}

function getPartyColor(party?: string | null): string {
  const normalized = (party ?? "").toUpperCase();
  if (normalized.includes("DEM")) return "#2563EB"; // blue-600
  if (normalized.includes("REP")) return "#DC2626"; // red-600
  return "#CA8A04"; // yellow-600
}

function formatDistrictLabel(office?: string | null, state?: string | null, district?: string | null): string {
  if (office === "H") {
    return `${state}-${district}`;
  }
  if (office === "S") {
    return `${state}-SEN`;
  }
  return state || "—";
}

export function RaceChart({ data, metrics }: RaceChartProps) {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

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

    // Show 10 candidates on mobile, 20 on desktop
    const limit = isMobile ? 10 : 20;

    const sorted = [...data]
      .sort((a, b) => {
        const aValue = (a[sortKey] as number) ?? 0;
        const bValue = (b[sortKey] as number) ?? 0;
        return bValue - aValue;
      })
      .slice(0, limit);

    return sorted.map((candidate) => ({
      name: candidate.name,
      shortName: getLastName(candidate.name),
      totalReceipts: candidate.totalReceipts ?? 0,
      totalDisbursements: candidate.totalDisbursements ?? 0,
      cashOnHand: candidate.cashOnHand ?? 0,
      candidate_id: candidate.candidate_id,
      party: candidate.party,
      office: candidate.office,
      state: candidate.state,
      district: candidate.district,
    }));
  }, [data, metrics, isMobile]);

  const visibleMetrics = (Object.keys(metrics) as MetricKey[]).filter(
    (metric) => metrics[metric]
  );

  // Calculate Y-axis ticks based on max value
  const yAxisTicks = useMemo(() => {
    if (chartData.length === 0) return [];

    // Find max value across all visible metrics
    let maxValue = 0;
    chartData.forEach((item) => {
      visibleMetrics.forEach((metric) => {
        const key = METRIC_CONFIG[metric].key;
        const value = item[key] || 0;
        maxValue = Math.max(maxValue, value);
      });
    });

    // Round up to nearest 5
    const ceiling = Math.ceil(maxValue / 5000000) * 5000000;

    // Create 5 evenly-spaced ticks and round each
    const ticks = [];
    for (let i = 0; i <= 4; i++) {
      const tickValue = (ceiling * i) / 4;
      ticks.push(Math.round(tickValue));
    }

    return ticks;
  }, [chartData, visibleMetrics]);

  if (chartData.length === 0) {
    return (
      <div className="rounded-2xl border border-rb-border bg-rb-white p-12 text-center text-sm text-rb-grey shadow-sm">
        Chart will appear once data loads.
      </div>
    );
  }

  return (
    <div className={`h-[540px] w-full rounded-2xl border border-rb-border bg-rb-white shadow-sm ${isMobile ? 'p-3' : 'p-6'}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={isMobile
            ? { top: 16, right: 8, bottom: 80, left: 4 }
            : { top: 24, right: 32, bottom: 80, left: 8 }
          }
        >
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
            ticks={yAxisTicks}
            domain={[0, yAxisTicks[yAxisTicks.length - 1]]}
            tickFormatter={(value) => `$${Math.round(value / 1000000)}M`}
            axisLine={{ stroke: "#E4E4E7" }}
            tickLine={false}
            tick={{ fill: "#2B2F36", fontSize: 12 }}
            width={isMobile ? 40 : 50}
          />
          <Tooltip content={<CustomTooltip chartData={chartData} />} cursor={{ fill: "rgba(20, 40, 85, 0.08)" }} />
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
