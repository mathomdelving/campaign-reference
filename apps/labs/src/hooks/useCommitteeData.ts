'use client';

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { toCommitteeSeries, type CommitteeSeriesDatum } from "@/utils/toCommitteeSeries";
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

const COMMITTEE_IDS = {
  dccc: "C00000935",
  dscc: "C00042366",
  nrcc: "C00075820",
  nrsc: "C00027466",
} as const;

export type CommitteeSlug = keyof typeof COMMITTEE_IDS;

export interface CommitteeSummary {
  slug: CommitteeSlug;
  name: string;
  receipts: number;
  disbursements: number;
  cash: number;
  coverageEnd: string | null;
}

export interface CommitteeDataResult {
  loading: boolean;
  error: string | null;
  series: CommitteeSeriesDatum[];
  summaries: CommitteeSummary[];
}

export function useCommitteeData(metric: "receipts" | "disbursements" | "cashEnding", cycle = 2026): CommitteeDataResult {
  const [series, setSeries] = useState<CommitteeSeriesDatum[]>([]);
  const [summaries, setSummaries] = useState<CommitteeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchCommitteeData() {
      setLoading(true);
      setError(null);

      try {
        const { data, error: queryError } = await browserClient
          .from("quarterly_financials")
          .select(
            "committee_id, committee_name, total_receipts, total_disbursements, cash_ending, coverage_end_date"
          )
          .eq("cycle", cycle)
          .in("committee_id", Object.values(COMMITTEE_IDS));

        if (queryError) throw queryError;

        const normalized =
          data?.map((row) => ({
            committeeId: row.committee_id,
            committeeName: row.committee_name,
            quarterLabel: row.coverage_end_date
              ? formatQuarterLabel(row.coverage_end_date)
              : "Unknown",
            receipts: row.total_receipts,
            disbursements: row.total_disbursements,
            cashEnding: row.cash_ending,
            coverageEnd: row.coverage_end_date,
          })) ?? [];

        const chartSeries = toCommitteeSeries(normalized, metric);

        const latestByCommittee = new Map<CommitteeSlug, CommitteeSummary>();
        for (const row of normalized) {
          const slug = mapCommitteeId(row.committeeId);
          if (!slug) continue;

          const existing = latestByCommittee.get(slug);
          const currentDate = row.coverageEnd ? new Date(row.coverageEnd) : null;
          const existingDate = existing?.coverageEnd ? new Date(existing.coverageEnd) : null;

          if (
            !existingDate ||
            (currentDate && existingDate && currentDate > existingDate)
          ) {
            latestByCommittee.set(slug, {
              slug,
              name: committeeLabel(slug),
              receipts: row.receipts ?? 0,
              disbursements: row.disbursements ?? 0,
              cash: row.cashEnding ?? 0,
              coverageEnd: row.coverageEnd ?? null,
            });
          }
        }

        if (!cancelled) {
          setSeries(chartSeries);
          setSummaries(
            (["dccc", "dscc", "nrcc", "nrsc"] as CommitteeSlug[]).map(
              (slug) =>
                latestByCommittee.get(slug) ?? {
                  slug,
                  name: committeeLabel(slug),
                  receipts: 0,
                  disbursements: 0,
                  cash: 0,
                  coverageEnd: null,
                }
            )
          );
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Unable to load committee data.";
          setError(message);
          setSeries([]);
          setSummaries([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchCommitteeData();

    return () => {
      cancelled = true;
    };
  }, [metric, cycle]);

  return { loading, error, series, summaries };
}

function mapCommitteeId(committeeId?: string | null): CommitteeSlug | null {
  if (!committeeId) return null;
  const entry = Object.entries(COMMITTEE_IDS).find(
    ([, id]) => id === committeeId
  );
  return entry ? (entry[0] as CommitteeSlug) : null;
}

function committeeLabel(slug: CommitteeSlug) {
  switch (slug) {
    case "dccc":
      return "DCCC";
    case "dscc":
      return "DSCC";
    case "nrcc":
      return "NRCC";
    case "nrsc":
      return "NRSC";
    default:
      return slug.toUpperCase();
  }
}
