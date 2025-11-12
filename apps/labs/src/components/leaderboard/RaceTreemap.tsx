'use client';

import { useMemo, useState } from "react";
import { ResponsiveContainer, Treemap } from "recharts";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";
import { formatCompactCurrency, formatCurrency } from "@/utils/formatters";

const METRIC_CONFIG = {
  totalRaised: { key: "totalReceipts", label: "Total Raised" },
  totalDisbursed: { key: "totalDisbursements", label: "Total Spent" },
  cashOnHand: { key: "cashOnHand", label: "Cash on Hand" },
} as const;

type MetricKey = keyof typeof METRIC_CONFIG;

interface RaceTreemapProps {
  data: LeaderboardCandidate[];
  metrics: MetricToggles;
}

interface TreemapNode {
  name: string;
  size: number;
  value: number;
  party: string;
  rank: number;
  totalInParty: number;
  fullName: string;
  candidateId: string;
  office: string;
  state: string;
  district: string;
}

// Party color bases (darker = higher ranked)
const PARTY_COLORS = {
  dem: {
    base: '#3B82F6', // blue-500
    light: '#93C5FD', // blue-300
  },
  gop: {
    base: '#EF4444', // red-500
    light: '#FCA5A5', // red-300
  },
  other: {
    base: '#F59E0B', // amber-500
    light: '#FCD34D', // amber-300
  },
};

function getPartyKey(party?: string | null): 'dem' | 'gop' | 'other' {
  const normalized = (party ?? "").toLowerCase();
  if (normalized.includes("dem")) return "dem";
  if (normalized.includes("rep") || normalized.includes("gop")) return "gop";
  return "other";
}

function interpolateColor(baseColor: string, lightColor: string, intensity: number): string {
  // intensity: 0 (light) to 1 (dark/base)
  // Parse hex colors
  const parseHex = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  };

  const base = parseHex(baseColor);
  const light = parseHex(lightColor);

  const r = Math.round(light.r + (base.r - light.r) * intensity);
  const g = Math.round(light.g + (base.g - light.g) * intensity);
  const b = Math.round(light.b + (base.b - light.b) * intensity);

  return `rgb(${r}, ${g}, ${b})`;
}

function getTreemapBackgroundColor(party: string, rank: number, totalInParty: number): string {
  const partyKey = getPartyKey(party);
  const colors = PARTY_COLORS[partyKey];

  // Calculate intensity: rank 1 = darkest (1.0), last rank = lightest (0.3)
  // This ensures even the lowest ranked still has decent color saturation
  const intensity = totalInParty > 1
    ? 0.3 + (0.7 * (1 - (rank - 1) / (totalInParty - 1)))
    : 1.0;

  return interpolateColor(colors.base, colors.light, intensity);
}

function getLastName(name: string): string {
  const parts = name.split(",");

  if (parts.length >= 2) {
    return parts[0].trim();
  }

  const words = name.trim().split(" ");
  return words[words.length - 1];
}

