# Bug Fixes - FEC Dashboard Data Loading Issue

## Problem Summary
The dashboard was only showing 995 candidates instead of all 2,880+ candidates with financial data. Top fundraisers like Jon Ossoff ($33.3M) and AOC ($19.8M) were missing from the display.

---

## Root Cause Analysis

### Bug #1: Supabase Query Row Limit (PRIMARY ISSUE)
**Symptom:** Dashboard showed only 995-996 candidates regardless of filters

**Root Cause:**
Supabase has a **default 1,000 row limit** on all queries. Our initial query was:
```javascript
const { data: financials } = await supabase
  .from('financial_summary')
  .select('...')
  .eq('cycle', filters.cycle);
```

This query returned only the **first 1,000 out of 2,880 financial records**, which contained ~996 unique candidate IDs. The remaining 1,880 financial records (including Jon Ossoff and other top fundraisers) were never fetched.

**How We Discovered It:**
- Verified local JSON files had all 2,832 candidates ✓
- Verified Supabase database had all 2,880 financial records ✓
- Tested direct Supabase query and noticed only 1,000 records returned
- Console logs showed: `Total financial records: 1000` (not 2,880)

**Solution:**
Implemented pagination to fetch ALL financial records in batches:

```javascript
// BEFORE (BROKEN - only gets first 1000 records)
const { data: financials } = await supabase
  .from('financial_summary')
  .select('candidate_id, total_receipts, total_disbursements, cash_on_hand, updated_at')
  .eq('cycle', filters.cycle);

// AFTER (FIXED - gets all records with pagination)
const financials = [];
let from = 0;
const PAGE_SIZE = 1000;
let hasMore = true;

while (hasMore) {
  const { data: page, error } = await supabase
    .from('financial_summary')
    .select('candidate_id, total_receipts, total_disbursements, cash_on_hand, updated_at')
    .eq('cycle', filters.cycle)
    .range(from, from + PAGE_SIZE - 1);

  if (error) throw error;

  if (page && page.length > 0) {
    financials.push(...page);
    from += PAGE_SIZE;
    hasMore = page.length === PAGE_SIZE;
  } else {
    hasMore = false;
  }
}
```

**Location:** `frontend/src/hooks/useCandidateData.js:16-43`

**Result:** Now fetches all 2,880 financial records across 3 pages (1000 + 1000 + 880)

---

### Bug #2: Duplicate candidate_id Keys in React
**Symptom:** React console errors:
```
Encountered two children with the same key, `S4MS00187`.
Keys should be unique so that components maintain their identity across updates.
```

**Root Cause:**
The `financial_summary` table contains **multiple records per candidate** (different coverage periods/report dates). When we fetched all 2,880 financial records, some candidates appeared 2-3 times with different `coverage_end_date` values.

For example:
- S4MS00187 had 2 records (Q2 2025 and Q3 2025)
- Each became a separate row in the table with the same `candidate_id` key

**How We Discovered It:**
- After fixing Bug #1, saw ~2,875 candidates displayed but React warnings in console
- Supabase showed 2,880 financial records but only 5,185 total candidates
- Difference (2,880 - 2,800 = 80) indicated ~80 duplicate candidates

**Solution:**
Deduplicate financial records by `candidate_id`, keeping only the **most recent** record for each candidate:

```javascript
// Deduplicate by candidate_id - keep the most recent record for each candidate
const financialsMap = {};
financials.forEach(fin => {
  const existing = financialsMap[fin.candidate_id];
  if (!existing || new Date(fin.updated_at) > new Date(existing.updated_at)) {
    financialsMap[fin.candidate_id] = fin;
  }
});

const uniqueFinancials = Object.values(financialsMap);
console.log(`After deduplication: ${uniqueFinancials.length} unique candidates`);
```

**Location:** `frontend/src/hooks/useCandidateData.js:47-57`

**Result:**
- Reduced from 2,880 records to ~2,850 unique candidates
- Eliminated all React duplicate key warnings
- Each candidate appears exactly once with their most recent financial data

---

### Bug #3: Incomplete Data Load to Supabase (RESOLVED EARLIER)
**Symptom:** Jon Ossoff and other senators not appearing in dashboard

**Root Cause:**
Previous run of `load_to_supabase.py` didn't complete successfully - only partial data was uploaded to Supabase.

**Solution:**
Re-ran `load_to_supabase.py` which used UPSERT to fill in missing records:
```bash
python3 load_to_supabase.py
```

**Result:**
- Candidates: 5,185/5,185 inserted
- Financials: 2,832/2,832 inserted
- Jon Ossoff (S8GA00180) now present in both tables

