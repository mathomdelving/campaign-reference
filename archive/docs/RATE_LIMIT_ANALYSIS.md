# FEC API Rate Limit Analysis - Political Pole

**Date:** October 22, 2025
**Status:** ✅ Rate limiting properly configured

---

## ⚠️ Critical Issue Identified & Fixed

Your question caught a **critical timing miscalculation** that would have caused problems!

### Original Problem
The initial code had only ONE 4-second delay per candidate, but was making **MULTIPLE API calls** per candidate:
- Call #1: `/candidate/{id}/totals/` (summary data)
- Call #2: `/candidate/{id}/committees/` (get committee IDs)
- Call #3+: `/committee/{id}/filings/` (quarterly filings - one per committee)

**This would have caused:**
- Bunched API calls without proper delays
- Likely rate limit violations (429 errors)
- Failed data collection

---

## ✅ Fix Implemented

Added 4-second delays **AFTER EACH API CALL**:

### Updated Flow (Per Candidate)

```
1. Call /candidate/{id}/totals/
   └─ Wait 4 seconds

2. Call /candidate/{id}/committees/
   └─ Wait 4 seconds

3. For each committee:
     Call /committee/{committee_id}/filings/
     └─ Wait 4 seconds
```

### Code Changes

**In `fetch_committee_quarterly_filings()` function:**
- Added `time.sleep(4)` after committees call (line 150)
- Added `time.sleep(4)` after each filings call (line 169)

**In main loop:**
- Kept `time.sleep(4)` after totals call (line 266)
- Removed duplicate delay after quarterly function (function handles it internally)

---

## 📊 Updated Timeline Calculation

### FEC API Limits
- **Limit:** 1,000 requests per hour
- **Our rate:** 4 seconds between calls = 900 requests/hour = **10% safety margin** ✅

### API Calls Per Candidate
- **Most candidates:** 3 calls (totals + committees + filings)
  - 1 for totals
  - 1 for committees
  - 1 for filings (most candidates have 1 principal committee)

- **Some candidates:** 4+ calls
  - Candidates with multiple committees
  - Rare, but possible

**Average: ~3 calls per candidate**

### Time Calculation

```
5,185 candidates × 3 API calls = 15,555 total API calls
15,555 calls × 4 seconds = 62,220 seconds
62,220 seconds ÷ 3,600 = 17.3 hours
```

**Estimated completion: 17-18 hours**

### Hourly Progress
- **~300 candidates per hour**
- **Progress saves every 50 candidates** (~10 minutes)
- **Resume capability** if interrupted

---

## 🕐 Timeline Breakdown

### If Started at 10 PM Tonight:
- **10:00 PM** - Start collection
- **12:00 AM** - ~600 candidates done (12%)
- **6:00 AM** - ~2,400 candidates done (46%)
- **12:00 PM** - ~4,200 candidates done (81%)
- **3:00 PM** - ~5,000 candidates done (96%)
- **4:00 PM** - ✅ Complete!

### If Started at 11 PM Tonight:
- **11:00 PM** - Start collection
- **7:00 AM** - ~2,400 candidates done (46%)
- **1:00 PM** - ~4,200 candidates done (81%)
- **5:00 PM** - ✅ Complete!

---

## 🛡️ Safety Features

### Rate Limit Protection
1. **4-second delays** between ALL API calls
2. **Automatic retry** with exponential backoff on 429 errors:
   - 1st retry: Wait 60 seconds
   - 2nd retry: Wait 120 seconds
   - 3rd retry: Wait 240 seconds
3. **Under FEC limit:** 900 req/hour vs 1,000 limit (10% safety margin)

### Progress Saving
- **Saves every 50 candidates** (~10 minutes)
- **Resume capability** - Just run script again if interrupted
- **Progress file:** `progress.json` tracks:
  - Last processed candidate index
  - All financials collected so far
  - All quarterly filings collected so far

### Error Handling
- **Network errors:** Logs error, continues with next candidate
- **Timeouts:** 10-second timeout per request
- **Missing data:** Gracefully handles candidates with no filings

---

## 🔍 Comparison to Original Collection

### Original Collection (Phase 1)
- **API calls:** 1 per candidate (totals only)
- **Total calls:** ~5,200
- **Time:** ~5.8 hours
- **Data:** Summary totals only (no quarterly breakdown)

### New Collection (Current)
- **API calls:** 3 per candidate (totals + committees + filings)
- **Total calls:** ~15,500
- **Time:** ~17-18 hours
- **Data:** Summary totals + quarterly timeseries ✅

