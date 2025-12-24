# Database Schema Reference - Campaign Reference

**Complete guide to database tables, FEC API mappings, and data flow.**

**Last Updated:** November 24, 2025
**Data Version:** 2026 Election Cycle

---

## Quick Reference

### Core Data Model

The database uses a hierarchical model to represent political persons, their campaigns, and financial data:

```
political_persons (14,495)    ← Top-level entity (the actual person)
    ↓ (via person_id FK)
candidates (17,459)           ← Campaign registrations (multiple per person)
    ↓ (via candidate_id FK)
quarterly_financials (53,122) ← Financial filings
    ↓ (via committee_id FK)
committee_designations        ← Committee metadata (principal vs. other)
```

### Four Main Tables

| Table | Purpose | Records | Key Use |
|-------|---------|---------|---------|
| **political_persons** | Unified person entities | 14,495 | De-duplication, search |
| **candidates** | Candidate registration info | 17,459 | Campaign metadata |
| **financial_summary** | Cumulative cycle totals | ~5,185 | Leaderboard rankings |
| **quarterly_financials** | Per-quarter breakdowns | ~53,122 | Trend charts |

### Key Concepts

**CRITICAL DISTINCTION:**
- `financial_summary.total_receipts` = **CUMULATIVE** (all money raised in cycle)
- `quarterly_financials.total_receipts` = **PER QUARTER** (only that quarter)

**Example:** Eugene Vindman (H4VA07234)
```
financial_summary:    total_receipts = $5,325,053  (Q1+Q2+Q3)
quarterly_financials: Q1 = $2,065,104
                     Q2 = $1,602,668
                     Q3 = $1,657,281
                     Sum = $5,325,053 ✅
```

---

## Critical Data Integrity Rule

**ALL committees MUST map to a candidate. If a candidate does not exist, it MUST be created before loading committee data.**

This ensures referential integrity in the query flow:
```
political_person → candidates → quarterly_financials → committees
```

Without a candidate record, committee financial data cannot be properly attributed to a political person.

---

## Table 0: political_persons

### Purpose
Stores unified person entities to solve duplicate candidate problems. Each political person can have multiple candidate_ids (e.g., House → Senate transitions, or multiple Senate cycles).

### Schema
```sql
CREATE TABLE political_persons (
  person_id VARCHAR(255) PRIMARY KEY,           -- Slug: 'firstname-lastname-state'
  display_name VARCHAR(255) NOT NULL,           -- Display name: 'First Last'
  first_name VARCHAR(255),                      -- First name (optional)
  last_name VARCHAR(255),                       -- Last name (optional)
  party VARCHAR(100),                           -- Party affiliation
  state VARCHAR(2),                             -- Primary state (alphabetically first)
  district VARCHAR(10),                         -- District (for House members)
  current_office VARCHAR(50),                   -- Current office (H/S/P)
  is_incumbent BOOLEAN DEFAULT FALSE,           -- Is currently serving
  notes TEXT,                                   -- Additional notes
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_political_persons_state ON political_persons(state);
CREATE INDEX idx_political_persons_party ON political_persons(party);
CREATE INDEX idx_political_persons_office ON political_persons(current_office);
CREATE INDEX idx_political_persons_name ON political_persons(display_name);
```

### Person ID Generation
Format: `{first_name}-{last_name}-{state}`
- Uses alphabetically first state if person appears in multiple states
- Example: `bernard-sanders-vt`

### Example Records
```sql
-- Bernard Sanders (3 candidate_ids: House, Senate 2018/2024, Senate 2026)
person_id: 'bernard-sanders-vt'
display_name: 'Bernard Sanders'
party: 'DEM'
state: 'VT'
current_office: 'S'

-- Ruben Gallego (2 candidate_ids: House 2022/2024, Senate 2026)
person_id: 'ruben-gallego-az'
display_name: 'Ruben Gallego'
party: 'DEM'
state: 'AZ'
current_office: 'S'
```

### Data Location
- **Populated by:** `scripts/simple_populate_persons.js`
- **Used by:** `apps/labs/src/hooks/usePersonQuarterlyData.ts` (via person_id lookup)

---

## Table 1: candidates

### Purpose
Stores FEC candidate registration information and metadata.

