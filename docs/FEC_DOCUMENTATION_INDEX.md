# FEC Dashboard Documentation Index

## Overview

This index guides you to the complete FEC bulk data documentation created for the FEC Dashboard project. These documents provide everything needed to understand how FEC bulk CSV files map to the application's Supabase database schema.

---

## Quick Navigation

### START HERE: Main Entry Point
**File:** `data/FEC_API_GUIDE.md` (26 KB, comprehensive)
- Complete FEC OpenFEC API reference
- Authentication and rate limits
- All major endpoints (candidates, totals, reports)
- Data structures and field descriptions
- Common usage patterns with code examples
- Best practices and optimization tips

### For Complete Field Mappings
**File:** `data/FEC_SCHEMA_REFERENCE.md` (24 KB, comprehensive)
- Exact column names and PostgreSQL types for each table
- Field-by-field FEC API to database mappings
- SQL CREATE TABLE statements
- Real example data and transformations
- Data type reference and validation queries

### For Implementation Details
**File:** `data/FEC_INTEGRATION_PATTERNS.md` (20 KB, comprehensive)
- Complete data flow architecture
- Python collection scripts documentation
- Frontend TypeScript hooks documentation
- Common integration patterns with code examples
- Best practices for data collection and querying

### For Quick Troubleshooting
**File:** `data/FEC_TROUBLESHOOTING_GUIDE.md` (15 KB, comprehensive)
- Solutions to common API issues
- Data collection problem fixes
- Database query optimization
- Data quality troubleshooting
- Frontend integration debugging
- Quick fixes and error message reference

---

## What's Documented

### Three Main Database Tables

#### 1. candidates
- **Records:** 5,185 (2026 cycle)
- **Purpose:** Candidate registration information
- **Source:** FEC `/candidates/` API endpoint
- **Contains:** Name, party, state, district, office, registration metadata
- **Used for:** Filtering, display, lookups

#### 2. financial_summary
- **Records:** 5,185 (one per candidate)
- **Purpose:** Cumulative cycle totals
- **Source:** FEC `/candidate/{id}/totals/` API endpoint
- **Contains:** Total receipts, disbursements, cash on hand, report dates
- **Used for:** Leaderboard rankings, candidate overview
- **Key:** All financial fields are CUMULATIVE for the entire cycle

#### 3. quarterly_financials
- **Records:** ~20,000 (multiple per candidate)
- **Purpose:** Per-quarter financial breakdown for timeseries
- **Source:** FEC `/committee/{id}/filings/` API endpoint
- **Contains:** Quarterly receipts, disbursements, cash flows, filing metadata
- **Used for:** Timeseries charts, quarterly trends
- **Key:** All financial fields are PER-QUARTER ONLY, not cumulative

### Data Files Available
- `candidates_2026.json` - 5,185 candidates
- `financials_2026.json` - Financial summaries
- `quarterly_financials_2026.json` - ~20,000 quarterly filings

---

## Reading Guide by Use Case

### "I need to understand the FEC API"
1. Read: `data/FEC_API_GUIDE.md` (complete API reference)
2. Reference: `data/FEC_SCHEMA_REFERENCE.md` (field mappings)
3. Troubleshoot: `data/FEC_TROUBLESHOOTING_GUIDE.md` (common issues)

### "I need to create database tables"
1. Read: `data/FEC_SCHEMA_REFERENCE.md` (SQL CREATE statements)
2. Reference: `data/database-schema.md` (complete current schema)
3. Validate: SQL queries in `data/FEC_SCHEMA_REFERENCE.md`

### "I need to collect FEC data"
1. Read: `guides/collection-guide.md` (quick start)
2. Reference: `data/FEC_INTEGRATION_PATTERNS.md` (collection scripts)
3. Follow: 2-step workflow in `DATA_COLLECTION_WORKFLOW.md`

### "I'm debugging data issues"
1. Start: `data/FEC_TROUBLESHOOTING_GUIDE.md` (common problems)
2. Reference: `data/FEC_SCHEMA_REFERENCE.md` (validation queries)
3. Check: `history/lessons-learned.md` (past issues)

### "I need to integrate with frontend"
1. Read: `data/FEC_INTEGRATION_PATTERNS.md` (frontend hooks)
2. Reference: `data/FEC_SCHEMA_REFERENCE.md` (data structures)
3. Example: Code patterns in `data/FEC_INTEGRATION_PATTERNS.md`

