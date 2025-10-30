import { useState, useEffect, useMemo } from 'react';
import { supabase } from '../utils/supabaseClient';
import { useAuth } from '../contexts/AuthContext';
import { useQuarterlyData } from '../hooks/useQuarterlyData';
import { QuarterlyChart } from '../components/QuarterlyChart';
import { StateToggle } from '../components/StateToggle';
import { DistrictToggle } from '../components/DistrictToggle';
import { MetricToggle } from '../components/MetricToggle';
import { DataFreshnessIndicator } from '../components/DataFreshnessIndicator';
import { FollowButton } from '../components/follow/FollowButton';
import { getPartyColor, formatCurrency, formatCompactCurrency } from '../utils/formatters';

// Valid district counts per state (as of 2022 redistricting)
const VALID_DISTRICT_COUNTS = {
  'AL': 7, 'AK': 1, 'AZ': 9, 'AR': 4, 'CA': 52, 'CO': 8, 'CT': 5, 'DE': 1,
  'FL': 28, 'GA': 14, 'HI': 2, 'ID': 2, 'IL': 17, 'IN': 9, 'IA': 4, 'KS': 4,
  'KY': 6, 'LA': 6, 'ME': 2, 'MD': 8, 'MA': 9, 'MI': 13, 'MN': 8, 'MS': 4,
  'MO': 8, 'MT': 2, 'NE': 3, 'NV': 4, 'NH': 2, 'NJ': 12, 'NM': 3, 'NY': 26,
  'NC': 14, 'ND': 1, 'OH': 15, 'OK': 5, 'OR': 6, 'PA': 17, 'RI': 2, 'SC': 7,
  'SD': 1, 'TN': 9, 'TX': 38, 'UT': 4, 'VT': 1, 'VA': 11, 'WA': 10, 'WV': 2,
  'WI': 8, 'WY': 1, 'DC': 0
};

