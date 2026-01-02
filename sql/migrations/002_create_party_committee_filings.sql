-- Create party_committee_filings table for DCCC, DSCC, NRCC, NRSC monthly filings
-- These are party committees that file monthly (Form F3X), not quarterly like candidates

CREATE TABLE IF NOT EXISTS party_committee_filings (
  id SERIAL PRIMARY KEY,

  -- Committee identification
  committee_id VARCHAR(9) NOT NULL,
  committee_name VARCHAR(10) NOT NULL,        -- 'DCCC', 'DSCC', 'NRCC', 'NRSC'
  committee_full_name TEXT,                   -- Full name
  party VARCHAR(10) NOT NULL,                 -- 'DEM' or 'REP'
  chamber VARCHAR(10) NOT NULL,               -- 'house' or 'senate'
  cycle INTEGER NOT NULL,

  -- Report identification
  report_type VARCHAR(10),                    -- 'M1', 'M2', etc. or 'YE', '12G'
  report_type_full VARCHAR(100),              -- 'JANUARY MONTHLY', 'YEAR-END', etc.

  -- Period coverage
  coverage_start_date DATE,
  coverage_end_date DATE NOT NULL,

  -- Financial data for THIS PERIOD ONLY (not cumulative)
  total_receipts DECIMAL(15,2) DEFAULT 0,
  total_disbursements DECIMAL(15,2) DEFAULT 0,
  cash_on_hand_beginning DECIMAL(15,2) DEFAULT 0,
  cash_on_hand_end DECIMAL(15,2) DEFAULT 0,
  debts_owed DECIMAL(15,2) DEFAULT 0,

  -- Breakdown (optional)
  individual_contributions DECIMAL(15,2) DEFAULT 0,
  other_committee_contributions DECIMAL(15,2) DEFAULT 0,
  independent_expenditures DECIMAL(15,2) DEFAULT 0,
  coordinated_expenditures DECIMAL(15,2) DEFAULT 0,

  -- FEC metadata
  file_number BIGINT,
  receipt_date DATE,
  is_amended BOOLEAN DEFAULT false,
  pdf_url TEXT,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint: One filing per committee, cycle, and coverage end date
  UNIQUE(committee_id, cycle, coverage_end_date, file_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pcf_committee ON party_committee_filings(committee_id);
CREATE INDEX IF NOT EXISTS idx_pcf_cycle ON party_committee_filings(cycle);
CREATE INDEX IF NOT EXISTS idx_pcf_party ON party_committee_filings(party);
CREATE INDEX IF NOT EXISTS idx_pcf_chamber ON party_committee_filings(chamber);
CREATE INDEX IF NOT EXISTS idx_pcf_coverage ON party_committee_filings(coverage_end_date);
CREATE INDEX IF NOT EXISTS idx_pcf_timeseries ON party_committee_filings(committee_id, cycle, coverage_end_date);

-- Comments
COMMENT ON TABLE party_committee_filings IS 'Monthly FEC filings for major party committees (DCCC, DSCC, NRCC, NRSC)';
COMMENT ON COLUMN party_committee_filings.total_receipts IS 'Money raised during THIS PERIOD only (not cumulative)';
COMMENT ON COLUMN party_committee_filings.total_disbursements IS 'Money spent during THIS PERIOD only (not cumulative)';
COMMENT ON COLUMN party_committee_filings.cash_on_hand_end IS 'Cash on hand at END of this period';
