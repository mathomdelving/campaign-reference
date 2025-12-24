# Actual Database Schemas in FEC Dashboard

## Location & How to Create

These schemas are defined in:
1. Python fetch script: `/Users/benjaminnelson/Desktop/fec-dashboard/fetch_fec_data.py` (lines 38-320)
2. SQL file: `/Users/benjaminnelson/Desktop/fec-dashboard/sql/create_quarterly_table.sql`
3. Frontend queries: `/Users/benjaminnelson/Desktop/fec-dashboard/apps/labs/src/hooks/*.ts`

The tables are created manually in Supabase (no migrations exist for main tables - only for user profiles).

---

## 1. CANDIDATES TABLE

**Status:** Created manually in Supabase from FEC API response
**Source Data:** FEC `/candidates/` endpoint
**Created By:** `fetch_fec_data.py` - fetches data, stores in `candidates_2026.json`
**Loaded To DB:** Manual Supabase insert (load script needed)

### Inferred Schema from Code Analysis
```sql
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) UNIQUE NOT NULL,
  name VARCHAR(255),
  party VARCHAR(100),
  party_full VARCHAR(255),
  state VARCHAR(2),
  district VARCHAR(10),
  district_number INTEGER,
  office VARCHAR(50),
  office_full VARCHAR(100),
  cycle INTEGER NOT NULL,
  active_through INTEGER,
  candidate_status VARCHAR(10),
  candidate_inactive BOOLEAN,
  cycles INTEGER[],
  election_years INTEGER[],
  incumbent_challenge VARCHAR(100),
  incumbent_challenge_full VARCHAR(100),
  federal_funds_flag BOOLEAN,
  has_raised_funds BOOLEAN,
  first_file_date DATE,
  last_f2_date DATE,
  last_file_date DATE,
  load_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(candidate_id, cycle),
  FOREIGN KEY(cycle) REFERENCES election_cycles(cycle)
);

CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_candidates_office ON candidates(office);
CREATE INDEX idx_candidates_party ON candidates(party);
CREATE INDEX idx_candidates_name ON candidates(name);
```

### Actual Data Sample
From `/Users/benjaminnelson/Desktop/fec-dashboard/candidates_2026.json`:
```json
{
  "active_through": 2026,
  "candidate_id": "H6MI04188",
  "candidate_inactive": false,
  "candidate_status": "N",
  "cycles": [2026],
  "district": "04",
  "district_number": 4,
  "election_districts": ["04"],
  "election_years": [2026],
  "federal_funds_flag": false,
  "first_file_date": "2025-02-20",
  "has_raised_funds": false,
  "inactive_election_years": null,
  "incumbent_challenge": "C",
  "incumbent_challenge_full": "Challenger",
  "last_f2_date": "2025-02-20",
  "last_file_date": "2025-02-20",
  "load_date": "2025-03-13T20:59:32",
  "name": "AARON, RICHARD",
  "office": "H",
  "office_full": "House",
  "party": "DEM",
  "party_full": "DEMOCRATIC PARTY",
  "state": "MI"
}
```

**Total Records:** 5,185 candidates (2,841 House + 2,344 Senate for 2026 cycle)

---

## 2. FINANCIAL_SUMMARY TABLE

**Status:** Created manually in Supabase from FEC API response
**Source Data:** FEC `/candidate/{id}/totals/` endpoint
**Created By:** `fetch_fec_data.py` lines 86-120 (`fetch_candidate_financials()`)
**Loaded To DB:** Manual Supabase insert
**Frontend Query:** `apps/labs/src/hooks/useCandidateData.ts` lines 68-71

### Actual Schema (From Code Analysis)
```sql
CREATE TABLE financial_summary (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) UNIQUE NOT NULL REFERENCES candidates(candidate_id),
  cycle INTEGER NOT NULL,
  
  -- Cumulative cycle totals
  total_receipts DECIMAL(15,2),
  total_disbursements DECIMAL(15,2),
  cash_on_hand DECIMAL(15,2),
  
  -- Coverage period
  coverage_start_date TIMESTAMP,
  coverage_end_date TIMESTAMP,
  
  -- Report metadata
  report_year INTEGER,
  report_type VARCHAR(100),
  last_report_type VARCHAR(100),
  last_report_type_full VARCHAR(100),
  
  -- FEC metadata
  committee_id VARCHAR(9),
  filing_id BIGINT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(candidate_id, cycle, filing_id),
  FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE INDEX idx_fs_candidate_cycle ON financial_summary(candidate_id, cycle);
CREATE INDEX idx_fs_cycle ON financial_summary(cycle);
CREATE INDEX idx_fs_updated ON financial_summary(updated_at);
```

