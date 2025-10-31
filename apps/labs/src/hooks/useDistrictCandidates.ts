'use client';

import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import type { ChamberFilter } from "@/hooks/useFilters";

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

export interface DistrictCandidate {
  candidate_id: string;
  name: string;
  party: string | null;
  state: string | null;
  district: string | null;
  office: string | null;
  totalRaised: number;
  totalDisbursed: number;
  cashOnHand: number;
  updatedAt: string | null;
}

export interface DistrictCandidatesResult {
  data: DistrictCandidate[];
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

export function useDistrictCandidates({
  state,
  chamber,
  district,
  cycle,
}: {
  state: string;
  chamber: ChamberFilter;
  district: string;
  cycle: number;
}): DistrictCandidatesResult {
  const [data, setData] = useState<DistrictCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const key = useMemo(() => `${state}-${chamber}-${district}-${cycle}`, [state, chamber, district, cycle]);

  useEffect(() => {
    if (state === "all") {
      setData([]);
      setLastUpdated(null);
      return;
    }

    let cancelled = false;

    async function fetchCandidates() {
      setLoading(true);
      setError(null);

      try {
        let query = browserClient
          .from("candidates")
          .select(
            `
            candidate_id,
            name,
            party,
            state,
            district,
            office,
            financial_summary!inner(
              total_receipts,
              total_disbursements,
              cash_on_hand,
              updated_at
            )
          `
          )
          .eq("cycle", cycle)
          .eq("state", state);

        if (chamber === "H") {
          query = query.eq("office", "H");
          if (district !== "all") {
            query = query.eq("district", district);
          }
        } else if (chamber === "S") {
          query = query.eq("office", "S");
        }

        const { data: results, error: queryError } = await query;
        if (queryError) throw queryError;

        let flattened =
          results?.map((candidate) => ({
            candidate_id: candidate.candidate_id,
            name: candidate.name,
            party: candidate.party,
            state: candidate.state,
            district: candidate.district,
            office: candidate.office,
            totalRaised:
              candidate.financial_summary?.[0]?.total_receipts ?? 0,
            totalDisbursed:
              candidate.financial_summary?.[0]?.total_disbursements ?? 0,
            cashOnHand:
              candidate.financial_summary?.[0]?.cash_on_hand ?? 0,
            updatedAt: candidate.financial_summary?.[0]?.updated_at ?? null,
          })) ?? [];

        if (chamber === "S" && district !== "all") {
          const classToChar: Record<string, string> = {
            I: "4",
            II: "0",
            III: "6",
            Special: "8",
          };
          const classChar = classToChar[district];
          if (classChar) {
            flattened = flattened.filter((candidate) =>
              candidate.candidate_id?.includes(classChar)
            );
          }
        }

        flattened.sort(
          (a, b) => (b.totalRaised ?? 0) - (a.totalRaised ?? 0)
        );

        if (!cancelled) {
          setData(flattened);

          const mostRecent = flattened.reduce<string | null>((latest, current) => {
            if (!current.updatedAt) return latest;
            if (!latest) return current.updatedAt;
            return new Date(current.updatedAt) > new Date(latest)
              ? current.updatedAt
              : latest;
          }, null);
          setLastUpdated(mostRecent);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Unable to load candidates.";
          setError(message);
          setData([]);
          setLastUpdated(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchCandidates();

    return () => {
      cancelled = true;
    };
  }, [key, state, chamber, district, cycle]);

  return { data, loading, error, lastUpdated };
}
