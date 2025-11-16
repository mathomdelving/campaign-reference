-- Enable Row Level Security on all tables
-- This prevents unauthorized modification while allowing public read access

-- Enable RLS on existing tables only
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE quarterly_financials ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_refresh_log ENABLE ROW LEVEL SECURITY;

-- Create policies: Allow public READ access, but only service role can WRITE

-- Candidates table
DROP POLICY IF EXISTS "Allow public read access" ON candidates;
CREATE POLICY "Allow public read access" ON candidates
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow service role full access" ON candidates;
CREATE POLICY "Allow service role full access" ON candidates
  FOR ALL USING (auth.role() = 'service_role');

-- Financial Summary table
DROP POLICY IF EXISTS "Allow public read access" ON financial_summary;
CREATE POLICY "Allow public read access" ON financial_summary
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow service role full access" ON financial_summary;
CREATE POLICY "Allow service role full access" ON financial_summary
  FOR ALL USING (auth.role() = 'service_role');

-- Quarterly Financials table
DROP POLICY IF EXISTS "Allow public read access" ON quarterly_financials;
CREATE POLICY "Allow public read access" ON quarterly_financials
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow service role full access" ON quarterly_financials;
CREATE POLICY "Allow service role full access" ON quarterly_financials
  FOR ALL USING (auth.role() = 'service_role');

-- Data Refresh Log (admin only - no public read)
DROP POLICY IF EXISTS "Allow service role full access" ON data_refresh_log;
CREATE POLICY "Allow service role full access" ON data_refresh_log
  FOR ALL USING (auth.role() = 'service_role');

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
