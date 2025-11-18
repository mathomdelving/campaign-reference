'use client';

import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import type { LeaderboardFilters } from "@/hooks/useFilters";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error("Supabase credentials are missing. Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
}

const browserClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
  },
});

export interface LeaderboardCandidate {
  candidate_id: string;
  name: string;
  party: string | null;
  state: string | null;
  district: string | null;
  office: string | null;
  totalReceipts: number;
  totalDisbursements: number;
  cashOnHand: number;
  updatedAt: string | null;
}

interface CandidateDataResult {
  data: LeaderboardCandidate[];
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

export function useCandidateData(filters: LeaderboardFilters): CandidateDataResult {
  const [data, setData] = useState<LeaderboardCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      console.log('🚀 [useCandidateData] Using leaderboard_data view - FAST VERSION');
      setLoading(true);
      setError(null);

      try {
        // Build the query using the pre-joined view
        let query = browserClient
          .from("leaderboard_data")
          .select("*")
          .eq("cycle", filters.cycle);

        // Apply chamber filter
        if (filters.chamber === "H") {
          query = query.eq("office", "H");
        } else if (filters.chamber === "S") {
          query = query.eq("office", "S");
        }

        // Apply state filter
        if (filters.state !== "all") {
          query = query.eq("state", filters.state);
        }

        // Apply district filter
        if (filters.district !== "all") {
          if (filters.chamber === "H") {
            query = query.eq("district", filters.district);
          } else if (filters.chamber === "S") {
            // For Senate, district stores the class (I, II, III)
            query = query.ilike("candidate_id", `%${filters.district}%`);
          }
        }

        const { data: results, error: queryError } = await query;

        if (queryError) throw queryError;

        // Map to LeaderboardCandidate format
        const processed = (results ?? []).map((row) => ({
          candidate_id: row.candidate_id,
          name: row.display_name, // Already clean from political_persons!
          party: row.party,
          state: row.state,
          district: row.district,
          office: row.office,
          totalReceipts: row.total_receipts ?? 0,
          totalDisbursements: row.total_disbursements ?? 0,
          cashOnHand: row.cash_on_hand ?? 0,
          updatedAt: row.updated_at,
        }));

        // Deduplicate candidates with same name
        // When chamber filter is "both", use name + office as key to keep both House and Senate
        // When chamber is specific (H or S), deduplicate by name only
        const useOfficeInKey = filters.chamber === "both";
        const deduplicatedByName = new Map<string, LeaderboardCandidate>();

        processed.forEach((candidate) => {
          const nameKey = candidate.name.toUpperCase().trim();
          const key = useOfficeInKey ? `${nameKey}-${candidate.office}` : nameKey;
          const existing = deduplicatedByName.get(key);

          if (!existing) {
            deduplicatedByName.set(key, candidate);
          } else {
            // Keep the one with higher receipts (handles amendments/duplicates for same office)
            if (candidate.totalReceipts > existing.totalReceipts) {
              deduplicatedByName.set(key, candidate);
            }
          }
        });

        const final = Array.from(deduplicatedByName.values());
        final.sort((a, b) => (b.totalReceipts ?? 0) - (a.totalReceipts ?? 0));

        if (!cancelled) {
          setData(final);

          const mostRecent = final.reduce<string | null>((latest, current) => {
            if (!current.updatedAt) return latest;
            if (!latest) return current.updatedAt;
            return new Date(current.updatedAt) > new Date(latest) ? current.updatedAt : latest;
          }, null);

          setLastUpdated(mostRecent);
        }
      } catch (err) {
        if (!cancelled) {
          console.error('[useCandidateData] Error:', err);
          const message = err instanceof Error ? err.message : "Unable to load candidate data.";
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

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [filterKey, filters.cycle, filters.chamber, filters.state, filters.district]);

  return { data, loading, error, lastUpdated };
}