### Schema
```sql
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) UNIQUE NOT NULL,      -- FEC ID (e.g., 'H4VA07234')
  person_id VARCHAR(255),                        -- FK to political_persons (CRITICAL)
  name VARCHAR(255),                             -- Full candidate name
  party VARCHAR(100),                            -- Party code (DEM, REP, etc.)
  party_full VARCHAR(255),                       -- Full party name
  state VARCHAR(2),                              -- State abbreviation (VA, NY)
  district VARCHAR(10),                          -- District (01-27, or blank for Senate)
  district_number INTEGER,                       -- District as integer
  office VARCHAR(50),                            -- 'H' (House) or 'S' (Senate)
  office_full VARCHAR(100),                      -- 'House' or 'Senate'
  cycle INTEGER NOT NULL,                        -- Election cycle (2026, 2024, etc.)
  active_through INTEGER,                        -- Last active cycle
  candidate_status VARCHAR(10),                  -- N=New, C=Candidate, P=Previous
  candidate_inactive BOOLEAN,                    -- True if inactive
  cycles INTEGER[],                              -- Array of cycles candidate ran
  election_years INTEGER[],                      -- Years of elections
  incumbent_challenge VARCHAR(100),              -- I=Incumbent, C=Challenger, O=Open
  incumbent_challenge_full VARCHAR(100),         -- Full description
  federal_funds_flag BOOLEAN,                    -- Receives federal funding
  has_raised_funds BOOLEAN,                      -- True if raised any money
  first_file_date DATE,                          -- First FEC filing date
  last_f2_date DATE,                             -- Last Statement of Candidacy
  last_file_date DATE,                           -- Most recent filing
  load_date TIMESTAMP,                           -- When FEC data was loaded
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle),
  FOREIGN KEY (person_id) REFERENCES political_persons(person_id)
);

-- Indexes
CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_candidates_office ON candidates(office);
CREATE INDEX idx_candidates_party ON candidates(party);
CREATE INDEX idx_candidates_name ON candidates(name);
CREATE INDEX idx_candidates_person_id ON candidates(person_id);  -- CRITICAL for joins
```

### FEC API Source
**Endpoint:** `GET /candidates/`
**Parameters:** `?cycle=2026&office=H,S&per_page=100`

**Example Response:**
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
  "has_raised_funds": true,
  "incumbent_challenge": "C",
  "incumbent_challenge_full": "Challenger"
}
```

### Field Mapping
| Database Field | FEC API Field | Transform |
|---|---|---|
| candidate_id | candidate_id | Direct |
| name | name | Direct |
| party | party | Direct |
| state | state | Direct |
| district | district | Zero-pad (7 → "07") |
| office | office | Direct ('H' or 'S') |
| cycle | (query parameter) | Passed to query |

### Data Location
- **Fetched by:** `scripts/data-collection/fetch_fec_data.py` (lines 38-84)
- **Saved to:** `candidates_2026.json`
- **Loaded by:** `scripts/data-loading/load_to_supabase.py`
- **Used by:** `apps/labs/src/hooks/useCandidateData.ts`

---

## Table 2: financial_summary

### Purpose
Stores **cumulative** financial totals for each candidate for the entire election cycle.

### Schema
```sql
CREATE TABLE financial_summary (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) NOT NULL,              -- FK to candidates
  cycle INTEGER NOT NULL,                        -- Election cycle
  total_receipts DECIMAL(15,2),                  -- CUMULATIVE total raised
  total_disbursements DECIMAL(15,2),             -- CUMULATIVE total spent
  cash_on_hand DECIMAL(15,2),                    -- Current balance
  coverage_start_date DATE,                      -- Start of reporting period
  coverage_end_date DATE,                        -- End of reporting period
  report_year INTEGER,                           -- Filing year
  report_type VARCHAR(100),                      -- Report type (QUARTERLY, etc.)
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle, coverage_end_date),
  FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- Indexes
