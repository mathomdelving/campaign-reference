import { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';

/**
 * Hook to fetch quarterly financial data for one or more candidates
 * @param {string|string[]} candidateIds - Single candidate ID or array of IDs
 * @param {number} cycle - Election cycle (default 2026)
 * @returns {object} { data, loading, error }
 */
export function useQuarterlyData(candidateIds, cycle = 2026) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Convert candidateIds array to stable string for dependency comparison
  const candidateIdsKey = Array.isArray(candidateIds)
    ? candidateIds.sort().join(',')
    : String(candidateIds);

  useEffect(() => {
    async function fetchQuarterlyData() {
      try {
        setLoading(true);
        setError(null);

        // Convert single ID to array
        const ids = Array.isArray(candidateIds) ? candidateIds : [candidateIds];

        // Filter out empty/null IDs
        const validIds = ids.filter(id => id);

        if (validIds.length === 0) {
          setData([]);
          setLoading(false);
          return;
        }

        const { data: results, error: queryError } = await supabase
          .from('quarterly_financials')
          .select('*')
          .in('candidate_id', validIds)
          .eq('cycle', cycle)
          .order('coverage_end_date', { ascending: true });

        if (queryError) throw queryError;

        // Process and format data
        const processedData = results.map(q => ({
          candidateId: q.candidate_id,
          candidateName: q.name,
          party: q.party,
          state: q.state,
          district: q.district,
          reportType: q.report_type,
          coverageStart: q.coverage_start_date,
          coverageEnd: q.coverage_end_date,
          receipts: q.total_receipts || 0,
          disbursements: q.total_disbursements || 0,
          cashBeginning: q.cash_beginning || 0,
          cashEnding: q.cash_ending || 0,
          // Quarter label for chart (e.g., "Q3 2025")
          quarterLabel: formatQuarterLabel(q.coverage_end_date, q.report_type)
        }));

        setData(processedData);
      } catch (err) {
        console.error('Error fetching quarterly data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchQuarterlyData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateIdsKey, cycle]);

  return { data, loading, error };
}

/**
 * Helper function to format quarter label
 */
function formatQuarterLabel(coverageEndDate, reportType) {
  if (!coverageEndDate) return reportType || 'Unknown';

  const date = new Date(coverageEndDate);
  const month = date.getMonth() + 1; // 0-indexed
  const year = date.getFullYear();

  let quarter = '';
  if (month <= 3) quarter = 'Q1';
  else if (month <= 6) quarter = 'Q2';
  else if (month <= 9) quarter = 'Q3';
  else quarter = 'Q4';

  return `${quarter} ${year}`;
}
