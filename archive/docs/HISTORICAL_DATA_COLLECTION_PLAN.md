# Historical FEC Data Collection Plan
**Created:** November 3, 2025
**Status:** Draft - Ready for Implementation
**Cycles:** 2024, 2022, 2020, 2018

---

## 🚨 Problem Statement

**Current Issue:**
The backfill completed but fetched **incorrect data**:
- Fetterman (2022 PA Senate): Shows $1.2M instead of ~$60M
- Data has 2025 dates instead of 2021-2022 dates
- Only 1,496 filings for 2022 (should be 10,000+)
- **Root Cause:** Script fetches candidates from historical cycles but gets their CURRENT fundraising data, not historical data

**Example:**
- Fetterman's `S6PA00274` candidate ID is for 2022 cycle
- But FEC API returns his 2026 fundraising (current Senate term)
- We need his actual 2021-2022 fundraising data from when he ran

---

## 📊 Data Requirements

### Required Fields (Per Candidate, Per Cycle)
1. **Candidate Name**
2. **Candidate ID** (e.g., S6PA00274)
3. **Committee ID** (e.g., C00755645)
4. **Cycle** (2018, 2020, 2022, 2024)
5. **Total Raised** (cumulative receipts for the cycle)
6. **Total Spent** (cumulative disbursements for the cycle)
7. **Cash on Hand** (end of cycle)
8. **State**
9. **District** (for House races)
10. **Office** (H/S)
11. **Party**

### Data Granularity
- **Summary Level:** One row per candidate per cycle (for leaderboard)
- **Quarterly Level:** Multiple rows per candidate (for trend charts)

---

## 🎯 Correct Approach

### The FEC API Structure

**Key Understanding:**
- Candidates have **unique IDs per cycle** (e.g., S6PA00274 is Fetterman 2022)
- Committees have **IDs that span multiple cycles** (e.g., C00755645 might be active 2021-2026)
- Financial data is tied to **committees**, not candidates
- We must query committee filings filtered by the **specific election cycle**

### Three-Step Data Flow

```
Step 1: Get Candidates by Cycle
   ↓
Step 2: Get Their Committees (filtered by cycle)
   ↓
Step 3: Get Committee Filings (filtered by cycle + report year)
```

---

## 📋 Implementation Plan

### Phase 1: Design Correct Script (1-2 hours)

**Script Name:** `fetch_historical_complete.py`

**Approach:**
1. **For each cycle (2024, 2022, 2020, 2018):**
   - Query FEC API: `/v1/candidates/` with `election_year={cycle}`
   - Get all House and Senate candidates

2. **For each candidate:**
   - Query FEC API: `/v1/candidate/{candidate_id}/committees/`
   - Filter by `cycle={cycle}` to get committees active during that cycle

3. **For each committee:**
   - Query FEC API: `/v1/committee/{committee_id}/totals/`
   - Filter by `cycle={cycle}` to get summary totals for that specific cycle
   - **OR** Query `/v1/reports/{committee_type}/`
   - Filter by `cycle={cycle}` and aggregate quarterly filings

4. **Calculate Totals:**
   - Sum all receipts across quarters
   - Sum all disbursements across quarters
   - Take final cash on hand from last report

5. **Save to Database:**
   - Insert into `financial_summary` table
   - Insert quarterly details into `quarterly_financials` table

---

### Phase 2: API Endpoints to Use

#### A. Get Candidates for Cycle
```
GET /v1/candidates/
Parameters:
  - election_year: 2022
  - office: H,S  (House and Senate only)
  - per_page: 100
  - page: 1,2,3...
```

**Expected:** ~3,500 candidates per cycle

#### B. Get Candidate's Committees
```
GET /v1/candidate/{candidate_id}/committees/
Parameters:
  - cycle: 2022
  - per_page: 20
```

**Key:** Must filter by `cycle` to get only committees active during that election

#### C. Get Committee Financial Totals (PREFERRED METHOD)
```
GET /v1/committee/{committee_id}/totals/
Parameters:
  - cycle: 2022
```

**Returns:**
- `receipts` - Total raised in cycle
- `disbursements` - Total spent in cycle
- `cash_on_hand_end_period` - Cash remaining
- `coverage_end_date` - Report date

**Advantage:** One API call per committee, pre-aggregated data

#### D. Alternative: Get Committee Reports (for quarterly breakdown)
```
GET /v1/committee/{committee_id}/reports/
Parameters:
  - cycle: 2022
  - sort: coverage_end_date
  - per_page: 20
```

