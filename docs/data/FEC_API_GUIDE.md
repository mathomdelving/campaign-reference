# FEC OpenFEC API Guide

**Purpose:** Complete reference for integrating Federal Election Commission data via the OpenFEC API

**Last Updated:** November 19, 2025
**API Version:** v1
**Official Documentation:** https://api.open.fec.gov/developers/

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Key Endpoints](#key-endpoints)
4. [Data Structures](#data-structures)
5. [Common Usage Patterns](#common-usage-patterns)
6. [Rate Limits & Best Practices](#rate-limits--best-practices)
7. [Examples](#examples)

---

## Getting Started

### Authentication

All API requests require an API key from api.data.gov.

**Get Your API Key:**
1. Visit https://api.open.fec.gov/developers/
2. Sign up for a free API key (instant approval)
3. Store in `.env` file: `FEC_API_KEY=your_key_here`

**Usage:**
```bash
https://api.open.fec.gov/v1/candidates/?api_key=YOUR_API_KEY
```

### Base URL
```
https://api.open.fec.gov/v1/
```

### Rate Limits
- **7,000 requests per hour** (upgraded API key, Dec 2025)
- **120 requests per minute** (per API key)
- Returns `429 Too Many Requests` if exceeded
- Note: Default keys are 1,000/hour; our key was upgraded

---

## Core Concepts

### Entity Identifiers

**Candidate ID Format:** `[Office][Cycle Year][State][District][Sequence]`
- Office: H (House), S (Senate), P (Presidential)
- Cycle Year: 2-digit year when first registered (e.g., `6` for 2006)
- State: 2-letter state code
- District: 2-digit district number (House only, `00` for Senate)
- Sequence: 5-digit unique sequence number

**Examples:**
- `H6CA47001` = House candidate, registered 2006, CA-47, sequence 001
- `S6OH00163` = Senate candidate, registered 2006, Ohio, sequence 163

**Committee ID Format:** `C00000000`
- Always starts with `C`
- 8-digit sequence number

**Examples:**
- `C00264697` = Sherrod Brown's principal campaign committee
- `C00000935` = DCCC (Democratic Congressional Campaign Committee)

### Election Cycles

- **Cycle:** 2-year period ending in election year (e.g., 2026 cycle = 2025-2026)
- **Quarters:** Calendar quarters (Q1-Q4) for financial reporting
- **Report Types:** Q1, Q2, Q3, Q4, YE (Year-End), PRE-PRIMARY, PRE-GENERAL, etc.

### Cumulative vs. Per-Period Data

**CRITICAL DISTINCTION:**

**Candidate Totals (Cumulative):**
- `/candidate/{id}/totals/` endpoint
- Fields represent ENTIRE CYCLE totals
- Example: `total_receipts = $3.2M` = all money raised in cycle

**Committee Reports (Per-Period):**
- `/committee/{id}/reports/` endpoint
- Fields represent SINGLE REPORT PERIOD only
- Example: `total_receipts = $500K` = money raised in that quarter only

---

## Key Endpoints

### 1. Candidates

#### Search Candidates
```
GET /candidates/search/
```

**Key Parameters:**
- `q` - Search term (name)
- `office` - H, S, or P
- `state` - Two-letter state code
- `district` - District number (House only)
- `cycle` - Election cycle (2024, 2026, etc.)
- `candidate_status` - C (current), F (future), N (not yet a candidate), P (prior)
- `incumbent_challenge` - I (incumbent), C (challenger), O (open seat)
- `party` - Party abbreviation (DEM, REP, LIB, etc.)

**Response Fields:**
```json
{
  "candidate_id": "H6CA47001",
  "name": "SMITH, JANE",
  "office": "H",
  "state": "CA",
  "district": "47",
  "party": "DEM",
  "party_full": "DEMOCRATIC PARTY",
  "candidate_status": "C",
  "incumbent_challenge": "I",
  "cycles": [2024, 2026],
  "election_years": [2024, 2026],
  "has_raised_funds": true,
  "federal_funds_flag": false,
  "active_through": 2026
}
```

#### Get Candidate Details
```
GET /candidate/{candidate_id}/
```

Returns comprehensive candidate profile including address, election history, and financial flags.

#### Get Candidate History
```
GET /candidate/{candidate_id}/history/
```

Returns all historical records for this candidate across cycles.

---

### 2. Financial Totals

#### Candidate Totals (Cumulative)
```
GET /candidate/{candidate_id}/totals/
```

**Key Parameters:**
- `cycle` - Filter by specific cycle (default: all cycles)
- `election_full` - Include full election totals (true/false)

**Response Fields (CUMULATIVE):**
```json
{
  "candidate_id": "H6CA47001",
  "cycle": 2026,
  "receipts": 3200000.00,          // Total raised (entire cycle)
  "disbursements": 1800000.00,     // Total spent (entire cycle)
  "cash_on_hand_end_period": 1400000.00,  // Latest balance
  "debts_owed_by_committee": 0.00,
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-09-30",
  "last_report_type_full": "Q3 QUARTERLY REPORT",
  "last_cash_on_hand_end_period": 1400000.00,
  "last_debts_owed_by_committee": 0.00
}
```

**IMPORTANT:** All financial fields are cumulative totals for the entire cycle, NOT per-period.

---

### 3. Committee Reports & Filings

#### Get Committee Reports
```
GET /committee/{committee_id}/reports/
```

**Key Parameters:**
- `cycle` - Election cycle
- `report_type` - Q1, Q2, Q3, Q4, YE, 12G, 30D, etc.
- `is_amended` - Filter amendments (true/false)
- `most_recent` - Only latest version (true/false, default: true)

**Response Fields (PER-PERIOD):**
```json
{
  "committee_id": "C00264697",
  "cycle": 2026,
  "report_type": "Q1",
  "report_type_full": "Q1 QUARTERLY REPORT",
  "coverage_start_date": "2026-01-01",
  "coverage_end_date": "2026-03-31",
  "total_receipts": 500000.00,           // THIS QUARTER ONLY
  "total_disbursements": 200000.00,      // THIS QUARTER ONLY
  "cash_on_hand_beginning_period": 100000.00,
  "cash_on_hand_end_period": 400000.00,
  "debts_owed_by_committee": 0.00,
  "fec_file_id": 1234567,
  "receipt_date": "2026-04-15",
  "is_amended": false,
  "most_recent": true,
  "pdf_url": "https://docquery.fec.gov/pdf/567/...",
  "csv_url": "https://docquery.fec.gov/csv/567/..."
}
```

**IMPORTANT:** All financial fields are per-period (this quarter/report only), NOT cumulative.

#### Get Committee Filings
```
GET /committee/{committee_id}/filings/
```

Similar to `/reports/` but includes all filing types (amendments, terminations, etc.).

---

### 4. Search & Lookup

#### Name Search (Autocomplete)
```
GET /names/candidates/
```

**Parameters:**
- `q` - Search query (partial name)

Fast autocomplete endpoint for candidate name search.

**Example:**
```bash
/names/candidates/?q=brown&api_key=YOUR_KEY
```

Returns candidates with "brown" in their name.

---

## Data Structures

### Candidate Object

**Core Fields:**
- `candidate_id` (string) - FEC unique identifier
- `name` (string) - Format: "LAST, FIRST"
- `office` (string) - H, S, or P
- `state` (string) - Two-letter state code
- `district` (string) - Two-digit district (House only)
- `party` (string) - Abbreviated party name (DEM, REP)
- `party_full` (string) - Full party name (DEMOCRATIC PARTY)
- `cycles` (array) - Election cycles candidate is active
- `election_years` (array) - Years candidate ran for office

**Status Fields:**
- `candidate_status` (string) - C, F, N, P
- `incumbent_challenge` (string) - I, C, O
- `active_through` (integer) - Latest cycle candidate is active

**Address Fields:**
- `address_street_1`, `address_street_2`
- `address_city`, `address_state`, `address_zip`

**Financial Flags:**
- `has_raised_funds` (boolean) - Whether candidate has any financial activity
- `federal_funds_flag` (boolean) - Whether candidate received federal matching funds

### Financial Summary Object (Cumulative)

**Cumulative Totals:**
- `receipts` (decimal) - Total raised in cycle
- `disbursements` (decimal) - Total spent in cycle
- `cash_on_hand_end_period` (decimal) - Latest balance
- `debts_owed_by_committee` (decimal) - Total debt

**Coverage Dates:**
- `coverage_start_date` (date) - First day of cycle
- `coverage_end_date` (date) - Latest filing date

**Metadata:**
- `cycle` (integer) - Election cycle
- `last_report_type_full` (string) - Most recent report type
- `last_report_year` (integer) - Most recent report year

### Committee Report Object (Per-Period)

**Per-Period Financials:**
- `total_receipts` (decimal) - Money raised THIS period
- `total_disbursements` (decimal) - Money spent THIS period
- `cash_on_hand_beginning_period` (decimal) - Starting balance
- `cash_on_hand_end_period` (decimal) - Ending balance

**Report Metadata:**
- `report_type` (string) - Q1, Q2, Q3, Q4, YE, etc.
- `report_type_full` (string) - Full description
- `coverage_start_date` (date) - Period start
- `coverage_end_date` (date) - Period end
- `is_amended` (boolean) - Whether this is an amendment
- `most_recent` (boolean) - Latest version of this report

**Filing Details:**
- `fec_file_id` (integer) - Unique filing ID
- `receipt_date` (date) - When FEC received filing
- `pdf_url` (string) - Link to PDF version
- `csv_url` (string) - Link to CSV data

---

## Common Usage Patterns

### Pattern 1: Find Candidate by Name
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.open.fec.gov/v1"

def search_candidate(name):
    response = requests.get(
        f"{BASE_URL}/candidates/search/",
        params={
            "api_key": API_KEY,
            "q": name,
            "office": "H",  # House only
            "cycle": 2026,
            "per_page": 20
        }
    )
    return response.json()["results"]

candidates = search_candidate("Brown")
for c in candidates:
    print(f"{c['name']} ({c['state']}-{c['district']}) - {c['party']}")
```

### Pattern 2: Get Candidate Totals (Cumulative)
```python
def get_candidate_totals(candidate_id, cycle=2026):
    response = requests.get(
        f"{BASE_URL}/candidate/{candidate_id}/totals/",
        params={
            "api_key": API_KEY,
            "cycle": cycle
        }
    )
    totals = response.json()["results"][0]
    return {
        "raised": totals["receipts"],
        "spent": totals["disbursements"],
        "cash": totals["cash_on_hand_end_period"]
    }

totals = get_candidate_totals("H6CA47001")
print(f"Raised: ${totals['raised']:,.2f}")
print(f"Spent: ${totals['spent']:,.2f}")
print(f"Cash: ${totals['cash']:,.2f}")
```

### Pattern 3: Get Quarterly Breakdowns (Per-Period)
```python
def get_quarterly_reports(committee_id, cycle=2026):
    response = requests.get(
        f"{BASE_URL}/committee/{committee_id}/reports/",
        params={
            "api_key": API_KEY,
            "cycle": cycle,
            "report_type": ["Q1", "Q2", "Q3", "Q4"],
            "most_recent": True,
            "per_page": 100
        }
    )
    return response.json()["results"]

reports = get_quarterly_reports("C00264697")
for r in reports:
    print(f"{r['report_type']} {r['cycle']}: ${r['total_receipts']:,.2f}")
```

### Pattern 4: Pagination
```python
def get_all_candidates(office="H", cycle=2026):
    candidates = []
    page = 1

    while True:
        response = requests.get(
            f"{BASE_URL}/candidates/",
            params={
                "api_key": API_KEY,
                "office": office,
                "cycle": cycle,
                "per_page": 100,
                "page": page
            }
        )
        data = response.json()
        candidates.extend(data["results"])

        # Check if more pages exist
        if len(data["results"]) < 100:
            break
        page += 1

    return candidates
```

---

## Rate Limits & Best Practices

### Rate Limits
- **7,000 requests/hour** (our upgraded key; default is 1,000/hour)
- **120 requests/minute**
- Monitor via response headers:
  - `X-RateLimit-Limit: 120`
  - `X-RateLimit-Remaining: 115`

### Best Practices

**1. Implement Rate Limiting**
```python
import time

def rate_limited_get(url, params, delay=0.05):
    """Make request with delay to stay under rate limit"""
    time.sleep(delay)  # ~900 requests/hour
    return requests.get(url, params=params)
```

**2. Handle 429 Errors**
```python
def safe_api_call(url, params, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 429:
            wait_time = 60  # Wait 1 minute
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response.json()

    raise Exception("Max retries exceeded")
```

**3. Cache Responses**
```python
import json
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_candidate_cached(candidate_id):
    """Cache candidate lookups to reduce API calls"""
    response = requests.get(
        f"{BASE_URL}/candidate/{candidate_id}/",
        params={"api_key": API_KEY}
    )
    return response.json()
```

**4. Use Filters to Reduce Response Size**
```python
# Good: Filter to specific fields
response = requests.get(
    f"{BASE_URL}/candidates/",
    params={
        "api_key": API_KEY,
        "office": "H",
        "state": "CA",
        "cycle": 2026,
        "has_raised_funds": True  # Only candidates with financial data
    }
)

# Better: Use pagination
params["per_page"] = 100  # Max allowed
```

**5. Batch Operations**
```python
# Good: Batch related requests
candidate_ids = ["H6CA47001", "H6CA47002", "H6CA47003"]

# Make one request per candidate with delay
for candidate_id in candidate_ids:
    totals = get_candidate_totals(candidate_id)
    time.sleep(0.05)  # Rate limit
```

---

## Examples

### Example 1: Build 2026 House Leaderboard
```python
import requests
import time

API_KEY = "your_key"
BASE_URL = "https://api.open.fec.gov/v1"

# Step 1: Get all House candidates for 2026
candidates = []
page = 1

while True:
    response = requests.get(
        f"{BASE_URL}/candidates/",
        params={
            "api_key": API_KEY,
            "office": "H",
            "cycle": 2026,
            "has_raised_funds": True,
            "per_page": 100,
            "page": page
        }
    )
    data = response.json()
    candidates.extend(data["results"])

    if len(data["results"]) < 100:
        break
    page += 1
    time.sleep(0.05)

print(f"Found {len(candidates)} House candidates")

# Step 2: Get financial totals for each
leaderboard = []

for c in candidates:
    totals_response = requests.get(
        f"{BASE_URL}/candidate/{c['candidate_id']}/totals/",
        params={
            "api_key": API_KEY,
            "cycle": 2026
        }
    )

    if totals_response.json()["results"]:
        totals = totals_response.json()["results"][0]
        leaderboard.append({
            "name": c["name"],
            "state": c["state"],
            "district": c["district"],
            "party": c["party"],
            "raised": totals["receipts"],
            "spent": totals["disbursements"],
            "cash": totals["cash_on_hand_end_period"]
        })

    time.sleep(0.05)  # Rate limit

# Step 3: Sort by money raised
leaderboard.sort(key=lambda x: x["raised"], reverse=True)

# Step 4: Display top 10
for i, candidate in enumerate(leaderboard[:10], 1):
    print(f"{i}. {candidate['name']} ({candidate['state']}-{candidate['district']})")
    print(f"   Raised: ${candidate['raised']:,.2f} | Cash: ${candidate['cash']:,.2f}")
```

### Example 2: Get Quarterly Time Series
```python
def get_quarterly_time_series(candidate_id, cycle=2026):
    # Step 1: Get candidate's principal committee
    candidate_response = requests.get(
        f"{BASE_URL}/candidate/{candidate_id}/",
        params={"api_key": API_KEY}
    )
    candidate = candidate_response.json()["results"][0]
    principal_committees = candidate.get("principal_committees", [])

    if not principal_committees:
        return []

    committee_id = principal_committees[0]["committee_id"]

    # Step 2: Get quarterly reports for committee
    reports_response = requests.get(
        f"{BASE_URL}/committee/{committee_id}/reports/",
        params={
            "api_key": API_KEY,
            "cycle": cycle,
            "report_type": ["Q1", "Q2", "Q3", "Q4"],
            "most_recent": True,
            "per_page": 100
        }
    )

    reports = reports_response.json()["results"]

    # Step 3: Format for time series
    time_series = []
    for r in sorted(reports, key=lambda x: x["coverage_end_date"]):
        time_series.append({
            "quarter": r["report_type"],
            "year": r["report_year"],
            "date": r["coverage_end_date"],
            "receipts": r["total_receipts"],
            "disbursements": r["total_disbursements"],
            "cash": r["cash_on_hand_end_period"]
        })

    return time_series

# Usage
time_series = get_quarterly_time_series("H6CA47001")
for quarter in time_series:
    print(f"{quarter['quarter']} {quarter['year']}: ${quarter['receipts']:,.2f} raised")
```

---

## Additional Resources

- **Official Documentation:** https://api.open.fec.gov/developers/
- **GitHub Repository:** https://github.com/fecgov/openFEC
- **Interactive API Explorer:** https://api.open.fec.gov/developers/ (Swagger UI)
- **Bulk Downloads:** https://www.fec.gov/data/browse-data/?tab=bulk-data
- **FEC Help:** APIinfo@fec.gov

---

## Related Documentation

- `FEC_SCHEMA_REFERENCE.md` - Complete field mappings
- `FEC_INTEGRATION_PATTERNS.md` - Integration examples for this app
- `FEC_TROUBLESHOOTING_GUIDE.md` - Common issues and solutions
- `database-schema.md` - Local database schema
- `data-model-summary.md` - Data model overview

---

**Last Updated:** November 19, 2025
**Maintainer:** FEC Dashboard Team
**API Version:** OpenFEC v1
