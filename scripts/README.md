# FEC Dashboard Scripts

Production-ready scripts for collecting and managing FEC campaign finance data.

---

## ⚠️ CRITICAL: READ THIS FIRST

**Before running ANY data collection script, you MUST read:**

**`docs/DATA_COLLECTION_WORKFLOW.md`**

**THE GOLDEN RULE: NEVER upload data directly to Supabase. ALWAYS use the 2-step workflow:**

1. **Collect → JSON files** (using `scripts/data-collection/fetch_fec_data.py`)
2. **Review JSON → Load to Supabase** (using `scripts/data-loading/load_to_supabase.py`)

**Violating this workflow causes data integrity incidents. See November 18-19, 2025 incident documentation.**

---

## 📂 Directory Structure

```
scripts/
├── README.md                    ← You are here
├── collect_fec_cycle_data.py   ← Main collection script (use this!)
└── (future scripts will go here)
```

---

## 📂 Directory Structure (CORRECTED)

```
scripts/
├── README.md                          ← You are here
├── data-collection/                   ← ✅ Collection scripts (Step 1: Save to JSON)
│   ├── fetch_fec_data.py             ← Main collection script
│   └── README.md
├── data-loading/                      ← ✅ Loading scripts (Step 2: Load JSON to DB)
│   ├── load_to_supabase.py           ← Main loading script
│   ├── load_quarterly_data.py
│   └── backfill_committee_designations.py
├── maintenance/                       ← ✅ Notification & maintenance scripts
│   ├── detect_new_filings.py         ← ⭐ Filing detection (polls FEC API)
│   ├── send_notifications.py         ← ⭐ Email notifications (SendGrid)
│   ├── README_NOTIFICATIONS.md       ← Notification system documentation
│   ├── update_cash_on_hand.py
│   └── retry_failed.py
└── archive/                           ← ❌ BROKEN/DEPRECATED scripts
    └── collect_fec_cycle_data_BROKEN_UPLOADS_DIRECTLY.py  ← DO NOT USE
```

---

## 🚀 CORRECT Collection Workflow

### Step 1: Collection → JSON Files

```bash
# Use the proper collection script
cd /Users/benjaminnelson/Desktop/campaign-reference
python3 scripts/data-collection/fetch_fec_data.py
```

**What it does:**
- Collects candidate metadata, financial summaries, and quarterly reports
- Saves to JSON files: `candidates_{cycle}.json`, `financials_{cycle}.json`, `quarterly_financials_{cycle}.json`
- Includes retry logic, progress tracking, and resume capability

**What it does NOT do:**
- Does NOT upload to Supabase
- Does NOT touch your database
- Gives you time to review data first

### Step 2: Review → Load to Supabase

```bash
# After reviewing JSON files
python3 scripts/data-loading/load_to_supabase.py
```

**What it does:**
- Reads the JSON files you created in Step 1
- Uploads to Supabase with proper error handling
- Respects unique constraints
- Provides clear success/failure reporting

---

## ❌ WHAT NOT TO DO

### DO NOT Use Archived Scripts

The script `collect_fec_cycle_data.py` has been ARCHIVED because it uploads directly to Supabase without saving to JSON first.

**Location:** `archive/collect_fec_cycle_data_BROKEN_UPLOADS_DIRECTLY.py`

**Why it's archived:**
- Violates 2-step workflow
- Caused data integrity incident (Nov 18-19, 2025)
- No human review before upload
- No backup if upload fails
- **DO NOT USE THIS SCRIPT**

---

## 📖 Usage Examples

### Collect Data for a Cycle

```bash
# This saves to JSON (does NOT upload)
python3 scripts/data-collection/fetch_fec_data.py
```

### Review the JSON Files

```bash
# Check file sizes
ls -lh *.json

# Preview data
head -20 candidates_2026.json
head -20 financials_2026.json
head -20 quarterly_financials_2026.json

# Count records
python3 -c "import json; print(f'{len(json.load(open(\"candidates_2026.json\")))} candidates')"
```

### Load to Supabase

```bash
# After reviewing, upload
python3 scripts/data-loading/load_to_supabase.py
```

### Run in Background

```bash
nohup python3 -u scripts/collect_fec_cycle_data.py --cycle 2024 > collection_2024.log 2>&1 &
```

### Monitor Background Process

```bash
# Watch the log file
tail -f collection_2024.log

# Check progress
python3 -c "import json; data = json.load(open('collection_progress.json')); print('Progress:', data.get('2024', {}))"
```

---

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```env
FEC_API_KEY=your_fec_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key_here
```

### Rate Limiting

- **FEC API Limit:** 7,000 calls per hour (upgraded December 2025)
- **Script Rate:** ~900 calls per hour for collection (4 seconds between calls)
- **Notification Polling:** ~120 calls per hour (30 second intervals)
- **Retry Logic:** Up to 5 attempts with exponential backoff on 429 errors

### Backoff Sequence for Rate Limit Errors

1. First retry: Wait 4 seconds
2. Second retry: Wait 8 seconds
3. Third retry: Wait 16 seconds
4. Fourth retry: Wait 32 seconds
5. Fifth retry: Wait 64 seconds

---

## 📊 Data Storage

### Database Tables

#### `candidates`
Stores candidate metadata (one record per candidate).

**Key fields:**
- `candidate_id` (PK)
- `name`, `party`, `state`, `district`, `office`
- `incumbent_challenge`

#### `quarterly_financials`
Stores all financial filings (multiple per candidate).

