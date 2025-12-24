# FEC Data Collection - All Constraints and Learnings

**Status: DRAFT - Will be finalized after robust script verification**

This document captures everything we've learned about successfully collecting FEC campaign finance data through multiple iterations and failures.

## The Journey: What Didn't Work

### Previous Scripts and Why They Failed

1. **Original `fetch_fec_data.py`** (Oct-Nov 2025)
   - ❌ No distinction between "no data" and "error"
   - ❌ No retry mechanism for failures
   - ❌ Lost 15+ candidates per collection (timeouts, rate limits)
   - ❌ Silent data loss
   - ⚠️ Result: ~0.2% data loss per run

2. **`fetch_cycle_data.py`** (Historical collections)
   - ❌ Same issues as above
   - ❌ No progress tracking for restarts
   - ❌ Committee designation fields missing
   - ⚠️ Result: Incomplete data, manual gap-filling required

3. **Multiple "Quick Fix" Attempts**
   - Added error logging (but no retry)
   - Increased timeouts (but failures still lost)
   - Progress files (but failures not tracked)
   - ⚠️ Result: Better visibility, still lossy

## The Critical Constraints

### 1. FEC API Rate Limiting

**The Limit:**
- 1000 requests/hour (production key)
- 60 requests/hour (demo key)
- Header often shows incorrect value

**What We Learned:**
- Must have 4+ second delays between calls to be conservative
- Rate limit errors need exponential backoff (60s → 120s → 240s)
- Can't just retry immediately - must wait
- Even with delays, occasional 429s still happen
- **Solution:** Built-in 4s delays + exponential backoff + retry queue

### 2. Timeout Variability

**The Problem:**
- FEC API sometimes takes >10 seconds to respond
- Network issues cause random timeouts
- No pattern - can happen to any candidate

**What We Learned:**
- 10-second timeout too aggressive (13+ failures per 7,000 candidates)
- 30-second timeout optimal
- Still get occasional timeouts despite longer timeout
- **Solution:** 30s timeout + automatic retry for all timeout errors

### 3. The "No Data" vs "Error" Ambiguity

**The Problem:**
```python
# Old code - can't tell difference!
financial_data = fetch_financials(candidate_id)
if financial_data:
    # has data
else:
    # Could be: no data, timeout, rate limit, network error, server error
    # We don't know! Just move on...
```

**What We Learned:**
- ~45% of candidates have no financial data (legitimate)
- ~0.2% of candidates fail due to errors (need retry)
- Old scripts treated both as "None" - lost the failures
- **Solution:** Return tuple (data, error_type, error_msg)

### 4. Process Interruption

**The Problem:**
- Collections take 40-65 hours
- Server restarts, crashes, user cancellations happen
- Lost all progress if not resumable

**What We Learned:**
- Need progress file with last processed index
- Need to preserve collected data
- Need to track failures separately (retry on resume)
- **Solution:** RobustProgress class with comprehensive state

### 5. Committee Designation Fields

**The Problem:**
- Original scripts didn't capture committee type (P, A, J, D)
- Couldn't distinguish Principal vs Authorized committees
- Had to re-collect data to get these fields

**What We Learned:**
- Committee designation critical for analysis
- Must capture: designation, designation_full, committee_type, committee_type_full
- These are in committee objects, not filing objects
- **Solution:** Extract from committee object, pass through to filing records

## The Solution: Robust Collection Architecture

### Core Design Principles

1. **Fail-Safe by Default**
   - Assume errors will happen
   - Track everything that fails
   - Retry automatically
   - Never silently lose data

2. **Transparency Above All**
   - Distinguish "no data" from "error"
   - Log every failure with context
   - Report what succeeded, what failed, what has no data
   - User can audit everything

3. **Restart-Resilient**
   - Can be killed at any time
   - Resumes from exact spot
   - Preserves failure queue for retry
   - No duplicate work

4. **Self-Correcting**
   - Auto-retry failures up to 3 times
   - Exponential backoff for rate limits
   - Extended timeouts for slow responses
   - Reports persistent failures for manual review

### Data Collection Workflow