---

## Key Concepts Explained

### Quarterly vs Cumulative (MOST IMPORTANT)

**financial_summary (CUMULATIVE):**
```
One row per candidate per cycle
total_receipts = SUM of all money raised
total_disbursements = SUM of all money spent
cash_on_hand = Latest balance
```

**quarterly_financials (PER QUARTER):**
```
Multiple rows per candidate (one per quarter)
total_receipts = Money raised ONLY that quarter
total_disbursements = Money spent ONLY that quarter
cash_beginning = Balance at quarter start
cash_ending = Balance at quarter end
```

### Quarter Assignment
- Q1: January - March (1/1 to 3/31)
- Q2: April - June (4/1 to 6/30)
- Q3: July - September (7/1 to 9/30)
- Q4: October - December (10/1 to 12/31)

Determined by `coverage_end_date`, not report type name.

### FEC Bulk Data Files
- Format: JSON arrays or CSV (comma-separated values)
- Field format: Snake_case or camelCase depending on API version
- Date format: YYYY-MM-DD
- Currency: Decimal with 2 decimal places
- IDs: 9-character FEC identifiers

---

## File Organization

### Documentation Files
```
/docs/
├── FEC_DOCUMENTATION_INDEX.md              ← You are here
├── DATA_COLLECTION_WORKFLOW.md             ← **CRITICAL** 2-step workflow
├── data/
│   ├── FEC_API_GUIDE.md                   ← **START HERE** - Complete API reference
│   ├── FEC_SCHEMA_REFERENCE.md            ← Field mappings & database schema
│   ├── FEC_INTEGRATION_PATTERNS.md        ← Integration with our app
│   ├── FEC_TROUBLESHOOTING_GUIDE.md       ← Problem solving
│   ├── database-schema.md                  ← Current production schema
│   ├── data-model-summary.md               ← Data model overview
│   └── bulk-import.md                      ← Bulk import procedures
├── guides/
│   ├── collection-guide.md                 ← Quick reference for collection
│   └── political-persons.md                ← Political persons system
└── history/
    ├── lessons-learned.md                  ← Past issues & solutions
    └── ...
```

### Source Code
```
/
├── scripts/
│   ├── data-collection/
│   │   └── fetch_fec_data.py              ← Full collection
│   └── data-loading/
│       ├── incremental_update.py           ← Daily updates
│       └── load_to_supabase.py             ← Load JSON to database
├── sql/
│   └── migrations/                         ← Database migrations
└── apps/labs/src/hooks/
    ├── useCandidateData.ts                 ← Frontend: financial_summary
    ├── useQuarterlyData.ts                 ← Frontend: quarterly_financials
    └── useDistrictCandidates.ts            ← Frontend: district races
```

### Generated Data (Temporary)
```
/
├── candidates_{cycle}.json
├── financials_{cycle}.json
└── quarterly_financials_{cycle}.json
```

---

## Documentation Details

### FEC_API_GUIDE.md (Main Entry Point - START HERE)
- **26 KB** - Complete FEC OpenFEC API reference
- Authentication & API key setup
- Rate limits and best practices
- All major endpoints with parameters
- Data structures and field descriptions
- Common usage patterns with Python code examples
- Integration patterns for our application

### FEC_SCHEMA_REFERENCE.md (Database Schema & Mappings)
- **24 KB** - Complete field mappings
- PostgreSQL CREATE TABLE statements
- Field-by-field FEC API → database mappings
- All tables: candidates, financial_summary, quarterly_financials
- Committee designations and political persons tables
- Data type reference and constraints
- Validation queries and integrity checks

### FEC_INTEGRATION_PATTERNS.md (Application Integration)
- **20 KB** - How our app integrates FEC data
- Complete data flow architecture diagram
- Python collection scripts documentation
- Frontend TypeScript hooks (useCandidateData, useQuarterlyData)
- Common integration patterns with code examples
- Best practices for collection and querying

### FEC_TROUBLESHOOTING_GUIDE.md (Problem Solving)
- **15 KB** - Solutions to common issues
- API problems (rate limits, authentication)
- Data collection issues (crashes, missing data)
- Database query optimization
- Data quality troubleshooting
- Frontend integration debugging
- Quick fixes and error message reference

---

## Sample Data Available