**Key fields:**
- `candidate_id` (FK)
- `cycle`, `report_type`, `coverage_start_date`, `coverage_end_date`
- `total_receipts`, `total_disbursements` (PERIOD amounts)
- `cash_beginning`, `cash_ending`
- `is_amendment`

**Important:** Uses `total_receipts_period` and `total_disbursements_period` (not YTD) for accurate per-period timeseries data.

### Progress Tracking

**File:** `collection_progress.json`

```json
{
  "2024": {
    "started": "2025-11-07T12:00:00",
    "completed": "2025-11-07T18:30:00",
    "processed_ids": ["H0AL01234", "S2TX00123", ...],
    "candidates_processed": 5226,
    "filings_collected": 12450,
    "last_updated": "2025-11-07T18:30:00"
  }
}
```

---

## ⏱️ Expected Duration

| Cycle | Candidates | Estimated Time |
|-------|-----------|----------------|
| 2026 | ~2,500 | 5-6 hours |
| 2024 | ~5,000 | 6-8 hours |
| 2022 | ~4,500 | 6-8 hours |
| 2020 | ~1,200 | 3-4 hours |
| 2018 | ~3,800 | 5-7 hours |
| 2016 | ~2,000 | 4-6 hours |
| 2014 | ~1,500 | 3-5 hours |

**Factors affecting duration:**
- Number of candidates
- Number of committees per candidate
- Number of reports per committee
- Network speed and FEC API response time

---

## 🛠️ Troubleshooting

### Script Fails with "Missing environment variables"

**Solution:** Create `.env` file with required variables (see Configuration section)

### Getting 429 (Rate Limit) Errors

**Solution:** Script automatically handles this with retry logic. If persistent:
- Check if someone else is using the same API key
- Increase `RATE_LIMIT_DELAY` in the script (line 50)
- Run during off-peak hours (late night EST)

### Script Stops/Interrupted

**Solution:** Simply run the script again - it will automatically resume from where it left off.

### Want to Re-collect a Cycle

**Solution:** Edit `collection_progress.json` and remove that cycle's entry, then run the script.

### Checking if Collection is Complete

```sql
-- Check record counts
SELECT
  cycle,
  COUNT(*) as filings,
  COUNT(DISTINCT candidate_id) as candidates
FROM quarterly_financials
GROUP BY cycle
ORDER BY cycle DESC;

-- Check top fundraisers
SELECT
  candidate_id, name, office,
  SUM(total_receipts)::BIGINT as total_raised
FROM quarterly_financials
WHERE cycle = 2024
GROUP BY candidate_id, name, office
ORDER BY total_raised DESC
LIMIT 10;
```

---

## 📋 Examples

### Collect Recent Cycles
```bash
python3 scripts/collect_fec_cycle_data.py --cycle 2024,2022,2020
```

### Collect Historical Data
```bash
python3 scripts/collect_fec_cycle_data.py --cycle 2016,2014,2012,2010
```

### Presidential Cycles Only
```bash
python3 scripts/collect_fec_cycle_data.py --cycle 2024,2020,2016,2012
```

### Midterm Cycles Only
```bash
python3 scripts/collect_fec_cycle_data.py --cycle 2022,2018,2014,2010
```

---

## 🔒 Data Quality Features

The script includes several data quality improvements:

1. **Deduplication:** Database has unique constraint on report periods
2. **Office standardization:** Uses "H" and "S" consistently
3. **Amendment handling:** Flags amendments with `is_amendment` field
4. **Period amounts:** Uses `_period` not `_ytd` for accurate timeseries
5. **Error handling:** Gracefully handles 404s (normal for candidates without committees)

---

## 📬 Notification System

For detecting new filings and sending email notifications, see:

**`scripts/maintenance/README_NOTIFICATIONS.md`**

### Quick Commands

```bash
# Detect new filings (runs continuously)
python3 scripts/maintenance/detect_new_filings.py

# Detect once and exit (for cron jobs)
python3 scripts/maintenance/detect_new_filings.py --once

# Test-all mode: catch ANY new filing (for testing)
python3 scripts/maintenance/detect_new_filings.py --test-all your@email.com --dry-run --once

# Send pending email notifications
python3 scripts/maintenance/send_notifications.py
```

### Key Features (December 2025)

- **Test-All Mode:** Catch any early filer (Jan 5-11) without following specific candidates
- **Per-Filing Amounts:** Shows specific filing data, not cumulative cycle totals
- **Consistent Office Display:** Properly formats House/Senate/President with district
- **Candidate Resolution:** Looks up candidate info when FEC API returns null candidate_id

---

## 📚 Additional Resources

- **FEC API Documentation:** https://api.open.fec.gov/developers/
- **Supabase Documentation:** https://supabase.com/docs
- **Project Documentation:** See `/docs` directory

---

## 🚨 Important Notes

1. **API Key:** Keep your FEC API key secure - never commit to git
2. **Rate Limiting:** Always respect FEC rate limits (7,000 calls/hour as of Dec 2025)
3. **Progress File:** Don't delete `collection_progress.json` during active collection
4. **Database:** Ensure unique constraint exists on `quarterly_financials` table
5. **Monitoring:** For long-running collections, use background mode with logging

---

## 🎯 Quick Start

1. Set up environment variables in `.env`
2. Run for the cycle you want: `python3 scripts/collect_fec_cycle_data.py --cycle 2024`
3. Monitor progress: `tail -f collection_2024.log` (if using background mode)
4. Wait for completion (~5-8 hours depending on cycle)
5. Verify data in Supabase

That's it! The script handles everything else automatically.

---

**Last Updated:** December 15, 2025
**Script Version:** 1.1
**Python Required:** 3.7+
