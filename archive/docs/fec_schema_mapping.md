# FEC Bulk Data to Database Schema Mapping

## Overview
This document provides the complete mapping between FEC API bulk data files and the application's Supabase database schema. The FEC Dashboard uses three main tables to store candidate information and financial data.

---

## 1. CANDIDATES TABLE

### Database Schema
```sql
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) UNIQUE NOT NULL,      -- FEC Candidate ID (e.g., 'H4VA07234')
  name VARCHAR(255),                             -- Full candidate name
  party VARCHAR(100),                            -- Party code (DEM, REP, NON, LIB, etc.)
  party_full VARCHAR(255),                       -- Full party name (DEMOCRATIC PARTY, etc.)
  state VARCHAR(2),                              -- State abbreviation (VA, NY, etc.)
  district VARCHAR(10),                          -- Congressional district (01-27)
  office VARCHAR(50),                            -- Office code: 'H' (House) or 'S' (Senate)
  office_full VARCHAR(100),                      -- Full office name (House, Senate)
  cycle INTEGER NOT NULL,                        -- Election cycle (2024, 2026, etc.)
  active_through INTEGER,                        -- Last active cycle
  candidate_status VARCHAR(10),                  -- N=New, C=Candidate, P=Previous, I=Inactive
  incumbent_challenge VARCHAR(100),              -- Incumbent, Challenger, Open Seat
  federal_funds_flag BOOLEAN,                    -- Receives federal funds
  has_raised_funds BOOLEAN,                      -- True if total_receipts > 0
  first_file_date DATE,                          -- First FEC filing date
  last_file_date DATE,                           -- Most recent FEC filing date
  load_date TIMESTAMP,                           -- When FEC data was loaded
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle)
);

CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_candidates_office ON candidates(office);
CREATE INDEX idx_candidates_party ON candidates(party);
```

### FEC API Source Data (`/candidates/` endpoint)
```json
{
  "active_through": 2026,
  "candidate_id": "H4VA07234",
  "candidate_inactive": false,
  "candidate_status": "N",
  "cycles": [2026],
  "district": "07",
  "district_number": 7,
  "federal_funds_flag": false,
  "first_file_date": "2025-02-20",
  "has_raised_funds": true,
  "incumbent_challenge": "C",
  "incumbent_challenge_full": "Challenger",
  "last_f2_date": "2025-02-20",
  "last_file_date": "2025-02-20",
  "load_date": "2025-03-13T20:59:32",
  "name": "VINDMAN, YEVGENY 'EUGENE'",
  "office": "H",
  "office_full": "House",
  "party": "DEM",
  "party_full": "DEMOCRATIC PARTY",
  "state": "VA"
}
```

### Mapping
| Database Field | FEC Field | Type | Notes |
|---|---|---|---|
| candidate_id | candidate_id | VARCHAR(9) | PK - FEC Candidate ID |
| name | name | VARCHAR(255) | Full candidate name |
| party | party | VARCHAR(100) | 2-char party code |
| party_full | party_full | VARCHAR(255) | Full party name |
| state | state | VARCHAR(2) | State abbreviation |
| district | district | VARCHAR(10) | Congressional district |
| office | office | VARCHAR(50) | 'H' or 'S' |
| office_full | office_full | VARCHAR(100) | Full office name |
| cycle | (from query param) | INTEGER | 2026 for this dataset |
| active_through | active_through | INTEGER | Last active election cycle |
| candidate_status | candidate_status | VARCHAR(10) | Registration status |
| incumbent_challenge | incumbent_challenge_full | VARCHAR(100) | Incumbent/Challenger status |
| federal_funds_flag | federal_funds_flag | BOOLEAN | Receives matching funds |
| has_raised_funds | has_raised_funds | BOOLEAN | Ever filed contributions |
| first_file_date | first_file_date | DATE | First filing date |
| last_file_date | last_file_date | DATE | Most recent filing |
| load_date | load_date | TIMESTAMP | FEC load timestamp |

---

## 2. FINANCIAL_SUMMARY TABLE

