-- ==================================================================================
-- DEDUPLICATION AND UNIQUE CONSTRAINT FOR quarterly_financials
-- ==================================================================================
--
-- This script:
-- 1. Removes duplicate filings (keeping most recent per report period)
-- 2. Adds a unique constraint to prevent future duplicates
--
-- A "duplicate" is defined as same candidate + report period
-- We keep the most recent filing (by updated_at, then created_at)
-- ==================================================================================

-- Step 1: Create a backup table (optional but recommended)
-- CREATE TABLE quarterly_financials_backup AS SELECT * FROM quarterly_financials;

-- Step 2: Identify and delete duplicates
-- Keep only the most recent filing for each unique report period
WITH ranked_filings AS (
  SELECT
    id,
    ROW_NUMBER() OVER (
      PARTITION BY candidate_id, cycle, report_type, coverage_start_date, coverage_end_date
      ORDER BY updated_at DESC, created_at DESC
    ) as rn
  FROM quarterly_financials
),
duplicates_to_delete AS (
  SELECT id FROM ranked_filings WHERE rn > 1
)
DELETE FROM quarterly_financials
WHERE id IN (SELECT id FROM duplicates_to_delete);

-- Step 3: Add unique constraint to prevent future duplicates
-- This ensures each candidate can only have ONE filing per report period
ALTER TABLE quarterly_financials
ADD CONSTRAINT unique_filing_period
UNIQUE (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date);

-- Step 4: Create an index for faster queries
CREATE INDEX IF NOT EXISTS idx_quarterly_financials_lookup
ON quarterly_financials (candidate_id, cycle, coverage_end_date DESC);

-- Step 5: Verify the results
SELECT
  'Total records after deduplication' as metric,
  COUNT(*) as value
FROM quarterly_financials
UNION ALL
SELECT
  'Records by cycle' as metric,
  cycle || ': ' || COUNT(*)::text as value
FROM quarterly_financials
GROUP BY cycle
ORDER BY value DESC;
