# FEC Dashboard - Quick Reference Guide

## Key Files & Locations

### Python Data Fetching
- **Main Script:** `/Users/benjaminnelson/Desktop/campaign-reference/fetch_fec_data.py`
  - Lines 38-84: `fetch_candidates()` - Gets all House/Senate candidates
  - Lines 86-120: `fetch_candidate_financials()` - Gets cumulative totals for each candidate
  - Lines 122-204: `fetch_committee_quarterly_filings()` - Gets quarterly filings with timeseries data
  - Lines 206-360: `main()` - Orchestrates fetching and saving to JSON files

### SQL Schemas
- **Quarterly Table:** `/Users/benjaminnelson/Desktop/campaign-reference/sql/create_quarterly_table.sql`
- **User Features:** `/Users/benjaminnelson/Desktop/campaign-reference/database/migrations/`
  - `001_user_profiles.sql`
  - `002_user_candidate_follows.sql`
  - `003_notification_queue.sql`

### Frontend Data Hooks
- **Candidate Data:** `/Users/benjaminnelson/Desktop/campaign-reference/apps/labs/src/hooks/useCandidateData.ts`
  - Fetches: `financial_summary` table
  - Returns: LeaderboardCandidate[] with totals and metadata
  - Lines 68-71: Main query to financial_summary

- **Quarterly Data:** `/Users/benjaminnelson/Desktop/campaign-reference/apps/labs/src/hooks/useQuarterlyData.ts`
  - Fetches: `quarterly_financials` table
  - Returns: QuarterlyRecord[] with per-quarter breakdowns
  - Lines 74-79: Main query to quarterly_financials

### Generated Data Files
- `candidates_2026.json` - 5,185 candidates (House + Senate)
- `financials_2026.json` - Financial summaries with cumulative totals
- `quarterly_financials_2026.json` - ~20,000 quarterly filings

### Documentation
- **Schema Analysis:** `/Users/benjaminnelson/Desktop/campaign-reference/docs/DEBUGGING_FINDINGS.md`
- **Implementation Plan:** `/Users/benjaminnelson/Desktop/campaign-reference/docs/IMPLEMENTATION_PLAN.md`

---

## Database Schema Quick View

### 3 Main Tables

#### 1. candidates
```
One row per candidate per cycle (5,185 rows)
├─ candidate_id (PK)
├─ name
├─ party / party_full
├─ state / district
├─ office (H or S)
└─ ... (registration metadata)
```

#### 2. financial_summary
```
One row per candidate per cycle (5,185 rows)
├─ candidate_id (FK) (PK)
├─ total_receipts (CUMULATIVE)
├─ total_disbursements (CUMULATIVE)
├─ cash_on_hand (latest)
├─ coverage_end_date
└─ report_type
```

#### 3. quarterly_financials
```
Multiple rows per candidate per cycle (~20,000 rows)
├─ candidate_id (FK)
├─ quarter ('Q1', 'Q2', 'Q3', 'Q4')
├─ total_receipts (THIS QUARTER ONLY)
├─ total_disbursements (THIS QUARTER ONLY)
├─ cash_beginning / cash_ending
├─ coverage_start_date / coverage_end_date
└─ filing_id
```

---

## FEC API Endpoints Used

### Step 1: Fetch Candidates
```
GET https://api.open.fec.gov/v1/candidates/
Parameters:
  - api_key: {FEC_API_KEY}
  - cycle: 2026
  - office: 'H' or 'S'
  - per_page: 100
  - page: 1-N
  - sort: 'name'
```
**Output:** Populates `candidates` table

### Step 2: Fetch Financial Totals
```
GET https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/
Parameters:
  - api_key: {FEC_API_KEY}
  - cycle: 2026
```
**Output:** Populates `financial_summary` table (cumulative only)

### Step 3: Get Committee IDs
```
GET https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/
Parameters:
  - api_key: {FEC_API_KEY}
  - cycle: 2026
```
**Output:** Committee IDs for each candidate

### Step 4: Fetch Quarterly Filings
```
GET https://api.open.fec.gov/v1/committee/{committee_id}/filings/
Parameters:
  - api_key: {FEC_API_KEY}
  - cycle: 2026
  - form_type: 'F3' (House/Senate) or 'F3X' (PAC)
  - sort: '-coverage_end_date'
  - per_page: 20
```
**Output:** Populates `quarterly_financials` table (timeseries)

---

## Data Structure Mapping

### From FEC API to JSON

