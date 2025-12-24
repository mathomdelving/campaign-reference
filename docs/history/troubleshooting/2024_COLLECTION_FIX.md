# 2024 Cycle Collection - Issue Analysis & Fix

**Date:** November 7, 2025
**Status:** Ready to Resume Collection

---

## 🔍 What Went Wrong

### The Failure
During the initial 30-hour collection run, the script successfully collected data for:
- ✅ 2026: 2,378 candidates
- ❌ 2024: Only 200 candidates (stopped at page 3)
- ✅ 2022: 4,450 candidates
- ✅ 2020: 1,200 candidates
- ✅ 2018: 3,777 candidates

**Error Log:**
```
PROCESSING CYCLE 2024
  Fetching ALL candidates for 2024...
    Error fetching page 3: 429
  ✓ Found 200 total candidates
```

---

## 🐛 Root Cause

### Problem 1: No Retry Logic
**File:** `collect_all_filings_complete.py` (lines 90-92)

```python
if not response.ok:
    print(f"Error fetching page {page}: {response.status_code}")
    break  # ← GIVES UP IMMEDIATELY!
```

When the script encountered a 429 (rate limit) error, it **immediately quit** instead of:
- Waiting for the rate limit to reset
- Retrying the failed request
- Using exponential backoff

### Problem 2: Rolling Rate Limit Window
The FEC API uses a **rolling 1-hour window** for rate limiting:
- Limit: 1,000 API calls per hour
- Script rate: 900 calls/hour (4 seconds between calls)
- Issue: Calls from the previous hour still count

**What happened:**
1. Script processed 2026 successfully (~5,400 calls over 6 hours)
2. Started 2024, made 2 successful pages
3. On page 3, some calls from the previous hour were still in the rolling window
4. Hit rate limit → script quit

### Problem 3: Sleep AFTER Request
```python
response = requests.get(...)
time.sleep(RATE_LIMIT_DELAY)  # ← Too late if already at limit
```

The delay happens after the request is made, so if you're already at the limit, the damage is done.

---

## ✅ The Fix

### New Script: `collect_2024_resume.py`

**Key Improvements:**

#### 1. Retry Logic with Exponential Backoff
```python
def make_fec_request_with_retry(url, params, max_retries=5):
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            return response

        # Rate limit error - wait and retry
        if response.status_code == 429:
            wait_time = RATE_LIMIT_DELAY * (2 ** attempt)
            print(f"Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
```

**Backoff sequence for 429 errors:**
- Attempt 1: Wait 4 seconds
- Attempt 2: Wait 8 seconds
- Attempt 3: Wait 16 seconds
- Attempt 4: Wait 32 seconds
- Attempt 5: Wait 64 seconds

#### 2. Resume Capability
The script automatically:
- Checks `collection_progress.json` for already-processed candidates
- Skips candidates that were already collected
- Continues from where it left off

#### 3. Better Error Handling
- Catches all exceptions and retries
- Logs detailed error information
- Doesn't quit on first error

#### 4. Progress Tracking
- Saves progress every 25 candidates
- Can be safely interrupted (Ctrl+C)
- Resumes automatically on next run

---

## 🚀 How to Resume Collection

### Step 1: Review Current Status
```bash
python3 -c "import json; data = json.load(open('collection_progress.json')); print('2024 status:', data.get('2024', {}).get('candidates_processed', 0), 'candidates processed')"
```

Expected output: `2024 status: 200 candidates processed`

### Step 2: Run the Resume Script
```bash
python3 collect_2024_resume.py
```

**Or run in background:**
```bash
nohup python3 -u collect_2024_resume.py > 2024_collection.log 2>&1 &
```

### Step 3: Monitor Progress
```bash
# Watch the log file
tail -f 2024_collection.log

# Or check progress file
watch -n 60 'python3 -c "import json; data = json.load(open(\"collection_progress.json\")); print(\"Progress:\", data.get(\"2024\", {}).get(\"candidates_processed\", 0), \"candidates\")"'
```

---

## ⏱️ Expected Timeline

**Estimated API calls for complete 2024 cycle:**
- Fetch candidates: ~20-40 pages = 40 calls
- Per candidate (assume ~2,000 candidates):
  - Get committees: 2,000 calls
  - Get reports: ~3,000 calls
- **Total: ~5,000 calls**

**Duration:**
- At 4 seconds per call: ~5.5 hours
- With retry delays for 429s: ~6-8 hours
- **Total estimated: 6-8 hours**

---

## 📊 How to Verify Completion

### After Collection Completes

1. **Check record counts:**
```sql
SELECT
  cycle,
  COUNT(*) as filings,
  COUNT(DISTINCT candidate_id) as unique_candidates
FROM quarterly_financials
WHERE cycle = 2024
GROUP BY cycle;
```

Expected: ~1,500-2,000 candidates, ~5,000-10,000 filings

2. **Check top fundraisers:**
```sql
SELECT
  candidate_id,
  name,
  office,
  SUM(total_receipts)::BIGINT as total_raised
FROM quarterly_financials
WHERE cycle = 2024
GROUP BY candidate_id, name, office
ORDER BY total_raised DESC
LIMIT 10;
```

3. **Verify against FEC data:**
- Check known high-profile races (Senate, competitive House)
- Compare top fundraisers with public reporting

---

## 🔄 If Collection Fails Again

### Safe to Interrupt
The script saves progress every 25 candidates. You can safely:
- Press Ctrl+C to stop
- Run the script again to resume
- No data will be duplicated (thanks to the unique constraint)

### If 429 Errors Persist
1. Check if someone else is using the same FEC API key
2. Consider increasing `RATE_LIMIT_DELAY` to 5-6 seconds
3. Run collection during off-peak hours (late night EST)

### Manual Resume
If needed, you can manually start from a specific page:
```python
candidates = get_all_candidates(2024, start_page=10)  # Start from page 10
```

---

## 📋 Comparison: Old vs New Script

| Feature | Original Script | New Script |
|---------|----------------|------------|
| **Rate limit delay** | 4 seconds | 4 seconds |
| **Retry on 429** | ❌ Quits immediately | ✅ Retries with backoff |
| **Max retries** | 0 | 5 attempts |
| **Exponential backoff** | ❌ No | ✅ Yes (4s → 64s) |
| **Resume capability** | ✅ Yes | ✅ Yes (improved) |
| **Error logging** | Basic | Detailed |
| **Safe interruption** | ✅ Yes | ✅ Yes |

---

## ✅ Checklist

Before running the resume script:

- [ ] Confirmed SQL deduplication script was run successfully
- [ ] Checked current 2024 progress (200 candidates)
- [ ] Reviewed `collect_2024_resume.py` script
- [ ] Decided whether to run in foreground or background
- [ ] Ready to monitor for 6-8 hours

To start collection:
```bash
python3 collect_2024_resume.py
```

---

## 📝 Summary

**Issue:** Original script quit immediately on 429 error, leaving 2024 cycle incomplete
**Fix:** New script with retry logic, exponential backoff, and better error handling
**Next Step:** Run `collect_2024_resume.py` to complete collection (~6-8 hours)
**Safety:** Can interrupt and resume at any time without data loss

After collection completes, you'll have complete data for all 5 cycles (2018-2026)!
