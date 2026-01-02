'use client';

import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { formatQuarterLabel } from "@/utils/quarters";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error(
    "Supabase credentials are missing. Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
  );
}

const browserClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
  },
});

// Party committee IDs that use the party_committee_filings table
const PARTY_COMMITTEE_IDS = new Set([
  "C00000935", // DCCC
  "C00042366", // DSCC
  "C00075820", // NRCC
  "C00027466", // NRSC
]);

export interface CommitteeQuarterlyRecord {
  committeeId: string;
  committeeName: string | null;
  party: string | null;
  quarterLabel: string;
  receipts: number;
  disbursements: number;
  cashEnding: number;
  coverageEnd: string | null;
  reportType?: string | null;
}

interface CommitteeQuarterlyResult {
  data: CommitteeQuarterlyRecord[];
  loading: boolean;
  error: string | null;
}

export function useCommitteeQuarterlyData(
  committeeIds: string[],
  cycles: number | number[] = 2026
): CommitteeQuarterlyResult {
  const [data, setData] = useState<CommitteeQuarterlyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const key = useMemo(() => committeeIds.slice().sort().join(","), [committeeIds]);
  const cycleKey = useMemo(() => {
    const cycleArray = Array.isArray(cycles) ? cycles : [cycles];
    return [...cycleArray].sort().join(",");
  }, [cycles]);

  useEffect(() => {
    if (committeeIds.length === 0) {
      setData([]);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;

    async function fetchQuarterlies() {
      setLoading(true);
      setError(null);

      try {
        const cyclesArray = Array.isArray(cycles) ? cycles : [cycles];

        // Separate party committees from candidate committees
        const partyCommitteeIds = committeeIds.filter(id => PARTY_COMMITTEE_IDS.has(id));
        const candidateCommitteeIds = committeeIds.filter(id => !PARTY_COMMITTEE_IDS.has(id));

        const allResults: CommitteeQuarterlyRecord[] = [];

        // Fetch party committee data from party_committee_filings table
        if (partyCommitteeIds.length > 0) {
          const { data: partyResults, error: partyError } = await browserClient
            .from("party_committee_filings")
            .select(
              "committee_id, committee_name, party, total_receipts, total_disbursements, cash_on_hand_end, coverage_end_date, report_type_full"
            )
            .in("cycle", cyclesArray)
            .in("committee_id", partyCommitteeIds)
            .order("coverage_end_date", { ascending: true });

          if (partyError) throw partyError;

          const partyProcessed = partyResults?.map((row) => ({
            committeeId: row.committee_id,
            committeeName: row.committee_name,
            party: row.party,
            quarterLabel: row.coverage_end_date
              ? formatQuarterLabel(row.coverage_end_date, row.report_type_full)
              : row.report_type_full ?? "Unknown",
            receipts: row.total_receipts ?? 0,
            disbursements: row.total_disbursements ?? 0,
            cashEnding: row.cash_on_hand_end ?? 0,
            coverageEnd: row.coverage_end_date ?? null,
            reportType: row.report_type_full,
          })) ?? [];

          allResults.push(...partyProcessed);
        }

        // Fetch candidate committee data from quarterly_financials table
        if (candidateCommitteeIds.length > 0) {
          const { data: candidateResults, error: candidateError } = await browserClient
            .from("quarterly_financials")
            .select(
              "committee_id, committee_name, party, total_receipts, total_disbursements, cash_ending, coverage_end_date, report_type"
            )
            .in("cycle", cyclesArray)
            .in("committee_id", candidateCommitteeIds)
            .order("coverage_end_date", { ascending: true });

          if (candidateError) throw candidateError;

          const candidateProcessed = candidateResults?.map((row) => ({
            committeeId: row.committee_id,
            committeeName: row.committee_name,
            party: row.party,
            quarterLabel: row.coverage_end_date
              ? formatQuarterLabel(row.coverage_end_date, row.report_type)
              : row.report_type ?? "Unknown",
            receipts: row.total_receipts ?? 0,
            disbursements: row.total_disbursements ?? 0,
            cashEnding: row.cash_ending ?? 0,
            coverageEnd: row.coverage_end_date ?? null,
            reportType: row.report_type,
          })) ?? [];

          allResults.push(...candidateProcessed);
        }

        // Deduplicate reports: FEC provides duplicates with different report_type names
        // for the same filing (e.g., "12G" and "PRE-GENERAL" are the same report).
        // Keep descriptive names (PRE-GENERAL, POST-GENERAL) over short codes (12G, 30G).
        const deduplicated: CommitteeQuarterlyRecord[] = [];
        const seenKeys = new Map<string, CommitteeQuarterlyRecord>();

        for (const record of allResults) {
          const key = `${record.committeeId}-${record.coverageEnd}`;
          const existing = seenKeys.get(key);

          if (!existing) {
            seenKeys.set(key, record);
          } else {
            // Prefer descriptive names over short codes
            const isCurrentDescriptive = record.reportType?.includes('-') ?? false;
            const isExistingDescriptive = existing.reportType?.includes('-') ?? false;

            if (isCurrentDescriptive && !isExistingDescriptive) {
              // Replace with descriptive name
              seenKeys.set(key, record);
            }
            // Otherwise keep existing
          }
        }

        deduplicated.push(...seenKeys.values());

        // Sort by coverage date
        deduplicated.sort((a, b) => {
          if (!a.coverageEnd) return -1;
          if (!b.coverageEnd) return 1;
          return a.coverageEnd.localeCompare(b.coverageEnd);
        });

        if (!cancelled) {
          setData(deduplicated);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Unable to load committee quarterlies.";
          setError(message);
          setData([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchQuarterlies();

    return () => {
      cancelled = true;
    };
  }, [key, cycleKey, committeeIds]);

  return { data, loading, error };
}
