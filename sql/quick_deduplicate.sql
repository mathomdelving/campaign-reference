-- ==================================================================================
-- FAST DEDUPLICATION FOR quarterly_financials
-- ==================================================================================
-- This SQL script is much faster than API-based deletion
-- Run this directly in your Supabase SQL Editor
-- ==================================================================================

-- STEP 1: Show current state
SELECT
  'Before deduplication' as status,
  COUNT(*) as total_records,
  COUNT(DISTINCT (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date)) as unique_report_periods,
  COUNT(*) - COUNT(DISTINCT (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date)) as duplicates
FROM quarterly_financials;

-- STEP 2: Delete duplicates (keeping most recent per report period)
WITH ranked_filings AS (
  SELECT
    id,
    ROW_NUMBER() OVER (
      PARTITION BY candidate_id, cycle, report_type, coverage_start_date, coverage_end_date
      ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST
    ) as rn
  FROM quarterly_financials
)
DELETE FROM quarterly_financials
WHERE id IN (
  SELECT id FROM ranked_filings WHERE rn > 1
);

-- STEP 3: Show results
SELECT
  'After deduplication' as status,
  COUNT(*) as total_records,
  COUNT(DISTINCT (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date)) as unique_report_periods
FROM quarterly_financials;

-- STEP 4: Add unique constraint to prevent future duplicates
ALTER TABLE quarterly_financials
DROP CONSTRAINT IF EXISTS unique_filing_period;

ALTER TABLE quarterly_financials
ADD CONSTRAINT unique_filing_period
UNIQUE (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date);

-- STEP 5: Create helpful indexes
CREATE INDEX IF NOT EXISTS idx_qf_candidate_cycle
ON quarterly_financials (candidate_id, cycle);

CREATE INDEX IF NOT EXISTS idx_qf_coverage_dates
ON quarterly_financials (cycle, coverage_end_date DESC);

-- STEP 6: Final verification by cycle
SELECT
  cycle,
  COUNT(*) as filings,
  COUNT(DISTINCT candidate_id) as unique_candidates,
  SUM(total_receipts)::BIGINT as total_raised,
  SUM(total_disbursements)::BIGINT as total_spent
FROM quarterly_financials
GROUP BY cycle
ORDER BY cycle DESC;