### Database Schema
```sql
CREATE TABLE financial_summary (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  cycle INTEGER NOT NULL,
  committee_id VARCHAR(9),                       -- Principal campaign committee
  
  -- Cumulative totals for the entire cycle
  total_receipts DECIMAL(15,2),                 -- Total money raised
  total_disbursements DECIMAL(15,2),            -- Total money spent
  cash_on_hand DECIMAL(15,2),                   -- Cash remaining
  
  -- Coverage period for this report
  coverage_start_date DATE,
  coverage_end_date DATE,
  
  -- Report metadata
  report_year INTEGER,                          -- Year of report
  report_type VARCHAR(100),                     -- OCTOBER QUARTERLY, YEAR-END, etc.
  last_report_type_full VARCHAR(100),           -- Full report type name
  
  -- FEC metadata
  filing_id BIGINT,                             -- FEC file_number
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle, filing_id)
);

CREATE INDEX idx_fs_candidate_cycle ON financial_summary(candidate_id, cycle);
CREATE INDEX idx_fs_cycle ON financial_summary(cycle);
CREATE INDEX idx_fs_updated ON financial_summary(updated_at);
```

### FEC API Source Data (`/candidate/{id}/totals/` endpoint)
The financial_summary table is populated using the `/candidate/{candidate_id}/totals/?cycle={cycle}` endpoint.

**Example response structure:**
```json
{
  "candidate_id": "H4VA07234",
  "receipts": 5325053.15,
  "disbursements": 2329785.05,
  "cash_on_hand": 3130201.84,
  "last_cash_on_hand_end_period": 3130201.84,
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-09-30",
  "last_report_year": 2025,
  "last_report_type_full": "OCTOBER QUARTERLY"
}
```

### Mapping
| Database Field | FEC Field | Type | Notes |
|---|---|---|---|
| candidate_id | (from path) | VARCHAR(9) | FK to candidates |
| cycle | (from query param) | INTEGER | 2026 for this dataset |
| total_receipts | receipts | DECIMAL(15,2) | CUMULATIVE - total for entire cycle |
| total_disbursements | disbursements | DECIMAL(15,2) | CUMULATIVE - total for entire cycle |
| cash_on_hand | cash_on_hand or last_cash_on_hand_end_period | DECIMAL(15,2) | Cash remaining at end of latest period |
| coverage_start_date | coverage_start_date | DATE | Start of reporting period |
| coverage_end_date | coverage_end_date | DATE | End of reporting period |
| report_year | last_report_year | INTEGER | Year of last report |
| report_type | last_report_type_full | VARCHAR(100) | Type of last report filed |

**NOTE:** This table stores CUMULATIVE totals for the entire cycle. For quarterly breakdowns, see quarterly_financials table.

---

## 3. QUARTERLY_FINANCIALS TABLE

### Database Schema
```sql
CREATE TABLE quarterly_financials (
  id SERIAL PRIMARY KEY,
  
  -- Candidate information
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),                      -- Principal campaign committee
  cycle INTEGER NOT NULL,
  name VARCHAR(255),                            -- Candidate name (denormalized)
  party VARCHAR(100),                           -- Party code (denormalized)
  state VARCHAR(2),                             -- State (denormalized)
  district VARCHAR(10),                         -- District (denormalized)
  
  -- Quarter identification
  quarter VARCHAR(10),                          -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  report_type VARCHAR(100),                     -- 'APRIL QUARTERLY', 'JULY QUARTERLY', etc.
  
  -- Period coverage
  coverage_start_date DATE,
  coverage_end_date DATE,
  
  -- Financial data for THIS QUARTER ONLY (NOT cumulative)
  total_receipts DECIMAL(15,2),                -- Money raised this quarter only
  total_disbursements DECIMAL(15,2),           -- Money spent this quarter only
  cash_beginning DECIMAL(15,2),                -- Cash at start of quarter
  cash_ending DECIMAL(15,2),                   -- Cash at end of quarter
  
  -- FEC metadata
  filing_id BIGINT,                            -- FEC file_number
  is_amendment BOOLEAN DEFAULT false,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle, coverage_end_date, filing_id)
);

CREATE INDEX idx_qf_candidate ON quarterly_financials(candidate_id);
CREATE INDEX idx_qf_cycle ON quarterly_financials(cycle);
CREATE INDEX idx_qf_quarter ON quarterly_financials(quarter, report_year);
CREATE INDEX idx_qf_committee ON quarterly_financials(committee_id);
CREATE INDEX idx_qf_timeseries ON quarterly_financials(candidate_id, cycle, coverage_end_date);
CREATE INDEX idx_qf_filing ON quarterly_financials(filing_id);
```

### FEC API Source Data
Requires TWO API calls per candidate:

#### Step 1: Get committees
```
GET /candidate/{candidate_id}/committees/?cycle={cycle}
```

**Response:**
```json
{
  "results": [
    {
      "committee_id": "C00776658",
      "committee_name": "VINDMAN FOR CONGRESS",
      "designation": "P"  // P = Principal
    }
  ]
}
```

