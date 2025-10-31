type FinancialMetric = "receipts" | "disbursements" | "cashEnding";

export interface QuarterlyCommitteeRecord {
  committeeId?: string | null;
  committeeName?: string | null;
  quarterLabel: string;
  receipts?: number | null;
  disbursements?: number | null;
  cashEnding?: number | null;
}

export type CommitteeSlug = "dccc" | "dscc" | "nrcc" | "nrsc";

export interface CommitteeSeriesDatum {
  quarter: string;
  dccc: number;
  dscc: number;
  nrcc: number;
  nrsc: number;
}

const COMMITTEE_ALIASES: Record<
  CommitteeSlug,
  { ids: string[]; keywords: string[] }
> = {
  dccc: {
    ids: ["C00000935"],
    keywords: ["DEMOCRATIC CONGRESSIONAL CAMPAIGN COMMITTEE", "DCCC"],
  },
  dscc: {
    ids: ["C00042366"],
    keywords: ["DEMOCRATIC SENATORIAL CAMPAIGN COMMITTEE", "DSCC"],
  },
  nrcc: {
    ids: ["C00075820"],
    keywords: ["NATIONAL REPUBLICAN CONGRESSIONAL COMMITTEE", "NRCC"],
  },
  nrsc: {
    ids: ["C00027466"],
    keywords: ["NATIONAL REPUBLICAN SENATORIAL COMMITTEE", "NRSC"],
  },
};

const SLUGS: CommitteeSlug[] = ["dccc", "dscc", "nrcc", "nrsc"];

function parseQuarterLabel(quarter: string): [number, number] {
  const match = quarter.match(/^Q([1-4])\s+(\d{4})$/i);
  if (!match) {
    return [0, 0];
  }
  const [, q, year] = match;
  return [Number(year), Number(q)];
}

function matchCommitteeSlug(record: QuarterlyCommitteeRecord): CommitteeSlug | null {
  const byId = (record.committeeId || "").toUpperCase();
  const byName = (record.committeeName || "").toUpperCase();

  for (const slug of SLUGS) {
    const { ids, keywords } = COMMITTEE_ALIASES[slug];
    if (ids.includes(byId)) return slug;
    if (keywords.some((keyword) => byName.includes(keyword))) return slug;
  }

  return null;
}

function getMetricValue(record: QuarterlyCommitteeRecord, metric: FinancialMetric) {
  const value = record[metric];
  return typeof value === "number" ? value : 0;
}

export function toCommitteeSeries(
  records: QuarterlyCommitteeRecord[],
  metric: FinancialMetric = "receipts"
): CommitteeSeriesDatum[] {
  const grouped = new Map<string, CommitteeSeriesDatum>();

  for (const record of records) {
    const quarter = record.quarterLabel;
    if (!quarter) continue;

    const slug = matchCommitteeSlug(record);
    if (!slug) continue;

    const value = getMetricValue(record, metric);
    const existing = grouped.get(quarter) ?? {
      quarter,
      dccc: 0,
      dscc: 0,
      nrcc: 0,
      nrsc: 0,
    };

    existing[slug] += value;
    grouped.set(quarter, existing);
  }

  return Array.from(grouped.values()).sort((a, b) => {
    const [yearA, quarterA] = parseQuarterLabel(a.quarter);
    const [yearB, quarterB] = parseQuarterLabel(b.quarter);

    if (yearA === yearB) {
      return quarterA - quarterB;
    }
    return yearA - yearB;
  });
}
