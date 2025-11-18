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

export interface PersonQuarterlyRecord {
  personId: string;
  candidateId: string;
  committeeId: string | null;
  candidateName: string;
  party: string | null;
  state: string | null;
  district: string | null;
  reportType: string | null;
  coverageStart: string | null;
  coverageEnd: string | null;
  receipts: number;
  disbursements: number;
  cashBeginning: number;
  cashEnding: number;
  quarterLabel: string;
  isPrincipal: boolean; // Whether this was a principal committee for this cycle
}

interface UsePersonQuarterlyDataResult {
  data: PersonQuarterlyRecord[];
  loading: boolean;
  error: string | null;
}

/**
 * Fetch quarterly financial data for a political person, combining all their candidate_ids
 * and filtering to show only principal committee data based on committee_designations.
 */
export function usePersonQuarterlyData(
  personIds: string[] | string,
  cycles: number | number[] = 2026
): UsePersonQuarterlyDataResult {
  const [data, setData] = useState<PersonQuarterlyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const personKey = useMemo(() => {
    const ids = Array.isArray(personIds) ? personIds : [personIds];
    return [...ids].sort().join(",");
  }, [personIds]);

  const cycleKey = useMemo(() => {
    const cycleArray = Array.isArray(cycles) ? cycles : [cycles];
    return [...cycleArray].sort().join(",");
  }, [cycles]);

  useEffect(() => {
    async function fetchPersonQuarterly() {
      const ids = Array.isArray(personIds)
        ? personIds.filter(Boolean)
        : [personIds].filter(Boolean);

      if (ids.length === 0) {
        setData([]);
        setLoading(false);
        setError(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const cyclesArray = Array.isArray(cycles) ? cycles : [cycles];

        // Step 1: Get all candidate_ids linked to these person_ids
        const { data: candidates, error: candidatesError } = await browserClient
          .from("candidates")
          .select("candidate_id, person_id")
          .in("person_id", ids);

        if (candidatesError) {
          throw candidatesError;
        }

        if (!candidates || candidates.length === 0) {
          setData([]);
          setLoading(false);
          return;
        }

        const candidateIds = candidates.map(c => c.candidate_id);
        const candidateToPerson = new Map(
          candidates.map(c => [c.candidate_id, c.person_id])
        );

        // Step 2: Get committee designations to identify principal committees per cycle
        const { data: designations, error: designationsError } = await browserClient
          .from("committee_designations")
          .select("committee_id, cycle, candidate_id, is_principal")
          .in("candidate_id", candidateIds)
          .in("cycle", cyclesArray);

        if (designationsError) {
          throw designationsError;
        }

        // Build a set of (committee_id, cycle) pairs that are principal
        const principalCommittees = new Set<string>();
        designations?.forEach(d => {
          if (d.is_principal) {
            principalCommittees.add(`${d.committee_id}-${d.cycle}`);
          }
        });

        // Step 3: Fetch quarterly financial data for all linked candidate_ids
        const { data: results, error: queryError } = await browserClient
          .from("quarterly_financials")
          .select("*")
          .in("candidate_id", candidateIds)
          .in("cycle", cyclesArray)
          .order("coverage_end_date", { ascending: true });

        if (queryError) {
          throw queryError;
        }

        // Step 4: Process and filter to only principal committee data
        const processed =
          results
            ?.map((row) => {
              const personId = candidateToPerson.get(row.candidate_id);
              if (!personId) return null;

              // Check if this committee was principal for this cycle
              const isPrincipal = row.committee_id
                ? principalCommittees.has(`${row.committee_id}-${row.cycle}`)
                : false;

              return {
                personId,
                candidateId: row.candidate_id,
                committeeId: row.committee_id,
                candidateName: row.name,
                party: row.party,
                state: row.state,
                district: row.district,
                reportType: row.report_type,
                coverageStart: row.coverage_start_date,
                coverageEnd: row.coverage_end_date,
                receipts: row.total_receipts ?? 0,
                disbursements: row.total_disbursements ?? 0,
                cashBeginning: row.cash_beginning ?? 0,
                cashEnding: row.cash_ending ?? 0,
                quarterLabel: row.coverage_end_date
                  ? formatQuarterLabel(row.coverage_end_date, row.report_type)
                  : row.report_type ?? "Unknown",
                isPrincipal,
              };
            })
            .filter((record): record is PersonQuarterlyRecord => {
              // Filter to only principal committee records
              return record !== null && record.isPrincipal;
            }) ?? [];

        // Step 5: Deduplicate records by committee + coverage date
        // When the same committee is used across multiple candidate IDs (e.g., House → Senate),
        // the same quarterly reports can appear multiple times. Keep only unique data points.
        // Also deduplicate report type duplicates: FEC provides both "12G" and "PRE-GENERAL" for
        // the same filing. Prefer descriptive names (PRE-GENERAL) over short codes (12G).
        const deduplicated: PersonQuarterlyRecord[] = [];
        const seenMap = new Map<string, PersonQuarterlyRecord>();

        for (const record of processed) {
          const key = `${record.committeeId}-${record.coverageEnd}`;
          const existing = seenMap.get(key);

          if (!existing) {
            seenMap.set(key, record);
          } else {
            // Prefer descriptive names over short codes
            const isCurrentDescriptive = record.reportType?.includes('-') ?? false;
            const isExistingDescriptive = existing.reportType?.includes('-') ?? false;

            if (isCurrentDescriptive && !isExistingDescriptive) {
              // Replace with descriptive name
              seenMap.set(key, record);
            }
            // Otherwise keep existing
          }
        }

        deduplicated.push(...seenMap.values());

        setData(deduplicated);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Unable to load person quarterly data.";
        setError(message);
        setData([]);
      } finally {
        setLoading(false);
      }
    }

    fetchPersonQuarterly();
  }, [personKey, personIds, cycleKey]);

  return { data, loading, error };
}