#### Step 2: Get filings for each committee
```
GET /committee/{committee_id}/filings/?cycle={cycle}&form_type=F3&sort=-coverage_end_date
```

**Response example (quarterly filing):**
```json
{
  "results": [
    {
      "committee_id": "C00776658",
      "file_number": 1918383,
      "report_type_full": "OCTOBER QUARTERLY",
      "coverage_start_date": "2025-07-01",
      "coverage_end_date": "2025-09-30",
      "total_receipts": 0.0,
      "total_disbursements": 1121.24,
      "cash_on_hand_beginning_period": 106230.94,
      "cash_on_hand_end_period": 105109.7,
      "is_amended": false
    }
  ]
}
```

### Mapping
| Database Field | FEC Field | Type | Notes |
|---|---|---|---|
| candidate_id | (from path) | VARCHAR(9) | FK to candidates |
| committee_id | committee_id | VARCHAR(9) | From committees endpoint |
| cycle | (from query param) | INTEGER | 2026 for this dataset |
| name | (from candidates table) | VARCHAR(255) | Denormalized from candidates |
| party | (from candidates table) | VARCHAR(100) | Denormalized from candidates |
| state | (from candidates table) | VARCHAR(2) | Denormalized from candidates |
| district | (from candidates table) | VARCHAR(10) | Denormalized from candidates |
| quarter | (computed from coverage_end_date) | VARCHAR(10) | Q1/Q2/Q3/Q4 based on date |
| report_year | (from coverage_end_date year) | INTEGER | Year of the quarter |
| report_type | report_type_full | VARCHAR(100) | APRIL QUARTERLY, JULY QUARTERLY, etc. |
| coverage_start_date | coverage_start_date | DATE | Start of this quarter |
| coverage_end_date | coverage_end_date | DATE | End of this quarter |
| total_receipts | total_receipts | DECIMAL(15,2) | PER QUARTER - not cumulative |
| total_disbursements | total_disbursements | DECIMAL(15,2) | PER QUARTER - not cumulative |
| cash_beginning | cash_on_hand_beginning_period | DECIMAL(15,2) | Cash at start of quarter |
| cash_ending | cash_on_hand_end_period | DECIMAL(15,2) | Cash at end of quarter |
| filing_id | file_number | BIGINT | FEC filing identifier |
| is_amendment | is_amended | BOOLEAN | True if amended report |

### Quarter Calculation Logic
```typescript
function getQuarter(coverageEndDate: Date): string {
  const month = coverageEndDate.getMonth() + 1; // 1-12
  
  if (month <= 3) return 'Q1';      // Jan-Mar
  if (month <= 6) return 'Q2';      // Apr-Jun
  if (month <= 9) return 'Q3';      // Jul-Sep
  return 'Q4';                       // Oct-Dec
}
```

---

## Data Flow Summary

### From FEC API to Database

```
FEC Bulk Files/API
        ↓
Python fetch_fec_data.py
        ↓
┌─────────────────────────┬──────────────────────────┬──────────────────────────┐
│   candidates_2026.json  │  financials_2026.json    │ quarterly_financials...  │
│   (5,185 records)       │  (financial summaries)   │ (quarterly filings)      │
└─────────────────────────┴──────────────────────────┴──────────────────────────┘
        ↓                         ↓                          ↓
   candidates table        financial_summary table    quarterly_financials table
   (5,185 rows)            (5,185 rows)               (~20,000 rows)
```

### Key Differences Between Tables

| Aspect | candidates | financial_summary | quarterly_financials |
|--------|-----------|-------------------|----------------------|
| **Granularity** | One row per candidate | One row per candidate (summary) | Multiple rows per candidate (timeseries) |
| **Data Type** | Registration info | Cycle totals | Quarter-level detail |
| **Receipts Field** | N/A | CUMULATIVE for entire cycle | PER QUARTER only |
| **Disbursements Field** | N/A | CUMULATIVE for entire cycle | PER QUARTER only |
| **Cash on Hand** | N/A | Latest balance | Beginning and ending per quarter |
| **Time Periods** | Fixed | One period per cycle | Multiple quarters per cycle |
| **Rows for 2026 Cycle** | ~5,185 | ~5,185 | ~20,000+ |

---

## Sample Data Flows

### Example 1: Eugene Vindman (H4VA07234)

#### candidates table
```json
{
  "candidate_id": "H4VA07234",
  "name": "VINDMAN, YEVGENY 'EUGENE'",
  "party": "DEM",
  "party_full": "DEMOCRATIC PARTY",
  "state": "VA",
  "district": "07",
  "office": "H",
  "office_full": "House",
  "cycle": 2026,
  "candidate_status": "N",
  "incumbent_challenge": "C"
}
```

