# FEC Schema Reference & Field Mappings

**Purpose:** Complete field-by-field mapping between FEC OpenFEC API and our Supabase database schema

**Last Updated:** November 19, 2025
**Database:** PostgreSQL 15 (Supabase)

---

## Table of Contents

1. [Overview](#overview)
2. [Candidates Table](#candidates-table)
3. [Financial Summary Table](#financial-summary-table)
4. [Quarterly Financials Table](#quarterly-financials-table)
5. [Committee Designations Table](#committee-designations-table)
6. [Political Persons Table](#political-persons-table)
7. [Data Type Reference](#data-type-reference)

---

## Overview

### Mapping Philosophy

Our database schema follows these principles:
1. **Normalized** - Candidate info stored once, referenced by foreign keys
2. **Denormalized where needed** - Financial tables include candidate_name for quick queries
3. **FEC-aligned** - Field names match FEC API when possible
4. **Type-safe** - Proper PostgreSQL types (TEXT, BIGINT, NUMERIC, DATE, TIMESTAMP)

### Three-Layer Architecture

```
FEC OpenFEC API
      ↓
Python Collection Scripts (fetch_fec_data.py, incremental_update.py)
      ↓
Supabase PostgreSQL Database (candidates, financial_summary, quarterly_financials)
      ↓
Frontend TypeScript Hooks (useCandidateData, useQuarterlyData)
```

---

## Candidates Table

### Purpose
Store basic candidate registration information from FEC Form 1.

### Source Endpoint
`GET /candidates/` or `GET /candidates/search/`

### Database Schema
```sql
CREATE TABLE candidates (
  -- Primary Key
  candidate_id TEXT PRIMARY KEY,

  -- Basic Info
  name TEXT NOT NULL,
  party TEXT,
  party_full TEXT,

  -- Office Info
  office TEXT NOT NULL,  -- 'H' or 'S'
  state TEXT NOT NULL,
  district TEXT,         -- NULL for Senate

  -- Election Info
  cycle INTEGER NOT NULL,
  election_years INTEGER[],

  -- Status
  candidate_status TEXT,
  incumbent_challenge TEXT,  -- 'I', 'C', or 'O'
  active_through INTEGER,

  -- Address
  address_street_1 TEXT,
  address_street_2 TEXT,
  address_city TEXT,
  address_state TEXT,
  address_zip TEXT,

  -- Flags
  has_raised_funds BOOLEAN DEFAULT FALSE,
  federal_funds_flag BOOLEAN DEFAULT FALSE,

  -- Political Persons Integration
  person_id TEXT REFERENCES political_persons(person_id),

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_candidates_office ON candidates(office);
CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_candidates_person_id ON candidates(person_id);
```

### Field Mappings

| Database Field | FEC API Field | Type | Notes |
|----------------|---------------|------|-------|
| `candidate_id` | `candidate_id` | TEXT | PK, format: H6CA47001 |
| `name` | `name` | TEXT | Format: "LAST, FIRST" |
| `party` | `party` | TEXT | Abbreviated: DEM, REP, LIB, etc. |
| `party_full` | `party_full` | TEXT | Full name: "DEMOCRATIC PARTY" |
| `office` | `office` | TEXT | H, S, or P (we filter P out) |
| `state` | `state` | TEXT | Two-letter code |
| `district` | `district` | TEXT | Two-digit, NULL for Senate |
| `cycle` | `cycles[0]` | INTEGER | Latest cycle candidate is active |
| `election_years` | `election_years` | INTEGER[] | Array of years |
| `candidate_status` | `candidate_status` | TEXT | C (current), F, N, P |
| `incumbent_challenge` | `incumbent_challenge` | TEXT | I, C, or O |
| `active_through` | `active_through` | INTEGER | Latest active cycle |
| `address_street_1` | `address_street_1` | TEXT | Mailing address |
| `address_street_2` | `address_street_2` | TEXT | Apt/Suite |
| `address_city` | `address_city` | TEXT | City |
| `address_state` | `address_state` | TEXT | State |
| `address_zip` | `address_zip` | TEXT | ZIP code |
| `has_raised_funds` | `has_raised_funds` | BOOLEAN | Whether candidate has financial activity |
| `federal_funds_flag` | `federal_funds_flag` | BOOLEAN | Federal matching funds recipient |
| `person_id` | N/A | TEXT | FK to political_persons (our extension) |

### Example API Response → Database Insert

**FEC API Response:**
```json
{
  "candidate_id": "H6CA47001",
  "name": "SMITH, JANE",
  "party": "DEM",
  "party_full": "DEMOCRATIC PARTY",
  "office": "H",
  "state": "CA",
  "district": "47",
  "cycles": [2024, 2026],
  "election_years": [2024, 2026],
  "candidate_status": "C",
  "incumbent_challenge": "I",
  "active_through": 2026,
  "has_raised_funds": true,
  "federal_funds_flag": false
}
```

**Database INSERT:**
```sql
INSERT INTO candidates (
  candidate_id, name, party, party_full, office, state, district,
  cycle, election_years, candidate_status, incumbent_challenge,
  active_through, has_raised_funds, federal_funds_flag
) VALUES (
  'H6CA47001', 'SMITH, JANE', 'DEM', 'DEMOCRATIC PARTY', 'H', 'CA', '47',
  2026, ARRAY[2024, 2026], 'C', 'I',
  2026, TRUE, FALSE
);
```

---

## Financial Summary Table

### Purpose
Store cumulative cycle totals for each candidate (one row per candidate per cycle).

### Source Endpoint
`GET /candidate/{id}/totals/?cycle={cycle}`

### Database Schema
```sql
CREATE TABLE financial_summary (
  -- Composite Primary Key
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  cycle INTEGER NOT NULL,

  -- Denormalized for Quick Queries
  name TEXT,
  office TEXT,
  state TEXT,
  district TEXT,
  party TEXT,

  -- CUMULATIVE Financial Totals
  total_receipts NUMERIC(12, 2) DEFAULT 0,
  total_disbursements NUMERIC(12, 2) DEFAULT 0,
  cash_on_hand NUMERIC(12, 2) DEFAULT 0,
  debts_owed_by_committee NUMERIC(12, 2) DEFAULT 0,

  -- Coverage Dates
  coverage_start_date DATE,
  coverage_end_date DATE,

  -- Latest Report Info
  report_type TEXT,
  report_year INTEGER,

  -- Timestamps
  updated_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),

  PRIMARY KEY (candidate_id, cycle)
);

CREATE INDEX idx_financial_summary_cycle ON financial_summary(cycle);
CREATE INDEX idx_financial_summary_receipts ON financial_summary(total_receipts DESC);
CREATE INDEX idx_financial_summary_state ON financial_summary(state);
```

### Field Mappings

| Database Field | FEC API Field | Type | Notes |
|----------------|---------------|------|-------|
| `candidate_id` | `candidate_id` | TEXT | PK |
| `cycle` | `cycle` | INTEGER | PK |
| `name` | N/A | TEXT | Copied from candidates table |
| `office` | N/A | TEXT | Copied from candidates table |
| `state` | N/A | TEXT | Copied from candidates table |
| `district` | N/A | TEXT | Copied from candidates table |
| `party` | N/A | TEXT | Copied from candidates table |
| `total_receipts` | `receipts` | NUMERIC | **CUMULATIVE** total raised |
| `total_disbursements` | `disbursements` | NUMERIC | **CUMULATIVE** total spent |
| `cash_on_hand` | `cash_on_hand_end_period` | NUMERIC | Latest cash balance |
| `debts_owed_by_committee` | `debts_owed_by_committee` | NUMERIC | Total debt |
| `coverage_start_date` | `coverage_start_date` | DATE | First date of cycle |
| `coverage_end_date` | `coverage_end_date` | DATE | Latest filing date |
| `report_type` | `last_report_type_full` | TEXT | Latest report type |
| `report_year` | `last_report_year` | INTEGER | Latest report year |

### Example API Response → Database UPSERT

**FEC API Response:**
```json
{
  "candidate_id": "H6CA47001",
  "cycle": 2026,
  "receipts": 3200000.00,
  "disbursements": 1800000.00,
  "cash_on_hand_end_period": 1400000.00,
  "debts_owed_by_committee": 0.00,
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-09-30",
  "last_report_type_full": "Q3 QUARTERLY REPORT",
  "last_report_year": 2025
}
```

**Database UPSERT:**
```sql
INSERT INTO financial_summary (
  candidate_id, cycle, name, office, state, district, party,
  total_receipts, total_disbursements, cash_on_hand, debts_owed_by_committee,
  coverage_start_date, coverage_end_date, report_type, report_year
) VALUES (
  'H6CA47001', 2026, 'SMITH, JANE', 'H', 'CA', '47', 'DEM',
  3200000.00, 1800000.00, 1400000.00, 0.00,
  '2025-01-01', '2025-09-30', 'Q3 QUARTERLY REPORT', 2025
)
ON CONFLICT (candidate_id, cycle)
DO UPDATE SET
  total_receipts = EXCLUDED.total_receipts,
  total_disbursements = EXCLUDED.total_disbursements,
  cash_on_hand = EXCLUDED.cash_on_hand,
  updated_at = NOW();
```

---

## Quarterly Financials Table

### Purpose
Store per-quarter financial breakdowns for time series charts (multiple rows per candidate).

### Source Endpoint
`GET /committee/{committee_id}/reports/?cycle={cycle}`

### Database Schema
```sql
CREATE TABLE quarterly_financials (
  -- Primary Key
  id SERIAL PRIMARY KEY,

  -- Foreign Keys
  candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
  committee_id TEXT NOT NULL,

  -- Denormalized Candidate Info
  name TEXT NOT NULL,
  office TEXT NOT NULL,
  state TEXT NOT NULL,
  district TEXT,
  party TEXT,

  -- Election Info
  cycle INTEGER NOT NULL,
  report_type TEXT NOT NULL,  -- 'Q1', 'Q2', 'Q3', 'Q4', 'YE', etc.

  -- Coverage Period
  coverage_start_date DATE NOT NULL,
  coverage_end_date DATE NOT NULL,

  -- PER-PERIOD Financial Data
  total_receipts NUMERIC(12, 2) DEFAULT 0,
  total_disbursements NUMERIC(12, 2) DEFAULT 0,
  cash_beginning NUMERIC(12, 2) DEFAULT 0,
  cash_ending NUMERIC(12, 2) DEFAULT 0,
  debts_owed NUMERIC(12, 2) DEFAULT 0,

  -- Filing Metadata
  filing_id BIGINT,
  report_year INTEGER,
  is_amendment BOOLEAN DEFAULT FALSE,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique Constraint (prevent duplicate filings)
  UNIQUE(candidate_id, committee_id, cycle, coverage_end_date, filing_id)
);

CREATE INDEX idx_quarterly_candidate ON quarterly_financials(candidate_id);
CREATE INDEX idx_quarterly_cycle ON quarterly_financials(cycle);
CREATE INDEX idx_quarterly_date ON quarterly_financials(coverage_end_date);
CREATE INDEX idx_quarterly_committee ON quarterly_financials(committee_id, cycle);
```

### Field Mappings

| Database Field | FEC API Field | Type | Notes |
|----------------|---------------|------|-------|
| `id` | N/A | SERIAL | Auto-increment PK |
| `candidate_id` | N/A | TEXT | Looked up via committee |
| `committee_id` | `committee_id` | TEXT | From committee reports endpoint |
| `name` | N/A | TEXT | From candidates table |
| `office` | N/A | TEXT | From candidates table |
| `state` | N/A | TEXT | From candidates table |
| `district` | N/A | TEXT | From candidates table |
| `party` | N/A | TEXT | From candidates table |
| `cycle` | `cycle` | INTEGER | Election cycle |
| `report_type` | `report_type` | TEXT | Q1, Q2, Q3, Q4, YE, etc. |
| `coverage_start_date` | `coverage_start_date` | DATE | Quarter start date |
| `coverage_end_date` | `coverage_end_date` | DATE | Quarter end date |
| `total_receipts` | `total_receipts` | NUMERIC | **PER-QUARTER** receipts |
| `total_disbursements` | `total_disbursements` | NUMERIC | **PER-QUARTER** disbursements |
| `cash_beginning` | `cash_on_hand_beginning_period` | NUMERIC | Starting balance |
| `cash_ending` | `cash_on_hand_end_period` | NUMERIC | Ending balance |
| `debts_owed` | `debts_owed_by_committee` | NUMERIC | Debt at period end |
| `filing_id` | `fec_file_id` | BIGINT | FEC filing ID |
| `report_year` | `report_year` | INTEGER | Report year |
| `is_amendment` | `is_amended` | BOOLEAN | Whether filing is amendment |

### Example API Response → Database INSERT

**FEC API Response:**
```json
{
  "committee_id": "C00264697",
  "cycle": 2026,
  "report_type": "Q1",
  "coverage_start_date": "2026-01-01",
  "coverage_end_date": "2026-03-31",
  "total_receipts": 500000.00,
  "total_disbursements": 200000.00,
  "cash_on_hand_beginning_period": 100000.00,
  "cash_on_hand_end_period": 400000.00,
  "debts_owed_by_committee": 0.00,
  "fec_file_id": 1234567,
  "report_year": 2026,
  "is_amended": false
}
```

**Database INSERT:**
```sql
INSERT INTO quarterly_financials (
  candidate_id, committee_id, name, office, state, district, party,
  cycle, report_type, coverage_start_date, coverage_end_date,
  total_receipts, total_disbursements, cash_beginning, cash_ending, debts_owed,
  filing_id, report_year, is_amendment
) VALUES (
  'H6CA47001', 'C00264697', 'SMITH, JANE', 'H', 'CA', '47', 'DEM',
  2026, 'Q1', '2026-01-01', '2026-03-31',
  500000.00, 200000.00, 100000.00, 400000.00, 0.00,
  1234567, 2026, FALSE
)
ON CONFLICT (candidate_id, committee_id, cycle, coverage_end_date, filing_id)
DO NOTHING;
```

---

## Committee Designations Table

### Purpose
Track which committees are principal campaign committees vs. JFCs/Leadership PACs per cycle.

### Source Endpoint
`GET /committee/{committee_id}/history/` (designation field)

### Database Schema
```sql
CREATE TABLE committee_designations (
  -- Composite Primary Key
  committee_id TEXT NOT NULL,
  cycle INTEGER NOT NULL,

  -- Designation Info
  candidate_id TEXT REFERENCES candidates(candidate_id),
  designation TEXT NOT NULL,  -- 'P', 'J', 'D', etc.

  -- Computed Boolean Flags (for easier queries)
  is_principal BOOLEAN GENERATED ALWAYS AS (designation = 'P') STORED,
  is_joint_fundraising BOOLEAN GENERATED ALWAYS AS (designation = 'J') STORED,
  is_leadership_pac BOOLEAN GENERATED ALWAYS AS (designation = 'D') STORED,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  PRIMARY KEY (committee_id, cycle)
);

CREATE INDEX idx_designations_candidate ON committee_designations(candidate_id);
CREATE INDEX idx_designations_principal ON committee_designations(committee_id, cycle)
  WHERE is_principal = TRUE;
```

### Field Mappings

| Database Field | FEC API Field | Type | Notes |
|----------------|---------------|------|-------|
| `committee_id` | `committee_id` | TEXT | PK |
| `cycle` | `cycle` | INTEGER | PK |
| `candidate_id` | `candidate_id` | TEXT | FK |
| `designation` | `designation` | TEXT | P, J, D, A, U, B |
| `is_principal` | N/A | BOOLEAN | Computed: designation = 'P' |
| `is_joint_fundraising` | N/A | BOOLEAN | Computed: designation = 'J' |
| `is_leadership_pac` | N/A | BOOLEAN | Computed: designation = 'D' |

### Designation Codes

| Code | Meaning | Include in Charts? |
|------|---------|-------------------|
| `P` | Principal campaign committee | ✅ YES |
| `J` | Joint fundraising committee | ❌ NO (shared funds) |
| `D` | Leadership PAC | ⏸️ FUTURE |
| `A` | Authorized committee | ✅ YES |
| `U` | Unauthorized committee | ❌ NO |
| `B` | Lobbyist/Registrant PAC | ❌ NO |

---

## Political Persons Table

### Purpose
Merge multiple candidate_ids into single political person entities (e.g., Sherrod Brown's 3 candidate IDs).

### Source
Manual curation or algorithmic matching (not from FEC API directly).

### Database Schema
```sql
CREATE TABLE political_persons (
  -- Primary Key
  person_id TEXT PRIMARY KEY,  -- Slug: 'sherrod-brown-oh'

  -- Display Info
  display_name TEXT NOT NULL,  -- 'Sherrod Brown'
  first_name TEXT,
  last_name TEXT,

  -- Current Info
  party TEXT,
  state TEXT,
  current_office TEXT,  -- 'H' or 'S'
  is_incumbent BOOLEAN DEFAULT FALSE,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_political_persons_state ON political_persons(state);
CREATE INDEX idx_political_persons_party ON political_persons(party);
CREATE INDEX idx_political_persons_name ON political_persons(display_name);
```

### Usage Pattern

**Link candidate_ids to person:**
```sql
-- Sherrod Brown has 3 candidate IDs
UPDATE candidates SET person_id = 'sherrod-brown-oh'
WHERE candidate_id IN ('H2OH13033', 'S6OH00163', 'S6OH00379');

-- Now query all of Sherrod's data:
SELECT qf.*
FROM quarterly_financials qf
JOIN candidates c ON qf.candidate_id = c.candidate_id
WHERE c.person_id = 'sherrod-brown-oh'
ORDER BY qf.coverage_end_date;
```

---

## Data Type Reference

### PostgreSQL Types Used

| Type | Usage | Example |
|------|-------|---------|
| `TEXT` | Strings of any length | Candidate names, IDs |
| `INTEGER` | Whole numbers | Cycles, years |
| `BIGINT` | Large whole numbers | FEC filing IDs |
| `NUMERIC(12, 2)` | Money amounts | $3,200,000.00 |
| `DATE` | Date only | 2026-03-31 |
| `TIMESTAMP` | Date + time | 2025-11-19 14:30:00 |
| `BOOLEAN` | True/false | has_raised_funds |
| `INTEGER[]` | Array of integers | election_years |

### Money Fields

**All financial amounts:**
- Type: `NUMERIC(12, 2)`
- Max: $999,999,999,999.99 (1 trillion)
- Precision: 2 decimal places (cents)
- NULL: Treated as 0 in queries

**Example:**
```sql
-- Store
total_receipts NUMERIC(12, 2) = 3200000.00

-- Query
SELECT total_receipts::BIGINT as receipts_dollars
FROM financial_summary
WHERE candidate_id = 'H6CA47001';
-- Returns: 3200000
```

### Date Fields

**Date formats:**
- Database: `DATE` type
- FEC API: "YYYY-MM-DD" string
- Frontend: ISO 8601 string

**Example:**
```sql
-- Insert
INSERT INTO quarterly_financials (coverage_end_date)
VALUES ('2026-03-31');

-- Query
SELECT coverage_end_date
FROM quarterly_financials
WHERE coverage_end_date >= '2026-01-01';
```

---

## Validation Queries

### Check Candidate Data Integrity
```sql
-- Verify all candidates have basic fields
SELECT COUNT(*) as invalid_candidates
FROM candidates
WHERE name IS NULL OR office IS NULL OR state IS NULL;
-- Should return 0

-- Check for duplicate candidate_ids
SELECT candidate_id, COUNT(*) as duplicates
FROM candidates
GROUP BY candidate_id
HAVING COUNT(*) > 1;
-- Should return 0 rows
```

### Check Financial Data Integrity
```sql
-- Verify financial_summary totals match quarterly sum
WITH quarterly_totals AS (
  SELECT
    candidate_id,
    cycle,
    SUM(total_receipts) as quarterly_sum
  FROM quarterly_financials
  WHERE report_type IN ('Q1', 'Q2', 'Q3', 'Q4')
  GROUP BY candidate_id, cycle
)
SELECT
  fs.candidate_id,
  fs.cycle,
  fs.total_receipts as summary_total,
  qt.quarterly_sum,
  ABS(fs.total_receipts - qt.quarterly_sum) as difference
FROM financial_summary fs
JOIN quarterly_totals qt
  ON fs.candidate_id = qt.candidate_id
  AND fs.cycle = qt.cycle
WHERE ABS(fs.total_receipts - qt.quarterly_sum) > 100  -- Allow $100 rounding
ORDER BY difference DESC
LIMIT 10;
```

### Check for Missing Data
```sql
-- Find candidates with totals but no quarterly data
SELECT c.candidate_id, c.name, fs.total_receipts
FROM candidates c
JOIN financial_summary fs ON c.candidate_id = fs.candidate_id
LEFT JOIN quarterly_financials qf
  ON c.candidate_id = qf.candidate_id
  AND fs.cycle = qf.cycle
WHERE qf.id IS NULL
  AND fs.total_receipts > 0
ORDER BY fs.total_receipts DESC
LIMIT 20;
```

---

## Related Documentation

- `FEC_API_GUIDE.md` - API usage and examples
- `FEC_INTEGRATION_PATTERNS.md` - Integration with our app
- `FEC_TROUBLESHOOTING_GUIDE.md` - Common issues
- `database-schema.md` - Complete database documentation

---

**Last Updated:** November 19, 2025
**Database Version:** PostgreSQL 15.6 (Supabase)
**Schema Version:** 2.0 (with political_persons)
