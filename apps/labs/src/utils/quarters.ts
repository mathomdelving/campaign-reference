export function formatQuarterLabel(coverageEndDate: string | Date, reportType?: string | null): string {
  const date = new Date(coverageEndDate);
  if (Number.isNaN(date.valueOf())) {
    return "Unknown";
  }

  const month = date.getUTCMonth(); // 0-indexed
  const year = date.getUTCFullYear();
  const day = date.getUTCDate();
  const quarter = Math.floor(month / 3) + 1;

  // If no report type, default to standard quarter
  if (!reportType) {
    return `Q${quarter} ${year}`;
  }

  const reportTypeUpper = reportType.toUpperCase();

  // Check if this is a standard quarterly report
  const isQuarterly =
    reportTypeUpper.includes('QUARTERLY') ||
    reportTypeUpper === 'Q1' ||
    reportTypeUpper === 'Q2' ||
    reportTypeUpper === 'Q3' ||
    reportTypeUpper === 'Q4';

  if (isQuarterly) {
    return `Q${quarter} ${year}`;
  }

  // For special filings, use the report type name with date for sorting
  // Format: "PRE-GENERAL Q4 2022.10.19" - readable name with sortable date
  const monthPadded = String(month + 1).padStart(2, '0');
  const dayPadded = String(day).padStart(2, '0');

  // Shorten common report type names for display
  let displayName = reportType;
  if (reportTypeUpper.includes('PRE-')) displayName = reportType;
  else if (reportTypeUpper.includes('POST-')) displayName = reportType;
  else if (reportTypeUpper === 'YEAR-END') displayName = 'Year-End';

  return `${displayName} Q${quarter} ${year}.${monthPadded}.${dayPadded}`;
}

export function getDisplayLabel(quarterLabel: string): string {
  // Strip date suffix for special filings to create clean tooltip labels
  // "PRE-RUN-OFF Q4 2022.11.16" → "PRE-RUN-OFF"
  // "Q4 2022" → "Q4 2022" (unchanged)

  // If label starts with Q, it's a standard quarter - return as-is
  if (quarterLabel.match(/^Q[1-4]/)) {
    return quarterLabel;
  }

  // For special filings, extract just the report type name before " Q"
  const match = quarterLabel.match(/^(.+?)\s+Q[1-4]/);
  if (match) {
    return match[1];
  }

  return quarterLabel;
}

export function sortQuarterLabels(a: string, b: string) {
  // Match standard quarters: "Q1 2022"
  // Or special filings: "PRE-GENERAL Q4 2022.10.19", "Year-End Q4 2022.12.31"
  // Extract: Q#, year, optional month, optional day
  const matchA = a.match(/Q([1-4])\s+(\d{4})(?:\.(\d{2})\.(\d{2}))?/i);
  const matchB = b.match(/Q([1-4])\s+(\d{4})(?:\.(\d{2})\.(\d{2}))?/i);

  if (!matchA || !matchB) return a.localeCompare(b);

  const [, qa, ya, ma = '00', da = '00'] = matchA; // Default to start of period if no date
  const [, qb, yb, mb = '00', db = '00'] = matchB;

  // First compare years
  if (ya !== yb) {
    return Number(ya) - Number(yb);
  }

  // Then quarters
  if (qa !== qb) {
    return Number(qa) - Number(qb);
  }

  // Then months (if special filings)
  if (ma !== mb) {
    return Number(ma) - Number(mb);
  }

  // Finally days (if special filings)
  return Number(da) - Number(db);
}
