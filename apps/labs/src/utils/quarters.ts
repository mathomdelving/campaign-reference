export function formatQuarterLabel(coverageEndDate: string | Date): string {
  const date = new Date(coverageEndDate);
  if (Number.isNaN(date.valueOf())) {
    return "Unknown";
  }

  const month = date.getUTCMonth(); // 0-indexed
  const year = date.getUTCFullYear();

  const quarter = Math.floor(month / 3) + 1;
  return `Q${quarter} ${year}`;
}

export function sortQuarterLabels(a: string, b: string) {
  const matchA = a.match(/^Q([1-4])\s+(\d{4})$/i);
  const matchB = b.match(/^Q([1-4])\s+(\d{4})$/i);

  if (!matchA || !matchB) return a.localeCompare(b);

  const [, qa, ya] = matchA;
  const [, qb, yb] = matchB;

  if (ya === yb) {
    return Number(qa) - Number(qb);
  }

  return Number(ya) - Number(yb);
}
