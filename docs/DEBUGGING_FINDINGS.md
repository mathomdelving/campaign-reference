# FEC Dashboard Debugging Findings & Implementation Plan

**Date:** October 22, 2025
**Status:** Analysis Complete - Ready for Implementation

---

## Executive Summary

After thorough investigation of the FEC API and current codebase, I've identified the root causes of the data issues and created a comprehensive plan to fix them.

### Issues Identified

1. **Missing Quarterly Timeseries Data** ✅ ROOT CAUSE IDENTIFIED
   - Current implementation fetches `/candidate/{id}/totals/` which returns ONE cumulative total
   - We need to fetch `/committee/{id}/filings/` which returns quarterly reports
   - Example: Vindman shows $5.3M total, but we don't have Q1, Q2, Q3 breakdowns

2. **Some Financial Data Shows $0** ✅ EXPLAINED
   - 32% of candidates (909/2841) have $0 in total_receipts
   - These are legitimate - candidates who haven't filed or raised money yet
   - This is normal for early in the cycle

3. **Missing Candidates** ⚠️ NEEDS VERIFICATION
   - Need to verify specific examples from FEC website
   - May be due to:
     - Candidates who registered after our last data pull
     - Candidates in different cycles (2024 vs 2026)
     - Filtering issues in our query

---

## FEC API Structure Analysis

### Current Approach (WRONG)
```
/candidate/{candidate_id}/totals/?cycle=2026
```
**Returns:** Single cumulative total for the entire cycle
**Problem:** No quarterly breakdown, no timeseries

### Correct Approach (RIGHT)
```
1. /candidate/{candidate_id}/committees/?cycle=2026
   → Get committee_id(s) for the candidate

2. /committee/{committee_id}/filings/?cycle=2026&form_type=F3
   → Get ALL quarterly filings with detailed amounts
```

**Returns:** Individual quarterly reports with:
- `total_receipts` - Money raised this quarter
- `total_disbursements` - Money spent this quarter
- `cash_on_hand_end_period` - Cash at end of quarter
- `cash_on_hand_beginning_period` - Cash at start of quarter
- `coverage_start_date` / `coverage_end_date` - Quarter dates
- `report_type_full` - "APRIL QUARTERLY", "JULY QUARTERLY", etc.

### Real Example: Eugene Vindman (H4VA07234)

**Current Data (Cumulative):**
- Total Receipts: $5,325,053.15
- Total Disbursements: $2,329,785.05
- Coverage: 2025-01-01 to 2025-09-30

**Quarterly Breakdown (What We Need):**

| Quarter | Period | Raised | Spent | Cash on Hand |
|---------|--------|--------|-------|--------------|
| Q1 2025 | Jan-Mar | $2,065,104.31 | $964,354.03 | $1,235,684.02 |
| Q2 2025 | Apr-Jun | $1,602,668.11 | $731,667.72 | $2,106,684.41 |
| Q3 2025 | Jul-Sep | $1,657,280.73 | $633,763.30 | $3,130,201.84 |

**Data Validation:**
- Sum of quarterly receipts: $5,325,053.15 ✅ Matches cumulative
- Q3 ending cash: $3,130,201.84 ✅ Matches latest

---

## Database Schema Changes Required

### Current Schema (financial_summary table)
```sql
CREATE TABLE financial_summary (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  cycle INTEGER NOT NULL,
  total_receipts DECIMAL(15,2),           -- Cumulative only
  total_disbursements DECIMAL(15,2),      -- Cumulative only
  cash_on_hand DECIMAL(15,2),
  coverage_start_date DATE,
  coverage_end_date DATE,
  report_year INTEGER,
  report_type VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Proposed New Schema

**Option A: Keep Existing Table, Add New Columns**
```sql
ALTER TABLE financial_summary ADD COLUMN IF NOT EXISTS
  committee_id VARCHAR(9),
  filing_id BIGINT,                       -- FEC file_number
  quarter VARCHAR(10),                     -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  is_quarterly BOOLEAN DEFAULT false,      -- Distinguish quarterly vs cumulative
  beginning_cash DECIMAL(15,2),           -- Cash at start of period
  ending_cash DECIMAL(15,2),              -- Cash at end of period
  is_amendment BOOLEAN DEFAULT false;

