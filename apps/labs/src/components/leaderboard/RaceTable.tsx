"use client";

import { useMemo, useState } from "react";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";
import { formatCurrency, formatCompactCurrency } from "@/utils/formatters";
import { FollowButton } from "@/components/follow/FollowButton";

type SortKey = "totalReceipts" | "totalDisbursements" | "cashOnHand";

interface RaceTableProps {
  data: LeaderboardCandidate[];
  metrics: MetricToggles;
}

export function RaceTable({ data, metrics }: RaceTableProps) {
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: "asc" | "desc" }>({
    key: "totalReceipts",
    direction: "desc",
  });

  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      const aValue = (a[sortConfig.key] ?? 0) as number;
      const bValue = (b[sortConfig.key] ?? 0) as number;

      if (sortConfig.direction === "asc") {
        return aValue - bValue;
      }
      return bValue - aValue;
    });
    return sorted;
  }, [data, sortConfig]);

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc",
    }));
  };

  const renderSortIcon = (column: SortKey) => {
    if (sortConfig.key !== column) {
      // Unsorted - show up/down arrows
      return (
        <svg className="w-4 h-4 text-rb-grey opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    return sortConfig.direction === "asc" ? (
      // Ascending - up arrow
      <svg className="w-4 h-4 text-rb-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      // Descending - down arrow
      <svg className="w-4 h-4 text-rb-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  if (data.length === 0) {
    return (
      <div className="p-12 text-center text-sm text-rb-grey">
        No data available for the selected filters yet.
      </div>
    );
  }

  return (
    <table className="w-full border-collapse text-sm text-rb-black">
      <thead className="border-b-2 border-rb-border bg-gray-50">
        <tr>
          <th className="w-12 px-2 py-3"></th>
          <th className="w-12 px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-rb-grey">Rank</th>
          <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-rb-grey">Candidate</th>
          {metrics.totalRaised && (
            <th
              className="w-1/4 px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("totalReceipts")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Total Raised
                {renderSortIcon("totalReceipts")}
              </span>
            </th>
          )}
          {metrics.totalDisbursed && (
            <th
              className="w-1/4 px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("totalDisbursements")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Total Spent
                {renderSortIcon("totalDisbursements")}
              </span>
            </th>
          )}
          {metrics.cashOnHand && (
            <th
              className="w-1/4 px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("cashOnHand")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Cash on Hand
                {renderSortIcon("cashOnHand")}
              </span>
            </th>
          )}
        </tr>
      </thead>
      <tbody>
        {sortedData.map((candidate, index) => (
          <tr
            key={candidate.candidate_id}
            className="border-b border-rb-border bg-white transition-colors hover:bg-gray-50"
          >
            <td className="w-12 px-2 py-4 text-center">
              <FollowButton
                candidateId={candidate.candidate_id}
                candidateName={candidate.name}
                party={candidate.party}
                office={candidate.office}
                state={candidate.state}
                district={candidate.district}
                size="sm"
              />
            </td>
            <td className="w-12 px-2 py-4 text-center font-medium text-rb-black">{index + 1}.</td>
            <td className="px-3 py-4">
              <div className="font-semibold text-rb-black">{candidate.name}</div>
              <div className="text-xs text-rb-grey flex items-center gap-1.5">
                <span>{candidate.candidate_id}</span>
                <span>•</span>
                <span className={getPartyTextColor(candidate.party)}>
                  {formatPartyLabel(candidate.party)}
                </span>
                <span>•</span>
                <span>{formatDistrictLabel(candidate)}</span>
              </div>
            </td>
            {metrics.totalRaised && (
              <td
                className="w-1/4 px-6 py-4 text-right text-base font-semibold text-rb-black cursor-help"
                title={formatCurrency(candidate.totalReceipts)}
              >
                {formatCompactCurrency(candidate.totalReceipts)}
              </td>
            )}
            {metrics.totalDisbursed && (
              <td
                className="w-1/4 px-6 py-4 text-right text-base font-semibold text-rb-black cursor-help"
                title={formatCurrency(candidate.totalDisbursements)}
              >
                {formatCompactCurrency(candidate.totalDisbursements)}
              </td>
            )}
            {metrics.cashOnHand && (
              <td
                className="w-1/4 px-6 py-4 text-right text-base font-semibold text-rb-black cursor-help"
                title={formatCurrency(candidate.cashOnHand)}
              >
                {formatCompactCurrency(candidate.cashOnHand)}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function formatPartyLabel(party?: string | null) {
  if (!party) return "N/A";
  const normalized = party.toLowerCase();
  if (normalized.includes("dem")) return "DEM";
  if (normalized.includes("rep")) return "GOP";
  if (normalized.includes("ind")) return "IND";
  return party;
}

function getPartyTextColor(party?: string | null) {
  const normalized = (party ?? "").toUpperCase();

  if (normalized.includes("DEM")) {
    return "text-blue-600 font-medium";
  }
  if (normalized.includes("REP")) {
    return "text-red-600 font-medium";
  }
  return "text-yellow-600 font-medium";
}

function formatDistrictLabel(candidate: LeaderboardCandidate) {
  const state = candidate.state ?? "";
  if (candidate.office === "H") {
    const district = candidate.district ?? "";
    return `${state}-${district}`;
  }
  if (candidate.office === "S") {
    return `${state}-SEN`;
  }
  return state || "—";
}
