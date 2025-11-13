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

export interface DistrictOption {
  value: string;
  label: string;
}

// Maximum number of congressional districts per state (as of 2024)
const STATE_DISTRICT_COUNT: Record<string, number> = {
  AL: 7, AK: 1, AZ: 9, AR: 4, CA: 52, CO: 8, CT: 5, DE: 1,
  FL: 28, GA: 14, HI: 2, ID: 2, IL: 17, IN: 9, IA: 4, KS: 4,
  KY: 6, LA: 6, ME: 2, MD: 8, MA: 9, MI: 13, MN: 8, MS: 4,
  MO: 8, MT: 2, NE: 3, NV: 4, NH: 2, NJ: 12, NM: 3, NY: 26,
  NC: 14, ND: 1, OH: 15, OK: 5, OR: 6, PA: 17, RI: 2, SC: 7,
  SD: 1, TN: 9, TX: 38, UT: 4, VT: 1, VA: 11, WA: 10, WV: 2,
  WI: 8, WY: 1, DC: 0
};

export function useDistrictOptions(
  state: string,
  chamber: ChamberFilter,
  cycle: number
) {
  const [districts, setDistricts] = useState<DistrictOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const key = useMemo(() => `${state}-${chamber}-${cycle}`, [state, chamber, cycle]);

  useEffect(() => {
    if (state === "all") {
      setDistricts([]);
      return;
    }

    let cancelled = false;

    async function fetchOptions() {
      setLoading(true);
      setError(null);

      try {
        if (chamber === "H") {
          const { data, error: queryError } = await browserClient
            .from("candidates")
            .select("district, financial_summary!inner(cycle)")
            .filter("financial_summary.cycle", "eq", cycle)
            .eq("state", state)
            .eq("office", "H")
            .not("district", "is", null);

          if (queryError) throw queryError;

          const maxDistricts = STATE_DISTRICT_COUNT[state] || 0;

          const unique = Array.from(
            new Set((data ?? []).map((row) => row.district))
          )
            .filter((value): value is string => {
              if (!value) return false;
              const districtNum = Number(value);
              // Include "00" for at-large districts, or valid numbered districts within range
              return value === "00" || value === "0" || (districtNum > 0 && districtNum <= maxDistricts);
            })
            .sort((a, b) => Number(a) - Number(b));

          if (!cancelled) {
            const options: DistrictOption[] = unique.map((districtValue) => {
              const normalized =
                districtValue === "00" || districtValue === "0"
                  ? "At Large"
                  : `District ${districtValue}`;

              return {
                value: districtValue,
                label: normalized,
              };
            });

            setDistricts(options);
          }
        } else if (chamber === "S") {
          const { data, error: queryError } = await browserClient
            .from("candidates")
            .select("candidate_id, financial_summary!inner(cycle)")
            .filter("financial_summary.cycle", "eq", cycle)
            .eq("state", state)
            .eq("office", "S");

          if (queryError) throw queryError;

          const classMap: Record<string, string> = {
            "0": "Class II",   // 2020 election
            "2": "Class III",  // 2022 election
            "4": "Class I",    // 2024 election
            "6": "Class II",   // 2026 election
            "8": "Class III",  // 2028 election (or Special elections)
          };

          const uniqueClasses = Array.from(
            new Set(
              (data ?? []).map((row) => {
                const char = row.candidate_id?.charAt(1) ?? "";
                return classMap[char];
              })
            )
          ).filter((value): value is string => Boolean(value));

          if (!cancelled) {
            const options = uniqueClasses.map((label) => ({
              value: label.replace("Class ", ""),
              label,
            }));
            setDistricts(options);
          }
        } else {
          setDistricts([]);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Unable to load district options.";
          setError(message);
          setDistricts([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchOptions();

    return () => {
      cancelled = true;
    };
  }, [key, state, chamber, cycle]);

  return { districts, loading, error };
}
