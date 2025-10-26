import { formatRelativeTime } from '../utils/formatters';

export function DataFreshnessIndicator({ lastUpdated, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="animate-pulse h-2 w-2 bg-gray-400 rounded-full" />
        Loading...
      </div>
    );
  }

  if (!lastUpdated) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-rb-yellow/20 border-2 border-rb-yellow rounded-md">
      <div className="h-2 w-2 bg-green-500 rounded-full" />
      <span className="text-sm text-white italic font-medium">Last updated: {formatRelativeTime(lastUpdated)}</span>
    </div>
  );
}