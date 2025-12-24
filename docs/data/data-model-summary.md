# FEC Dashboard - Current Data Model Summary

**Last Updated:** November 24, 2025
**Status:** Production Architecture

## Overview

Our system uses a **hierarchical data model** with political persons at the top level, linking to their various campaigns and financial data.

```
political_persons (14,495)    ← Top-level: The actual person
    ↓ (via person_id FK)
candidates (17,459)           ← Middle-level: Campaign registrations
    ↓ (via candidate_id FK)
quarterly_financials (53,122) ← Bottom-level: Financial filings
    ↓ (via committee_id reference)
committee_designations        ← Metadata: Principal vs. other committees
```

## Database Tables

### 0. `political_persons` (14,495 records)
**Top-level entity** - Stores unified person records to solve duplicate candidate problems.

**Fields:**
- `person_id` (PK) - Slug format: 'firstname-lastname-state'
- `display_name` - Display name: 'First Last'
- `first_name`, `last_name` - Name components (optional)
- `party` - Party affiliation
- `state` - Primary state (alphabetically first if multi-state)
- `district` - District (for House members)
- `current_office` - Current office (H/S/P)
- `is_incumbent` - Is currently serving
- `notes` - Additional notes
- `created_at`, `updated_at` - Timestamps

**Example:**
```sql
person_id: 'bernard-sanders-vt'
display_name: 'Bernard Sanders'
party: 'DEM'
state: 'VT'
current_office: 'S'
```

**Key Concept:** One person can have multiple candidate_ids linked via `candidates.person_id` foreign key.

### 1. `candidates` (17,459 records)
**Campaign registrations** - One record per FEC candidate ID.

**Fields:**
- `candidate_id` (PK) - FEC Candidate ID
- `person_id` (FK) - Links to political_persons (CRITICAL)
- `name` - Candidate name in "LAST, FIRST" format
- `office` - H (House), S (Senate), or P (President)
- `state` - Two-letter state code
- `district` - District number (for House)
- `party` - Party affiliation
- `incumbent_challenge` - I (Incumbent), C (Challenger), O (Open)
- `created_at`, `updated_at` - Timestamps

**Important:** Each **political person** can have **multiple candidate_id records**:
- One for each office they run for (House → Senate)
- Multiple for the same office when they have different Senate classes
- Example: Bernard Sanders (`bernard-sanders-vt`) has **3 candidate_ids**:
  - `H2OH13033` - House (VT-00) - old House seat, no data
  - `S6VT00033` - Senate - 2018/2024 runs
  - `S8VT00106` - Senate - 2026 run

### 2. `quarterly_financials` (53,122 records)
Stores all financial data for candidates.

**Fields:**
- `id` (PK) - Auto-increment ID
- `candidate_id` - Links to candidates table
- `committee_id` - FEC Committee ID for the campaign committee
- `name` - Candidate name (duplicated from candidates)
- `office`, `state`, `district`, `party` - Candidate info (duplicated)
- `cycle` - Election cycle (2022, 2024, 2026, etc.)
- `report_type` - Type of filing (Q1, Q2, Q3, Q4, YE, etc.)
- `coverage_start_date`, `coverage_end_date` - Reporting period
- `total_receipts` - Money raised
- `total_disbursements` - Money spent
- `cash_beginning`, `cash_ending` - Cash on hand
- `filing_id` - Reference to original FEC filing
- `is_amendment` - Whether this is an amended filing
- `created_at`, `updated_at` - Timestamps

**Important characteristics:**
- **Denormalized** - Candidate info is duplicated in each row
- **No committee_name field** - Only has `committee_id`
- **Party committees (DCCC, NRCC) are NOT in this table** - They're only hardcoded in the UI

### 3. Other tables
- `committees` table - Doesn't exist or isn't accessible
- `committee_financial_summaries` table - Doesn't exist or isn't accessible

## FEC ID System

