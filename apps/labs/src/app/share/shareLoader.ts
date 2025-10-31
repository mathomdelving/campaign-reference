import { supabase } from "@/lib/supabaseClient";
import { toPartySeries } from "@/utils/toPartySeries";
import { toCommitteeSeries } from "@/utils/toCommitteeSeries";
import { formatQuarterLabel } from "@/utils/quarters";

export type Scope = "party" | "committee";
export type FinancialMetric = "receipts" | "disbursements" | "cashEnding";

export const METRIC_TITLES: Record<FinancialMetric, string> = {
  receipts: "Fundraising",
  disbursements: "Spending",
  cashEnding: "Cash on Hand",
};

const METRIC_ALIASES: Record<string, FinancialMetric> = {
  receipts: "receipts",
  raised: "receipts",
  fundraising: "receipts",
  disbursements: "disbursements",
  spending: "disbursements",
  spent: "disbursements",
  cash: "cashEnding",
  cashonhand: "cashEnding",
  cashonhandending: "cashEnding",
};

export class ShareNotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ShareNotFoundError";
  }
}

function sanitizeSearchParams(
  searchParams: Record<string, string | string[] | undefined>
) {
  return new URLSearchParams(
    Object.entries(searchParams).reduce<Record<string, string>>(
      (acc, [key, value]) => {
        if (Array.isArray(value)) {
          acc[key] = value.at(-1) ?? "";
        } else if (value) {
          acc[key] = value;
        }
        return acc;
      },
      {}
    )
  );
}

export function resolveMetric(metric?: string | null): FinancialMetric {
  if (!metric) return "receipts";
  const normalized = metric.replace(/[^a-z]/gi, "").toLowerCase();
  return METRIC_ALIASES[normalized] ?? "receipts";
}

export function resolveScope(parts: string[]): Scope {
  const scope = parts[0];
  if (scope === "committee") return "committee";
  return "party";
}

export function resolveCycle(
  parts: string[],
  searchParams: URLSearchParams
): number {
  const direct = searchParams.get("cycle");
  if (direct) {
    const parsed = Number(direct);
    if (!Number.isNaN(parsed)) return parsed;
  }

  const maybeCycle = parts.find((part) => /^\d{4}$/.test(part));
  if (maybeCycle) return Number(maybeCycle);

  return 2026;
}

function formatISODate(input?: string | null): string {
  if (!input) return "Unknown";
  const date = new Date(input);
  if (Number.isNaN(date.valueOf())) return input;
  return date.toISOString().slice(0, 10);
}

type ChartSeries = Array<{ quarter: string } & { [key: string]: number | string }>;

type PartyPayload = {
  scope: "party";
  metric: FinancialMetric;
  cycle: number;
  series: ChartSeries;
  asOfDate: string;
};

type CommitteePayload = {
  scope: "committee";
  metric: FinancialMetric;
  cycle: number;
  series: ChartSeries;
  asOfDate: string;
};

export type SharePayload = PartyPayload | CommitteePayload;

async function loadPartySeries(
  cycle: number,
  metric: FinancialMetric
): Promise<PartyPayload> {
  const { data, error } = await supabase
    .from("quarterly_financials")
    .select(
      "party, total_receipts, total_disbursements, cash_ending, coverage_end_date"
    )
    .eq("cycle", cycle)
    .neq("party", null);

  if (error) {
    throw error;
  }

  let latestCoverage: string | null = null;
  const normalized = (data ?? []).map((row) => {
    if (row.coverage_end_date) {
      if (
        !latestCoverage ||
        new Date(row.coverage_end_date) > new Date(latestCoverage)
      ) {
        latestCoverage = row.coverage_end_date;
      }
    }

    return {
      quarterLabel: row.coverage_end_date
        ? formatQuarterLabel(row.coverage_end_date)
        : "Unknown",
      party: row.party,
      receipts: row.total_receipts,
      disbursements: row.total_disbursements,
      cashEnding: row.cash_ending,
    };
  });

  const series = toPartySeries(normalized, metric).map((row) => ({ ...row })) as ChartSeries;
  if (series.length === 0) {
    console.warn("[labs] No party data returned; using demo fallback series.");
    return {
      scope: "party" as const,
      metric,
      cycle,
      series: [
        { quarter: "Q1 2025", dem: 10.8, gop: 8.2, ind: 6.8 },
        { quarter: "Q2 2025", dem: 11.2, gop: 8.3, ind: 6.7 },
        { quarter: "Q3 2025", dem: 13.1, gop: 9.4, ind: 6.9 },
        { quarter: "Q4 2025", dem: 12.6, gop: 11.2, ind: 7.0 },
        { quarter: "Q1 2026", dem: 12.0, gop: 13.0, ind: 7.2 },
        { quarter: "Q2 2026", dem: 13.7, gop: 16.8, ind: 7.5 },
        { quarter: "Q3 2026", dem: 14.3, gop: 20.5, ind: 8.1 },
      ],
      asOfDate: formatISODate(latestCoverage),
    };
  }

  return {
    scope: "party",
    metric,
    cycle,
    series,
    asOfDate: formatISODate(latestCoverage),
  };
}

