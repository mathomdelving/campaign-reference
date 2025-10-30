import { useState, useEffect, useMemo } from 'react';
import { supabase } from '../utils/supabaseClient';
import { useQuarterlyData } from '../hooks/useQuarterlyData';
import { QuarterlyChart } from '../components/QuarterlyChart';
import { MetricToggle } from '../components/MetricToggle';
import { DataFreshnessIndicator } from '../components/DataFreshnessIndicator';
import { FollowButton } from '../components/follow/FollowButton';
import { getPartyColor, formatCompactCurrency, formatCandidateName } from '../utils/formatters';

export default function CandidateView() {
  const [searchTerm, setSearchTerm] = useState('');
  const [allCandidates, setAllCandidates] = useState([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [metrics, setMetrics] = useState({
    totalRaised: true,
    totalDisbursed: false,
    cashOnHand: false
  });
  const [partyFilter, setPartyFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Update metric
  const updateMetric = (metricKey, isChecked) => {
    setMetrics(prev => ({
      ...prev,
      [metricKey]: isChecked
    }));
  };

  // Fetch all candidates on mount
  useEffect(() => {
    async function fetchCandidates() {
      setLoading(true);
      try {
        let allData = [];
        let from = 0;
        const batchSize = 1000;
        let hasMore = true;

        // Fetch in batches to get all candidates
        while (hasMore) {
          const { data, error } = await supabase
            .from('candidates')
            .select(`
              candidate_id,
              name,
              party,
              state,
              district,
              office,
              financial_summary!inner (
                total_receipts,
                total_disbursements,
                cash_on_hand,
                updated_at
              )
            `)
            .eq('cycle', 2026)
            .range(from, from + batchSize - 1);

          if (error) throw error;

          if (data && data.length > 0) {
            allData = [...allData, ...data];
            from += batchSize;
            hasMore = data.length === batchSize;
          } else {
            hasMore = false;
          }
        }

        console.log(`Loaded ${allData.length} candidates`);

        // Flatten the data structure
        const flattenedData = allData.map(c => ({
          candidate_id: c.candidate_id,
          name: c.name,
          formattedName: formatCandidateName(c.name),
          party: c.party,
          state: c.state,
          district: c.district,
          office: c.office,
          totalRaised: c.financial_summary[0]?.total_receipts || 0,
          totalDisbursed: c.financial_summary[0]?.total_disbursements || 0,
          cashOnHand: c.financial_summary[0]?.cash_on_hand || 0,
          updatedAt: c.financial_summary[0]?.updated_at
        }));

        setAllCandidates(flattenedData);

        // Get most recent update timestamp
        if (flattenedData.length > 0) {
          const mostRecent = flattenedData.reduce((latest, current) => {
            if (!latest.updatedAt) return current;
            if (!current.updatedAt) return latest;
            return new Date(current.updatedAt) > new Date(latest.updatedAt) ? current : latest;
          });
          setLastUpdated(mostRecent.updatedAt);
        }
      } catch (err) {
        console.error('Error fetching candidates:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchCandidates();
  }, []);

  // Filter candidates by search term and party
  const filteredCandidates = allCandidates.filter(c => {
    // Search filter - check both original name and formatted name
    const searchLower = searchTerm.toLowerCase().trim();

    // Split search into words for multi-word matching
    const searchWords = searchLower.split(/\s+/);
    const nameLower = c.name.toLowerCase();
    const formattedNameLower = c.formattedName.toLowerCase();
    const stateLower = c.state.toLowerCase();

    // If all search words appear in either name format or state, it's a match
    const matchesSearch = searchWords.every(word =>
      nameLower.includes(word) ||
      formattedNameLower.includes(word) ||
      stateLower.includes(word)
    );

    // Party filter
    let matchesParty = true;
    if (partyFilter === 'democrat') {
      matchesParty = c.party?.toLowerCase().includes('democratic');
    } else if (partyFilter === 'republican') {
      matchesParty = c.party?.toLowerCase().includes('republican');
    } else if (partyFilter === 'third-party') {
      const party = c.party?.toLowerCase() || '';
      matchesParty = !party.includes('democratic') && !party.includes('republican');
    }

    return matchesSearch && matchesParty;
  });

  // Get selected candidates
  const selectedCandidates = allCandidates.filter(c =>
    selectedCandidateIds.includes(c.candidate_id)
  );

  // Get the first selected metric for sorting (default to totalRaised)
  const primaryMetric = metrics.totalRaised ? 'totalRaised' :
                       metrics.totalDisbursed ? 'totalDisbursed' :
                       metrics.cashOnHand ? 'cashOnHand' : 'totalRaised';

  // Sort selected candidates by primary metric
  const sortedSelectedCandidates = [...selectedCandidates].sort((a, b) => {
    const aValue = a[primaryMetric] || 0;
    const bValue = b[primaryMetric] || 0;
    return bValue - aValue; // Descending order
  });

  // Memoize candidate IDs for quarterly data fetch
  const candidateIdsToFetch = useMemo(() => {
    return selectedCandidateIds;
  }, [selectedCandidateIds]);

  // Fetch quarterly data for selected candidates
  const { data: quarterlyData, loading: quarterlyLoading } = useQuarterlyData(candidateIdsToFetch);

  // Toggle candidate selection
  const toggleCandidate = (candidateId) => {
    if (selectedCandidateIds.includes(candidateId)) {
      setSelectedCandidateIds(selectedCandidateIds.filter(id => id !== candidateId));
    } else {
      setSelectedCandidateIds([...selectedCandidateIds, candidateId]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-rb-navy border-b border-rb-blue shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">
                By Candidate
              </h1>
              <p className="mt-1 text-sm text-gray-300">
                Search and compare candidates across all races
              </p>
            </div>
            <DataFreshnessIndicator lastUpdated={lastUpdated} loading={loading} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col gap-4">
            {/* Search Bar */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Candidates
              </label>
              <input
                type="text"
                placeholder="Search by name or state..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rb-red"
              />
            </div>

            {/* Filters Row */}
            <div className="flex items-center justify-between">
              {/* Party Filter Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => setPartyFilter('all')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    partyFilter === 'all'
                      ? 'bg-rb-navy text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setPartyFilter('democrat')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    partyFilter === 'democrat'
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                  }`}
                >
                  Democrats
                </button>
                <button
                  onClick={() => setPartyFilter('republican')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    partyFilter === 'republican'
                      ? 'bg-red-600 text-white'
                      : 'bg-red-50 text-red-700 hover:bg-red-100'
                  }`}
                >
                  Republicans
                </button>
                <button
                  onClick={() => setPartyFilter('third-party')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    partyFilter === 'third-party'
                      ? 'bg-green-600 text-white'
                      : 'bg-green-50 text-green-700 hover:bg-green-100'
                  }`}
                >
                  Third Party
                </button>
              </div>

              {/* Metric Selector */}
              {selectedCandidateIds.length > 0 && (
                <MetricToggle
                  metrics={metrics}
                  onChange={updateMetric}
                />
              )}
            </div>
          </div>

          {/* Search Results */}
          {searchTerm && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">
                {filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? 's' : ''} found
              </p>
              <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
                {filteredCandidates.slice(0, 50).map((candidate) => (
                  <button
                    key={candidate.candidate_id}
                    onClick={() => toggleCandidate(candidate.candidate_id)}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors ${
                      selectedCandidateIds.includes(candidate.candidate_id) ? 'bg-red-50' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getPartyColor(candidate.party) }}
                      ></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">
                          {candidate.formattedName}
                        </div>
                        <div className="text-xs text-gray-500">
                          {candidate.state} {candidate.office === 'H' ? `District ${candidate.district}` : 'Senate'} • {candidate.party?.split(' ')[0]}
                        </div>
                      </div>
                      {selectedCandidateIds.includes(candidate.candidate_id) && (
                        <svg className="h-5 w-5 text-rb-red" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Selected Candidates Display */}
        {selectedCandidateIds.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="h-24 w-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Search for Candidates</h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Use the search bar above to find candidates by name or state, then click to add them to your comparison.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Selected Candidates List */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Selected Candidates ({sortedSelectedCandidates.length})
              </h3>

              {/* Ranked Candidate List */}
              <div className="space-y-2">
                {sortedSelectedCandidates.map((candidate, index) => {
                  return (
                    <div
                      key={candidate.candidate_id}
                      className="flex items-center gap-3 p-3 border rounded-md"
                    >
                      <div className="flex items-center gap-3">
                        {/* Rank Number */}
                        <div className="flex-shrink-0 w-8 text-center flex items-center justify-center">
                          <span className="text-sm font-bold text-gray-600">
                            {index + 1}.
                          </span>
                        </div>

                        {/* Party Color Dot */}
                        <div className="flex items-center justify-center flex-shrink-0">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getPartyColor(candidate.party) }}
                          ></div>
                        </div>

                        {/* Follow Button */}
                        <div className="flex items-center justify-center flex-shrink-0">
                          <FollowButton
                            candidateId={candidate.candidate_id}
                            candidateName={candidate.name}
                            party={candidate.party}
                            office={candidate.office}
                            state={candidate.state}
                            district={candidate.district}
                            size="sm"
                          />
                        </div>
                      </div>

                      {/* Candidate Info */}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-gray-900">
                          {candidate.formattedName}
                        </div>
                        <div className="text-xs text-gray-500">
                          {candidate.state} {candidate.office === 'H' ? `District ${candidate.district}` : 'Senate'} • {candidate.party?.split(' ')[0]}
                        </div>
                      </div>

                      {/* Metric Values */}
                      <div className="text-right flex-shrink-0 space-y-1">
                        {metrics.totalRaised && (
                          <div className="text-xs text-gray-600">
                            Raised: <span className="font-semibold text-gray-900">{formatCompactCurrency(candidate.totalRaised || 0)}</span>
                          </div>
                        )}
                        {metrics.totalDisbursed && (
                          <div className="text-xs text-gray-600">
                            Spent: <span className="font-semibold text-gray-900">{formatCompactCurrency(candidate.totalDisbursed || 0)}</span>
                          </div>
                        )}
                        {metrics.cashOnHand && (
                          <div className="text-xs text-gray-600">
                            Cash: <span className="font-semibold text-gray-900">{formatCompactCurrency(candidate.cashOnHand || 0)}</span>
                          </div>
                        )}
                      </div>

                      {/* Remove Button */}
                      <button
                        onClick={() => toggleCandidate(candidate.candidate_id)}
                        className="flex-shrink-0 text-red-600 hover:text-red-800 transition-colors"
                      >
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Quarterly Charts - one for each selected metric */}
            {metrics.totalRaised && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={sortedSelectedCandidates}
                  metric="receipts"
                />
              </div>
            )}
            {metrics.totalDisbursed && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={sortedSelectedCandidates}
                  metric="disbursements"
                />
              </div>
            )}
            {metrics.cashOnHand && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={sortedSelectedCandidates}
                  metric="cashOnHand"
                />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
