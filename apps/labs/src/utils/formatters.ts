export function formatCurrency(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "N/A";

  const num = Number(value);
  if (Number.isNaN(num)) return "N/A";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "N/A";

  const num = Number(value);
  if (Number.isNaN(num)) return "N/A";

  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatCompactCurrency(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "N/A";

  const num = Number(value);
  if (Number.isNaN(num)) return "N/A";

  if (num >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(2)}B`;
  }
  if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(2)}M`;
  }
  if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(2)}K`;
  }
  return formatCurrency(num);
}

export function formatRelativeTime(timestamp?: string | Date | null) {
  if (!timestamp) return "Unknown";

  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();

  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`;
  }
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  }
  if (diffDays < 7) {
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
  }

  return then.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function getPartyColor(party?: string | null) {
  if (!party) return "#7F8FA4";

  const normalized = party.toUpperCase();
  if (normalized.includes("DEMOCRAT") || normalized === "DEM") return "#5B8AEF";
  if (normalized.includes("REPUBLICAN") || normalized === "REP") return "#E06A6A";
  if (normalized.includes("INDEPENDENT") || normalized === "IND") return "#F4B400";
  if (normalized.includes("LIBERTARIAN") || normalized === "LIB") return "#F59E0B";
  if (normalized.includes("GREEN") || normalized === "GRE") return "#10B981";

  return "#7F8FA4";
}
