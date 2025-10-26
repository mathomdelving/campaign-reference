import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCompactCurrency, getPartyColor } from '../utils/formatters';

export function RaceChart({ data, metrics }) {
  const chartData = useMemo(() => {
    // Take top 20 candidates by total receipts for readability
    const sorted = [...data]
      .sort((a, b) => (b.totalReceipts || 0) - (a.totalReceipts || 0))
      .slice(0, 20);

    return sorted.map(candidate => ({
      name: candidate.name.split(',').reverse().join(' ').trim(),
      shortName: getShortName(candidate.name),
      party: candidate.party,
      totalRaised: candidate.totalReceipts || 0,
      totalDisbursed: candidate.totalDisbursements || 0,
      cashOnHand: candidate.cashOnHand || 0,
      state: candidate.state,
      district: candidate.district
    }));
  }, [data]);

  function getShortName(fullName) {
    // Convert "LAST, FIRST MIDDLE" to "F. Last"
    const parts = fullName.split(',');
    if (parts.length < 2) return fullName;
    
    const lastName = parts[0].trim();
    const firstName = parts[1].trim().split(' ')[0];
    
    return `${firstName.charAt(0)}. ${lastName.charAt(0) + lastName.slice(1).toLowerCase()}`;
  }

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
        <p className="font-semibold text-gray-900 mb-2">{data.name}</p>
        <p className="text-sm text-gray-600 mb-3">
          {data.party} • {data.state}{data.district ? `-${data.district}` : ''}
        </p>
        <div className="space-y-1">
          {metrics.totalRaised && (
            <div className="flex justify-between gap-4">
              <span className="text-sm text-gray-600">Total Raised:</span>
              <span className="text-sm font-mono font-semibold text-blue-600">
                {formatCompactCurrency(data.totalRaised)}
              </span>
            </div>
          )}
          {metrics.totalDisbursed && (
            <div className="flex justify-between gap-4">
              <span className="text-sm text-gray-600">Total Disbursed:</span>
              <span className="text-sm font-mono font-semibold text-red-600">
                {formatCompactCurrency(data.totalDisbursed)}
              </span>
            </div>
          )}
          {metrics.cashOnHand && (
            <div className="flex justify-between gap-4">
              <span className="text-sm text-gray-600">Cash on Hand:</span>
              <span className="text-sm font-mono font-semibold text-green-600">
                {formatCompactCurrency(data.cashOnHand)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const CustomTick = ({ x, y, payload }) => {
    return (
      <g transform={`translate(${x},${y})`}>
        <text
          x={0}
          y={0}
          dy={16}
          textAnchor="end"
          fill="#666"
          fontSize={12}
          transform="rotate(-45)"
        >
          {payload.value}
        </text>
      </g>
    );
  };

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No data available for the selected filters
      </div>
    );
  }

  // Determine which bars to show based on enabled metrics
  const visibleMetrics = [];
  if (metrics.totalRaised) visibleMetrics.push({ key: 'totalRaised', label: 'Total Raised', color: '#3B82F6' });
  if (metrics.totalDisbursed) visibleMetrics.push({ key: 'totalDisbursed', label: 'Total Disbursed', color: '#EF4444' });
  if (metrics.cashOnHand) visibleMetrics.push({ key: 'cashOnHand', label: 'Cash on Hand', color: '#10B981' });

  return (
    <div className="w-full h-[600px] p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Top 20 Candidates by Total Raised
        </h3>
        <p className="text-sm text-gray-600">
          Showing {Math.min(20, data.length)} of {data.length} candidates
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height="90%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="shortName"
            tick={<CustomTick />}
            interval={0}
            height={100}
          />
          <YAxis
            tickFormatter={(value) => formatCompactCurrency(value)}
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="square"
          />
          
          {visibleMetrics.map(metric => (
            <Bar
              key={metric.key}
              dataKey={metric.key}
              name={metric.label}
              fill={metric.color}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}