"use client";

import { useMemo, useState } from "react";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";
import { formatCurrency } from "@/utils/formatters";
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

  const renderSortGlyph = (column: SortKey) => {
    if (sortConfig.key !== column) {
      return <span className="text-rb-grey opacity-40">↕</span>;
    }
    return sortConfig.direction === "asc" ? (
      <span className="text-rb-brand-navy">↑</span>
    ) : (
      <span className="text-rb-brand-navy">↓</span>
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
    <table className="w-full table-fixed border-collapse text-sm text-rb-black">
      <thead className="border-b-2 border-rb-border bg-gray-50">
        <tr>
          <th className="w-12 px-2 py-3"></th>
          <th className="w-12 px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-rb-grey">Rank</th>
          <th className="w-[220px] px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-rb-grey">Candidate</th>
          <th className="w-16 px-1 py-3 text-center text-xs font-semibold uppercase tracking-wider text-rb-grey">Party</th>
          <th className="w-16 px-1 py-3 text-center text-xs font-semibold uppercase tracking-wider text-rb-grey">State</th>
          <th className="w-20 px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-rb-grey">District</th>
          {metrics.totalRaised && (
            <th
              className="px-8 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("totalReceipts")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Total Raised
                {renderSortGlyph("totalReceipts")}
              </span>
            </th>
          )}
          {metrics.totalDisbursed && (
            <th
              className="px-8 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("totalDisbursements")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Total Spent
                {renderSortGlyph("totalDisbursements")}
              </span>
            </th>
          )}
          {metrics.cashOnHand && (
            <th
              className="px-8 py-3 text-right text-xs font-semibold uppercase tracking-wider text-rb-grey cursor-pointer hover:text-rb-brand-navy"
              onClick={() => handleSort("cashOnHand")}
            >
              <span className="inline-flex items-center justify-end gap-2">
                Cash on Hand
                {renderSortGlyph("cashOnHand")}
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
            <td className="w-[220px] px-3 py-4">
              <div className="font-semibold text-rb-black">{candidate.name}</div>
              <div className="text-xs text-rb-grey">
                {candidate.candidate_id}
              </div>
            </td>
            <td className="w-16 px-1 py-4 text-center">
              <span className={partyLinkClasses(candidate.party)}>
                {formatPartyLabel(candidate.party)}
              </span>
            </td>
            <td className="w-16 px-1 py-4 text-center font-medium text-rb-black">
              {candidate.state ?? "—"}
            </td>
            <td className="w-20 px-2 py-4 text-center font-medium text-rb-black">
              {candidate.office === "H"
                ? candidate.district ?? "—"
                : candidate.office === "S"
                ? "SEN"
                : "—"}
            </td>
            {metrics.totalRaised && (
              <td className="px-8 py-4 text-right font-medium text-rb-black">
                {formatCurrency(candidate.totalReceipts)}
              </td>
            )}
            {metrics.totalDisbursed && (
              <td className="px-8 py-4 text-right font-medium text-rb-black">
                {formatCurrency(candidate.totalDisbursements)}
              </td>
            )}
            {metrics.cashOnHand && (
              <td className="px-8 py-4 text-right font-medium text-rb-black">
                {formatCurrency(candidate.cashOnHand)}
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

function partyLinkClasses(party?: string | null) {
  const normalized = (party ?? "").toUpperCase();
  const baseClasses = "font-medium hover:underline cursor-pointer";

  if (normalized.includes("DEM")) {
    return `${baseClasses} text-blue-600`;
  }
  if (normalized.includes("REP")) {
    return `${baseClasses} text-red-600`;
  }
  return `${baseClasses} text-yellow-600`;
}