**Returns:** Quarterly reports (Q1, Q2, Q3, YE, etc.)

**Use Case:** When we need quarterly trend data

---

### Phase 3: Data Validation

**Critical Checks:**

1. **Date Validation:**
   ```python
   # 2022 cycle should have dates in 2021-2022
   assert filing_date.year in [2021, 2022], "Wrong cycle data!"
   ```

2. **Amount Sanity Checks:**
   ```python
   # Major Senate races should have $1M+ raised
   if office == 'S' and total_raised < 1_000_000:
       print(f"WARNING: Senate candidate {name} only raised ${total_raised:,}")
   ```

3. **Known Benchmark Validation:**
   ```python
   # Test cases for 2022 cycle:
   benchmarks = {
       'S6PA00274': {'name': 'FETTERMAN', 'min_raised': 50_000_000},  # ~$60M
       'S2AZ00285': {'name': 'KELLY', 'min_raised': 60_000_000},      # ~$70M
       'S0GA00523': {'name': 'WARNOCK', 'min_raised': 80_000_000},    # ~$120M
   }
   ```

4. **Completeness Check:**
   ```python
   # Should have 3,000+ candidates per cycle with financial data
   assert len(candidates_with_data) > 3000, "Missing candidates!"
   ```

---

### Phase 4: Database Schema

**Existing Tables:** ✅ Already created

1. **`candidates`** - One row per candidate per cycle
2. **`financial_summary`** - Summary totals per candidate per cycle
3. **`quarterly_financials`** - Quarterly breakdown (optional, for charts)

**No schema changes needed!**

---

## ⏱️ Execution Estimates

### API Call Calculations

**Per Cycle (e.g., 2022):**
- Candidates: ~35 API calls (3,500 candidates ÷ 100 per page)
- Committees: ~3,500 calls (1 per candidate, most have 1 committee)
- Totals: ~3,500 calls (1 per committee)
- **Total: ~7,035 API calls per cycle**

**Rate Limits:**
- FEC API: 1,000 calls/hour (with API key)
- With delays: ~720 calls/hour (5 second delay)

**Time Per Cycle:**
- 7,035 calls ÷ 720 calls/hour = **~9.8 hours per cycle**

**All 4 Cycles:**
- 2024 + 2022 + 2020 + 2018 = **~40 hours total**
- Can run overnight or over 2 days

---

## 📝 Script Pseudocode

```python
#!/usr/bin/env python3
"""
Correct Historical FEC Data Fetcher
Fetches accurate financial data for past election cycles
"""

def fetch_cycle_data(cycle):
    """Fetch all candidate financial data for a specific cycle."""

    # Step 1: Get all candidates for this cycle
    candidates = fetch_candidates(cycle)
    print(f"Found {len(candidates)} candidates for {cycle}")

    results = []

    for candidate in candidates:
        candidate_id = candidate['candidate_id']

        # Step 2: Get candidate's committees active during this cycle
        committees = fetch_committees(candidate_id, cycle)

        if not committees:
            continue

        # Step 3: Aggregate financial data from all committees
        total_raised = 0
        total_spent = 0
        cash_on_hand = 0

        for committee in committees:
            committee_id = committee['committee_id']

            # Get financial totals for this committee in this cycle
            totals = fetch_committee_totals(committee_id, cycle)

            # Validate dates are correct for this cycle
            if not validate_cycle_dates(totals, cycle):
                print(f"WARNING: Wrong cycle data for {committee_id}")
                continue

            total_raised += totals.get('receipts', 0)
            total_spent += totals.get('disbursements', 0)
            cash_on_hand = totals.get('cash_on_hand_end_period', 0)

        # Step 4: Save to database
        results.append({
            'candidate_id': candidate_id,
            'name': candidate['name'],
            'cycle': cycle,
            'total_raised': total_raised,
            'total_spent': total_spent,
            'cash_on_hand': cash_on_hand,
            # ... other fields
        })

    # Save batch to database
    save_to_database(results, cycle)

    return results


def validate_cycle_dates(totals, cycle):
    """Ensure financial data is from the correct cycle."""
    coverage_date = totals.get('coverage_end_date')

    if not coverage_date:
        return False

    year = int(coverage_date.split('-')[0])

    # Financial data should be from cycle year or year before
    # (e.g., 2022 cycle covers 2021-2022)
    return year in [cycle - 1, cycle]


def fetch_candidates(cycle):
    """Fetch candidates from FEC API."""
    url = f"{BASE_URL}/candidates/"
    params = {
        'api_key': FEC_API_KEY,
        'election_year': cycle,
        'office': ['H', 'S'],
        'per_page': 100
    }
    # Paginate through all results...


def fetch_committees(candidate_id, cycle):
    """Fetch committees for candidate filtered by cycle."""
    url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle  # CRITICAL: Filter by cycle!
    }
    # Return committees...


def fetch_committee_totals(committee_id, cycle):
    """Fetch financial totals for committee in specific cycle."""
    url = f"{BASE_URL}/committee/{committee_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle  # CRITICAL: Filter by cycle!
    }
    # Return totals...
```

