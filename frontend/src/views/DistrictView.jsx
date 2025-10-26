import { useState, useEffect, useMemo } from 'react';
import { supabase } from '../utils/supabaseClient';
import { useQuarterlyData } from '../hooks/useQuarterlyData';
import { QuarterlyChart } from '../components/QuarterlyChart';
import { StateToggle } from '../components/StateToggle';
import { DistrictToggle } from '../components/DistrictToggle';
import { getPartyColor, formatCurrency, formatCompactCurrency } from '../utils/formatters';

export default function DistrictView() {
  const [state, setState] = useState('all');
  const [chamber, setChamber] = useState('H');
  const [district, setDistrict] = useState('all');
  const [selectedMetric, setSelectedMetric] = useState('receipts');
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [partyFilter, setPartyFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch candidates for the selected district
  useEffect(() => {
    async function fetchCandidates() {
      // Don't fetch if state or district is not selected
      if (state === 'all' || district === 'all') {
        setCandidates([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Query candidates table directly with joins
        let query = supabase
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
              cash_on_hand
            )
          `)
          .eq('cycle', 2026)
          .eq('state', state);

        // Add office-specific filters
        if (chamber === 'H') {
          query = query.eq('office', 'H').eq('district', district);
        } else if (chamber === 'S') {
          query = query.eq('office', 'S');
        }

        const { data, error: queryError } = await query;

        if (queryError) throw queryError;

        // Filter by Senate class if applicable
        let filteredData = data;
        if (chamber === 'S' && district !== 'all') {
          // Map district value (Senate class) to candidate_id pattern
          const classToChar = {
            'I': '4',
            'II': '0',
            'III': '6',
            'Special': '8'
          };
          const classChar = classToChar[district];

          if (classChar) {
            filteredData = data.filter(c => c.candidate_id.charAt(1) === classChar);
          }
        }

        // Flatten the data structure
        const flattenedData = filteredData.map(c => ({
          candidate_id: c.candidate_id,
          name: c.name,
          party: c.party,
          state: c.state,
          district: c.district,
          office: c.office,
          totalRaised: c.financial_summary[0]?.total_receipts || 0,
          totalDisbursed: c.financial_summary[0]?.total_disbursements || 0,
          cashOnHand: c.financial_summary[0]?.cash_on_hand || 0
        }));

        setCandidates(flattenedData);
      } catch (err) {
        console.error('Error fetching candidates:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchCandidates();
  }, [state, chamber, district]);

  // Memoize candidate IDs to prevent infinite re-renders
  const candidateIdsToFetch = useMemo(() => {
    if (selectedCandidateIds.length > 0) {
      return selectedCandidateIds;
    }
    return candidates.map(c => c.candidate_id);
  }, [selectedCandidateIds, candidates]);

  // Fetch quarterly data for selected candidates
  const { data: quarterlyData, loading: quarterlyLoading } = useQuarterlyData(candidateIdsToFetch);

  // Auto-select all candidates when district changes
  const handleDistrictChange = (newDistrict) => {
    setDistrict(newDistrict);
    setSelectedCandidateIds([]); // Reset selection
  };

  const handleStateChange = (newState) => {
    setState(newState);
    setDistrict('all'); // Reset district when state changes
    setSelectedCandidateIds([]);
  };

  const handleChamberChange = (newChamber) => {
    setChamber(newChamber);
    setDistrict('all'); // Reset district when chamber changes
    setSelectedCandidateIds([]);
  };

  // Toggle candidate selection
  const toggleCandidate = (candidateId) => {
    if (selectedCandidateIds.includes(candidateId)) {
      setSelectedCandidateIds(selectedCandidateIds.filter(id => id !== candidateId));
    } else {
      setSelectedCandidateIds([...selectedCandidateIds, candidateId]);
    }
  };

  // Filter candidates by party
  const filteredCandidates = candidates.filter(c => {
    if (partyFilter === 'all') return true;
    if (partyFilter === 'democrat') return c.party?.toLowerCase().includes('democratic');
    if (partyFilter === 'republican') return c.party?.toLowerCase().includes('republican');
    if (partyFilter === 'third-party') {
      const party = c.party?.toLowerCase() || '';
      return !party.includes('democratic') && !party.includes('republican');
    }
    return true;
  });

  // Sort candidates by current metric value (highest to lowest)
  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    let aValue = 0;
    let bValue = 0;

    switch (selectedMetric) {
      case 'receipts':
        aValue = a.totalRaised || 0;
        bValue = b.totalRaised || 0;
        break;
      case 'disbursements':
        aValue = a.totalDisbursed || 0;
        bValue = b.totalDisbursed || 0;
        break;
      case 'cashOnHand':
        aValue = a.cashOnHand || 0;
        bValue = b.cashOnHand || 0;
        break;
    }

    return bValue - aValue; // Descending order
  });

  // Get selected candidate objects for the chart
  const selectedCandidates = selectedCandidateIds.length > 0
    ? sortedCandidates.filter(c => selectedCandidateIds.includes(c.candidate_id))
    : sortedCandidates;

  const showChart = state !== 'all' && district !== 'all' && candidates.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-rb-navy border-b border-rb-blue shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div>
            <h1 className="text-3xl font-bold text-white">
              District Race View
            </h1>
            <p className="mt-1 text-sm text-gray-300">
              Compare all candidates within a single district across quarters
            </p>
          </div>
        </div>
      </header>

      {/* Selectors */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-6">
            <StateToggle
              value={state}
              onChange={handleStateChange}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chamber
              </label>
              <select
                value={chamber}
                onChange={(e) => handleChamberChange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-rb-red"
              >
                <option value="H">House</option>
                <option value="S">Senate</option>
              </select>
            </div>

            <DistrictToggle
              value={district}
              onChange={handleDistrictChange}
              state={state}
              chamber={chamber}
            />

            {showChart && (
              <div className="ml-auto">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metric
                </label>
                <select
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-rb-red"
                >
                  <option value="receipts">Total Raised</option>
                  <option value="disbursements">Total Spent</option>
                  <option value="cashOnHand">Cash on Hand</option>
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="inline-flex items-center gap-3 text-gray-600">
              <svg className="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-lg">Loading candidates...</span>
            </div>
          </div>
        ) : error ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-red-600">
              <p>Error: {error}</p>
            </div>
          </div>
        ) : !showChart ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="h-24 w-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Select a District</h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Choose a state and district above to see all candidates in that race and compare their quarterly fundraising trends.
            </p>
          </div>
        ) : candidates.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="h-24 w-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Candidates Found</h2>
            <p className="text-gray-600 max-w-md mx-auto">
              No candidates with financial data found for {state} {chamber === 'H' ? `District ${district}` : `Senate Class ${district}`}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Candidate Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Candidates in {state} {chamber === 'H' ? `District ${district}` : `Senate Class ${district}`} ({sortedCandidates.length})
                </h3>

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
              </div>

              {/* Ranked Candidate List */}
              <div className="space-y-2">
                {sortedCandidates.map((candidate, index) => {
                  const isSelected = selectedCandidateIds.length === 0 || selectedCandidateIds.includes(candidate.candidate_id);

                  let metricValue = 0;
                  switch (selectedMetric) {
                    case 'receipts':
                      metricValue = candidate.totalRaised || 0;
                      break;
                    case 'disbursements':
                      metricValue = candidate.totalDisbursed || 0;
                      break;
                    case 'cashOnHand':
                      metricValue = candidate.cashOnHand || 0;
                      break;
                  }

                  return (
                    <label
                      key={candidate.candidate_id}
                      className="flex items-center gap-3 p-3 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleCandidate(candidate.candidate_id)}
                        className="h-4 w-4 text-rb-red focus:ring-rb-red border-gray-300 rounded"
                      />

                      {/* Rank Number */}
                      <div className="flex-shrink-0 w-8 text-center">
                        <span className="text-sm font-bold text-gray-600">
                          {index + 1}.
                        </span>
                      </div>

                      {/* Party Color Dot */}
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getPartyColor(candidate.party) }}
                      ></div>

                      {/* Candidate Info */}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-gray-900">
                          {candidate.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {candidate.party?.split(' ')[0]}
                        </div>
                      </div>

                      {/* Metric Value */}
                      <div className="text-right flex-shrink-0">
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCompactCurrency(metricValue)}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>

              <div className="mt-4 text-sm text-gray-600">
                {selectedCandidateIds.length === 0 ? (
                  <p>All candidates selected</p>
                ) : (
                  <p>{selectedCandidateIds.length} of {sortedCandidates.length} candidates selected</p>
                )}
              </div>
            </div>

            {/* Quarterly Chart */}
            <div className="bg-white rounded-lg shadow">
              <QuarterlyChart
                data={quarterlyData}
                selectedCandidates={selectedCandidates}
                metric={selectedMetric}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
