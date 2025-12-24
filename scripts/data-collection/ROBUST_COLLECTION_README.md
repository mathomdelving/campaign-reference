# Robust FEC Data Collection - Ironclad Edition

## Overview

This document describes the **robust, failure-resilient data collection system** designed to thoroughly collect ALL FEC campaign finance data regardless of API rate limits, timeouts, server restarts, or other failures.

## The Problem (Original Scripts)

The original collection scripts (`fetch_fec_data.py`, `fetch_cycle_data.py`) had critical weaknesses:

1. **No Distinction Between "No Data" vs "Error"**:
   - When a candidate had no financial data, result was `None`
   - When a timeout/rate limit occurred, result was also `None`
   - No way to tell which candidates failed vs legitimately had no data

2. **No Retry Mechanism**:
   - Errors were logged but never retried
   - Data for failed candidates was permanently lost
   - Example: In 2022 collection, 15 candidates failed (13 timeouts + 2 persistent rate limits)

3. **Silent Data Loss**:
   - Progress file marked candidates as "processed" even if they failed
   - Failed candidates were never revisited
   - No tracking of what was lost

## The Solution: `fetch_cycle_data_robust.py`

### Key Features

#### 1. **Dual Tracking System**

The robust script maintains TWO separate lists:

- **`failed_candidates`**: Candidates that hit errors (timeouts, rate limits, network issues)
  - These WILL be retried automatically
  - Includes error type, error message, timestamp

- **`no_data_candidates`**: Candidates that legitimately have no financial data
  - These are DONE, no retry needed
  - Helps distinguish "no data" from "error"

#### 2. **Enhanced Error Categorization**

Every function returns `(data, error_type, error_msg)` tuple:

```python
# Example: fetch_candidate_financials
(data, error_type, error_msg) = fetch_candidate_financials(candidate_id, cycle)

# If successful:
(financial_data, None, None)

# If timeout:
(None, "timeout", "Timeout after 30s: Read timed out")

# If rate limit:
(None, "rate_limit", "Rate limit persists after 3 retries")

# If legitimate no data:
(None, None, None)
```

Error types:
- `"timeout"`: Request timed out
- `"rate_limit"`: API rate limit hit and persisted after exponential backoff
- `"network"`: Connection error or network issue
- `"server"`: HTTP error from FEC API (4xx, 5xx)
- `None`: Success or legitimate "no data"

#### 3. **Automatic Retry Logic**

After processing all candidates, the script automatically retries failures:

1. **Main Collection Pass**: Process all 7,000+ candidates
2. **Retry Pass #1**: Retry all failed candidates
3. **Retry Pass #2**: Retry any still failing
4. **Retry Pass #3**: Final retry attempt
5. **Report**: Any persistent failures saved to `failures_{cycle}.json`

Default: 3 retry passes (configurable via `--max-retries`)

#### 4. **Restart-Safe Progress Tracking**

Progress file (`progress_{cycle}_robust.json`) contains:

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
      "error_msg": "Timeout after 30s: Read timed out",
      "timestamp": "2025-11-19T18:32:15.123456",
      "retry_count": 0
    }
  ],
  "no_data_candidates": [
    {
      "candidate_id": "H0VA01234",
      "name": "SMITH, BOB",
      "timestamp": "2025-11-19T18:30:10.123456"
    }
  ],
  "retry_count": 0,
  "last_updated": "2025-11-19T18:32:15.123456"
}
```

If the script crashes or is stopped:
- Run it again with same `--cycle` argument
- It will resume from `last_processed_index`
- It will preserve existing financials/quarterly data
- It will preserve failure/no-data tracking

#### 5. **Committee Designation Fields**

Includes all committee designation fields for quarterly reports:
- `designation`: Single letter code (P, A, J, D)
- `designation_full`: Full description ("Principal Campaign Committee", etc.)
- `committee_type`: Single letter type code
- `committee_type_full`: Full type description

## Usage

### Basic Collection

```bash
# Collect data for a single cycle
python3 scripts/data-collection/fetch_cycle_data_robust.py --cycle 2022