CREATE INDEX idx_financial_candidate ON financial_summary(candidate_id);
CREATE INDEX idx_financial_cycle ON financial_summary(cycle);
CREATE INDEX idx_financial_coverage ON financial_summary(coverage_end_date);
```

### FEC API Source
**Endpoint:** `GET /candidate/{candidate_id}/totals/`
**Parameters:** `?cycle=2026`

**Example Response:**
```json
{
  "candidate_id": "H4VA07234",
  "cycle": 2026,
  "receipts": 5325053.15,         // CUMULATIVE
  "disbursements": 2329785.05,    // CUMULATIVE
  "cash_on_hand_end_period": 3130201.84,
  "coverage_end_date": "2025-09-30",
  "last_report_type_full": "OCTOBER QUARTERLY"
}
```

### Field Mapping
| Database Field | FEC API Field | Notes |
|---|---|---|
| candidate_id | candidate_id | Direct |
| cycle | cycle | Direct |
| total_receipts | receipts | CUMULATIVE total for cycle |
| total_disbursements | disbursements | CUMULATIVE total for cycle |
| cash_on_hand | cash_on_hand_end_period | Latest balance |
| coverage_end_date | coverage_end_date | Most recent report date |
| report_type | last_report_type_full | Most recent filing type |

### Data Location
- **Fetched by:** `scripts/data-collection/fetch_fec_data.py` (lines 86-120)
- **Saved to:** `financials_2026.json`
- **Loaded by:** `scripts/data-loading/load_to_supabase.py`
- **Used by:** `apps/labs/src/hooks/useCandidateData.ts` (lines 68-71)

### Frontend Query Example
```typescript
const { data } = await supabase
  .from('financial_summary')
  .select('candidate_id, total_receipts, total_disbursements, cash_on_hand')
  .eq('cycle', 2026)
  .order('total_receipts', { ascending: false })
  .range(0, 999);
```

---

## Table 3: quarterly_financials

### Purpose
Stores **per-quarter** financial breakdowns for timeseries analysis and trend charts.

### Schema
```sql
CREATE TABLE quarterly_financials (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) NOT NULL,              -- FK to candidates
  committee_id VARCHAR(9),                       -- Committee ID
  cycle INTEGER NOT NULL,                        -- Election cycle
  quarter VARCHAR(10),                           -- Q1, Q2, Q3, Q4
  report_type VARCHAR(100),                      -- Report type
  coverage_start_date DATE,                      -- Quarter start date
  coverage_end_date DATE,                        -- Quarter end date
  total_receipts DECIMAL(15,2),                  -- THIS QUARTER ONLY
  total_disbursements DECIMAL(15,2),             -- THIS QUARTER ONLY
  cash_beginning DECIMAL(15,2),                  -- Balance at start
  cash_ending DECIMAL(15,2),                     -- Balance at end
  debts_owed DECIMAL(15,2),                      -- Debts owed
  filing_id BIGINT,                              -- FEC filing number
  is_amendment BOOLEAN DEFAULT FALSE,            -- True if amended filing
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle, coverage_end_date, is_amendment),
  FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

-- Indexes
CREATE INDEX idx_quarterly_candidate ON quarterly_financials(candidate_id);
CREATE INDEX idx_quarterly_cycle ON quarterly_financials(cycle);
CREATE INDEX idx_quarterly_quarter ON quarterly_financials(quarter);
CREATE INDEX idx_quarterly_coverage ON quarterly_financials(coverage_end_date);
```

### FEC API Source
**Endpoint:** `GET /committee/{committee_id}/filings/`
**Parameters:** `?cycle=2026&form_type=F3`

**Example Response:**
```json
{
  "file_number": 1918383,
  "report_type_full": "OCTOBER QUARTERLY",
  "coverage_start_date": "2025-07-01",
  "coverage_end_date": "2025-09-30",
  "total_receipts": 1657280.73,                  // Q3 only
  "total_disbursements": 633763.30,              // Q3 only
  "cash_on_hand_beginning_period": 2106684.41,
  "cash_on_hand_end_period": 3130201.84
}
```

### Field Mapping
| Database Field | FEC API Field | Transform |
|---|---|---|
| candidate_id | (from parent query) | Linked from committee |
| committee_id | committee_id | Direct |
| total_receipts | total_receipts | **Per quarter only** |
| total_disbursements | total_disbursements | **Per quarter only** |
| cash_beginning | cash_on_hand_beginning_period | Start balance |
| cash_ending | cash_on_hand_end_period | End balance |
| coverage_end_date | coverage_end_date | Direct |
| quarter | (calculated) | From coverage_end_date month |
| filing_id | file_number | Direct |

### Quarter Calculation
```python
def calculate_quarter(coverage_end_date):
    month = coverage_end_date.month
    if month <= 3:
        return 'Q1'
    elif month <= 6:
        return 'Q2'
    elif month <= 9:
        return 'Q3'
    else:
        return 'Q4'
```

### Data Location
- **Fetched by:** `scripts/data-collection/fetch_fec_data.py` (lines 122-204)
- **Saved to:** `quarterly_financials_2026.json`
- **Loaded by:** `scripts/data-loading/load_quarterly_data.py`
- **Used by:** `apps/labs/src/hooks/useQuarterlyData.ts` (lines 74-79)

### Frontend Query Example
```typescript
const { data } = await supabase
  .from('quarterly_financials')
  .select('*')
  .in('candidate_id', candidateIds)
  .eq('cycle', 2026)
  .order('coverage_end_date', { ascending: true });