### Actual Data Sample
From `/Users/benjaminnelson/Desktop/fec-dashboard/financials_2026.json`:
```json
{
  "candidate_id": "H2NY12197",
  "name": "ABDELHAMID, RANA",
  "party": "DEMOCRATIC PARTY",
  "state": "NY",
  "district": "12",
  "office": "House",
  "total_receipts": 2652.99,
  "total_disbursements": 8213.09,
  "cash_on_hand": 105109.7,
  "coverage_start_date": "2025-01-01T00:00:00",
  "coverage_end_date": "2025-09-30T00:00:00",
  "last_report_year": 2025,
  "last_report_type": "OCTOBER QUARTERLY",
  "cycle": 2026
}
```

**Total Records:** 5,185 (one per candidate)
**Data Characteristics:**
- 32% have $0 total_receipts (candidates who haven't raised money)
- coverage_end_date is typically the latest quarter end date (Q3 = Sept 30, Q4 = Dec 31)
- CUMULATIVE totals for entire cycle

### How Frontend Uses It
```typescript
// apps/labs/src/hooks/useCandidateData.ts lines 68-71
const { data: page, error: financialsError } = await browserClient
  .from("financial_summary")
  .select("candidate_id, total_receipts, total_disbursements, cash_on_hand, updated_at")
  .eq("cycle", filters.cycle)
  .range(from, from + PAGE_SIZE - 1);
```

---

## 3. QUARTERLY_FINANCIALS TABLE

**Status:** Created via SQL file at `/Users/benjaminnelson/Desktop/fec-dashboard/sql/create_quarterly_table.sql`
**Source Data:** FEC `/committee/{id}/filings/?form_type=F3` endpoint
**Created By:** `fetch_fec_data.py` lines 122-204 (`fetch_committee_quarterly_filings()`)
**Loaded To DB:** Manual Supabase insert
**Frontend Query:** `apps/labs/src/hooks/useQuarterlyData.ts` lines 74-79

### Actual Schema (SQL File)
```sql
CREATE TABLE IF NOT EXISTS quarterly_financials (
  id SERIAL PRIMARY KEY,

  -- Candidate information
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),
  cycle INTEGER NOT NULL,

  -- Quarter identification
  quarter VARCHAR(10),                     -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  report_type VARCHAR(100),                -- 'APRIL QUARTERLY', 'JULY QUARTERLY', etc.

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
```

### Table Comments
```sql
COMMENT ON TABLE quarterly_financials IS 'Individual quarterly FEC filings for timeseries analysis - stores per-quarter financial data for each candidate';
COMMENT ON COLUMN quarterly_financials.quarter IS 'Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)';
COMMENT ON COLUMN quarterly_financials.total_receipts IS 'Money raised during THIS QUARTER only (not cumulative)';
COMMENT ON COLUMN quarterly_financials.total_disbursements IS 'Money spent during THIS QUARTER only (not cumulative)';
COMMENT ON COLUMN quarterly_financials.cash_ending IS 'Cash on hand at END of this quarter';
```

### Actual Data Sample
From `/Users/benjaminnelson/Desktop/fec-dashboard/quarterly_financials_2026.json`:
```json
{
  "candidate_id": "H2NY12197",
  "name": "ABDELHAMID, RANA",
  "party": "DEMOCRATIC PARTY",
  "state": "NY",
  "district": "12",
  "office": "House",
  "committee_id": "C00776658",
  "filing_id": 1918383,
  "report_type": "OCTOBER QUARTERLY",
  "coverage_start_date": "2025-07-01",
  "coverage_end_date": "2025-09-30",
  "total_receipts": 0.0,
  "total_disbursements": 1121.24,
  "cash_beginning": 106230.94,
  "cash_ending": 105109.7,
  "is_amendment": false,
  "cycle": 2026
}
```

**Total Records:** ~20,000-25,000 quarterly filings
**Data Characteristics:**
- Multiple rows per candidate (one per quarter)
- total_receipts and total_disbursements are PER QUARTER ONLY (not cumulative)
- coverage_end_date determines which quarter (Jan-Mar=Q1, Apr-Jun=Q2, Jul-Sep=Q3, Oct-Dec=Q4)
- Some candidates have fewer than 4 quarterly records (e.g., late registrations, terminated)

### How Frontend Uses It
```typescript
// apps/labs/src/hooks/useQuarterlyData.ts lines 74-79
const { data: results, error: queryError } = await browserClient
  .from("quarterly_financials")
  .select("*")
  .in("candidate_id", ids)
  .eq("cycle", cycle)
  .order("coverage_end_date", { ascending: true });
```

Then maps to internal format (lines 85-102):
```typescript
const processed = results?.map((row) => ({
  candidateId: row.candidate_id,
  candidateName: row.name,
  party: row.party,
  state: row.state,
  district: row.district,
  reportType: row.report_type,
  coverageStart: row.coverage_start_date,
  coverageEnd: row.coverage_end_date,
  receipts: row.total_receipts ?? 0,
  disbursements: row.total_disbursements ?? 0,
  cashBeginning: row.cash_beginning ?? 0,
  cashEnding: row.cash_ending ?? 0,
  quarterLabel: row.coverage_end_date
    ? formatQuarterLabel(row.coverage_end_date)
    : row.report_type ?? "Unknown",
})) ?? [];
```

---

## 4. RELATED TABLES (User Features)

### user_profiles
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
**Location:** `/Users/benjaminnelson/Desktop/fec-dashboard/database/migrations/001_user_profiles.sql`

### user_candidate_follows
```sql
CREATE TABLE IF NOT EXISTS user_candidate_follows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  candidate_id VARCHAR(9) NOT NULL REFERENCES candidates(candidate_id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, candidate_id)
);
```
**Location:** `/Users/benjaminnelson/Desktop/fec-dashboard/database/migrations/002_user_candidate_follows.sql`

### notification_queue
```sql
CREATE TABLE IF NOT EXISTS notification_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  candidate_id VARCHAR(9) NOT NULL REFERENCES candidates(candidate_id),
  event_type VARCHAR(50) NOT NULL,
  event_data JSONB,
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMP WITH TIME ZONE
);
```
**Location:** `/Users/benjaminnelson/Desktop/fec-dashboard/database/migrations/003_notification_queue.sql`

---

## Data Loading Flow

### Current Process
```
FEC API
   ↓
fetch_fec_data.py (Python)
   ├─ Step 1: Fetch all candidates → candidates_2026.json
   ├─ Step 2: For each candidate, fetch totals → financials_2026.json
   ├─ Step 3: For each candidate, fetch quarterly filings → quarterly_financials_2026.json
   └─ Progress saved every 50 candidates
   
   ↓ (Manual insertion needed)
   
Supabase Database
   ├─ candidates table (5,185 rows)
   ├─ financial_summary table (5,185 rows)
   └─ quarterly_financials table (20,000+ rows)
   
   ↓ (Supabase client)
   
Frontend Application
   ├─ useCandidateData.ts (financial_summary table)
   └─ useQuarterlyData.ts (quarterly_financials table)
```

### Execution Time
- Data fetching: 6-8 hours (includes rate limiting 4s between requests)
- Progress: Saved every 50 candidates
- Resume capability: If interrupted, can continue from last saved index

---

## Key Characteristics

### Size
| Table | Records | Est. Size |
|-------|---------|-----------|
| candidates | 5,185 | ~2 MB |
| financial_summary | 5,185 | ~2 MB |
| quarterly_financials | 20,000-25,000 | ~10-12 MB |
| **TOTAL** | **30,370-35,370** | **14-16 MB** |

### Update Frequency
- Manual updates from FEC API when needed
- No automatic sync (would require scheduled job/webhook)
- Current data: 2026 election cycle (updated as of October 2025)

### Data Validation
- Quarterly receipts + disbursements should match financial_summary totals for each quarter
- cash_beginning of Q2 should equal cash_ending of Q1
- coverage_end_date determines quarter assignment (not report_type alone)

---

End of Actual Database Schemas Document
