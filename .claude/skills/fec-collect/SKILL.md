---
name: fec-collect
description: Collect FEC campaign finance data using the 2-step workflow. Use when the user asks to collect FEC data, download campaign finance data, fetch candidate financials, run data collection, or populate the database with FEC records. CRITICAL - enforces the mandatory 2-step workflow (JSON first, then Supabase).
allowed-tools: Bash, Read, Write, Grep, Glob
---

# FEC Data Collection Skill

## THE GOLDEN RULE

**NEVER upload data directly to Supabase. ALWAYS use the 2-step workflow:**

1. **Collect → JSON files** (review before upload)
2. **JSON files → Supabase** (after human review)

This is NOT optional. This rule exists because of a real incident (November 18-19, 2025) where direct uploads caused data integrity failures.

---

## Quick Reference

### Step 1: Collect Data to JSON

```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
python3 scripts/collect_cycle_data.py --cycle <YEAR> --max-retries 3
```

**Available cycles:** 2026 (current), 2024, 2022, 2020, 2018, 2016, 2014, 2012...

**Output files created:**
- `candidates_{cycle}.json` - All House & Senate candidates
- `financials_{cycle}.json` - Financial summaries
- `quarterly_financials_{cycle}.json` - All quarterly/monthly/election reports
- `failures_{cycle}.json` - Any persistent failures (if errors remain)
- `no_data_{cycle}.json` - Candidates with no financial activity

### Step 2: Review JSON Files

```bash
# Check file sizes
ls -lh *_{cycle}.json

# Preview data structure
head -20 candidates_{cycle}.json

# Count records
python3 -c "import json; print(f'{len(json.load(open(\"candidates_{cycle}.json\")))} candidates')"
python3 -c "import json; print(f'{len(json.load(open(\"quarterly_financials_{cycle}.json\")))} filings')"
```

### Step 3: Load to Supabase

```bash
python3 scripts/data-loading/load_to_supabase.py
```

---

## Running in Background (Recommended for Large Collections)

Collections take 5-8 hours for large cycles. Run in background:

```bash
# Start collection in background
nohup python3 -u scripts/collect_cycle_data.py --cycle 2024 --max-retries 3 > collection_2024.log 2>&1 &

# Monitor progress
tail -f collection_2024.log

# Check if still running
ps aux | grep collect_cycle_data
```

---

## Expected Duration

| Cycle | Candidates | Time Estimate |
|-------|-----------|---------------|
| 2026  | ~2,500    | 5-6 hours     |
| 2024  | ~5,000    | 6-8 hours     |
| 2022  | ~4,500    | 6-8 hours     |
| 2020  | ~1,200    | 3-4 hours     |

---

## Environment Requirements

Required in `.env` or `.env.local`:
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key
```

---

## Built-in Safety Features

The collection script automatically:
- Retries on rate limit errors (429) with exponential backoff
- Handles network timeouts gracefully
- Saves progress every 25 candidates
- Resumes from where it left off if interrupted
- Skips already-collected candidates
- Tracks failures separately from "no data" cases

---

## Troubleshooting

### "Missing environment variables"
Create `.env` file with FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY

### Script keeps getting rate limited
- Script handles this automatically with backoff
- Check if others are using your API key
- Run during off-peak hours (late night EST)

### Want to stop collection
Press Ctrl+C - progress is saved automatically. Resume by running again.

### Want to re-collect a cycle
Delete the progress file and run again:
```bash
rm progress_{cycle}_robust.json
python3 scripts/collect_cycle_data.py --cycle {cycle}
```

---

## Verification Queries

After loading to Supabase, verify the data:

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

## File Locations

| Purpose | Location |
|---------|----------|
| Collection script | `scripts/collect_cycle_data.py` |
| Loading script | `scripts/data-loading/load_to_supabase.py` |
| Progress tracking | `progress_{cycle}_robust.json` |
| Output JSON files | Project root (`*.json`) |

---

## WHAT NOT TO DO

**NEVER use archived scripts that upload directly:**
- `archive/collect_fec_cycle_data_BROKEN_UPLOADS_DIRECTLY.py` - DO NOT USE

**NEVER skip the JSON review step** - this is your safety net for catching bad data before it reaches production.

---

## Data Integrity Rule

All committees MUST map to a candidate:
- If a candidate does not exist, create it BEFORE loading committee data
- This ensures proper query flow: `political_person → candidates → quarterly_financials → committees`
