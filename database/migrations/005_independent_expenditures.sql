-- Migration: Independent Expenditures Table
-- Description: Creates table for storing FEC independent expenditure data
-- Created: 2026-01-02

-- Create independent_expenditures table
CREATE TABLE IF NOT EXISTS independent_expenditures (
  id SERIAL PRIMARY KEY,

  -- FEC identifiers
  spender_committee_id VARCHAR(9) NOT NULL,
  spender_committee_name VARCHAR(255),
  candidate_id VARCHAR(9),
  candidate_name VARCHAR(255),

  -- Expenditure details
  support_oppose VARCHAR(1) NOT NULL,  -- 'S' (support) or 'O' (oppose)
  amount DECIMAL(15,2) NOT NULL,
  expenditure_date DATE,
  dissemination_date DATE,
  purpose TEXT,
  payee_name TEXT,

  -- Election context
  cycle INTEGER NOT NULL,
  office VARCHAR(1),  -- H/S/P
  state VARCHAR(2),
  district VARCHAR(2),

  -- Filing metadata
  filing_id BIGINT,
  transaction_id TEXT,
  receipt_date DATE,
  is_amendment BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Prevent duplicate entries
  UNIQUE(spender_committee_id, candidate_id, transaction_id, amount)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ie_candidate ON independent_expenditures(candidate_id);
CREATE INDEX IF NOT EXISTS idx_ie_cycle ON independent_expenditures(cycle);
CREATE INDEX IF NOT EXISTS idx_ie_date ON independent_expenditures(expenditure_date DESC);
CREATE INDEX IF NOT EXISTS idx_ie_receipt_date ON independent_expenditures(receipt_date DESC);
CREATE INDEX IF NOT EXISTS idx_ie_spender ON independent_expenditures(spender_committee_id);
CREATE INDEX IF NOT EXISTS idx_ie_support_oppose ON independent_expenditures(candidate_id, support_oppose);

-- Comments for documentation
COMMENT ON TABLE independent_expenditures IS 'FEC Schedule E independent expenditure data - spending for/against candidates by outside groups';
COMMENT ON COLUMN independent_expenditures.spender_committee_id IS 'FEC committee ID of the entity making the expenditure (Super PAC, 501c4, etc.)';
COMMENT ON COLUMN independent_expenditures.candidate_id IS 'FEC candidate ID being targeted by the expenditure';
COMMENT ON COLUMN independent_expenditures.support_oppose IS 'S = Support, O = Oppose';
COMMENT ON COLUMN independent_expenditures.amount IS 'Dollar amount of the expenditure';
COMMENT ON COLUMN independent_expenditures.dissemination_date IS 'Date the communication was publicly distributed';
COMMENT ON COLUMN independent_expenditures.transaction_id IS 'Unique FEC transaction identifier';
