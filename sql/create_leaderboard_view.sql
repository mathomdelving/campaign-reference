-- ============================================================================
-- LEADERBOARD DATA VIEW
-- ============================================================================
-- Purpose: Pre-joined "prep station" for fast leaderboard loading
-- Combines: candidates + political_persons + financial_summary
-- Benefits: 1 query instead of 30+, loads in <1 second instead of 10+ seconds
--
-- Usage in code:
--   Instead of: browserClient.from("candidates").select(...)
--                  .then fetch financial_summary
--                  .then fetch political_persons
--   Use: browserClient.from("leaderboard_data").select(...)
--
-- Created: 2025-11-18
-- ============================================================================

CREATE OR REPLACE VIEW leaderboard_data AS
SELECT
  -- Candidate identifiers
  c.candidate_id,
  c.person_id,

  -- Display name (prefer political_persons, fallback to candidate name)
  COALESCE(p.display_name, c.name) as display_name,

  -- Candidate metadata
  c.party,
  c.state,
  c.district,
  c.office,

  -- Financial data
  f.cycle,
  f.total_receipts,
  f.total_disbursements,
  f.cash_on_hand,
  f.updated_at,

  -- Original candidate name (for debugging/fallback)
  c.name as candidate_name_raw

FROM candidates c

-- LEFT JOIN ensures we show candidates even without a political person
LEFT JOIN political_persons p
  ON c.person_id = p.person_id

-- LEFT JOIN ensures we show candidates even without financial data
LEFT JOIN financial_summary f
  ON c.candidate_id = f.candidate_id

-- Optional: Add index hint for common query patterns
-- WHERE clauses in hooks will filter by:
--   - f.cycle (2022, 2024, 2026)
--   - c.office (H or S)
--   - c.state (two-letter code)
--   - c.district (for House races)
;

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================
-- This view is NOT materialized, meaning it computes results on every query.
-- For even better performance, consider a materialized view:
--
-- CREATE MATERIALIZED VIEW leaderboard_data_materialized AS ...
-- REFRESH MATERIALIZED VIEW leaderboard_data_materialized;
--
-- Trade-offs:
--   Regular View: Always up-to-date, slightly slower
--   Materialized View: Super fast, needs manual refresh after data updates
--
-- For now, regular view is fine. Upgrade to materialized if needed later.
-- ============================================================================

-- Grant access to the view (adjust role as needed)
-- GRANT SELECT ON leaderboard_data TO anon;
-- GRANT SELECT ON leaderboard_data TO authenticated;
