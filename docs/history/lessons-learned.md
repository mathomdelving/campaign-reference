# Lessons Learned

**A record of problems encountered, solutions implemented, and knowledge gained during Campaign Reference development.**

This document serves as institutional memory - helping future contributors (including AI assistants) understand WHY certain decisions were made and HOW we solved specific problems.

---

## Table of Contents

1. [Data Collection](#data-collection)
2. [Data Quality](#data-quality)
3. [Database Design](#database-design)
4. [Frontend Development](#frontend-development)
5. [Deployment & Infrastructure](#deployment--infrastructure)
6. [API Integration](#api-integration)

---

## Data Collection

### 2024 Rate Limit Failure (November 2025)

**Problem:** Collection script stopped after only 200 of ~5,000 candidates for 2024 cycle

**Root Cause:**
```python
if not response.ok:
    print(f"Error fetching page {page}: {response.status_code}")
    break  # ← GIVES UP IMMEDIATELY!
```

Script had NO retry logic. When it encountered a 429 (rate limit) error on page 3, it immediately quit instead of waiting and retrying.

**Why It Happened:**
- FEC API uses rolling 1-hour window for rate limiting (1,000 calls/hour)
- After processing 2026 cycle (~5,400 calls over 6 hours), some calls from previous hour still counted in rolling window
- On 3rd page of 2024 candidates, crossed the threshold
- Script gave up instead of waiting

**Solution:**
- Added exponential backoff retry logic (4s → 8s → 16s → 32s → 64s)
- Implemented automatic retry on 429 errors (up to 5 attempts)
- Better error handling that doesn't quit on first failure

**Files:**
- [Fix Documentation](./troubleshooting/2024-rate-limit-fix.md)
- [Improved Script](../../scripts/collect_fec_cycle_data.py)

**Lesson Learned:**
> **Always implement exponential backoff for rate-limited APIs.** Never assume perfect rate limiting will prevent 429 errors. Rolling time windows and shared API keys can cause unexpected rate limits even with proper delays.

**Impact:** Without retry logic, we would have needed manual intervention every time a collection hit a rate limit, making unattended multi-day collections impossible.

---

### Amendment Duplicates Creating Inflated Totals (November 2025)

**Problem:** 28.4% of all filings (18,804 records) were duplicates, inflating fundraising totals by 2-3x

**Example:**
- Colin Allred showed $293M raised (incorrect)
- After deduplication: $94.7M raised (correct)

**Root Cause:**
FEC API returns EVERY version of a filing:
- Original filing: Q3 for $30,317,590
- Amendment 1: Q3 for $30,317,590 (donor name correction, same amount)
- Amendment 2: Q3 for $30,317,590 (another correction, same amount)

Without deduplication, all three get added = $90.9M instead of $30.3M

**Why Traditional Dedup Failed:**
- `filing_id` field was NULL in 96.4% of records (FEC doesn't always return `report_key`)
- Couldn't deduplicate by filing ID
- Name-matching unreliable (amendments might have different text)

**Solution:**
Deduplicate by report period, not filing ID:
```sql
-- Unique key: (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date)
-- Keep: Most recent filing (by updated_at, created_at)
-- Delete: All older versions of same report period
```

Added database unique constraint to prevent future duplicates.

**Files:**
- [Fix Documentation](./troubleshooting/data-quality-fixes.md)
- [SQL Script](../../sql/quick_deduplicate.sql)
- [Summary Document](../../DATA_QUALITY_FIXES_SUMMARY.md)

**Lesson Learned:**
> **FEC amended filings must be deduplicated by report period, not filing ID.** When FEC API data lacks unique identifiers, create composite keys from report metadata. Always keep the most recent version.

**Impact:** This was a CRITICAL fix. Without it, all fundraising totals were wrong, making the entire dashboard misleading.

---

### 404 Errors Are Normal (November 2025)

**Problem:** During collection, seeing hundreds of 404 errors

**Initial Reaction:** Thought something was broken

**Reality:** 404s are completely normal for candidates without committees

**Why:**
1. Script fetches all candidates from FEC API
2. For each candidate, requests their committees
3. Many candidates register but never form a committee (exploratory candidates, withdrawn candidacies, etc.)
4. FEC returns 404 for candidates with no committees
5. This is expected behavior, not an error

**Solution:**
- Don't log 404s as errors (they're informational)
- Continue processing other candidates
- Only flag persistent 404s on known-good candidate IDs

**Lesson Learned:**
> **Not all HTTP errors are actual errors.** Understand the API's error semantics. 404 for "no committees found" is not the same as 404 for "bad endpoint". Context matters.

**Impact:** Reduced false alarm noise in logs, made real errors more visible.

---

### Python Default Parameter Bug - 2022 Collection (November 2025)

**Problem:** 2022 collection script returned data from ALL cycles (1979-2025) instead of just 2022

**Root Cause:**
```python
# CYCLE defined as None initially
CYCLE = None

# Functions defined with default parameter
def fetch_candidate_financials(candidate_id, cycle=CYCLE):
    # cycle is None because CYCLE was None when function was defined!
    ...

# CYCLE assigned later
CYCLE = 2022  # Too late! Functions already captured None
```

**Why It Happened:**
Python evaluates default parameters **at function definition time**, not at call time. When functions were defined, `CYCLE = None`, so all default parameters captured `None`.

**Impact:**
- First collection attempt captured 94.4% wrong cycle data
- Mixed data from 1979-2025 instead of pure 2022 data

**Solution:**
```python
# BEFORE (WRONG):
financial_data = fetch_candidate_financials(candidate_id)

# AFTER (CORRECT):
financial_data = fetch_candidate_financials(candidate_id, CYCLE)
```

Pass CYCLE explicitly to every function call.

**Files:**
- Fixed: `scripts/data-collection/fetch_historical_cycle.py`
- Template: `scripts/templates/fetch_historical_cycle_TEMPLATE.py`

**Lesson Learned:**
> **Python default parameters are evaluated at function definition, not call time.** Never use mutable defaults or variables that change. Always pass dynamic values explicitly or use `None` with runtime checks.

**Impact:** This was discovered through comprehensive testing before committing to a 66-hour collection. Without catching it, we would have wasted 3 days collecting useless multi-cycle data.

---

### FEC API: cycle vs election_year Parameters (November 2025)

**Problem:** Using `election_year=2024` to fetch candidates missed 47% of the candidates (4,584 out of 9,810)

**Examples of Missing Candidates:**
- Ted Cruz (S2TX00312) - Texas Senate
- Ruben Gallego (S4AZ00139) - Arizona Senate
- Angela Alsobrooks (S4MD00327) - Maryland Senate
- Kari Lake (S4AZ00220) - Arizona Senate

**Why They Were Missing:**
FEC API has two similar but different parameters:
- `election_year=2024` - Candidates whose election happens in 2024
- `cycle=2024` - All candidates with ANY activity in the 2024 cycle

Many candidates (especially those who started fundraising in 2023 for the 2024 election) appear in `cycle=2024` but not in early pages of `election_year=2024` results.

**Investigation:**
```python
# Wrong approach
response = requests.get(f'{BASE_URL}/candidates/', params={
    'election_year': 2024  # Returns only 5,226 candidates
})

# Correct approach
response = requests.get(f'{BASE_URL}/candidates/', params={
    'cycle': 2024  # Returns all 9,810 candidates
})
```

**Solution:**
Use `cycle` parameter for all historical data collection.

**Lesson Learned:**
> **API parameter names can have subtle semantic differences.** `election_year` and `cycle` sound similar but return vastly different result sets. Always test with known candidates and verify counts match expectations.

**Impact:** Would have collected only half the candidates for each historical cycle. Caught during investigation before 2022 collection started.

---

### Committee Designations Change Between Cycles (November 2025)

**Problem:** Sherrod Brown's principal committee showed $5,000 instead of $96.5M

**Root Cause:**
Committees can change names, designations, and purposes between election cycles:

**C00264697 Example:**
- **2023-2024 cycle**: "FRIENDS OF SHERROD BROWN" - Designation: **P** (Principal) - Type: S (Senate)
- **2025-2026 cycle**: "DIGNITY OF WORK PAC" - Designation: **U** (Unauthorized) - Type: V (Hybrid PAC)

When querying `/candidate/{id}/committees/`, the API returns **current** status (2025-2026), not historical (2023-2024).

**Why This Broke Collection:**
```python
# WRONG: Gets current designation, not cycle-specific
committees = get('/candidate/S6OH00163/committees/', params={'designation': 'P'})
# Returns nothing because committee is currently 'U', not 'P'
```

**Solution:**
Use `/committee/{id}/history/` endpoint to get cycle-specific designation:

```python
def get_principal_committee_for_cycle(candidate_id, cycle):
    committees = get(f'/candidate/{candidate_id}/committees/')

    for committee in committees:
        # Get historical data for this committee
        history = get(f'/committee/{committee["committee_id"]}/history/')

        # Find the record for our cycle
        for record in history:
            if record.get('cycle') == cycle and record.get('designation') == 'P':
                return committee  # Found principal committee for this cycle!

    return None
```

**Files:**
- Fixed: `scripts/data-collection/fetch_historical_cycle.py`
- Template: `scripts/templates/fetch_historical_cycle_TEMPLATE.py`

**Lesson Learned:**
> **Use committee history endpoints for cycle-specific data, never current committee status.** Committees evolve over time. A committee that's a PAC today might have been a principal campaign committee in a previous cycle.

**Impact:** Without this fix, candidates with multi-cycle committees would show wrong amounts or missing data entirely.

---

## Data Quality

### Office Field Inconsistency (November 2025)

**Problem:** Database had 4 different values for office: "H", "S", "House", "Senate"

**Why It Happened:**
- FEC API sometimes returns "H"/"S"
- Sometimes returns full words "House"/"Senate"
- Collection script didn't standardize
- Over time, inconsistency accumulated

**Impact:**
- Queries needed to check multiple values: `office IN ('H', 'House')`
- Increased query complexity
- Potential for missed records in filters

**Solution:**
```python
# Standardize on receipt
office = 'H' if office in ['H', 'House'] else 'S'
```

Plus database migration:
```sql
UPDATE quarterly_financials SET office = 'H' WHERE office = 'House';
UPDATE quarterly_financials SET office = 'S' WHERE office = 'Senate';
```

**Lesson Learned:**
> **Standardize enumerated fields at data ingestion, not query time.** Create a normalization layer between API and database. Never trust external APIs to maintain consistent formatting.

---

### Candidate ID Duplicates (November 2025)

**Problem:** Val Demings appeared twice with identical $81M amounts

**Why:**
- She ran for Senate in 2022
- Had filings under both House ID (H2FL08063) and Senate ID (S2FL00631)
- FEC API returned filings for both IDs with identical amounts

**Solution:**
- Identified she was running for Senate (not House) in 2022
- Deleted House ID filings for 2022 cycle only
- Kept Senate ID filings as authoritative

**Lesson Learned:**
> **When candidates switch offices (House → Senate), their filings may appear under multiple IDs.** Determine which office they're running for in each cycle and only keep filings for that office. Historical filings stay with original office.

---

### Period vs Cumulative Amounts (Ongoing)

**Critical Understanding:**
FEC provides two sets of amounts:
- `total_receipts_period` - Money raised THIS period only
- `total_receipts_ytd` - Cumulative since January 1 of calendar year

**We use PERIOD amounts because:**
1. Timeseries charts need per-period data
2. YTD resets every January (not every cycle)
3. Period amounts sum to cycle totals correctly

**Verified:**
```
Sum of all _period amounts = Cycle total from /totals/ endpoint ✓
```

**Lesson Learned:**
> **Always use `_period` amounts for timeseries financial data, never `_ytd`.** YTD resets on calendar years, not election cycles, making them unsuitable for multi-year cycle analysis.

---

## Database Design

### Unique Constraint on Report Periods (November 2025)

**Problem:** No constraint preventing duplicate filings for same report period

**Impact:** Amendments could create duplicate rows indefinitely

**Solution:**
```sql
ALTER TABLE quarterly_financials
ADD CONSTRAINT unique_filing_period
UNIQUE (candidate_id, cycle, report_type, coverage_start_date, coverage_end_date);
```

**Result:**
- Database automatically rejects duplicate insertions
- Collection script doesn't need to check for duplicates
- Data integrity enforced at database level

**Lesson Learned:**
> **Use database constraints to enforce data integrity, not application logic.** If business logic says "one filing per report period per candidate," encode that as a constraint. Databases are better at enforcing rules than application code.

---

### Missing Cycle Field in Candidates Table (Ongoing)

**Problem:** `candidates` table doesn't have `cycle` field

**Impact:**
- Can't easily query "all candidates who ran in 2024"
- Must join through `quarterly_financials` to filter by cycle
- Candidates who ran in multiple cycles appear only once

**Current Workaround:**
```sql
SELECT DISTINCT c.* FROM candidates c
JOIN quarterly_financials qf ON c.candidate_id = qf.candidate_id
WHERE qf.cycle = 2024;
```

**Potential Solution:**
Create `candidate_cycles` junction table or add cycle to candidates table (but candidates can run in multiple cycles, so normalization gets tricky)

**Lesson Learned:**
> **Consider many-to-many relationships in schema design.** A candidate can run in multiple cycles. Either use junction tables or denormalize strategically.

---

## Frontend Development

### [Future lessons will be added here as UI development progresses]

---

## Deployment & Infrastructure

### [Future lessons will be added here as deployment issues arise]

---

## API Integration

### FEC API Has No Direct "All Filings" Endpoint

**Discovery:** To get all filings for a candidate:
1. Get candidate ID
2. Get all committees for that candidate
3. For each committee, get all reports for the cycle
4. Multiple API calls per candidate (2-5 average)

**Impact:** Collection requires thousands of API calls even with pagination

**Lesson Learned:**
> **Plan for multi-level API traversal.** Not all APIs provide direct access to nested resources. Budget extra time for multi-step data fetching.

---

## General Principles Learned

### 1. Rate Limiting is Harder Than It Seems
- Rolling time windows are tricky
- Shared API keys compound the problem
- Always implement retry logic with backoff
- Monitor rate limit headers if available

### 2. External APIs Are Unpredictable
- Fields may be missing or null
- Formatting may be inconsistent
- Errors may be normal (like 404s)
- Always validate and normalize at ingestion

### 3. Data Quality Requires Active Management
- Duplicates happen in ways you don't expect
- Amendments create complex deduplication logic
- Constraints enforce quality better than code
- Regular audits catch issues early

### 4. Documentation is Infrastructure
- Future you will forget why you made decisions
- AI assistants need context to help effectively
- Lessons learned prevent repeating mistakes
- Good docs save more time than they cost

### 5. Automation Needs Robust Error Handling
- Unattended scripts must recover from errors
- Retry logic is not optional
- Progress tracking enables resumability
- Comprehensive logging is essential

---

## Quick Reference: Common Mistakes to Avoid

❌ **Don't:** Trust external APIs to maintain consistent formatting
✅ **Do:** Normalize data at ingestion time

❌ **Don't:** Assume API calls will always succeed
✅ **Do:** Implement retry logic with exponential backoff

❌ **Don't:** Use cumulative (YTD) amounts for timeseries
✅ **Do:** Use period amounts that sum to cycle totals

❌ **Don't:** Rely on application code for data integrity
✅ **Do:** Use database constraints to enforce rules

❌ **Don't:** Quit on first error in long-running processes
✅ **Do:** Implement resumability and progress tracking

❌ **Don't:** Ignore 404s as errors when they're expected
✅ **Do:** Understand API semantics and error meanings

❌ **Don't:** Deduplicate by unreliable fields (filing_id when often null)
✅ **Do:** Create composite keys from stable metadata

---

## Contributing to This Document

When you encounter a problem and solve it:

1. **Document it here** with:
   - Clear problem statement
   - Root cause analysis
   - Solution implemented
   - Lesson learned (one-liner)
   - Impact/importance

2. **Create detailed troubleshooting doc** in `./troubleshooting/` if fix was complex

3. **Update** relevant technical documentation

4. **Link** from this document to detailed docs

**Remember:** This document helps future contributors avoid repeating your mistakes. Be generous with details.

---

**Last Updated:** November 7, 2025
**Lessons Documented:** 10+ major issues
**Purpose:** Institutional memory & context preservation
