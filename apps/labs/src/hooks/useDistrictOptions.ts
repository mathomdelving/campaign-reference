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
            .select("district")
            .eq("cycle", cycle)
            .eq("state", state)
            .eq("office", "H")
            .not("district", "is", null);

          if (queryError) throw queryError;

          const unique = Array.from(
            new Set((data ?? []).map((row) => row.district))
          )
            .filter((value): value is string => Boolean(value))
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
            .select("candidate_id")
            .eq("cycle", cycle)
            .eq("state", state)
            .eq("office", "S");

          if (queryError) throw queryError;

          const classMap: Record<string, string> = {
            "0": "Class II",
            "4": "Class I",
            "6": "Class III",
            "8": "Special",
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
