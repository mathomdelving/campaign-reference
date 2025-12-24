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

// Helper function to format names from "LAST, FIRST" to "First Last"
function formatCandidateName(name: string): string {
  if (!name) return name;

  // Check if name is in "LAST, FIRST" format
  if (name.includes(',')) {
    const [last, first] = name.split(',').map(s => s.trim());

    // Convert to title case
    const titleCase = (str: string) => {
      return str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
    };

    return `${titleCase(first)} ${titleCase(last)}`;
  }

  // If no comma, just apply title case
  return name.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

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
      console.log('🔵 [useCandidateData] STARTING FETCH - CODE UPDATED 2025-11-05 19:24');
      setLoading(true);
      setError(null);

      try {
        const PAGE_SIZE = 1000;
        let from = 0;
        const financials: Array<{
          candidate_id: string;
          total_receipts: number | null;
          total_disbursements: number | null;
          cash_on_hand: number | null;
          updated_at: string | null;
        }> = [];

        while (true) {
          const { data: page, error: financialsError } = await browserClient
            .from("financial_summary")
            .select("candidate_id, total_receipts, total_disbursements, cash_on_hand, updated_at")
            .eq("cycle", filters.cycle)
            .range(from, from + PAGE_SIZE - 1);

          if (financialsError) throw financialsError;
          if (!page || page.length === 0) break;

          financials.push(...page);
          if (page.length < PAGE_SIZE) break;
          from += PAGE_SIZE;
        }

        console.log('[useCandidateData] Fetched', financials.length, 'financial records for cycle', filters.cycle);

        const deduped = new Map<string, (typeof financials)[number]>();
        financials.forEach((entry) => {
          const existing = deduped.get(entry.candidate_id);
          if (
            !existing ||
            (entry.updated_at && existing.updated_at && new Date(entry.updated_at) > new Date(existing.updated_at))
          ) {
            deduped.set(entry.candidate_id, entry);
          }
        });

        const candidateIds = Array.from(deduped.keys());
        if (candidateIds.length === 0) {
          setData([]);
          setLastUpdated(null);
          return;
        }

        const BATCH_SIZE = 500;
        const candidates: Array<{
          candidate_id: string;
          name: string;
          party: string | null;
          state: string | null;
          district: string | null;
          office: string | null;
        }> = [];

        for (let i = 0; i < candidateIds.length; i += BATCH_SIZE) {
          const batch = candidateIds.slice(i, i + BATCH_SIZE);

          let query = browserClient
            .from("candidates")
            .select("candidate_id, name, party, state, district, office")
            .in("candidate_id", batch);

          if (filters.chamber === "H") {
            query = query.eq("office", "H");
          } else if (filters.chamber === "S") {
            query = query.eq("office", "S");
          }

          if (filters.state !== "all") {
            query = query.eq("state", filters.state);
          }

          const { data: batchCandidates, error: candidatesError } = await query;
          if (candidatesError) throw candidatesError;

          candidates.push(...(batchCandidates ?? []));
        }

        console.log('[useCandidateData] Fetched', candidates.length, 'candidates out of', candidateIds.length, 'IDs');

        let processed = candidates.map((candidate) => {
          const financial = deduped.get(candidate.candidate_id);
          return {
            candidate_id: candidate.candidate_id,
            name: formatCandidateName(candidate.name),
            party: candidate.party,
            state: candidate.state,
            district: candidate.district,
            office: candidate.office,
            totalReceipts: financial?.total_receipts ?? 0,
            totalDisbursements: financial?.total_disbursements ?? 0,
            cashOnHand: financial?.cash_on_hand ?? 0,
            updatedAt: financial?.updated_at ?? null,
          } as LeaderboardCandidate;
        });

        if (filters.district !== "all") {
          processed = processed.filter((candidate) => {
            if (filters.chamber === "H") {
              return candidate.district === filters.district;
            }
            if (filters.chamber === "S") {
              if (!candidate.candidate_id) return false;
              return candidate.candidate_id.includes(filters.district);
            }
            return true;
          });
        }

        // Deduplicate candidates with same name (House-to-Senate switchers)
        // Prioritize Senate over House for 2026
        const deduplicatedByName = new Map<string, LeaderboardCandidate>();
        processed.forEach((candidate) => {
          const key = candidate.name.toUpperCase().trim();
          const existing = deduplicatedByName.get(key);

          if (!existing) {
            deduplicatedByName.set(key, candidate);
          } else {
            // If duplicate found, prefer Senate over House
            if (candidate.office === 'S' && existing.office === 'H') {
              deduplicatedByName.set(key, candidate);
            }
            // If both are same office, keep the one with higher receipts
            else if (candidate.office === existing.office && candidate.totalReceipts > existing.totalReceipts) {
              deduplicatedByName.set(key, candidate);
            }
          }
        });

        processed = Array.from(deduplicatedByName.values());
        processed.sort((a, b) => (b.totalReceipts ?? 0) - (a.totalReceipts ?? 0));

        if (!cancelled) {
          setData(processed);

          const mostRecent = processed.reduce<string | null>((latest, current) => {
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
