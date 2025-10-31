type FinancialMetric = "receipts" | "disbursements" | "cashEnding";

export interface QuarterlyCandidateRecord {
  quarterLabel: string;
  party?: string | null;
  receipts?: number | null;
  disbursements?: number | null;
  cashEnding?: number | null;
}

export interface PartySeriesDatum {
  quarter: string;
  dem: number;
  gop: number;
  ind: number;
}

const PARTY_KEYS = {
  DEM: "dem",
  D: "dem",
  DEMOCRAT: "dem",
  REP: "gop",
  R: "gop",
  GOP: "gop",
  REPUBLICAN: "gop",
  IND: "ind",
  I: "ind",
  INDEPENDENT: "ind",
} as const;

function parseQuarterLabel(quarter: string): [number, number] {
  const match = quarter.match(/^Q([1-4])\s+(\d{4})$/i);
  if (!match) {
    return [0, 0];
  }
  const [, q, year] = match;
  return [Number(year), Number(q)];
}

function getMetricValue(record: QuarterlyCandidateRecord, metric: FinancialMetric) {
  const value = record[metric];
  return typeof value === "number" ? value : 0;
}

export function toPartySeries(
  records: QuarterlyCandidateRecord[],
  metric: FinancialMetric = "receipts"
): PartySeriesDatum[] {
  const grouped = new Map<string, PartySeriesDatum>();

  for (const record of records) {
    const quarter = record.quarterLabel;
    if (!quarter) continue;

    const normalizedParty = (record.party || "").trim().toUpperCase();
    const key = (PARTY_KEYS as Record<string, keyof PartySeriesDatum | undefined>)[normalizedParty];
    if (!key) continue;

    const value = getMetricValue(record, metric);
    const existing = grouped.get(quarter) ?? {
      quarter,
      dem: 0,
      gop: 0,
      ind: 0,
    };

    existing[key] += value;
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