-- New index for timeseries queries
CREATE INDEX idx_financial_quarter ON financial_summary(candidate_id, cycle, coverage_end_date);
CREATE INDEX idx_financial_committee ON financial_summary(committee_id);
```

**Option B: Create New quarterly_financials Table (RECOMMENDED)**
```sql
CREATE TABLE quarterly_financials (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),
  cycle INTEGER NOT NULL,
  quarter VARCHAR(10),                     -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  report_type VARCHAR(100),                -- 'APRIL QUARTERLY', etc.

  -- Period coverage
  coverage_start_date DATE,
  coverage_end_date DATE,

  -- Financial data for THIS QUARTER ONLY
  total_receipts DECIMAL(15,2),           -- Raised this quarter
  total_disbursements DECIMAL(15,2),      -- Spent this quarter
  cash_beginning DECIMAL(15,2),           -- Cash at start of quarter
  cash_ending DECIMAL(15,2),              -- Cash at end of quarter

  -- FEC metadata
  filing_id BIGINT,                       -- FEC file_number
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
```

**Recommendation:** Use Option B - creates clean separation between summary and timeseries data.

---

## Implementation Plan

### Phase 1: Schema Update ✅
1. Create new `quarterly_financials` table in Supabase
2. Keep existing `financial_summary` for backward compatibility
3. Add indexes for performant timeseries queries

### Phase 2: Update Data Fetching Script ✅
**File:** `fetch_fec_data.py`

**Changes needed:**
1. Add new function `fetch_committee_quarterly_filings(candidate_id, cycle)`
2. For each candidate:
   - Get committee_id via `/candidate/{id}/committees/`
   - Fetch all filings via `/committee/{committee_id}/filings/?form_type=F3`
   - Parse quarterly reports (skip termination reports, amendments, etc.)
   - Extract: receipts, disbursements, cash beginning/ending, dates
3. Save to new file: `quarterly_financials_2026.json`
4. Keep existing totals fetch for backward compatibility

**Key considerations:**
- Filter `form_type=F3` (House/Senate) or `F3X` (PACs)
- Filter for quarterly reports only (not monthly, termination, etc.)
- Handle amendments (take most recent filing per period)
- Rate limiting: Still 4-second delay between requests

### Phase 3: Update Database Loading Script ✅
**File:** `load_to_supabase.py`

**Changes needed:**
1. Add function to load quarterly_financials table
2. Parse quarter from coverage dates:
   - Jan-Mar = Q1
   - Apr-Jun = Q2
   - Jul-Sep = Q3
   - Oct-Dec = Q4
3. Handle duplicates via unique constraint
4. Batch insert (1000 records at a time)

### Phase 4: Update Frontend Data Hook ✅
**File:** `frontend/src/hooks/useCandidateData.js`

**Changes needed:**
1. Query both `financial_summary` (for current totals) AND `quarterly_financials` (for timeseries)
2. Return structure:
```javascript
{
  candidate_id: "H4VA07234",
  name: "VINDMAN, YEVGENY 'EUGENE'",
  party: "DEMOCRATIC PARTY",
  state: "VA",
  district: "07",
  office: "H",

  // Current totals (from financial_summary)
  totalReceipts: 5325053.15,
  totalDisbursements: 2329785.05,
  cashOnHand: 3130201.84,

  // Quarterly breakdown (from quarterly_financials)
  quarters: [
    {
      quarter: "Q1",
      year: 2025,
      period: "2025-01-01 to 2025-03-31",
      receipts: 2065104.31,
      disbursements: 964354.03,
      cashEnding: 1235684.02
    },
    {
      quarter: "Q2",
      year: 2025,
      period: "2025-04-01 to 2025-06-30",
      receipts: 1602668.11,
      disbursements: 731667.72,
      cashEnding: 2106684.41
    },
    // ...
  ]
}
```

### Phase 5: Update UI Components ✅

**A. Update RaceTable.jsx**
- Add expandable rows to show quarterly breakdown
- Click on candidate row → expand to show quarters table
- Use accordion/collapse pattern

**B. Create New TimeseriesChart.jsx**
- Line chart showing quarterly trends
- Multiple lines: Receipts, Disbursements, Cash on Hand
- X-axis: Quarters (Q1 2025, Q2 2025, etc.)
- Y-axis: Dollar amounts
- Tooltip: Show all metrics for selected quarter

**C. Update App.jsx**
- Add new view mode: "Table", "Chart", "Timeseries"
- Wire up new timeseries chart component

### Phase 6: Testing & Validation ✅
1. Test with known high-profile candidates (Vindman, etc.)
2. Verify quarterly totals sum to cumulative totals
3. Check for missing quarters (some candidates may skip quarters)
4. Validate date ranges and quarter assignments
5. Test UI responsiveness and data export

---

## Missing Candidates Investigation

To verify which candidates are missing, we need specific examples. Steps:

1. User provides candidate name(s) they see on FEC website
2. Search FEC API for that candidate
3. Check if candidate is in our `candidates_2026.json`
4. Check if candidate is in our `financial_summary` table
5. Diagnose why missing:
   - Wrong cycle?
   - Registered after our data pull?
   - API query filters excluding them?

**Action Required:** User to provide specific candidate name(s) that are missing

---

## Estimated Timeline

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| 1. Schema | Create quarterly_financials table | 15 min |
| 2. Fetch Script | Update fetch_fec_data.py | 1-2 hours |
| 3. Load Script | Update load_to_supabase.py | 30 min |
| 4. Data Collection | Re-run fetch for all 5,185 candidates | 6-8 hours |
| 5. Frontend Hook | Update useCandidateData.js | 45 min |
| 6. UI Table | Add expandable rows to RaceTable | 1 hour |
| 7. UI Chart | Create TimeseriesChart component | 1.5 hours |
| 8. Testing | Full pipeline testing | 1 hour |
| **TOTAL** | | **12-15 hours** (including 6-8 hour data collection run) |

---

## Risk Assessment

### Low Risk ✅
- Schema changes (additive, non-breaking)
- New table creation
- Backend data fetching improvements

### Medium Risk ⚠️
- Long data collection time (6-8 hours)
- Rate limiting may require overnight run
- Frontend component complexity (expandable rows, new chart)

### High Risk 🔴
- None identified

### Mitigation Strategies
1. Keep existing tables for backward compatibility
2. Test fetch script on small sample first (10 candidates)
3. Use progress saving for resume capability
4. Build UI incrementally (table first, then chart)

---

## Next Steps

**Immediate actions:**
1. Get user approval for implementation plan
2. Ask user for specific examples of "missing candidates"
3. Create quarterly_financials table schema
4. Update fetch_fec_data.py to collect quarterly data
5. Test on small sample (10 candidates)
6. Once validated, run full data collection
7. Build frontend timeseries components

**Questions for User:**
1. Can you provide specific candidate name(s) that you see on FEC website but not in dashboard?
2. Do you want to keep existing summary data and ADD quarterly, or replace entirely?
3. Should we backfill 2024 cycle quarterly data as well, or just 2026?
4. What's your preferred approach for displaying timeseries in the UI?
   - Expandable table rows?
   - Separate timeseries chart view?
   - Both?

---

## Appendix: FEC API Endpoints Reference

### Candidates
- `GET /candidates/` - List all candidates
- `GET /candidates/search/` - Search by name
- `GET /candidate/{id}/` - Single candidate details
- `GET /candidate/{id}/committees/` - Get committees for candidate
- `GET /candidate/{id}/totals/` - Cumulative totals (what we use now)

### Committees
- `GET /committee/{id}/` - Committee details
- `GET /committee/{id}/filings/` - ALL filings (quarterly, amendments, etc.) ⭐ **USE THIS**
- `GET /committee/{id}/reports/` - Summary reports (sometimes incomplete)

### Filings Parameters
- `form_type`: F3 (House/Senate), F3X (PAC), F3P (Presidential)
- `report_type`: Q1, Q2, Q3, Q4, YE (year-end), M2 (monthly), etc.
- `cycle`: 2026, 2024, etc.
- `sort`: -coverage_end_date (most recent first)

---

**End of Report**
