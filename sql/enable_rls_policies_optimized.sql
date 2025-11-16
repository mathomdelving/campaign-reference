-- Optimized Row Level Security policies
-- Fixes performance issues by:
-- 1. Separating policies by action (no overlap between public SELECT and service INSERT/UPDATE/DELETE)
-- 2. Avoiding multiple permissive policies for same role+action

-- Enable RLS on existing tables
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE quarterly_financials ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_refresh_log ENABLE ROW LEVEL SECURITY;

-- Drop old policies
DROP POLICY IF EXISTS "Allow public read access" ON candidates;
DROP POLICY IF EXISTS "Allow service role full access" ON candidates;
DROP POLICY IF EXISTS "Allow public read access" ON financial_summary;
DROP POLICY IF EXISTS "Allow service role full access" ON financial_summary;
DROP POLICY IF EXISTS "Allow public read access" ON quarterly_financials;
DROP POLICY IF EXISTS "Allow service role full access" ON quarterly_financials;
DROP POLICY IF EXISTS "Allow service role full access" ON data_refresh_log;

-- Candidates table - optimized policies
CREATE POLICY "Public read access" ON candidates
  FOR SELECT USING (true);

CREATE POLICY "Service role write access" ON candidates
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role update access" ON candidates
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Service role delete access" ON candidates
  FOR DELETE USING (auth.role() = 'service_role');

-- Financial Summary table - optimized policies
CREATE POLICY "Public read access" ON financial_summary
  FOR SELECT USING (true);

CREATE POLICY "Service role write access" ON financial_summary
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role update access" ON financial_summary
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Service role delete access" ON financial_summary
  FOR DELETE USING (auth.role() = 'service_role');

-- Quarterly Financials table - optimized policies
CREATE POLICY "Public read access" ON quarterly_financials
  FOR SELECT USING (true);

CREATE POLICY "Service role write access" ON quarterly_financials
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role update access" ON quarterly_financials
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Service role delete access" ON quarterly_financials
  FOR DELETE USING (auth.role() = 'service_role');

-- Data Refresh Log - admin only (no public read)
CREATE POLICY "Service role read access" ON data_refresh_log
  FOR SELECT USING (auth.role() = 'service_role');

CREATE POLICY "Service role write access" ON data_refresh_log
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role update access" ON data_refresh_log
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Service role delete access" ON data_refresh_log
  FOR DELETE USING (auth.role() = 'service_role');

-- Verify RLS is enabled
SELECT
  schemaname,
  tablename,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'candidates',
    'financial_summary',
    'quarterly_financials',
    'data_refresh_log'
  )
ORDER BY tablename;
