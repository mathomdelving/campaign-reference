# FEC Bulk Data Integration Guide

## Overview

This guide explains how FEC bulk CSV data files map to the FEC Dashboard's database schema. It covers:
1. Understanding FEC bulk data formats
2. Exact database schemas and column definitions
3. Complete mappings from FEC files to database tables
4. Real examples and data flows
5. Implementation guidance for bulk CSV imports

## Quick Summary

The FEC Dashboard stores campaign finance data in 3 main tables:

| Table | Purpose | Source | Records | Use Case |
|-------|---------|--------|---------|----------|
| **candidates** | Candidate registration info | `/candidates/` API | 5,185 | Filtering, display |
| **financial_summary** | Cumulative cycle totals | `/candidate/{id}/totals/` API | 5,185 | Leaderboard rankings |
| **quarterly_financials** | Per-quarter breakdowns | `/committee/{id}/filings/` API | ~20,000 | Timeseries charts |

## Documentation Files

This guide is split into 3 focused documents:

### 1. **FEC_SCHEMA_MAPPING.md** - The Main Reference
- Complete FEC API to database schema mapping
- Field-by-field column definitions
- Example data for each table
- FEC API endpoint documentation
- Quarter calculation logic
- Data flow diagrams

**Use this to:**
- Create tables from scratch
- Understand FEC API response structure
- Map between FEC fields and database columns
- Validate data quality

### 2. **ACTUAL_DATABASE_SCHEMAS.md** - Implementation Details
- Exact SQL schemas as defined in this project
- File locations and code references
- How frontend accesses the data
- Sample JSON data from existing files
- Key characteristics and data validation rules
- Data loading process overview

**Use this to:**
- See actual table definitions used in production
- Understand current implementation
- Reference backend/frontend integration
- Debug data issues

### 3. **FEC_QUICK_REFERENCE.md** - Quick Lookup
- File locations and code references
- SQL schema quick view
- FEC API endpoints summary
- Checklists and common issues
- Test queries
- Next steps for implementation

**Use this to:**
- Find specific files quickly
- Look up schema details
- Copy/paste common queries
- Troubleshoot problems

## File Locations

### Source Code
```
/Users/benjaminnelson/Desktop/campaign-reference/
├── fetch_fec_data.py          # Python script to fetch from FEC API
├── sql/
│   └── create_quarterly_table.sql
└── apps/labs/src/hooks/
    ├── useCandidateData.ts     # Frontend query: financial_summary
    └── useQuarterlyData.ts     # Frontend query: quarterly_financials
```

### Documentation
```
/Users/benjaminnelson/Desktop/campaign-reference/docs/
├── fec_schema_mapping.md           # MAIN REFERENCE
├── actual_database_schemas.md      # IMPLEMENTATION
├── fec_quick_reference.md          # QUICK LOOKUP
├── FEC_BULK_DATA_GUIDE.md          # THIS FILE
├── DEBUGGING_FINDINGS.md           # Historical analysis
└── IMPLEMENTATION_PLAN.md          # Original plan
```

### Generated Data Files
```
/Users/benjaminnelson/Desktop/campaign-reference/
├── candidates_2026.json            # 5,185 candidates
├── financials_2026.json            # Financial summaries
└── quarterly_financials_2026.json  # ~20,000 quarterly records
```

## Working with Bulk CSV Files

If you're working with FEC bulk CSV exports instead of the API:

### Expected CSV Structure

#### candidates_2026.csv
```csv
candidate_id,name,party,party_full,state,district,office,office_full,cycle,active_through,candidate_status
H4VA07234,VINDMAN YEVGENY 'EUGENE',DEM,DEMOCRATIC PARTY,VA,07,H,House,2026,2026,N
H2NY12197,ABDELHAMID RANA,DEM,DEMOCRATIC PARTY,NY,12,H,House,2026,2026,N
```

Minimal required columns:
- candidate_id
- name
- party
- state
- district
- office ('H' or 'S')
- cycle

#### financial_summary_2026.csv
```csv
candidate_id,cycle,total_receipts,total_disbursements,cash_on_hand,coverage_end_date,report_type
H4VA07234,2026,5325053.15,2329785.05,3130201.84,2025-09-30,OCTOBER QUARTERLY
H2NY12197,2026,2652.99,8213.09,105109.7,2025-09-30,OCTOBER QUARTERLY
```

Minimal required columns:
- candidate_id
- cycle
- total_receipts (CUMULATIVE for entire cycle)
- total_disbursements (CUMULATIVE for entire cycle)
- cash_on_hand
- coverage_end_date

