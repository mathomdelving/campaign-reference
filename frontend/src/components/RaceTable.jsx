import { useState, useMemo } from 'react';
import { formatCurrency, getPartyColor } from '../utils/formatters';

export function RaceTable({ data, metrics }) {
  const [sortConfig, setSortConfig] = useState({
    key: 'totalReceipts',
    direction: 'desc'
  });

  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortConfig.key] || 0;
      const bValue = b[sortConfig.key] || 0;

      if (sortConfig.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    return sorted;
  }, [data, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const SortIcon = ({ column }) => {
    if (sortConfig.key !== column) {
      return <span className="text-gray-400">⇅</span>;
    }
    return sortConfig.direction === 'asc' ? <span>↑</span> : <span>↓</span>;
  };

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No data available for the selected filters
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rank
            </th>
            <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Candidate
            </th>
            <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Party
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              State
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              District
            </th>
            {metrics.totalRaised && (
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('totalReceipts')}
              >
                <div className="flex items-center justify-end gap-1">
                  Total Raised
                  <SortIcon column="totalReceipts" />
                </div>
              </th>
            )}
            {metrics.totalDisbursed && (
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('totalDisbursements')}
              >
                <div className="flex items-center justify-end gap-1">
                  Total Disbursed
                  <SortIcon column="totalDisbursements" />
                </div>
              </th>
            )}
            {metrics.cashOnHand && (
              <th
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('cashOnHand')}
              >
                <div className="flex items-center justify-end gap-1">
                  Cash on Hand
                  <SortIcon column="cashOnHand" />
                </div>
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((candidate, index) => (
            <tr key={candidate.candidate_id} className="hover:bg-gray-50">
              <td className="px-2 py-4 whitespace-nowrap">
                <div className="text-sm font-bold text-gray-900">
                  {index + 1}.
                </div>
              </td>
              <td className="px-2 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">
                  {candidate.name}
                </div>
                <div className="text-xs text-gray-500">
                  {candidate.candidate_id}
                </div>
              </td>
              <td className="px-2 py-4 whitespace-nowrap">
                <span
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  style={{
                    backgroundColor: `${getPartyColor(candidate.party)}15`,
                    color: getPartyColor(candidate.party)
                  }}
                >
                  {candidate.party}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {candidate.state}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {candidate.office === 'H' ? candidate.district || 'N/A' : 'SEN'}
              </td>
              {metrics.totalRaised && (
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                  {formatCurrency(candidate.totalReceipts)}
                </td>
              )}
              {metrics.totalDisbursed && (
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                  {formatCurrency(candidate.totalDisbursements)}
                </td>
              )}
              {metrics.cashOnHand && (
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                  {formatCurrency(candidate.cashOnHand)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}