import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import { formatCompactCurrency, getPartyColor } from '../utils/formatters';

export function QuarterlyChart({ data, selectedCandidates, metric = 'receipts' }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-12 text-center text-gray-500">
        <p>No quarterly data available</p>
        <p className="text-sm mt-2">Quarterly financial data will be displayed here once loaded</p>
      </div>
    );
  }

  // Group data by quarter across all candidates
  const quarters = [...new Set(data.map(d => d.quarterLabel))].sort();

  // Build chart data with one row per quarter
  const chartData = quarters.map(quarter => {
    const row = { quarter };

    // For each candidate, add their value for this quarter
    selectedCandidates.forEach(candidate => {
      const candidateData = data.find(d =>
        d.candidateId === candidate.candidate_id && d.quarterLabel === quarter
      );

      let value = 0;
      if (candidateData) {
        switch (metric) {
          case 'receipts':
            value = candidateData.receipts;
            break;
          case 'disbursements':
            value = candidateData.disbursements;
            break;
          case 'cashOnHand':
            value = candidateData.cashEnding;
            break;
          default:
            value = candidateData.receipts;
        }
      }

      row[candidate.candidate_id] = value;
    });

    return row;
  });

  // Generate colors for each candidate
  const candidateColors = selectedCandidates.map(c => ({
    id: c.candidate_id,
    color: getPartyColor(c.party)
  }));

  const metricLabel = {
    receipts: 'Total Raised',
    disbursements: 'Total Spent',
    cashOnHand: 'Cash on Hand'
  }[metric];

  return (
    <div className="p-6 relative">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Quarterly Trend: {metricLabel}
        </h3>
        <p className="text-sm text-gray-600">
          Comparing {selectedCandidates.length} candidate{selectedCandidates.length !== 1 ? 's' : ''} across {quarters.length} quarters
        </p>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 60, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="quarter"
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          {/* Left Y-axis */}
          <YAxis
            yAxisId="left"
            orientation="left"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => formatCompactCurrency(value)}
          />
          {/* Right Y-axis */}
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => formatCompactCurrency(value)}
          />

          {candidateColors.map(({ id, color }) => (
            <Line
              key={id}
              type="monotone"
              dataKey={id}
              yAxisId="left"
              stroke={color}
              strokeWidth={2.5}
              dot={{ fill: color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