#### quarterly_financials_2026.csv
```csv
candidate_id,committee_id,cycle,quarter,report_type,coverage_start_date,coverage_end_date,total_receipts,total_disbursements,cash_beginning,cash_ending,filing_id
H4VA07234,C00776658,2026,Q1,APRIL QUARTERLY,2025-01-01,2025-03-31,2065104.31,964354.03,0.00,1235684.02,1885857
H4VA07234,C00776658,2026,Q2,JULY QUARTERLY,2025-04-01,2025-06-30,1602668.11,731667.72,1235684.02,2106684.41,1899742
H4VA07234,C00776658,2026,Q3,OCTOBER QUARTERLY,2025-07-01,2025-09-30,1657280.73,633763.30,2106684.41,3130201.84,1918383
```

Minimal required columns:
- candidate_id
- cycle
- quarter (calculated from coverage_end_date)
- coverage_start_date
- coverage_end_date
- total_receipts (THIS QUARTER ONLY - not cumulative)
- total_disbursements (THIS QUARTER ONLY - not cumulative)
- cash_beginning
- cash_ending

## Key Differences: Quarterly vs Cumulative

This is THE most important concept:

### Financial Summary (CUMULATIVE)
- One row per candidate per cycle
- `total_receipts` = SUM of all money raised in the cycle
- `total_disbursements` = SUM of all money spent in the cycle
- `cash_on_hand` = Latest balance (usually end of last quarter)

### Quarterly Financials (PER QUARTER)
- Multiple rows per candidate (one per quarter filed)
- `total_receipts` = Money raised ONLY in that quarter
- `total_disbursements` = Money spent ONLY in that quarter
- `cash_beginning` = Balance at START of quarter
- `cash_ending` = Balance at END of quarter

### Example: Eugene Vindman
**Cumulative (financial_summary):**
```
total_receipts = $5,325,053.15  (all of 2025)
total_disbursements = $2,329,785.05  (all of 2025)
```

**Quarterly (quarterly_financials):**
```
Q1 2025: receipts $2,065,104.31, disbursements $964,354.03
Q2 2025: receipts $1,602,668.11, disbursements $731,667.72
Q3 2025: receipts $1,657,280.73, disbursements $633,763.30
Total:   receipts $5,325,053.15, disbursements $2,329,785.05 ✅
```

## Importing Bulk CSV Files

### Step 1: Prepare CSV Files
Ensure your CSV files have:
1. Correct column names (match table definitions)
2. Proper date formats (YYYY-MM-DD)
3. Decimal values for currency fields
4. No header rows repeated in data

### Step 2: Create Database Tables
Use the SQL in `fec_schema_mapping.md` or `actual_database_schemas.md`

### Step 3: Import Data
Using Supabase CLI:
```bash
supabase migration up

# Then insert data via Python or another script
```

### Step 4: Validate Data
Run validation checks:
```sql
-- Verify quarterly totals match summaries
SELECT c.candidate_id, c.name,
  (SELECT SUM(total_receipts) FROM quarterly_financials q 
   WHERE q.candidate_id = c.candidate_id AND q.cycle = 2026) as quarterly_sum,
  f.total_receipts
FROM candidates c
JOIN financial_summary f ON c.candidate_id = f.candidate_id
WHERE c.cycle = 2026 AND f.cycle = 2026
AND ABS(f.total_receipts - 
  (SELECT SUM(total_receipts) FROM quarterly_financials q 
   WHERE q.candidate_id = c.candidate_id AND q.cycle = 2026)) > 0.01
LIMIT 10;
```

## Understanding FEC API Responses

The FEC API returns different information depending on the endpoint:

### /candidates/ Response
```json
{
  "candidate_id": "H4VA07234",
  "name": "VINDMAN, YEVGENY 'EUGENE'",
  "office": "H",
  "state": "VA",
  "district": "07",
  "party": "DEM",
  ...
}
```
Maps to: **candidates** table

### /candidate/{id}/totals/ Response
```json
{
  "candidate_id": "H4VA07234",
  "receipts": 5325053.15,
  "disbursements": 2329785.05,
  "cash_on_hand": 3130201.84,
  "coverage_end_date": "2025-09-30"
}
```
Maps to: **financial_summary** table (CUMULATIVE)