---

## ✅ Validation Plan

### Benchmark Candidates (2022 Cycle)

Test against these known high-profile races:

| Candidate | State | Expected Total Raised | Expected Cash on Hand |
|-----------|-------|----------------------|----------------------|
| John Fetterman | PA-S | $60M+ | |
| Mark Kelly | AZ-S | $70M+ | |
| Raphael Warnock | GA-S | $120M+ | |
| Herschel Walker | GA-S | $50M+ | |
| Ron Johnson | WI-S | $30M+ | |
| Mandela Barnes | WI-S | $30M+ | |
| Catherine Cortez Masto | NV-S | $50M+ | |
| Adam Laxalt | NV-S | $20M+ | |
| Maggie Hassan | NH-S | $30M+ | |
| Don Bolduc | NH-S | $5M+ | |

### Validation Process

1. **Run script on 2022 cycle first** (test case)
2. **Check Fetterman's data:**
   - Should show ~$60M raised
   - Dates should be 2021-2022
   - Should have Q1, Q2, Q3, YE reports
3. **If correct, proceed to other cycles**
4. **If wrong, debug before running full dataset**

---

## 🎯 Success Criteria

**The data collection is successful when:**

✅ **Correct Totals:**
- Fetterman 2022: $50M-$70M (not $1.2M)
- Mark Kelly 2022: $60M-$80M
- Warnock 2022: $100M-$130M

✅ **Correct Dates:**
- 2022 cycle: Coverage dates in 2021-2022 (not 2025)
- 2020 cycle: Coverage dates in 2019-2020
- etc.

✅ **Complete Data:**
- 2024: 2,500+ candidates with financial data
- 2022: 3,000+ candidates with financial data
- 2020: 3,000+ candidates with financial data
- 2018: 3,500+ candidates with financial data

✅ **Quarterly Breakdown Available:**
- Each major candidate has Q1, Q2, Q3, YE reports
- Can build quarterly trend charts

---

## 🚧 Implementation Steps

### Step 1: Create New Script (2 hours)
- [ ] Create `fetch_historical_complete.py`
- [ ] Implement correct API calls with cycle filtering
- [ ] Add date validation
- [ ] Add benchmark testing
- [ ] Test on 10 candidates from 2022

### Step 2: Test on 2022 Cycle (10 hours)
- [ ] Run script for 2022 cycle only
- [ ] Validate Fetterman data is correct
- [ ] Validate Kelly data is correct
- [ ] Validate Warnock data is correct
- [ ] Check 10 random House candidates
- [ ] Verify dates are 2021-2022

### Step 3: Run Remaining Cycles (30 hours)
- [ ] Run 2024 cycle (~10 hours)
- [ ] Run 2020 cycle (~10 hours)
- [ ] Run 2018 cycle (~10 hours)
- [ ] Can run overnight or in parallel

### Step 4: Validation & QA (2 hours)
- [ ] Check total record counts
- [ ] Spot-check 20 random candidates
- [ ] Verify all cycles have correct date ranges
- [ ] Test frontend displays correct data

### Step 5: Documentation (1 hour)
- [ ] Document what was fixed
- [ ] Update README with correct data collection info
- [ ] Archive old incorrect script

---

## ⚠️ Current Data Status

**What We Have (Incorrect):**
- 15,011 candidates across 5 cycles ✅
- 17,740 filings ❌ (but many are wrong cycle/dates)
- 2026 data: Likely correct ✅
- 2024, 2022, 2020, 2018 data: **Incorrect/Incomplete** ❌

**What Needs to be Fixed:**
- Re-fetch 2024, 2022, 2020, 2018 cycles completely
- Use correct API approach with cycle filtering
- Validate against known benchmarks

**Can We Keep 2026 Data?**
- YES - 2026 data is likely correct
- Only re-fetch historical cycles

---

## 🔄 Alternative Approaches

