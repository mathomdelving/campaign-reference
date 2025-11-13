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
          .eq("state", state);

        // Filter financial_summary by cycle using the correct syntax
        query = query.filter("financial_summary.cycle", "eq", cycle);

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
            name: formatCandidateName(candidate.name),
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
          // State-based Senate class mapping
          // Each state has two Senate seats in different classes
          // Source: https://www.senate.gov/senators/ (as of 2024)
          const stateClassMap: Record<string, Record<string, string>> = {
            AL: { "II": "Class II", "III": "Class III" },
            AK: { "II": "Class II", "III": "Class III" },
            AZ: { "I": "Class I", "III": "Class III" },
            AR: { "II": "Class II", "III": "Class III" },
            CA: { "I": "Class I", "III": "Class III" },
            CO: { "II": "Class II", "III": "Class III" },
            CT: { "I": "Class I", "III": "Class III" },
            DE: { "I": "Class I", "II": "Class II" },
            FL: { "I": "Class I", "III": "Class III" },
            GA: { "II": "Class II", "III": "Class III" },
            HI: { "I": "Class I", "III": "Class III" },
            ID: { "II": "Class II", "III": "Class III" },
            IL: { "II": "Class II", "III": "Class III" },
            IN: { "I": "Class I", "III": "Class III" },
            IA: { "II": "Class II", "III": "Class III" },
            KS: { "II": "Class II", "III": "Class III" },
            KY: { "II": "Class II", "III": "Class III" },
            LA: { "II": "Class II", "III": "Class III" },
            ME: { "I": "Class I", "II": "Class II" },
            MD: { "I": "Class I", "III": "Class III" },
            MA: { "I": "Class I", "II": "Class II" },
            MI: { "I": "Class I", "II": "Class II" },
            MN: { "I": "Class I", "II": "Class II" },
            MS: { "I": "Class I", "II": "Class II" },
            MO: { "I": "Class I", "III": "Class III" },
            MT: { "I": "Class I", "II": "Class II" },
            NE: { "I": "Class I", "II": "Class II" },
            NV: { "I": "Class I", "III": "Class III" },
            NH: { "II": "Class II", "III": "Class III" },
            NJ: { "I": "Class I", "II": "Class II" },
            NM: { "I": "Class I", "II": "Class II" },
            NY: { "I": "Class I", "III": "Class III" },
            NC: { "II": "Class II", "III": "Class III" },
            ND: { "I": "Class I", "III": "Class III" },
            OH: { "I": "Class I", "III": "Class III" },
            OK: { "II": "Class II", "III": "Class III" },
            OR: { "II": "Class II", "III": "Class III" },
            PA: { "I": "Class I", "III": "Class III" },
            RI: { "I": "Class I", "II": "Class II" },
            SC: { "II": "Class II", "III": "Class III" },
            SD: { "II": "Class II", "III": "Class III" },
            TN: { "I": "Class I", "II": "Class II" },
            TX: { "I": "Class I", "II": "Class II" },
            UT: { "I": "Class I", "III": "Class III" },
            VT: { "I": "Class I", "III": "Class III" },
            VA: { "I": "Class I", "II": "Class II" },
            WA: { "I": "Class I", "III": "Class III" },
            WV: { "I": "Class I", "II": "Class II" },
            WI: { "I": "Class I", "III": "Class III" },
            WY: { "I": "Class I", "II": "Class II" },
          };

          // Filter candidates by Senate class based on their state
          if (district !== "Special") {
            flattened = flattened.filter((candidate) => {
              const candidateState = candidate.state;
              if (!candidateState) return false;

              const stateClasses = stateClassMap[candidateState];
              if (!stateClasses) return false;

              // Check if this state has the selected class
              return Object.keys(stateClasses).includes(district);
            });
          }
        }

        // Deduplicate candidates with same name (House-to-Senate switchers)
        // Prioritize Senate over House
        const deduplicatedByName = new Map<string, DistrictCandidate>();
        flattened.forEach((candidate) => {
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
            else if (candidate.office === existing.office && candidate.totalRaised > existing.totalRaised) {
              deduplicatedByName.set(key, candidate);
            }
          }
        });

        flattened = Array.from(deduplicatedByName.values());
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