**Why longer?**
- **3x more API calls** per candidate
- But we get **quarterly breakdown** for timeseries charts!

---

## ✅ Verification

### Test Results (3 candidates)
Tested on Vindman, Wahls, Miller-Meeks:
- ✅ All returned quarterly data
- ✅ Rate limiting worked correctly
- ✅ No 429 errors
- ✅ Delays properly spaced

### Rate Limit Math Check
```
3 API calls × 4 seconds = 12 seconds per candidate
3,600 seconds/hour ÷ 12 seconds = 300 candidates/hour
300 candidates/hour × 3 calls = 900 API calls/hour
900 < 1,000 FEC limit ✅
```

---

## 📋 Monitoring During Collection

### How to Check Progress

**While running:**
```bash
# Watch output in real-time
tail -f fetch_output.log  # If using nohup

# Check progress file
cat progress.json | grep last_processed_index

# See how many quarterly records so far
cat progress.json | grep -o "quarterly_financials" | wc -l
```

**Progress indicators:**
- Every 50 candidates: "💾 Progress saved" message
- Every candidate: "✓ (X quarterly filings)" message
- Errors logged with candidate name

### Expected Output Example
```
[1/5185] VINDMAN, YEVGENY (H4VA07234)... ✓ (3 quarterly filings)
[2/5185] WAHLS, ZACH P (S6IA00272)... ✓ (3 quarterly filings)
[3/5185] SMITH, JOHN (H6CA12345)... ✓ (no quarterly data)
...
[50/5185] ...
  💾 Progress saved: 48 summary, 120 quarterly (processed 50/5185)
```

---

## 🚨 What If Rate Limits Are Hit?

### Unlikely, but if it happens:

**Script will:**
1. Detect 429 error
2. Print: "⚠️  RATE LIMIT! Waiting 60s..."
3. Wait with exponential backoff
4. Retry up to 3 times
5. If still failing, skip that candidate and continue

**You should:**
- Let it run - automatic retry handles it
- Don't restart script - will just hit same limit
- Check FEC API status: https://api.open.fec.gov/developers/

**Prevention:**
- ✅ We're at 900 req/hour (10% under limit)
- ✅ Exponential backoff implemented
- ✅ Progress saves prevent data loss

---

## 📈 Expected Final Results

### Output Files

**financials_2026.json** (updated)
- ~2,800-3,000 summary records
- Same format as before
- Cumulative totals per candidate

**quarterly_financials_2026.json** (NEW!)
- **Estimated: 6,000-10,000 quarterly records**
- Breakdown by quarter:
  - Q1 2025 (Jan-Mar): ~2,000 filings
  - Q2 2025 (Apr-Jun): ~2,500 filings
  - Q3 2025 (Jul-Sep): ~2,800 filings
  - Q4 2025 (Oct-Dec): Data from late Oct onwards
- Includes amendments (we'll dedupe in database load)

### Data Quality

**Each quarterly record includes:**
- Period (coverage_start_date to coverage_end_date)
- Quarter (Q1, Q2, Q3, Q4)
- Total receipts (raised THIS quarter)
- Total disbursements (spent THIS quarter)
- Cash beginning (start of quarter)
- Cash ending (end of quarter)
- Filing metadata (filing_id, is_amendment)

---

## 🎯 Recommendation

**START TONIGHT** - Here's why:

1. **17-18 hour runtime** means starting at 10-11 PM = done by 4-5 PM tomorrow
2. **Can't parallelize** - Must respect rate limits
3. **Progress saves every 10 min** - Safe to interrupt if needed
4. **Tomorrow we build UI** - While data collects, we can work on frontend in parallel

**Alternative:** Start tomorrow morning at 8 AM = done by 1-2 AM next day (less ideal)

---

## ✅ Final Checklist

Before starting collection:

- ✅ Rate limiting: 4 seconds between EACH API call
- ✅ Safety margin: 900 req/hour (10% under FEC limit)
- ✅ Auto-retry: Exponential backoff on 429 errors
- ✅ Progress saving: Every 50 candidates
- ✅ Resume capability: Can restart anytime
- ✅ Tested: 3 candidates validated successfully
- ✅ Estimated time: 17-18 hours clearly communicated

**You are SAFE to start the overnight collection!** 🏁

---

*Fixed by Claude Code - October 22, 2025*
*Thanks for the excellent catch on rate limiting!*