### Option A: FEC Bulk Data Files (FASTEST)
**What:** FEC provides pre-processed CSV files
**URL:** https://www.fec.gov/data/browse-data/?tab=bulk-data
**Pros:**
- No API rate limits
- Complete data immediately
- Pre-aggregated totals
**Cons:**
- Large files (GB+)
- Need to parse and transform
- Different schema than API

**Estimate:** 4-8 hours total (download + parse + load)

### Option B: Correct API Approach (RECOMMENDED)
**What:** Fix our script to use correct cycle filtering
**Pros:**
- We control the data format
- Can incrementally validate
- Matches our existing schema
**Cons:**
- Slower (40 hours for 4 cycles)
- Rate limited

**Estimate:** 40 hours runtime + 5 hours development

### Option C: Hybrid Approach
**What:** Use bulk files for totals, API for quarterly breakdown
**Pros:**
- Fast for summary data
- Detailed for important races
**Cons:**
- Complex implementation
- Two data sources to maintain

---

## 💡 Recommendation

**Use Option B: Correct API Approach**

**Reasoning:**
1. We already have the infrastructure
2. Small script fix (not a rewrite)
3. Incremental validation possible
4. Consistent data format
5. Can run overnight (40 hours = 1-2 nights)

**Timeline:**
- **Today (Nov 3):** Write corrected script + test on 10 candidates
- **Tonight:** Run 2022 cycle overnight (~10 hours)
- **Tomorrow (Nov 4):** Validate 2022, run 2024 overnight
- **Nov 5-6:** Run 2020 and 2018 cycles
- **Nov 7:** Full validation and frontend testing

---

## 📊 Expected Results (After Fix)

### 2022 Cycle Summary
- Candidates: ~3,468
- With Financial Data: ~2,000-2,500
- Filings: ~10,000-15,000 (quarterly breakdowns)
- Date Range: 2021-01-01 to 2022-12-31
- Top Fundraiser (Senate): Warnock ($120M+)
- Top Fundraiser (House): ~$10-20M range

### All Cycles Combined
- Total Candidates: ~15,000
- Total Filings: ~60,000-80,000
- Date Range: 2017 to 2025
- Complete quarterly breakdowns for trend charts

---

## 🎯 Next Actions

**Priority 1: Fix the Script**
1. Review current `fetch_all_filings.py`
2. Identify where cycle filtering is missing
3. Add cycle parameter to all API calls
4. Add date validation
5. Test on 10 candidates

**Priority 2: Validate Approach**
1. Run on Fetterman (S6PA00274) for 2022
2. Verify returns $60M+
3. Verify dates are 2021-2022
4. If correct → proceed
5. If wrong → debug API calls

**Priority 3: Execute Full Backfill**
1. Start with 2022 (most important for validation)
2. Then 2024 (most recent)
3. Then 2020 and 2018
4. Monitor progress and validate samples

---

## 📝 Questions to Answer Before Starting

1. **Do we want quarterly breakdown or just totals?**
   - Totals: Faster, fewer API calls
   - Quarterly: Enables trend charts, more API calls

2. **Should we clear existing wrong data first?**
   - Option A: Keep 2026, delete 2024/2022/2020/2018
   - Option B: Keep everything, just update
   - Option C: Fresh start for all historical cycles

3. **What's the priority order?**
   - Option A: 2024 first (most recent)
   - Option B: 2022 first (best validation data)
   - Option C: 2018 first (oldest, least likely to change)

4. **Should we run serially or attempt parallel?**
   - Serial: Safer, easier to monitor
   - Parallel: Faster, but harder to debug

---

## 🔗 Resources

**FEC API Documentation:**
- API Overview: https://api.open.fec.gov/developers/
- Candidates endpoint: `/v1/candidates/`
- Committees endpoint: `/v1/candidate/{id}/committees/`
- Totals endpoint: `/v1/committee/{id}/totals/`
- Reports endpoint: `/v1/committee/{id}/reports/`

**Rate Limits:**
- With API key: 1,000 requests/hour
- Without: 100 requests/hour
- Per page max: 100 records

**Our Current Scripts:**
- `fetch_fec_data.py` - Original candidate fetcher
- `fetch_all_filings.py` - Attempted detailed filings (HAS BUG)
- `load_to_supabase.py` - Database loader

---

**Status:** Ready to implement
**Estimated Total Time:** 47 hours (5 hours dev + 42 hours runtime)
**Can Complete By:** November 7-8, 2025
**Blocker:** None - can start immediately

---

**Prepared by:** Claude Code
**For:** Benjamin Nelson / Campaign Reference
**Date:** November 3, 2025
