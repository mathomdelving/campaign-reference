'use client';

import type { DistrictCandidate } from "@/hooks/useDistrictCandidates";
import { FollowButton } from "@/components/follow/FollowButton";
import { formatCurrency } from "@/utils/formatters";

interface CandidateGridProps {
  candidates: DistrictCandidate[];
  selected: string[];
  onToggle: (candidateId: string) => void;
  metrics: {
    totalRaised: boolean;
    totalDisbursed: boolean;
    cashOnHand: boolean;
  };
}

export function CandidateGrid({
  candidates,
  selected,
  onToggle,
  metrics,
}: CandidateGridProps) {
  if (candidates.length === 0) {
    return (
      <div className="p-12 text-center text-sm text-rb-grey">
        Select a district to see race details.
      </div>
    );
  }

  const handleRowToggle = (candidateId: string) => {
    onToggle(candidateId);
  };

  return (
    <table className="w-full table-fixed border-collapse text-sm text-rb-black">
      <thead className="border-b-2 border-rb-border bg-gray-50 uppercase tracking-wider text-rb-grey">
        <tr>
          <th className="w-12 px-1 py-3"></th>
          <th className="w-12 px-2 py-3 text-center text-[11px] font-semibold tracking-[0.2rem]">Rank</th>
          <th className="w-[220px] px-3 py-3 text-left text-xs font-semibold">Candidate</th>
          <th className="w-16 px-1 py-3 text-center text-xs font-semibold">Party</th>
          {metrics.totalRaised && (
            <th className="px-8 py-3 text-right text-xs font-semibold">Raised</th>
          )}
          {metrics.totalDisbursed && (
            <th className="px-8 py-3 text-right text-xs font-semibold">Spent</th>
          )}
          {metrics.cashOnHand && (
            <th className="px-8 py-3 text-right text-xs font-semibold">Cash</th>
          )}
        </tr>
      </thead>
      <tbody>
        {candidates.map((candidate, index) => {
          const isSelected = selected.includes(candidate.candidate_id);
          return (
            <tr
              key={candidate.candidate_id}
              role="button"
              aria-pressed={isSelected}
              tabIndex={0}
              onClick={() => handleRowToggle(candidate.candidate_id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  handleRowToggle(candidate.candidate_id);
                }
              }}
              className={`relative cursor-pointer border-b border-rb-border transition-all ${
                isSelected
                  ? "bg-gray-200 ring-1 ring-inset ring-rb-gold shadow-[0_0_0_1px_rgba(255,201,6,0.25)]"
                  : "bg-white hover:bg-gray-50"
              }`}
            >
              <td className="w-12 px-1 py-4 text-center">
                <div
                  onClick={(event) => event.stopPropagation()}
                  onKeyDown={(event) => event.stopPropagation()}
                  className={`inline-flex items-center justify-center rounded-full p-1 transition-all ${
                    isSelected
                      ? "bg-rb-gold/20 ring-2 ring-rb-gold ring-offset-1 ring-offset-gray-200"
                      : ""
                  }`}
                >
                  <FollowButton
                    candidateId={candidate.candidate_id}
                    candidateName={candidate.name}
                    party={candidate.party}
                    office={candidate.office}
                    state={candidate.state}
                    district={candidate.district}
                    size="sm"
                  />
                </div>
              </td>
              <td className="w-12 px-2 py-4 text-center font-medium text-rb-black">
                {index + 1}
              </td>
              <td className="w-[220px] px-3 py-4">
                <div className="font-semibold text-rb-black">{candidate.name}</div>
                <div className="text-xs text-rb-grey">{candidate.candidate_id}</div>
              </td>
              <td className="w-16 px-1 py-4 text-center">
                <span className={partyLinkClasses(candidate.party)}>
                  {formatPartyLabel(candidate.party)}
                </span>
              </td>
              {metrics.totalRaised && (
                <td className="px-8 py-4 text-right font-medium text-rb-black">
                  {formatCurrency(candidate.totalRaised)}
                </td>
              )}
              {metrics.totalDisbursed && (
                <td className="px-8 py-4 text-right font-medium text-rb-black">
                  {formatCurrency(candidate.totalDisbursed)}
                </td>
              )}
              {metrics.cashOnHand && (
                <td className="px-8 py-4 text-right font-medium text-rb-black">
                  {formatCurrency(candidate.cashOnHand)}
                </td>
              )}
            </tr>
          );
        })}
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