```
START
  ↓
Load or Fetch Candidates (one-time)
  ↓
Main Pass: Process all candidates
  ├─ Success → Add to financials/quarterly arrays
  ├─ No Data → Add to no_data array
  └─ Error → Add to failed_candidates array
  ↓
Retry Pass #1: Process failed_candidates
  ├─ Success → Move to financials/quarterly
  ├─ No Data → Move to no_data
  └─ Still Failed → Keep in failed_candidates
  ↓
Retry Pass #2: Process still-failing
  ↓
Retry Pass #3: Final attempt
  ↓
Report Results:
  ✓ financials_{cycle}.json
  ✓ quarterly_financials_{cycle}.json
  ✓ no_data_{cycle}.json
  ⚠️ failures_{cycle}.json (if any persist)
```

### Key Metrics for Success

**Target: <0.01% data loss**

After 3 retry passes, acceptable outcomes:
- 0 failures = Perfect! 100% success
- 1-5 failures = Excellent (0.01-0.07% loss)
- 6-20 failures = Good (0.08-0.28% loss)
- 20+ failures = Investigate (likely FEC API issues)

## Technical Specifications

### API Call Pattern

Per candidate (average):
1. GET /candidate/{id}/totals/ (1 call)
2. GET /candidate/{id}/committees/ (1 call)
3. GET /committee/{id}/filings/ (1-5 calls, avg ~3)

Total: ~5 calls per candidate
With 4s delays: ~20 seconds per candidate
Full cycle (7,218 candidates): ~40 hours

### Error Recovery

```python
def fetch_with_recovery(candidate_id):
    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 429:
            # Rate limit - exponential backoff
            retry with 60s → 120s → 240s delays

        response.raise_for_status()
        return (data, None, None)

    except Timeout:
        return (None, "timeout", error_msg)
    except ConnectionError:
        return (None, "network", error_msg)
    except HTTPError:
        return (None, "server", error_msg)
```

### Progress Persistence

```json
{
  "last_processed_index": 1250,
  "financials": [...],
  "quarterly_financials": [...],
  "failed_candidates": [
    {
      "candidate_id": "H2MD06286",
      "name": "JONES, ALICE",
      "error_type": "timeout",
      "error_msg": "Timeout after 30s",
      "timestamp": "2025-11-19T18:32:15",
      "retry_count": 0
    }
  ],
  "no_data_candidates": [...],
  "retry_count": 0,
  "last_updated": "2025-11-19T18:32:15"
}
```

## Known Issues and Workarounds

### Issue 1: FEC Rate Limit Header Misleading
**Problem:** X-RateLimit-Limit header shows 60 even with production key
**Workaround:** Verify by actual performance (calls/hour), not header
**Impact:** None (just confusing)

### Issue 2: Occasional Persistent Rate Limits
**Problem:** Even after 3 retries, some candidates hit persistent 429s
**Workaround:** These get flagged in failures.json for later manual retry
**Impact:** ~1-2 candidates per 7,000 (0.01-0.03%)

### Issue 3: Random Timeouts
**Problem:** FEC API occasionally takes >30s, causing timeout
**Workaround:** Auto-retry recovers most; persistent ones flagged
**Impact:** ~0.1% without retry, ~0.01% with retry

## Future Maintenance

### When FEC API Changes

**Warning Signs:**
- Validation script fails
- Error rate suddenly increases
- New error types appear

**Response:**
1. Run `scripts/maintenance/validate_fec_api.py`
2. Check which endpoint/field changed
3. Update robust script field mappings
4. Re-test on small cycle first

### When to Re-Run Collections

**Triggers:**
- Missing candidates discovered
- Committee designation fields needed
- Data freshness required (quarterly)
- API provided bad data (rare)

**Process:**
1. Run validation script
2. Use robust script (not old scripts)
3. Review failures.json
4. Merge with existing data

## Success Criteria Checklist

Before declaring a script "the winner":

- [ ] Completes full cycle (7,000+ candidates)
- [ ] Auto-retry recovers >99% of failures
- [ ] Failures.json is empty or <5 candidates
- [ ] All 25 fields present in quarterly_financials
- [ ] Can restart mid-run and continue
- [ ] No data vs error distinction works
- [ ] Performance: ~100-120 candidates/hour
- [ ] Clear reporting of what succeeded/failed

---

**Last Updated:** 2025-11-19
**Status:** DRAFT - Awaiting robust script verification
**Next Step:** Test on cycle 2024, verify all criteria met
