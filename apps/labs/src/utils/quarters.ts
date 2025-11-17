export function formatQuarterLabel(coverageEndDate: string | Date, reportType?: string | null): string {
  const date = new Date(coverageEndDate);
  if (Number.isNaN(date.valueOf())) {
    return "Unknown";
  }

  const month = date.getUTCMonth(); // 0-indexed
  const year = date.getUTCFullYear();
  const day = date.getUTCDate();

  // Check if this is a special filing type (non-quarterly)
  // Special filings should plot as unique datapoints between quarters
  const specialFilingTypes = [
    'PRE-PRIMARY', '12P', '30P',
    'PRE-GENERAL', '12G', '30G',
    'PRE-RUN-OFF', '12R', '30R',
    'POST-RUN-OFF', 'POST-GENERAL', 'POST-ELECTION',
    'POST-SPECIAL'
  ];

  const isSpecialFiling = reportType && specialFilingTypes.some(
    type => reportType.toUpperCase().includes(type.replace('-', ''))
  );

  if (isSpecialFiling) {
    // For special filings, create a unique label with the actual date
    // Format: "Q3 2025" becomes "Q3 2025.10.19" for a filing ending Oct 19
    // This allows chronological sorting while keeping quarter context
    const quarter = Math.floor(month / 3) + 1;
    // Pad month and day to ensure proper sorting
    const monthPadded = String(month + 1).padStart(2, '0');
    const dayPadded = String(day).padStart(2, '0');
    return `Q${quarter} ${year}.${monthPadded}.${dayPadded}`;
  }

  // Standard quarterly filings use simple quarter labels
  const quarter = Math.floor(month / 3) + 1;
  return `Q${quarter} ${year}`;
}

export function sortQuarterLabels(a: string, b: string) {
  // Match standard quarters: "Q1 2022" or special filings: "Q4 2022.10.19"
  const matchA = a.match(/^Q([1-4])\s+(\d{4})(?:\.(\d{2})\.(\d{2}))?$/i);
  const matchB = b.match(/^Q([1-4])\s+(\d{4})(?:\.(\d{2})\.(\d{2}))?$/i);

  if (!matchA || !matchB) return a.localeCompare(b);

  const [, qa, ya, ma = '99', da = '99'] = matchA; // Default to end of period if no date
  const [, qb, yb, mb = '99', db = '99'] = matchB;

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
