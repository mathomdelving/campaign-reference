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

  // Calculate freshness for indicator color
  const now = new Date();
  const then = new Date(lastUpdated);
  const diffHours = Math.floor((now - then) / 3600000);

  // Green: < 24 hours, Yellow: 24-48 hours, Red: > 48 hours
  const indicatorColor = diffHours < 24 ? 'bg-green-500' : diffHours < 48 ? 'bg-yellow-500' : 'bg-red-500';
  const pulseAnimation = diffHours < 2 ? 'animate-pulse' : '';

  // Format exact timestamp for hover tooltip
  const exactTimestamp = then.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short'
  });

  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 bg-rb-yellow/20 border-2 border-rb-yellow rounded-md cursor-help"
      title={`Exact update time: ${exactTimestamp}`}
    >
      <div className={`h-2 w-2 ${indicatorColor} rounded-full ${pulseAnimation}`} />
      <span className="text-sm text-white italic font-medium">
        Data updated: {formatRelativeTime(lastUpdated)}
      </span>
    </div>
  );
}