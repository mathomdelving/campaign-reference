export function MetricToggle({ metrics, onChange }) {
  const metricOptions = [
    { key: 'totalRaised', label: 'Total Raised' },
    { key: 'totalDisbursed', label: 'Total Disbursed' },
    { key: 'cashOnHand', label: 'Cash on Hand' }
  ];

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">
        Metrics
      </label>
      <div className="flex gap-4 h-[42px] items-center">
        {metricOptions.map(option => (
          <label key={option.key} className="flex items-center gap-2 cursor-pointer whitespace-nowrap">
            <input
              type="checkbox"
              checked={metrics[option.key]}
              onChange={(e) => onChange(option.key, e.target.checked)}
              className="w-4 h-4 text-rb-red border-gray-300 rounded focus:ring-2 focus:ring-rb-red"
            />
            <span className="text-sm text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}