export default function DistrictView() {
  const { user } = useAuth();
  const [state, setState] = useState('all');
  const [chamber, setChamber] = useState('H');
  const [district, setDistrict] = useState('all');
  const [metrics, setMetrics] = useState({
    totalRaised: true,
    totalDisbursed: false,
    cashOnHand: false
  });
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [partyFilter, setPartyFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [watchingAll, setWatchingAll] = useState(false);

  // Update metric
  const updateMetric = (metricKey, isChecked) => {
    setMetrics(prev => ({
      ...prev,
      [metricKey]: isChecked
    }));
  };

  // Helper function to format district display text
  const getDistrictDisplayText = () => {
    if (chamber === 'H') {
      if (district === 'all') {
        return 'House';
      }
      // Check if this is an at-large district (00) or single-district state
      const isSingleDistrict = VALID_DISTRICT_COUNTS[state] === 1;
      const isAtLarge = district === '00' || district === '0' || isSingleDistrict;
      return isAtLarge ? 'At Large' : `District ${district}`;
    } else {
      return district === 'all' ? 'Senate' : `Senate Class ${district}`;
    }
  };

  // Fetch candidates for the selected district
  useEffect(() => {
    async function fetchCandidates() {
      // Don't fetch if state is not selected
      if (state === 'all') {
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
              cash_on_hand,
              updated_at
            )
          `)
          .eq('cycle', 2026)
          .eq('state', state);

        // Add office-specific filters
        if (chamber === 'H') {
          query = query.eq('office', 'H');
          // Only filter by specific district if not "all"
          if (district !== 'all') {
            query = query.eq('district', district);
          }
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
          cashOnHand: c.financial_summary[0]?.cash_on_hand || 0,
          updatedAt: c.financial_summary[0]?.updated_at
        }));

        setCandidates(flattenedData);

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

  // Watch all candidates in the current view
  const handleWatchAll = async () => {
    if (!user) {
      alert('Please sign in to watch candidates');
      return;
    }

    setWatchingAll(true);

    try {
      // Get current follow count
      const { count: currentCount, error: countError } = await supabase
        .from('user_candidate_follows')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id);

      if (countError) throw countError;

      const remainingSlots = 50 - (currentCount || 0);
      const candidatesToWatch = sortedCandidates.slice(0, remainingSlots);

      if (candidatesToWatch.length === 0) {
        alert('You have reached the maximum of 50 followed candidates.');
        setWatchingAll(false);
        return;
      }

      if (candidatesToWatch.length < sortedCandidates.length) {
        if (!confirm(`You can only watch ${candidatesToWatch.length} of ${sortedCandidates.length} candidates due to the 50-candidate limit. Continue?`)) {
          setWatchingAll(false);
          return;
        }
      }

      // Batch insert all candidates
      const followsToInsert = candidatesToWatch.map(candidate => ({
        user_id: user.id,
        candidate_id: candidate.candidate_id,
        candidate_name: candidate.name,
        party: candidate.party,
        office: candidate.office,
        state: candidate.state,
        district: candidate.district,
        notification_enabled: true,
      }));

      const { error } = await supabase
        .from('user_candidate_follows')
        .upsert(followsToInsert, { onConflict: 'user_id,candidate_id', ignoreDuplicates: true });

      if (error) throw error;

      alert(`Successfully watching ${candidatesToWatch.length} candidates!`);
    } catch (error) {
      console.error('Error watching all candidates:', error);
      alert('Failed to watch all candidates. Please try again.');
    } finally {
      setWatchingAll(false);
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

  // Get the first selected metric for sorting (default to totalRaised)
  const primaryMetric = metrics.totalRaised ? 'totalRaised' :
                       metrics.totalDisbursed ? 'totalDisbursed' :
                       metrics.cashOnHand ? 'cashOnHand' : 'totalRaised';

  // Sort candidates by primary metric value (highest to lowest)
  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    const aValue = a[primaryMetric] || 0;
    const bValue = b[primaryMetric] || 0;
    return bValue - aValue; // Descending order
  });

  // Get selected candidate objects for the chart
  const selectedCandidates = selectedCandidateIds.length > 0
    ? sortedCandidates.filter(c => selectedCandidateIds.includes(c.candidate_id))
    : sortedCandidates;

  const showChart = state !== 'all' && candidates.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-rb-navy border-b border-rb-blue shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-baskerville text-white">
                District Race View
              </h1>
              <p className="mt-1 text-sm text-gray-300">
                Compare all candidates within a single district across quarters
              </p>
            </div>
            <DataFreshnessIndicator lastUpdated={lastUpdated} loading={loading} />
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
                <MetricToggle
                  metrics={metrics}
                  onChange={updateMetric}
                />
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
            <h2 className="text-2xl font-bold font-baskerville text-gray-900 mb-2">Select a District</h2>
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
            <h2 className="text-2xl font-bold font-baskerville text-gray-900 mb-2">No Candidates Found</h2>
            <p className="text-gray-600 max-w-md mx-auto">
              No candidates with financial data found for {state} {getDistrictDisplayText()}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Candidate Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Candidates in {state} {getDistrictDisplayText()} ({sortedCandidates.length})
                  </h3>
                  <button
                    onClick={handleWatchAll}
                    disabled={watchingAll || sortedCandidates.length === 0}
                    className="px-3 py-1 text-sm font-medium text-rb-red hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    </svg>
                    {watchingAll ? 'Watching...' : 'Watch all'}
                  </button>
                </div>

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

                  return (
                    <label
                      key={candidate.candidate_id}
                      className="flex items-center gap-3 p-3 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleCandidate(candidate.candidate_id)}
                          className="h-4 w-4 text-rb-red focus:ring-rb-red border-gray-300 rounded"
                        />

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
                        <div className="flex items-center justify-center flex-shrink-0" onClick={(e) => e.preventDefault()}>
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
                          {candidate.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {candidate.party?.split(' ')[0]}
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

            {/* Quarterly Charts - one for each selected metric */}
            {metrics.totalRaised && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={selectedCandidates}
                  metric="receipts"
                />
              </div>
            )}
            {metrics.totalDisbursed && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={selectedCandidates}
                  metric="disbursements"
                />
              </div>
            )}
            {metrics.cashOnHand && (
              <div className="bg-white rounded-lg shadow">
                <QuarterlyChart
                  data={quarterlyData}
                  selectedCandidates={selectedCandidates}
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
