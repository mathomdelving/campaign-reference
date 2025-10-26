-- Create quarterly_financials table for timeseries data
-- This table stores individual quarterly filings for each candidate

CREATE TABLE IF NOT EXISTS quarterly_financials (
  id SERIAL PRIMARY KEY,

  -- Candidate information
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),
  cycle INTEGER NOT NULL,

  -- Quarter identification
  quarter VARCHAR(10),                     -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  report_type VARCHAR(100),                -- 'APRIL QUARTERLY', 'JULY QUARTERLY', 'OCTOBER QUARTERLY', etc.

  -- Period coverage
  coverage_start_date DATE,
  coverage_end_date DATE,

  -- Financial data for THIS QUARTER ONLY (not cumulative)
  total_receipts DECIMAL(15,2),           -- Money raised this quarter
  total_disbursements DECIMAL(15,2),      -- Money spent this quarter
  cash_beginning DECIMAL(15,2),           -- Cash at start of quarter
  cash_ending DECIMAL(15,2),              -- Cash at end of quarter

  -- FEC metadata
  filing_id BIGINT,                       -- FEC file_number
  is_amendment BOOLEAN DEFAULT false,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint: One filing per candidate, cycle, coverage end date, and filing_id
  -- This prevents duplicate filings while allowing amendments
  UNIQUE(candidate_id, cycle, coverage_end_date, filing_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_qf_candidate ON quarterly_financials(candidate_id);
CREATE INDEX IF NOT EXISTS idx_qf_cycle ON quarterly_financials(cycle);
CREATE INDEX IF NOT EXISTS idx_qf_quarter ON quarterly_financials(quarter, report_year);
CREATE INDEX IF NOT EXISTS idx_qf_committee ON quarterly_financials(committee_id);
CREATE INDEX IF NOT EXISTS idx_qf_timeseries ON quarterly_financials(candidate_id, cycle, coverage_end_date);
CREATE INDEX IF NOT EXISTS idx_qf_filing ON quarterly_financials(filing_id);

-- Comment on table
COMMENT ON TABLE quarterly_financials IS 'Individual quarterly FEC filings for timeseries analysis - stores per-quarter financial data for each candidate';
COMMENT ON COLUMN quarterly_financials.quarter IS 'Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)';
COMMENT ON COLUMN quarterly_financials.total_receipts IS 'Money raised during THIS QUARTER only (not cumulative)';
COMMENT ON COLUMN quarterly_financials.total_disbursements IS 'Money spent during THIS QUARTER only (not cumulative)';
COMMENT ON COLUMN quarterly_financials.cash_ending IS 'Cash on hand at END of this quarter';