### Candidate IDs
Format: `[Office][Year][State][Sequence]`
- **Office:** H (House), S (Senate), P (President)
- **Year:** 2-digit year when candidate first filed
- **State:** 2-letter state code
- **Sequence:** 5-digit number

Examples:
- `S6OH00163` = Senate candidate, filed in 2006, Ohio, sequence 163
- `H2OH13033` = House candidate, filed in 2002, Ohio district 13, sequence 033

### Committee IDs
Format: `C[8-digit-sequence]`

Examples:
- `C00264697` = Committee sequence 00264697
- `C00555342` = Committee sequence 00555342
- `C00000935` = DCCC (hardcoded in UI)

**Key distinction:**
- Candidate IDs start with H/S/P
- Committee IDs start with C

## How the UI Currently Works

### Search (CommitteeView.tsx)
The search box handles **two entity types**:

1. **Type: "candidate"**
   - Searches the `candidates` table by name
   - Uses `candidate_id` to query `quarterly_financials`
   - Shows candidate name as the label

2. **Type: "committee"**
   - Hardcoded list: DCCC, DSCC, NRCC, NRSC
   - Uses `committee_id` to query `quarterly_financials`
   - Shows committee acronym as the label

### Data fetching
- `useQuarterlyData(candidateIds, cycles)` - Fetches by candidate_id
- `useCommitteeQuarterlyData(committeeIds, cycles)` - Fetches by committee_id
- Both query the **same table**: `quarterly_financials`

## The Sherrod Brown Problem

### What we found:
Searching for "Sherrod Brown" returns **3 entries**:

| candidate_id | Name | Office | Data in quarterly_financials |
|-------------|------|--------|------------------------------|
| H2OH13033 | BROWN, SHERROD | H - OH-13 | ❌ 0 records |
| S6OH00163 | BROWN, SHERROD | S - OH-00 | ✓ 27 records (2022-2024) |
| S6OH00379 | BROWN, SHERROD | S - OH-II | ✓ 1 record (2026) |

### S6OH00163 details (2022-2024 runs):
- **19 records** with committee `C00264697` (old principal → now hybrid PAC)
- **8 records** with committee `C00555342` (unknown committee)
- Cycles: 2022, 2024
- Date range: 2021-01-01 to 2024-12-31
- Latest cash: $394,230

### S6OH00379 details (2026 run):
- **1 record** with committee `C00916288` (new 2026 principal committee)
- Cycle: 2026
- Latest: 2025-09-30
- Cash: $5.9M

## Critical Data Integrity Rule

**⚠️ ALL COMMITTEES MUST MAP TO A CANDIDATE**

When loading financial data:
1. **Check if candidate exists** in the `candidates` table
2. **If candidate does not exist**, create candidate record FIRST
3. **Then load** committee financial data

This ensures referential integrity in the query flow:
```
political_person → candidates (via person_id FK) → quarterly_financials (via candidate_id FK)
```

Without a candidate record, committee financial data cannot be properly attributed to a political person.

## How The System Works

**Query Flow for "Bernard Sanders":**
1. User searches "Bernard Sanders"
2. Query `political_persons` table → find `person_id = 'bernard-sanders-vt'`
3. Query `candidates` table → get all candidate_ids with `person_id = 'bernard-sanders-vt'`
4. Query `quarterly_financials` table → get all records for those candidate_ids
5. Filter using `committee_designations` table → show only principal committees
6. Return unified time series with all campaigns merged

**Result:** Single search entry with complete fundraising history across House, Senate 2018/2024, and Senate 2026.

## Production Status

**✅ Complete and Live (November 24, 2025)**

- 14,495 political_persons records created
- 17,459 candidates linked via person_id foreign key
- Bernard Sanders unified: 1 person_id → 3 candidate_ids
- Ruben Gallego unified: 1 person_id → 2 candidate_ids (House → Senate)
- Search returns single deduplicated results
- Charts show unified fundraising timelines