# Collect data with custom retry limit
python3 scripts/data-collection/fetch_cycle_data_robust.py --cycle 2024 --max-retries 5
```

### Complete Multi-Cycle Collection

```bash
# Uses the robust script automatically
python3 scripts/data-collection/collect_complete_cycle_data.py --cycle 2022
```

This will:
1. Run `fetch_cycle_data_robust.py --cycle 2022`
2. Run `fetch_committee_designations.py --cycles 2022`
3. Report which JSON files were created

### Resuming Interrupted Collections

If the script is stopped (Ctrl+C, crash, server restart):

```bash
# Just run it again - it will resume automatically
python3 scripts/data-collection/fetch_cycle_data_robust.py --cycle 2022
```

Output will show:
```
✓ Resuming from candidate #1251
✓ Already have 625 summary records
✓ Already have 3,142 quarterly records
✓ 8 candidates need retry
✓ 320 candidates with no data
```

## Output Files

### During Collection

- `progress_{cycle}_robust.json`: Progress tracking (deleted when complete)
- `candidates_{cycle}.json`: List of all candidates (created once at start)

### After Collection

- `financials_{cycle}.json`: Financial summaries for candidates with data
- `quarterly_financials_{cycle}.json`: All quarterly reports with designation fields
- `no_data_{cycle}.json`: Candidates with legitimately no financial data
- `failures_{cycle}.json`: **Only created if there are persistent failures**

### Understanding the Output

#### `financials_{cycle}.json`
Contains candidates that have financial summary data (17 fields):
- candidate_id, name, party, state, district, office
- total_receipts, total_disbursements, cash_on_hand
- coverage_start_date, coverage_end_date
- last_report_year, last_report_type
- cycle

#### `quarterly_financials_{cycle}.json`
Contains all quarterly filings (21 fields including 4 designation fields):
- All candidate fields above
- committee_id, filing_id, report_type
- coverage_start_date, coverage_end_date
- total_receipts, total_disbursements
- cash_beginning, cash_ending, is_amendment
- **designation, designation_full, committee_type, committee_type_full**
- cycle

#### `no_data_{cycle}.json`
Transparency file showing candidates with no financial data:
```json
[
  {
    "candidate_id": "H0VA01234",
    "name": "SMITH, BOB",
    "timestamp": "2025-11-19T18:30:10.123456"
  }
]
```

#### `failures_{cycle}.json` (if created)
Critical file showing persistent failures needing manual investigation:
```json
[
  {
    "candidate_id": "H2MD06286",
    "name": "JONES, ALICE",
    "error_type": "timeout",
    "error_msg": "Timeout after 30s: Read timed out",
    "timestamp": "2025-11-19T20:15:32.123456",
    "retry_count": 3
  }
]
```

If this file exists, it means:
- These candidates failed even after 3 retry passes
- Manual investigation may be needed
- Could be FEC API issues, specific candidate data corruption, etc.

## Success Criteria

### 100% Success
```
✓ Saved financials_2022.json: 3,842 records
✓ Saved quarterly_financials_2022.json: 18,532 records
✓ Saved no_data_2022.json: 3,376 candidates
✅ Zero failures - 100% success rate!
```

No `failures_2022.json` file created = perfect collection!

### Partial Failures
```
✓ Saved financials_2022.json: 3,840 records
✓ Saved quarterly_financials_2022.json: 18,510 records
✓ Saved no_data_2022.json: 3,376 candidates
⚠️  Saved failures_2022.json: 2 persistent failures

  ❌ Persistent failures: 2
     (See failures_2022.json for details)
```

`failures_2022.json` exists = review needed, 2 candidates lost

## Comparison: Old vs Robust

| Feature | Old Scripts | Robust Script |
|---------|-------------|---------------|
| Distinguishes "no data" from "error" | ❌ No | ✅ Yes |
| Automatic retry for failures | ❌ No | ✅ Yes (3 passes) |
| Tracks failed candidates | ❌ No | ✅ Yes |
| Resume after crash | ⚠️ Partial | ✅ Full |
| Error categorization | ❌ Basic | ✅ Detailed (5 types) |
| Committee designations | ❌ No | ✅ Yes (4 fields) |
| Data loss prevention | ❌ No | ✅ Yes |
| Transparency (no-data list) | ❌ No | ✅ Yes |

## Handling the 15 Failed Candidates from Current 2022 Collection

The current running process (PID 66657) using the OLD script has 15 failed candidates that won't be retried.

### Option 1: Let it finish, then retry manually
```bash
# Wait for PID 66657 to complete
# Then run robust script to fill gaps
python3 scripts/data-collection/fetch_cycle_data_robust.py --cycle 2022