```

---

## Data Validation Queries

### Check Quarterly Sums Match Summary
```sql
SELECT
  c.candidate_id,
  c.name,
  fs.total_receipts as summary_total,
  SUM(qf.total_receipts) as quarterly_sum,
  fs.total_receipts - SUM(qf.total_receipts) as difference
FROM candidates c
JOIN financial_summary fs ON c.candidate_id = fs.candidate_id
LEFT JOIN quarterly_financials qf ON c.candidate_id = qf.candidate_id
  AND c.cycle = qf.cycle
WHERE c.cycle = 2026
GROUP BY c.candidate_id, c.name, fs.total_receipts
HAVING ABS(fs.total_receipts - COALESCE(SUM(qf.total_receipts), 0)) > 0.01
LIMIT 10;
```

### Check Cash Flow Continuity
```sql
SELECT
  q1.candidate_id,
  q1.quarter,
  q1.cash_ending as q_end,
  q2.quarter as next_quarter,
  q2.cash_beginning as next_begin,
  q1.cash_ending - q2.cash_beginning as gap
FROM quarterly_financials q1
JOIN quarterly_financials q2 ON
  q1.candidate_id = q2.candidate_id
  AND q1.cycle = q2.cycle
  AND q1.coverage_end_date < q2.coverage_end_date
WHERE ABS(q1.cash_ending - q2.cash_beginning) > 0.01
LIMIT 10;
```

### Find Missing Quarterly Data
```sql
SELECT
  c.candidate_id,
  c.name,
  c.state,
  c.district,
  fs.total_receipts
FROM candidates c
JOIN financial_summary fs ON c.candidate_id = fs.candidate_id
LEFT JOIN quarterly_financials qf ON c.candidate_id = qf.candidate_id
WHERE c.cycle = 2026
  AND fs.total_receipts > 0
  AND qf.candidate_id IS NULL
ORDER BY fs.total_receipts DESC
LIMIT 20;
```

---

## Common Pitfalls

### ❌ WRONG: Treating quarterly as cumulative
```sql
-- This is WRONG - quarterly_financials is per-quarter
SELECT total_receipts FROM quarterly_financials WHERE quarter = 'Q3'
-- Result: $1,657,281 (Q3 only, not cumulative!)
```

### ✅ CORRECT: Use financial_summary for cumulative
```sql
-- This is CORRECT - financial_summary is cumulative
SELECT total_receipts FROM financial_summary WHERE candidate_id = 'H4VA07234'
-- Result: $5,325,053 (entire cycle)
```

### ❌ WRONG: Using report_type to determine quarter
```sql
-- This is WRONG - "APRIL QUARTERLY" ends on March 31 (Q1)
SELECT * FROM quarterly_financials WHERE report_type LIKE '%APRIL%'
-- This is Q1 data, not Q2!
```

### ✅ CORRECT: Use coverage_end_date for quarter
```sql
-- This is CORRECT - calculate from coverage_end_date
SELECT * FROM quarterly_financials
WHERE EXTRACT(MONTH FROM coverage_end_date) <= 3  -- Q1
```

---

## File Locations

### Python Scripts
- **Main fetcher:** `scripts/data-collection/fetch_fec_data.py`
- **Loader:** `scripts/data-loading/load_to_supabase.py`
- **Quarterly loader:** `scripts/data-loading/load_quarterly_data.py`

### Frontend Hooks
- **Candidate data:** `apps/labs/src/hooks/useCandidateData.ts`
- **Quarterly data:** `apps/labs/src/hooks/useQuarterlyData.ts`

### SQL Files
- **Quarterly table:** `sql/create_quarterly_table.sql`
- **User features:** `database/migrations/` (profiles, follows, notifications)

### Generated Data
- `candidates_2026.json` (5,185 candidates)
- `financials_2026.json` (financial summaries)
- `quarterly_financials_2026.json` (~20,000 quarterly records)

---

## Additional Resources

- **FEC API Documentation:** https://api.open.fec.gov/developers/
- **Bulk Import Guide:** `docs/data/bulk-import.md`
- **Data Collection Scripts:** `scripts/data-collection/`
- **Database Migrations:** `database/migrations/`

---

**Last Updated:** November 5, 2025
**Maintained By:** Campaign Reference Team
