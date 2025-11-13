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
          // For Senate, show all classes available for this state
          // Each state has exactly 2 Senate seats in different classes
          const stateClasses: Record<string, string[]> = {
            AL: ["II", "III"], AK: ["II", "III"], AZ: ["I", "III"], AR: ["II", "III"],
            CA: ["I", "III"], CO: ["II", "III"], CT: ["I", "III"], DE: ["I", "II"],
            FL: ["I", "III"], GA: ["II", "III"], HI: ["I", "III"], ID: ["II", "III"],
            IL: ["II", "III"], IN: ["I", "III"], IA: ["II", "III"], KS: ["II", "III"],
            KY: ["II", "III"], LA: ["II", "III"], ME: ["I", "II"], MD: ["I", "III"],
            MA: ["I", "II"], MI: ["I", "II"], MN: ["I", "II"], MS: ["I", "II"],
            MO: ["I", "III"], MT: ["I", "II"], NE: ["I", "II"], NV: ["I", "III"],
            NH: ["II", "III"], NJ: ["I", "II"], NM: ["I", "II"], NY: ["I", "III"],
            NC: ["II", "III"], ND: ["I", "III"], OH: ["I", "III"], OK: ["II", "III"],
            OR: ["II", "III"], PA: ["I", "III"], RI: ["I", "II"], SC: ["II", "III"],
            SD: ["II", "III"], TN: ["I", "II"], TX: ["I", "II"], UT: ["I", "III"],
            VT: ["I", "III"], VA: ["I", "II"], WA: ["I", "III"], WV: ["I", "II"],
            WI: ["I", "III"], WY: ["I", "II"],
          };

          const classes = stateClasses[state] || [];

          if (!cancelled) {
            const options = classes
              .sort()  // Sort I, II, III
              .map((classValue) => ({
                value: classValue,
                label: `Class ${classValue}`,
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