async function loadCommitteeSeries(
  cycle: number,
  metric: FinancialMetric
): Promise<CommitteePayload> {
  const committeeIds = [
    "C00000935", // DCCC
    "C00042366", // DSCC
    "C00075820", // NRCC
    "C00027466", // NRSC
  ];

  const { data, error } = await supabase
    .from("quarterly_financials")
    .select(
      "committee_id, total_receipts, total_disbursements, cash_ending, coverage_end_date"
    )
    .eq("cycle", cycle)
    .in("committee_id", committeeIds);

  if (error) {
    throw error;
  }

  let latestCoverage: string | null = null;
  const normalized = (data ?? []).map((row) => {
    if (row.coverage_end_date) {
      if (
        !latestCoverage ||
        new Date(row.coverage_end_date) > new Date(latestCoverage)
      ) {
        latestCoverage = row.coverage_end_date;
      }
    }

    return {
      quarterLabel: row.coverage_end_date
        ? formatQuarterLabel(row.coverage_end_date)
        : "Unknown",
      committeeId: row.committee_id,
      committeeName:
        (row as { committee_name?: string | null }).committee_name ?? null,
      receipts: row.total_receipts,
      disbursements: row.total_disbursements,
      cashEnding: row.cash_ending,
    };
  });

  const series = toCommitteeSeries(normalized, metric).map((row) => ({ ...row })) as ChartSeries;
  if (series.length === 0) {
    console.warn("[labs] No committee data returned; using demo fallback series.");
    return {
      scope: "committee" as const,
      metric,
      cycle,
      series: [
        { quarter: "Q1 2025", dccc: 18.2, dscc: 16.7, nrcc: 14.1, nrsc: 12.4 },
        { quarter: "Q2 2025", dccc: 19.9, dscc: 17.2, nrcc: 15.3, nrsc: 13.1 },
        { quarter: "Q3 2025", dccc: 21.4, dscc: 18.6, nrcc: 17.0, nrsc: 14.5 },
        { quarter: "Q4 2025", dccc: 23.7, dscc: 20.4, nrcc: 19.1, nrsc: 16.3 },
        { quarter: "Q1 2026", dccc: 24.9, dscc: 21.6, nrcc: 21.8, nrsc: 18.7 },
        { quarter: "Q2 2026", dccc: 26.4, dscc: 23.5, nrcc: 24.2, nrsc: 20.4 },
        { quarter: "Q3 2026", dccc: 28.1, dscc: 25.0, nrcc: 26.9, nrsc: 23.1 },
      ],
      asOfDate: formatISODate(latestCoverage),
    };
  }

  return {
    scope: "committee",
    metric,
    cycle,
    series,
    asOfDate: formatISODate(latestCoverage),
  };
}

export async function resolveSharePayload(
  props: {
    params: { slug: string };
    searchParams: Record<string, string | string[] | undefined>;
  },
  override?: { scope?: Scope; metric?: FinancialMetric; cycle?: number }
): Promise<SharePayload> {
  const search = sanitizeSearchParams(props.searchParams);
  const slug = props.params?.slug ?? override?.scope ?? "party";
  const parts = slug.split("-");
  const scope = override?.scope ?? resolveScope(parts);
  const metric =
    override?.metric ?? resolveMetric(search.get("metric") ?? parts[1]);
  const cycle = override?.cycle ?? resolveCycle(parts, search);

  if (scope === "party") {
    const payload = await loadPartySeries(cycle, metric);
    return {
      ...payload,
      asOfDate: search.get("asOf") ?? payload.asOfDate,
    };
  }

  const payload = await loadCommitteeSeries(cycle, metric);
  return {
    ...payload,
    asOfDate: search.get("asOf") ?? payload.asOfDate,
  };
}