#### financial_summary table
```json
{
  "candidate_id": "H4VA07234",
  "cycle": 2026,
  "total_receipts": 5325053.15,         // CUMULATIVE
  "total_disbursements": 2329785.05,    // CUMULATIVE
  "cash_on_hand": 3130201.84,           // Latest balance
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-09-30",
  "report_type": "OCTOBER QUARTERLY"
}
```

#### quarterly_financials table (3 rows)
```json
{
  "candidate_id": "H4VA07234",
  "quarter": "Q1",
  "report_type": "APRIL QUARTERLY",
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-03-31",
  "total_receipts": 2065104.31,        // Q1 only
  "total_disbursements": 964354.03,    // Q1 only
  "cash_beginning": 0.00,
  "cash_ending": 1235684.02
},
{
  "candidate_id": "H4VA07234",
  "quarter": "Q2",
  "report_type": "JULY QUARTERLY",
  "coverage_start_date": "2025-04-01",
  "coverage_end_date": "2025-06-30",
  "total_receipts": 1602668.11,        // Q2 only
  "total_disbursements": 731667.72,    // Q2 only
  "cash_beginning": 1235684.02,
  "cash_ending": 2106684.41
},
{
  "candidate_id": "H4VA07234",
  "quarter": "Q3",
  "report_type": "OCTOBER QUARTERLY",
  "coverage_start_date": "2025-07-01",
  "coverage_end_date": "2025-09-30",
  "total_receipts": 1657280.73,        // Q3 only
  "total_disbursements": 633763.30,    // Q3 only
  "cash_beginning": 2106684.41,
  "cash_ending": 3130201.84
}
```

### Verification
- Q1 + Q2 + Q3 receipts = $2,065,104.31 + $1,602,668.11 + $1,657,280.73 = $5,325,053.15 ✅
- Matches financial_summary.total_receipts
- Q3 ending cash = $3,130,201.84 = financial_summary.cash_on_hand ✅

---

## Bulk CSV File Format (Alternative to JSON)

If working with FEC bulk CSV exports instead of API:

### candidates_2026.csv
```
candidate_id,name,party,party_full,state,district,office,office_full,cycle
H4VA07234,VINDMAN YEVGENY 'EUGENE',DEM,DEMOCRATIC PARTY,VA,07,H,House,2026
H2NY12197,ABDELHAMID RANA,DEM,DEMOCRATIC PARTY,NY,12,H,House,2026
```

### financial_summary_2026.csv
```
candidate_id,cycle,total_receipts,total_disbursements,cash_on_hand,coverage_end_date,report_type
H4VA07234,2026,5325053.15,2329785.05,3130201.84,2025-09-30,OCTOBER QUARTERLY
H2NY12197,2026,2652.99,8213.09,105109.7,2025-09-30,OCTOBER QUARTERLY
```

### quarterly_financials_2026.csv
```
candidate_id,committee_id,cycle,quarter,report_type,coverage_start_date,coverage_end_date,total_receipts,total_disbursements,cash_beginning,cash_ending,filing_id
H4VA07234,C00776658,2026,Q1,APRIL QUARTERLY,2025-01-01,2025-03-31,2065104.31,964354.03,0.00,1235684.02,1885857
H4VA07234,C00776658,2026,Q2,JULY QUARTERLY,2025-04-01,2025-06-30,1602668.11,731667.72,1235684.02,2106684.41,1899742
H4VA07234,C00776658,2026,Q3,OCTOBER QUARTERLY,2025-07-01,2025-09-30,1657280.73,633763.30,2106684.41,3130201.84,1918383
```

---

## Important Notes

1. **Quarterly Data is NOT Cumulative**: Each row in quarterly_financials represents a single quarter's activity, not cumulative totals.

2. **Financial Summary Stores Latest**: financial_summary should be updated with the latest quarter's cash_on_hand and latest report info.

3. **Multiple Committees**: Candidates can have multiple committees (rare), but typically have one principal campaign committee.

4. **Amendments**: If is_amendment=true, it's a corrected/amended filing. The unique constraint ensures you keep the latest version.

5. **Missing Quarters**: Some candidates may not file for all quarters (e.g., terminated candidates, late registrations).

6. **FEC API Rate Limits**: 1,000 requests/hour. The Python script uses 4-second delays between requests.

7. **Dates Are Inclusive**: coverage_start_date and coverage_end_date define the quarter period inclusively.

---

End of Mapping Document