### Eugene Vindman (H4VA07234)
**Profile:** House candidate from Virginia's 7th District
**Totals:** $5.3M raised, $2.3M spent, $3.1M remaining
**Quarterly:** 3 filings (Q1-Q3 2025)

**Verification Example:**
```
Q1 receipts: $2,065,104.31
Q2 receipts: $1,602,668.11
Q3 receipts: $1,657,280.73
────────────────────────
Total:      $5,325,053.15 ✅ Matches financial_summary
```

### Rana Abdelhamid (H2NY12197)
**Profile:** House candidate from New York's 12th District
**Totals:** $2.6K raised, $8.2K spent, $105K cash
**Quarterly:** 3 filings (Q1-Q3 2025)

---

## Quick Reference: Table Structure

### candidates
```
candidate_id (PK)
├─ name
├─ party / party_full
├─ state
├─ district
├─ office (H or S)
├─ cycle
└─ registration metadata (status, incumbent_challenge, dates, etc.)
```

### financial_summary
```
candidate_id (FK, PK per cycle)
├─ cycle (PK)
├─ total_receipts (CUMULATIVE)
├─ total_disbursements (CUMULATIVE)
├─ cash_on_hand
├─ coverage_end_date
├─ report_type
└─ filing metadata
```

### quarterly_financials
```
candidate_id (FK)
├─ cycle
├─ quarter (Q1-Q4)
├─ coverage_start_date
├─ coverage_end_date
├─ total_receipts (THIS QUARTER)
├─ total_disbursements (THIS QUARTER)
├─ cash_beginning
├─ cash_ending
├─ filing_id
└─ is_amendment
```

---

## Common Questions

**Q: Which document should I start with?**
A: Begin with `FEC_BULK_DATA_GUIDE.md`. It provides context and pointers to specialized docs.

**Q: Where do I find exact column names?**
A: See `fec_schema_mapping.md` for FEC API to database mapping tables.

**Q: How do I import CSV data?**
A: Follow the procedure in `FEC_BULK_DATA_GUIDE.md` under "Importing Bulk CSV Files".

**Q: What's the difference between quarterly and summary data?**
A: See "Key Concepts Explained" section above, then read the detailed explanations in `FEC_BULK_DATA_GUIDE.md`.

**Q: Where's the SQL to create tables?**
A: Use schemas from `actual_database_schemas.md` (current production) or `fec_schema_mapping.md` (reference).

**Q: How do I validate data after import?**
A: Run the SQL validation queries in `FEC_BULK_DATA_GUIDE.md`.

**Q: What's the current data status?**
A: 2026 election cycle, Q1-Q3 2025 data, updated through October 2025.

---

## Total Documentation

- **4 main FEC documentation files** (~85 KB total)
- **Fresh from official FEC OpenFEC API** (November 2025)
- **Complete mapping from FEC API to database**
- **Real code examples** (Python + TypeScript)
- **SQL validation queries** and CREATE statements
- **Integration patterns** for our application
- **Comprehensive troubleshooting** solutions
- **Best practices** for rate limiting and optimization

---

## How to Use This Documentation

### Step 1: Understand the FEC API
Read `data/FEC_API_GUIDE.md` to understand authentication, endpoints, and rate limits.

### Step 2: Learn the Database Schema
Use `data/FEC_SCHEMA_REFERENCE.md` to understand our database structure and field mappings.

### Step 3: Integrate with Your Code
Reference `data/FEC_INTEGRATION_PATTERNS.md` for collection scripts and frontend hooks.

### Step 4: Troubleshoot Issues
Use `data/FEC_TROUBLESHOOTING_GUIDE.md` when you encounter problems.

---

## Related Documentation

Also available in `/docs/`:
- `DATA_COLLECTION_WORKFLOW.md` - **CRITICAL** 2-step workflow
- `guides/collection-guide.md` - Quick reference for collecting data
- `data/database-schema.md` - Complete current production schema
- `history/lessons-learned.md` - Past issues and solutions

---

**Documentation Status:** ✅ **COMPLETE & UP-TO-DATE**
**Last Updated:** November 19, 2025
**Source:** Official FEC OpenFEC API Documentation
**Coverage:** 2026 Election Cycle (current)
**Total Files:** 4 main FEC documentation files (~85 KB)

---

**🚀 START HERE:** Read `data/FEC_API_GUIDE.md` first!