# It will:
# - Load existing candidates_2022.json
# - Load existing progress (0 records since it's a new run)
# - Process all 7,218 candidates
# - Will get data for the 15 that failed before
# - Merge with existing data during load phase
```

### Option 2: Stop old process, switch to robust
```bash
# Stop the old process
kill 66657

# Start robust collection
python3 scripts/data-collection/fetch_cycle_data_robust.py --cycle 2022

# Will resume from where old script left off (700/7,218)
# Will properly track the 15 failures
# Will retry them automatically
```

**Recommendation**: Option 1 is safer - let the current process finish (it's 700/7,218 = 10% done), then use robust script for fresh 2024/2026 collections.

## Best Practices

1. **Monitor the collection**:
   - Check progress every few hours
   - Look for persistent rate limiting
   - Check failure counts in progress file

2. **Review output files**:
   - Always check if `failures_{cycle}.json` was created
   - Review `no_data_{cycle}.json` to understand "no data" candidates
   - Spot check financial data for accuracy

3. **If failures persist**:
   - Check FEC API status
   - Increase timeout values in code
   - Try running at different time (less API load)
   - Manually investigate specific failing candidates

4. **Before loading to Supabase**:
   - Verify no `failures_{cycle}.json` or acceptable failure count
   - Check total record counts match expectations
   - Spot check committee designation fields are populated

## Technical Details

### Timeout Values
- Candidate list fetching: 30 seconds
- Financial totals: 30 seconds (increased from 10s)
- Committee/filings: 30 seconds (increased from 10s)

### Rate Limit Handling
- Exponential backoff: 60s → 120s → 240s
- After 3 retries, marks as failed and moves on
- Failed candidates retried in subsequent retry passes

### API Call Pattern
Per candidate:
1. Fetch financial totals (1 call) + 4s delay
2. Fetch committees (1 call) + 4s delay
3. For each committee, fetch filings (N calls) + 4s delay each

Average: ~5 calls per candidate = ~20 seconds per candidate
Total time: 7,218 candidates × 20s = ~40 hours

With failures and retries: 40-45 hours typical

## Troubleshooting

### "Script seems stuck"
- Check if waiting for rate limit (prints "RATE LIMIT! Waiting Xs...")
- Check progress file to see last_updated timestamp
- Normal to have pauses during heavy rate limiting

### "Too many failures"
- FEC API might be having issues
- Try again later
- Consider increasing `--max-retries` to 5

### "Resume not working"
- Ensure using exact same `--cycle` argument
- Check progress file exists: `progress_{cycle}_robust.json`
- Check file isn't corrupted (valid JSON)

### "Missing designation fields"
- These should always be populated now
- If missing, check FEC API response format hasn't changed
- May need to update committee field extraction code

## Next Steps After Collection

1. Review all output JSON files
2. Verify no persistent failures (or acceptable count)
3. Load to Supabase:
   ```bash
   python3 scripts/data-loading/load_to_supabase.py
   python3 scripts/data-loading/load_committee_designations.py --cycles 2022
   ```
4. Verify missing candidates (like Christy Smith 2022) now appear in database
5. Run data quality checks

## Summary

The robust collection script provides **ironclad data collection**:
- **Zero tolerance for silent data loss**
- **Automatic recovery from failures**
- **Complete transparency** about what succeeded, what failed, what had no data
- **Restart-safe** - can survive server crashes, user interruptions, etc.
- **Comprehensive error tracking** - every failure categorized and logged

This ensures you can confidently collect campaign finance data for any cycle knowing that:
1. Every candidate will be attempted
2. Failures will be automatically retried
3. You'll have a complete record of what happened
4. No data will be silently lost