#### candidates_2026.json
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
  "active_through": 2026,
  "candidate_status": "N",
  "has_raised_funds": true,
  "load_date": "2025-03-13T20:59:32"
}
```

#### financials_2026.json
```json
{
  "candidate_id": "H4VA07234",
  "name": "VINDMAN, YEVGENY 'EUGENE'",
  "cycle": 2026,
  "total_receipts": 5325053.15,          // CUMULATIVE for entire cycle
  "total_disbursements": 2329785.05,     // CUMULATIVE for entire cycle
  "cash_on_hand": 3130201.84,            // Latest balance
  "coverage_start_date": "2025-01-01T00:00:00",
  "coverage_end_date": "2025-09-30T00:00:00",
  "last_report_type": "OCTOBER QUARTERLY"
}
```

#### quarterly_financials_2026.json
```json
[
  {
    "candidate_id": "H4VA07234",
    "quarter": "Q1",
    "report_type": "APRIL QUARTERLY",
    "coverage_start_date": "2025-01-01",
    "coverage_end_date": "2025-03-31",
    "total_receipts": 2065104.31,        // Q1 ONLY
    "total_disbursements": 964354.03,    // Q1 ONLY
    "cash_beginning": 0.00,
    "cash_ending": 1235684.02,
    "filing_id": 1885857,
    "is_amendment": false,
    "cycle": 2026
  },
  {
    "candidate_id": "H4VA07234",
    "quarter": "Q2",
    "report_type": "JULY QUARTERLY",
    "coverage_start_date": "2025-04-01",
    "coverage_end_date": "2025-06-30",
    "total_receipts": 1602668.11,        // Q2 ONLY
    "total_disbursements": 731667.72,    // Q2 ONLY
    "cash_beginning": 1235684.02,
    "cash_ending": 2106684.41,
    "filing_id": 1899742,
    "is_amendment": false,
    "cycle": 2026
  },
  {
    "candidate_id": "H4VA07234",
    "quarter": "Q3",
    "report_type": "OCTOBER QUARTERLY",
    "coverage_start_date": "2025-07-01",
    "coverage_end_date": "2025-09-30",
    "total_receipts": 1657280.73,        // Q3 ONLY
    "total_disbursements": 633763.30,    // Q3 ONLY
    "cash_beginning": 2106684.41,
    "cash_ending": 3130201.84,
    "filing_id": 1918383,
    "is_amendment": false,
    "cycle": 2026
  }
]
```

---

## Key Implementation Details

### Quarter Determination
```python
def get_quarter(coverage_end_date):
    month = coverage_end_date.month
    if month <= 3:
        return 'Q1'  # Jan-Mar
    elif month <= 6:
        return 'Q2'  # Apr-Jun
    elif month <= 9:
        return 'Q3'  # Jul-Sep
    else:
        return 'Q4'  # Oct-Dec
```

### Rate Limiting
- FEC API: 1,000 requests/hour
- Implementation: 4-second delay between EACH API call
- Resume: Progress saved every 50 candidates, can resume from last checkpoint

### Field Type Mappings
```
candidate_id:              VARCHAR(9)     // Fixed 9-char FEC ID
name:                      VARCHAR(255)   // Full name from FEC
party:                     VARCHAR(100)   // 3-char party code
total_receipts:            DECIMAL(15,2)  // Dollar amounts
total_disbursements:       DECIMAL(15,2)  // Dollar amounts
cash_on_hand:              DECIMAL(15,2)  // Dollar amounts
coverage_start_date:       DATE           // YYYY-MM-DD
coverage_end_date:         DATE           // YYYY-MM-DD
report_type:               VARCHAR(100)   // "APRIL QUARTERLY", etc.
filing_id:                 BIGINT         // FEC file_number
cycle:                     INTEGER        // Election cycle year
```

---

## Data Validation Checks

### Financial Summary vs Quarterly
- Sum of all quarterly total_receipts MUST equal financial_summary.total_receipts
- Sum of all quarterly total_disbursements MUST equal financial_summary.total_disbursements
- financial_summary.cash_on_hand MUST equal the last quarter's cash_ending

### Quarter Continuity
- Q2 cash_beginning SHOULD equal Q1 cash_ending
- Q3 cash_beginning SHOULD equal Q2 cash_ending
- Q4 cash_beginning SHOULD equal Q3 cash_ending

### Date Ranges
- coverage_start_date is INCLUSIVE (e.g., "2025-01-01")
- coverage_end_date is INCLUSIVE (e.g., "2025-03-31")
- Each quarter should have exactly 3 months
  - Q1: 1/1 - 3/31
  - Q2: 4/1 - 6/30
  - Q3: 7/1 - 9/30
  - Q4: 10/1 - 12/31

---

## Testing with Sample Data

### High-Profile Candidates (from data)
1. **Eugene Vindman** (H4VA07234)
   - $5.3M raised
   - 3 quarterly filings
   - Strong fundraiser

2. **Rana Abdelhamid** (H2NY12197)
   - $2.6K raised
   - 3 quarterly filings
   - Lower fundraiser

### Test Queries

#### Get all candidates in VA-07
```sql
SELECT * FROM candidates 
WHERE state = 'VA' AND district = '07' AND cycle = 2026;
```

#### Get financial summary for specific candidate
```sql
SELECT * FROM financial_summary 
WHERE candidate_id = 'H4VA07234' AND cycle = 2026;
```

#### Get quarterly breakdown for specific candidate
```sql
SELECT * FROM quarterly_financials 
WHERE candidate_id = 'H4VA07234' AND cycle = 2026 
ORDER BY coverage_end_date ASC;
```

#### Verify quarterly totals match summary
```sql
SELECT 
  candidate_id,
  SUM(total_receipts) as quarterly_sum
FROM quarterly_financials
WHERE cycle = 2026
GROUP BY candidate_id
HAVING SUM(total_receipts) > 0
LIMIT 10;

-- Compare with financial_summary.total_receipts
```

---

## Common Issues & Solutions

### Issue: CSV/JSON files don't have all expected columns
**Solution:** FEC API only returns fields that have data. Use defaults for missing fields.

### Issue: Some quarters are missing for a candidate
**Solution:** This is normal. Candidates may file late, terminate early, or skip quarters.

### Issue: Amendment vs Original filings
**Solution:** The unique constraint uses (candidate_id, cycle, coverage_end_date, filing_id). If is_amendment=true, it's a corrected version of a previous filing.

### Issue: Data doesn't match FEC website
**Solution:** 
1. Verify you're looking at same cycle (2026)
2. Quarterly reports show THAT QUARTER'S activity, not cumulative
3. Some candidates have multiple committees (rare - use principal only)

---

## Next Steps for Implementation

1. Create bulk CSV import script
2. Transform FEC bulk files to match schema
3. Load data into Supabase using Supabase CLI or Python client
4. Validate data integrity (quarterly sums, date ranges)
5. Test frontend queries
6. Set up automated refresh (if needed)

---

End of Quick Reference
