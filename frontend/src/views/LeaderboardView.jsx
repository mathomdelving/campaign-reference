import { useState, useRef } from 'react';
import { useFilters } from '../hooks/useFilters';
import { useCandidateData } from '../hooks/useCandidateData';
import { ToggleBar } from '../components/ToggleBar';
import { RaceTable } from '../components/RaceTable';
import { RaceChart } from '../components/RaceChart';
import { ExportButton } from '../components/ExportButton';
import { DataFreshnessIndicator } from '../components/DataFreshnessIndicator';
import { exportToCSV, exportChartToPNG, exportTableToPNG } from '../utils/exportUtils';

export default function LeaderboardView() {
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'chart'
  const { filters, updateFilter, updateMetric, resetFilters } = useFilters();
  const { data, loading, error, lastUpdated } = useCandidateData(filters);

  const chartRef = useRef(null);
  const tableRef = useRef(null);

  const handleExport = async (type) => {
    switch (type) {
      case 'csv':
        exportToCSV(data, filters.metrics, filters);
        break;
      case 'chart-png':
        await exportChartToPNG(chartRef, filters);
        break;
      case 'table-png':
        await exportTableToPNG(tableRef, filters);
        break;
      default:
        console.error('Unknown export type:', type);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-rb-navy border-b border-rb-blue shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-baskerville text-white">
                Campaign Finance Leaderboard
              </h1>
              <p className="mt-1 text-sm text-gray-300">
                Top fundraisers across all 2026 races
              </p>
            </div>
            <DataFreshnessIndicator lastUpdated={lastUpdated} loading={loading} />
          </div>
        </div>
      </header>

      {/* Filter Bar */}
      <ToggleBar
        filters={filters}
        updateFilter={updateFilter}
        updateMetric={updateMetric}
        resetFilters={resetFilters}
      />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Controls Bar */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {/* View Toggle */}
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => setViewMode('table')}
                className={`
                  px-4 py-2 text-sm font-medium border rounded-l-md
                  ${viewMode === 'table'
                    ? 'bg-rb-red text-white border-rb-red z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }
                  focus:z-10 focus:outline-none focus:ring-2 focus:ring-rb-red
                `}
              >
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Table
                </div>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('chart')}
                className={`
                  px-4 py-2 text-sm font-medium border rounded-r-md -ml-px
                  ${viewMode === 'chart'
                    ? 'bg-rb-red text-white border-rb-red z-10'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }
                  focus:z-10 focus:outline-none focus:ring-2 focus:ring-rb-red
                `}
              >
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Chart
                </div>
              </button>
            </div>

            {/* Results Count */}
            {!loading && data.length > 0 && (
              <span className="text-sm text-gray-600 ml-4">
                Showing <span className="font-semibold">{data.length}</span> candidate{data.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Export Button */}
          <ExportButton
            data={data}
            metrics={filters.metrics}
            filters={filters}
            chartRef={chartRef}
            tableRef={tableRef}
            onExport={handleExport}
          />
        </div>

        {/* Content Area */}
        <div className="bg-white rounded-lg shadow">
          {error && (
            <div className="p-6 text-center">
              <div className="inline-flex items-center gap-2 text-red-600">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Error loading data: {error}</span>
              </div>
            </div>
          )}

          {loading && !error && (
            <div className="p-12 text-center">
              <div className="inline-flex items-center gap-3 text-gray-600">
                <svg className="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-lg">Loading campaign finance data...</span>
              </div>
            </div>
          )}

          {!loading && !error && (
            <>
              {viewMode === 'table' ? (
                <div ref={tableRef}>
                  <RaceTable data={data} metrics={filters.metrics} />
                </div>
              ) : (
                <div ref={chartRef}>
                  <RaceChart data={data} metrics={filters.metrics} />
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