function properCase(value: string): string {
  return value
    .toLowerCase()
    .split(/(\s+|-)/g)
    .map((word) => {
      if (word === " " || word === "-") return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join("");
}

function formatFullName(name: string): string {
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

function formatDistrictLabel(office: string, state: string, district: string): string {
  if (office === "H") {
    return `${state}-${district}`;
  }
  if (office === "S") {
    return `${state}-SEN`;
  }
  return state || "—";
}

interface TooltipData {
  name: string;
  value: number;
  party: string;
  candidateId: string;
  office: string;
  state: string;
  district: string;
}

export function RaceTreemap({ data, metrics }: RaceTreemapProps) {
  const [tooltip, setTooltip] = useState<{ x: number; y: number; data: TooltipData } | null>(null);

  const treemapData = useMemo(() => {
    // Determine which metric to use (only use the first selected metric)
    const visibleMetrics = (Object.keys(metrics) as MetricKey[]).filter(
      (metric) => metrics[metric]
    );

    if (visibleMetrics.length === 0) {
      return [];
    }

    // Priority order: totalRaised > totalDisbursed > cashOnHand
    const metricPriority: MetricKey[] = ['totalRaised', 'totalDisbursed', 'cashOnHand'];
    const selectedMetric = metricPriority.find(m => visibleMetrics.includes(m)) ?? visibleMetrics[0];
    const metricKey = METRIC_CONFIG[selectedMetric].key as keyof LeaderboardCandidate;

    // Sort candidates by the selected metric
    const sorted = [...data]
      .filter(c => (c[metricKey] as number) > 0)
      .sort((a, b) => {
        const aValue = (a[metricKey] as number) ?? 0;
        const bValue = (b[metricKey] as number) ?? 0;
        return bValue - aValue;
      })
      .slice(0, 50); // Limit to top 50 to keep treemap readable

    // Calculate party rankings
    const partyRankings = new Map<string, number>();
    const partyTotals = new Map<string, number>();

    // Count total candidates per party
    sorted.forEach(candidate => {
      const partyKey = getPartyKey(candidate.party);
      partyTotals.set(partyKey, (partyTotals.get(partyKey) ?? 0) + 1);
    });

    // Assign ranks within each party
    const nodes: TreemapNode[] = sorted.map((candidate) => {
      const partyKey = getPartyKey(candidate.party);
      const currentRank = (partyRankings.get(partyKey) ?? 0) + 1;
      partyRankings.set(partyKey, currentRank);

      const value = (candidate[metricKey] as number) ?? 0;

      return {
        name: properCase(getLastName(candidate.name)),
        size: value,
        value: value,
        party: candidate.party ?? "Unknown",
        rank: currentRank,
        totalInParty: partyTotals.get(partyKey) ?? 1,
        fullName: candidate.name,
        candidateId: candidate.candidate_id,
        office: candidate.office ?? "",
        state: candidate.state ?? "",
        district: candidate.district ?? "",
      };
    });

    return nodes;
  }, [data, metrics]);

  if (treemapData.length === 0) {
    return (
      <div className="rounded-2xl border border-rb-border bg-rb-white p-12 text-center text-sm text-rb-grey shadow-sm">
        Treemap will appear once data loads.
      </div>
    );
  }

  const handleMouseEnter = (data: TooltipData, x: number, y: number) => {
    setTooltip({ x, y, data });
  };

  const handleMouseLeave = () => {
    setTooltip(null);
  };

  return (
    <div className="relative h-[600px] w-full bg-rb-white p-6">
      <div className="h-full w-full overflow-hidden rounded-lg" style={{ borderRadius: '8px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={treemapData}
            dataKey="size"
            aspectRatio={4 / 3}
            stroke="#fff"
            strokeWidth={2}
            content={<CustomTreemapContent onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />}
          />
        </ResponsiveContainer>
      </div>
      {tooltip && (
        <div
          className="pointer-events-none absolute z-50"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: 'translate(-50%, -120%)',
            transition: 'left 0.1s ease-out, top 0.1s ease-out',
            willChange: 'left, top',
          }}
        >
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
              {formatFullName(tooltip.data.name)}
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
              <span>{tooltip.data.candidateId}</span>
              <span>•</span>
              <span style={{ color: getPartyColor(tooltip.data.party), fontWeight: 500 }}>
                {formatPartyLabel(tooltip.data.party)}
              </span>
              <span>•</span>
              <span>{formatDistrictLabel(tooltip.data.office, tooltip.data.state, tooltip.data.district)}</span>
            </div>
            <div style={{ color: '#111827', fontSize: '15px', fontWeight: 600 }}>
              {formatCurrency(tooltip.data.value)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface CustomContentProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  value?: number;
  party?: string;
  rank?: number;
  totalInParty?: number;
  fullName?: string;
  candidateId?: string;
  office?: string;
  state?: string;
  district?: string;
  onMouseEnter?: (data: TooltipData, x: number, y: number) => void;
  onMouseLeave?: () => void;
}

function abbreviateName(name: string, maxLength: number): string {
  if (name.length <= maxLength) return name;

  // For very small spaces, just show first letter + last letter
  if (maxLength <= 3) {
    return name.charAt(0) + '.';
  }

  // For small spaces, show first 3-4 chars
  if (maxLength <= 6) {
    return name.substring(0, maxLength - 1) + '.';
  }

  // For medium spaces, show first initial + last name or abbreviated last name
  return name.substring(0, maxLength - 1) + '.';
}

function getDisplayName(fullName: string, lastName: string, width: number): string {
  // Estimate characters that can fit based on width
  // Rough estimate: 10px per character at font size 14
  const avgCharWidth = 9;
  const maxChars = Math.floor((width - 20) / avgCharWidth); // Subtract padding

  if (maxChars <= 0) return '';

  if (lastName.length <= maxChars) {
    return lastName;
  }

  return abbreviateName(lastName, maxChars);
}

function getTextColor(bgColor: string): string {
  // Parse RGB from color string
  const rgb = bgColor.match(/\d+/g);
  if (!rgb || rgb.length < 3) return '#111827'; // rb-black as fallback

  const r = parseInt(rgb[0]);
  const g = parseInt(rgb[1]);
  const b = parseInt(rgb[2]);

  // Calculate relative luminance using WCAG formula
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Use dark text for lighter backgrounds (higher threshold for more black text)
  // Adjusted threshold to 0.65 so more boxes get black text
  return luminance > 0.65 ? '#111827' : '#111827'; // Always use rb-black for now
}

function CustomTreemapContent(props: CustomContentProps) {
  const { x = 0, y = 0, width = 0, height = 0, name, value, party, rank, totalInParty, fullName, candidateId, office, state, district, onMouseEnter, onMouseLeave } = props;

  if (width < 30 || height < 25) return null;

  const bgColor = getTreemapBackgroundColor(party ?? '', rank ?? 1, totalInParty ?? 1);

  // Calculate font size based on box size
  const minDimension = Math.min(width, height);
  const baseFontSize = Math.max(11, Math.min(18, minDimension / 4.5));

  // Get display name based on available width
  const displayName = getDisplayName(fullName ?? name ?? '', name ?? '', width);

  // Only show name if we have a displayable string
  const showName = displayName.length > 0 && height >= 30;

  const handleMouseMove = (event: React.MouseEvent) => {
    if (onMouseEnter && fullName && value !== undefined && party && candidateId && office && state && district) {
      const rect = (event.currentTarget as SVGRectElement).getBoundingClientRect();
      const containerRect = (event.currentTarget as SVGRectElement).ownerSVGElement?.getBoundingClientRect();
      if (containerRect) {
        onMouseEnter(
          {
            name: fullName,
            value,
            party,
            candidateId,
            office,
            state,
            district
          },
          rect.left + rect.width / 2 - containerRect.left,
          rect.top - containerRect.top
        );
      }
    }
  };

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={bgColor}
        onMouseMove={handleMouseMove}
        onMouseLeave={onMouseLeave}
        style={{ cursor: 'pointer' }}
      />
      {showName && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#111827"
          stroke="none"
          strokeWidth={0}
          fontSize={baseFontSize}
          fontWeight="700"
          fontFamily="Inter, system-ui, sans-serif"
          style={{
            pointerEvents: 'none',
            userSelect: 'none',
            paintOrder: 'fill',
          }}
        >
          {displayName}
        </text>
      )}
    </g>
  );
}
