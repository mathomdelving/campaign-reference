export function formatCurrency(value) {
  if (value === null || value === undefined) return 'N/A';
  
  const num = Number(value);
  if (isNaN(num)) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(num);
}

export function formatNumber(value) {
  if (value === null || value === undefined) return 'N/A';
  
  const num = Number(value);
  if (isNaN(num)) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(num);
}

export function formatCompactCurrency(value) {
  if (value === null || value === undefined) return 'N/A';
  
  const num = Number(value);
  if (isNaN(num)) return 'N/A';
  
  if (num >= 1000000) {
    return `$${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `$${(num / 1000).toFixed(1)}K`;
  }
  return formatCurrency(num);
}

export function formatRelativeTime(timestamp) {
  if (!timestamp) return 'Unknown';
  
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  
  return then.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  });
}

export function getPartyColor(party) {
  if (!party) return '#9CA3AF'; // gray-400

  const partyUpper = party.toUpperCase();
  if (partyUpper.includes('DEMOCRAT')) return '#3B82F6'; // blue-500
  if (partyUpper.includes('REPUBLICAN')) return '#EF4444'; // red-500
  if (partyUpper.includes('INDEPENDENT')) return '#8B5CF6'; // purple-500
  if (partyUpper.includes('LIBERTARIAN')) return '#F59E0B'; // amber-500
  if (partyUpper.includes('GREEN')) return '#10B981'; // green-500

  return '#9CA3AF'; // gray-400 for other/unknown
}

export function formatCandidateName(name) {
  if (!name) return 'Unknown';

  // Handle names in "LAST, FIRST" or "LAST, FIRST MIDDLE" format
  // Convert to "First Middle Last" format

  // Remove any titles or suffixes in parentheses or after periods
  const cleanName = name
    .replace(/\s+(MR\.?|MRS\.?|MS\.?|DR\.?|SEN\.?|REP\.?)(\s|$)/gi, ' ')
    .replace(/\s+(JR\.?|SR\.?|II|III|IV|ESQ\.?)\s*$/gi, '')
    .trim();

  // Check if name contains a comma (indicating "LAST, FIRST" format)
  if (cleanName.includes(',')) {
    const [lastName, firstPart] = cleanName.split(',').map(s => s.trim());

    // Convert to title case
    const toTitleCase = (str) => {
      return str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
    };

    const formattedFirst = toTitleCase(firstPart);
    const formattedLast = toTitleCase(lastName);

    return `${formattedFirst} ${formattedLast}`;
  }

  // If no comma, assume it's already in a reasonable format
  return cleanName;
}