### /committee/{id}/filings/ Response
```json
{
  "file_number": 1918383,
  "report_type_full": "OCTOBER QUARTERLY",
  "coverage_start_date": "2025-07-01",
  "coverage_end_date": "2025-09-30",
  "total_receipts": 0.0,
  "total_disbursements": 1121.24,
  "cash_on_hand_beginning_period": 106230.94,
  "cash_on_hand_end_period": 105109.7
}
```
Maps to: **quarterly_financials** table (PER QUARTER)

## Data Quality Checks

Always run these checks after importing:

```sql
-- 1. Check for missing candidates
SELECT COUNT(*) FROM financial_summary f
WHERE NOT EXISTS (SELECT 1 FROM candidates c WHERE c.candidate_id = f.candidate_id);

-- 2. Verify quarterly sums match summaries
SELECT COUNT(*) FROM financial_summary f
WHERE ABS(f.total_receipts - COALESCE((
  SELECT SUM(total_receipts) FROM quarterly_financials q
  WHERE q.candidate_id = f.candidate_id AND q.cycle = f.cycle), 0)) > 0.01;

-- 3. Check for invalid dates
SELECT COUNT(*) FROM quarterly_financials
WHERE coverage_start_date > coverage_end_date;

-- 4. Verify quarter assignments
SELECT COUNT(*) FROM quarterly_financials
WHERE quarter != CASE
  WHEN EXTRACT(MONTH FROM coverage_end_date) <= 3 THEN 'Q1'
  WHEN EXTRACT(MONTH FROM coverage_end_date) <= 6 THEN 'Q2'
  WHEN EXTRACT(MONTH FROM coverage_end_date) <= 9 THEN 'Q3'
  ELSE 'Q4'
END;

-- 5. Check for cash flow continuity
SELECT DISTINCT 
  q1.candidate_id,
  q1.cash_ending as q1_ending,
  q2.cash_beginning as q2_beginning
FROM quarterly_financials q1
JOIN quarterly_financials q2 ON 
  q1.candidate_id = q2.candidate_id AND
  q1.cycle = q2.cycle
WHERE q1.quarter = 'Q1' AND q2.quarter = 'Q2'
AND ABS(q1.cash_ending - q2.cash_beginning) > 0.01;
```

## Using the Data in Your Application

### Query Financial Summary (Leaderboard)
```typescript
// Frontend hook: useCandidateData.ts
const { data: page } = await client
  .from("financial_summary")
  .select("candidate_id, total_receipts, total_disbursements, cash_on_hand")
  .eq("cycle", 2026)
  .range(0, 999);
```

### Query Quarterly Data (Charts)
```typescript
// Frontend hook: useQuarterlyData.ts
const { data: results } = await client
  .from("quarterly_financials")
  .select("*")
  .in("candidate_id", ["H4VA07234"])
  .eq("cycle", 2026)
  .order("coverage_end_date", { ascending: true });
```

## Common Pitfalls

1. **Forgetting quarterly is per-quarter, not cumulative**
   - total_receipts in quarterly_financials is ONLY for that quarter
   - Don't try to use it as a running total

2. **Mismatching quarters with report types**
   - Use coverage_end_date to determine quarter, not report_type
   - "APRIL QUARTERLY" always ends on 3/31 (Q1), not 4/30

3. **Missing foreign key relationships**
   - quarterly_financials.candidate_id must exist in candidates
   - financial_summary.candidate_id must exist in candidates

4. **Not handling amendments**
   - If is_amendment=true, it's a corrected version of an earlier filing
   - Use unique constraint to handle duplicates

5. **Wrong date format**
   - Always use YYYY-MM-DD format
   - Some CSV tools export as MM/DD/YYYY by default

## Next Steps

1. Review **FEC_SCHEMA_MAPPING.md** for complete field definitions
2. Check **ACTUAL_DATABASE_SCHEMAS.md** for production table structure
3. Use **FEC_QUICK_REFERENCE.md** for quick lookups during implementation
4. Follow the data import steps above
5. Run the validation SQL queries
6. Test with sample data (Eugene Vindman: H4VA07234)

## Questions?

Refer to the specific documentation:
- **"What fields should I have?"** → FEC_SCHEMA_MAPPING.md
- **"How is this table structured?"** → ACTUAL_DATABASE_SCHEMAS.md  
- **"Where is file X?"** → FEC_QUICK_REFERENCE.md
- **"What's the original plan?"** → IMPLEMENTATION_PLAN.md

---

**Created:** November 2, 2025
**Last Updated:** November 2, 2025
**Data Version:** 2026 Election Cycle (Q1-Q3 2025 data)