**Location:** `load_to_supabase.py` (no code changes needed - just re-execution)

---

## False Leads We Explored

### ❌ Attempted Fix #1: Batching Candidate Queries
**What we tried:** Split candidate IDs into batches of 500 and used `.in()` filter with `.range()`

**Why it didn't work:** The problem was BEFORE the candidate query - we were only fetching 1,000 financial records to begin with, so we only had 996 candidate IDs to query.

**Code attempted:**
```javascript
for (let i = 0; i < candidateIds.length; i += BATCH_SIZE) {
  const batchIds = candidateIds.slice(i, i + BATCH_SIZE);
  let query = supabase
    .from('candidates')
    .in('candidate_id', batchIds)
    .range(0, BATCH_SIZE - 1);  // This didn't help
}
```

### ❌ Attempted Fix #2: Reversed Query Approach
**What we tried:** Fetch financial_summary first, then fetch candidates

**Why it didn't work (initially):** Good idea, but we still hit the 1,000 row limit on the financial_summary query

**What we learned:** This was the RIGHT approach, we just needed to add pagination to the financial_summary query

---

## Final Solution Summary

The complete fix required TWO changes to `frontend/src/hooks/useCandidateData.js`:

1. **Add pagination to financial_summary query** (lines 19-43)
   - Fetch all 2,880 records in chunks of 1,000
   - Use `.range(from, to)` to get each page

2. **Deduplicate financial records** (lines 47-57)
   - Keep only the most recent record per candidate_id
   - Use Map-based deduplication with `updated_at` comparison

---

## Verification Steps

To verify the fix is working:

1. **Check browser console** (F12 → Console tab):
   ```
   🔍 Fetching ALL financial records with pagination...
   🔍 Fetched financial page: 0-1000 (total: 1000)
   🔍 Fetched financial page: 1000-2000 (total: 2000)
   🔍 Fetched financial page: 2000-2880 (total: 2880)
   🔍 Total financial records loaded: 2880
   🔍 After deduplication: 2850 unique candidates
   ```

2. **Check dashboard display:**
   - "Showing 2,850 Candidates" (or similar)
   - No React duplicate key warnings
   - Jon Ossoff appears at #1 with $33,345,718

3. **Check Supabase directly:**
   ```python
   # Count financial records
   SELECT COUNT(*) FROM financial_summary WHERE cycle = 2026;
   # Should return: 2880

   # Get top fundraiser
   SELECT c.name, f.total_receipts
   FROM financial_summary f
   JOIN candidates c ON f.candidate_id = c.candidate_id
   WHERE f.cycle = 2026
   ORDER BY f.total_receipts DESC
   LIMIT 1;
   # Should return: OSSOFF, T. JONATHAN | $33,345,718.47
   ```

---

## Key Lessons Learned

1. **Supabase has row limits** - Always use pagination for tables with >1,000 rows
2. **Test at scale** - A query that works with 100 records may fail with 3,000
3. **Verify data at every layer:**
   - Local JSON files ✓
   - Database ✓
   - API queries ✓
   - Frontend display ✓
4. **Deduplicate when necessary** - Financial data often has multiple records per entity
5. **Use console.log() liberally** - Debug logs helped us identify the exact point of failure

---

## Performance Impact

**Before:**
- 1 query to financial_summary (returned 1,000 records)
- 2 queries to candidates (2 batches of 500 IDs)
- Total: 3 queries, ~1 second load time

**After:**
- 3 queries to financial_summary (pagination: 1000 + 1000 + 880)
- 6 queries to candidates (6 batches of 500 IDs)
- Total: 9 queries, ~2-3 seconds load time

**Trade-off:** 2-3x more queries, but now displays ALL candidates correctly. This is acceptable since:
- Data only loads once on component mount
- User sees loading state
- Correctness > speed for this use case

---

## Future Improvements

1. **Add server-side aggregation** - Create a Supabase view that deduplicates and joins the data
2. **Implement caching** - Cache results in localStorage to avoid re-fetching on page refresh
3. **Add loading progress** - Show "Loading 1000/2880 records..." during pagination
4. **Consider virtual scrolling** - For rendering 2,850 rows efficiently
5. **Clean up duplicate financial records** - Update database schema to prevent duplicates

---

## Files Modified

1. `frontend/src/hooks/useCandidateData.js` - Added pagination and deduplication
2. `load_to_supabase.py` - Re-ran to ensure all data uploaded (no code changes)

## Related Documentation

- Supabase Pagination: https://supabase.com/docs/reference/javascript/range
- React Keys: https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key
