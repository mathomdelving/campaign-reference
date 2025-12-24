# FEC Data Collection Guide

Quick reference for collecting FEC campaign finance data.

---

## ⚠️ CRITICAL: READ FIRST

**Before collecting ANY data, you MUST read:**

**`docs/DATA_COLLECTION_WORKFLOW.md`**

**THE GOLDEN RULE: Use the 2-step workflow. NEVER upload directly to Supabase.**

---

## 🚀 Quick Start (CANONICAL SCRIPT)

**Step 1: Collect data → JSON files**

```bash
# Use the canonical robust collection script
python3 scripts/collect_cycle_data.py --cycle 2024 --max-retries 3
```

**Step 2: Review JSON files, then load to Supabase**

```bash
# Review first!
ls -lh *_2024.json
head -20 candidates_2024.json
python3 -c "import json; print(f'{len(json.load(open(\"quarterly_financials_2024.json\")))} filings')"

# Then upload
python3 scripts/data-loading/load_to_supabase.py
```

That's it! Always use this 2-step workflow.

---

## 📖 Common Use Cases

### Collect Data (Step 1)
```bash
# Collect and save to JSON (specify the cycle)
python3 scripts/collect_cycle_data.py --cycle 2024 --max-retries 3

# For historical data (e.g., 2022)
python3 scripts/collect_cycle_data.py --cycle 2022 --max-retries 3
```

**What this creates:**
- `candidates_{cycle}.json` - All House & Senate candidates
- `financials_{cycle}.json` - Financial summaries
- `quarterly_financials_{cycle}.json` - ALL report types (quarterly + pre/post election)
- `failures_{cycle}.json` - Any persistent failures (if any)
- `no_data_{cycle}.json` - Candidates with no financial activity

**Features:**
- ✅ Automatic retry with exponential backoff
- ✅ Historical committee designations (correct for the target cycle)
- ✅ Collects ALL report types (not just quarterly)
- ✅ Resume capability if interrupted
- ✅ Progress saved every 50 candidates

### Review JSON Files
```bash
# Check file sizes
ls -lh *.json

# Preview data
head -20 candidates_2026.json

# Count records
python3 -c "import json; print(f'{len(json.load(open(\"candidates_2026.json\")))} candidates')"
```

### Upload to Supabase (Step 2)
```bash
# After reviewing JSON files
python3 scripts/data-loading/load_to_supabase.py
```

### Run in Background
```bash
# Step 1: Collection (for long-running historical data)
nohup python3 -u scripts/collect_cycle_data.py --cycle 2022 --max-retries 3 > collection_2022.log 2>&1 &

# Monitor progress
tail -f collection_2022.log

# Check if still running
ps aux | grep collect_cycle_data

# Step 2: After completion, review JSON and upload
python3 scripts/data-loading/load_to_supabase.py
```

---

## 🎯 Available Cycles

You can collect data for any federal election cycle:

**Recent Cycles:**
- 2026 (current)
- 2024 (presidential)
- 2022 (midterm)
- 2020 (presidential)
- 2018 (midterm)

**Historical Cycles:**
- 2016, 2014, 2012, 2010, 2008, 2006, 2004, 2002, 2000...

---

## ⏱️ How Long Will It Take?

| Cycle | Candidates | Time Estimate |
|-------|-----------|---------------|
| Large (2024) | ~5,000 | 6-8 hours |
| Medium (2022) | ~4,500 | 6-8 hours |
| Small (2020) | ~1,200 | 3-4 hours |

**Why so long?**
- FEC API rate limit: 7,000 calls per hour (upgraded Dec 2025)
- Script makes ~900 calls per hour (conservative, with safety margins)
- Each candidate requires 2-5 API calls
- Could be faster by reducing delays if needed

---

## ✅ What Gets Collected

### Candidate Data
- Name, party, state, district
- Office (House/Senate)
- Incumbent/challenger status

### Financial Data
- All quarterly reports (Q1, Q2, Q3, Q4)
- All monthly reports
- Pre-election and post-election reports
- Special reports
- Amounts: Receipts, disbursements, cash on hand
- Per-period (not cumulative)

---

## 🛡️ Built-in Safety Features

The script automatically:
- ✅ Retries on rate limit errors (429)
- ✅ Handles network timeouts
- ✅ Saves progress every 25 candidates
- ✅ Resumes if interrupted
- ✅ Skips already-collected data
- ✅ Prevents duplicates (database constraint)

---

## 🎛️ Advanced Options

### Resume Interrupted Collection
Just run the same command again:
```bash
python3 scripts/collect_fec_cycle_data.py --cycle 2024
```
It automatically skips already-processed candidates.

### Re-collect a Cycle (Force Refresh)
1. Delete the cycle from `collection_progress.json`
2. Run the script again

### Collect Specific Year Ranges
```bash
# Presidential years only
python3 scripts/collect_fec_cycle_data.py --cycle 2024,2020,2016,2012

# Midterm years only
python3 scripts/collect_fec_cycle_data.py --cycle 2022,2018,2014,2010

# Recent 10 years
python3 scripts/collect_fec_cycle_data.py --cycle 2024,2022,2020,2018,2016,2014
```

---

## 📊 Verify Collection

After collection completes, verify the data:

```sql
-- Check what cycles you have
SELECT cycle, COUNT(*) as filings, COUNT(DISTINCT candidate_id) as candidates
FROM quarterly_financials
GROUP BY cycle
ORDER BY cycle DESC;

-- Check top fundraisers for a cycle
SELECT candidate_id, name, office, SUM(total_receipts)::BIGINT as total_raised
FROM quarterly_financials
WHERE cycle = 2024
GROUP BY candidate_id, name, office
ORDER BY total_raised DESC
LIMIT 10;
```

---

## 🔧 Troubleshooting

### "Missing environment variables"
**Solution:** Create `.env` file:
```env
FEC_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key_here
```

### Script keeps getting rate limited
**Solution:** Script handles this automatically. If persistent:
- Check if others are using your API key
- Run during off-peak hours (night EST)

### Want to stop collection
**Solution:** Press Ctrl+C. Progress is saved automatically. Resume by running again.

---

## 📁 File Locations

- **Main script:** `scripts/collect_fec_cycle_data.py`
- **Documentation:** `scripts/README.md`
- **Progress tracking:** `collection_progress.json` (created automatically)
- **Logs:** `collection_YYYY.log` (if using background mode)

---

## 💡 Pro Tips

1. **Use background mode** for collections over 2 hours
2. **Monitor with tail -f** to watch progress
3. **Check progress.json** to see how many candidates are left
4. **Run during off-peak hours** for fewer rate limit issues
5. **Collect multiple cycles overnight** for efficiency

---

## 🎓 Example Workflow

```bash
# 1. Collect 2024 data in background
nohup python3 -u scripts/collect_fec_cycle_data.py --cycle 2024 > 2024.log 2>&1 &

# 2. Monitor progress
tail -f 2024.log

# 3. Check status in another terminal
python3 -c "import json; p = json.load(open('collection_progress.json')); print(f\"Progress: {p['2024']['candidates_processed']}/{p['2024'].get('total_candidates', '?')} candidates\")"

# 4. When complete, verify in database
psql -c "SELECT COUNT(*) FROM quarterly_financials WHERE cycle = 2024;"
```

---

## 📚 Full Documentation

For complete details, see:
- `scripts/README.md` - Complete script documentation
- `DATA_QUALITY_FIXES_SUMMARY.md` - Data quality information
- `2024_COLLECTION_FIX.md` - Technical details on retry logic

---

**Last Updated:** November 7, 2025
