import { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';

export function useCandidateData(filters) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // REVERSED APPROACH: Start with financial_summary (2,880 records)
        // Fetch ALL using pagination to overcome 1000 row limit

        const financials = [];
        let from = 0;
        const PAGE_SIZE = 1000;
        let hasMore = true;

        console.log('🔍 Fetching ALL financial records with pagination...');

        while (hasMore) {
          const { data: page, error: financialsError } = await supabase
            .from('financial_summary')
            .select('candidate_id, total_receipts, total_disbursements, cash_on_hand, updated_at')
            .eq('cycle', filters.cycle)
            .range(from, from + PAGE_SIZE - 1);

          if (financialsError) throw financialsError;

          if (page && page.length > 0) {
            financials.push(...page);
            console.log(`🔍 Fetched financial page: ${from}-${from + page.length} (total: ${financials.length})`);
            from += PAGE_SIZE;
            hasMore = page.length === PAGE_SIZE;
          } else {
            hasMore = false;
          }
        }

        console.log(`🔍 Total financial records loaded: ${financials.length}`);

        // Deduplicate by candidate_id - keep the most recent record for each candidate
        const financialsMap = {};
        financials.forEach(fin => {
          const existing = financialsMap[fin.candidate_id];
          if (!existing || new Date(fin.updated_at) > new Date(existing.updated_at)) {
            financialsMap[fin.candidate_id] = fin;
          }
        });

        const uniqueFinancials = Object.values(financialsMap);
        console.log(`🔍 After deduplication: ${uniqueFinancials.length} unique candidates`);

        // Get candidate IDs that have financial data
        const candidateIds = uniqueFinancials.map(f => f.candidate_id);
        console.log(`🔍 Total candidate IDs to fetch: ${candidateIds.length}`);

        // Fetch candidates in batches to avoid query parameter limits
        // Split into chunks of 500 IDs per query
        const BATCH_SIZE = 500;
        const candidates = [];
        const totalBatches = Math.ceil(candidateIds.length / BATCH_SIZE);
        console.log(`🔍 Will fetch in ${totalBatches} batches of ${BATCH_SIZE}`);

        for (let i = 0; i < candidateIds.length; i += BATCH_SIZE) {
          const batchIds = candidateIds.slice(i, i + BATCH_SIZE);

          let candidatesQuery = supabase
            .from('candidates')
            .select('candidate_id, name, party, state, district, office, cycle')
            .eq('cycle', filters.cycle)
            .in('candidate_id', batchIds)
            .range(0, BATCH_SIZE - 1); // Add range to override default 1000 limit

          // Apply chamber filter
          if (filters.chamber === 'H') {
            candidatesQuery = candidatesQuery.eq('office', 'H');
          } else if (filters.chamber === 'S') {
            candidatesQuery = candidatesQuery.eq('office', 'S');
          }

          // Apply state filter
          if (filters.state !== 'all') {
            candidatesQuery = candidatesQuery.eq('state', filters.state);
          }

          // Apply district filter
          if (filters.district !== 'all' && filters.chamber === 'H') {
            candidatesQuery = candidatesQuery.eq('district', filters.district);
          }

          // Apply candidate filter
          if (filters.candidates.length > 0) {
            candidatesQuery = candidatesQuery.in('candidate_id', filters.candidates);
          }

          const { data: batchCandidates, error: candidatesError } = await candidatesQuery;
          if (candidatesError) throw candidatesError;

          console.log(`🔍 Batch ${Math.floor(i / BATCH_SIZE) + 1}/${totalBatches}: Fetched ${batchCandidates?.length || 0} candidates`);
          candidates.push(...batchCandidates);
        }

        console.log(`🔍 Total candidates fetched: ${candidates.length}`);

        // Join candidates with their financial data (using the deduplicated financialsMap)
        const processedData = candidates.map(candidate => {
          const financial = financialsMap[candidate.candidate_id];
          return {
            ...candidate,
            totalReceipts: financial.total_receipts || 0,
            totalDisbursements: financial.total_disbursements || 0,
            cashOnHand: financial.cash_on_hand || 0,
            updatedAt: financial.updated_at
          };
        });

        setData(processedData);

        // Get most recent update timestamp
        if (processedData.length > 0) {
          const mostRecent = processedData.reduce((latest, current) => {
            return new Date(current.updatedAt) > new Date(latest.updatedAt) ? current : latest;
          });
          setLastUpdated(mostRecent.updatedAt);
        }

      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [filters]);

  return { data, loading, error, lastUpdated };
}