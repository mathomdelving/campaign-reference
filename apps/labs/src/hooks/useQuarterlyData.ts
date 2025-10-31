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

export interface QuarterlyRecord {
  candidateId: string;
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
}

interface UseQuarterlyDataResult {
  data: QuarterlyRecord[];
  loading: boolean;
  error: string | null;
}

export function useQuarterlyData(
  candidateIds: string[] | string,
  cycle = 2026
): UseQuarterlyDataResult {
  const [data, setData] = useState<QuarterlyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const candidateKey = useMemo(() => {
    const ids = Array.isArray(candidateIds) ? candidateIds : [candidateIds];
    return [...ids].sort().join(",");
  }, [candidateIds]);

  useEffect(() => {
    async function fetchQuarterly() {
      const ids = Array.isArray(candidateIds)
        ? candidateIds.filter(Boolean)
        : [candidateIds].filter(Boolean);

      if (ids.length === 0) {
        setData([]);
        setLoading(false);
        setError(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const { data: results, error: queryError } = await browserClient
          .from("quarterly_financials")
          .select("*")
          .in("candidate_id", ids)
          .eq("cycle", cycle)
          .order("coverage_end_date", { ascending: true });

        if (queryError) {
          throw queryError;
        }

        const processed =
          results?.map((row) => ({
            candidateId: row.candidate_id,
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
              ? formatQuarterLabel(row.coverage_end_date)
              : row.report_type ?? "Unknown",
          })) ?? [];

        setData(processed);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Unable to load quarterly data.";
        setError(message);
        setData([]);
      } finally {
        setLoading(false);
      }
    }

    fetchQuarterly();
  }, [candidateKey, candidateIds, cycle]);

  return { data, loading, error };
}
