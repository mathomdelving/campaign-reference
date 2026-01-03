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
cd /Users/benjaminnelson/Desktop/campaign-reference
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
python3 scripts/data-loading/load_cycle_to_supabase.py --cycle <YEAR>

# Options:
#   --dry-run        Preview without writing
#   --quarterly-only Load only quarterly data (skip candidates/financial_summary)
#   --skip-quarterly Load candidates + financial_summary only
```

**Tables Updated:**
- `candidates` (upsert by candidate_id)
- `financial_summary` (upsert by candidate_id, cycle, coverage_end_date)
- `candidate_financials` (upsert by candidate_id, cycle, coverage_end_date)

---

## Historical Backfill (2018, 2020, etc.)

To backfill data for older cycles:

```bash
# Step 1: Collect (5-8 hours per cycle, run in background)
nohup python3 -u scripts/collect_cycle_data.py --cycle 2020 --max-retries 3 > collection_2020.log 2>&1 &
nohup python3 -u scripts/collect_cycle_data.py --cycle 2018 --max-retries 3 > collection_2018.log 2>&1 &

# Monitor progress
tail -f collection_2020.log

# Step 2: Review JSON files when complete
ls -lh *_2020.json *_2018.json

# Step 3: Load to Supabase (do one cycle at a time)
python3 scripts/data-loading/load_cycle_to_supabase.py --cycle 2020
python3 scripts/data-loading/load_cycle_to_supabase.py --cycle 2018
```

**Current Coverage:**

| Cycle | financial_summary | candidate_financials |
|-------|-------------------|---------------------|
| 2026  | ✓ 3,157           | ✓ 6,621             |
| 2024  | ✓ 3,568           | ✓ 23,459            |
| 2022  | ✓ 3,412           | ✓ 23,094            |
| 2020  | ✓ 1,642           | ✗ 0 (needs backfill)|
| 2018  | ✓ 2,465           | ✗ 0 (needs backfill)|

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
| Loading script (any cycle) | `scripts/data-loading/load_cycle_to_supabase.py` |
| Incremental update | `scripts/data-loading/incremental_update.py` |
| Quarterly update | `scripts/data-loading/update_quarterly_financials.py` |
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

---

## Database Architecture - CRITICAL

### Entity Relationship Diagram

```
political_persons (1) ←──── (many) candidates (1) ←──── (many) committee_designations
       │                           │                              │
       │                           │                              │
       │ person_id                 │ candidate_id                 │ committee_id
       │                           │                              │
       ▼                           ▼                              ▼
  Display names             financial_summary              candidate_financials
  across cycles             (cumulative totals)            (period breakdowns)
                                   │
                                   ▼
                            leaderboard_data (VIEW)
```

### Core Tables

| Table | Purpose | Primary Key | Updated By |
|-------|---------|-------------|------------|
| `political_persons` | Deduplicated person identities across election cycles | `person_id` | Manual/bulk scripts |
| `candidates` | Candidate info for a specific cycle | `candidate_id` | `incremental_update.py` |
| `committee_designations` | Maps committee_id → candidate_id | `committee_id, candidate_id` | Bulk collection |
| `financial_summary` | **Cumulative YTD totals** for leaderboard | `candidate_id, cycle, coverage_end_date` | `incremental_update.py` |
| `candidate_financials` | **Period breakdowns** for charts | `candidate_id, cycle, coverage_end_date` | `update_quarterly_financials.py` |

### Views

| View | Purpose | Source Tables |
|------|---------|---------------|
| `leaderboard_data` | Pre-joined data for leaderboard pages | `financial_summary` + `candidates` + `political_persons` |

### The Two Financial Tables - DO NOT MERGE

| Aspect | financial_summary | candidate_financials |
|--------|------------------|---------------------|
| **Purpose** | Leaderboard rankings | Quarterly charts |
| **Amount type** | Cumulative YTD | Period-only |
| **FEC endpoint** | `/candidate/{id}/totals/` | `/reports/house-senate/` |
| **Sum behavior** | Latest record = total | SUM all records = total |
| **Example** | "$5M raised this cycle" | "$500K raised in Q3" |

**WARNING:**
- If you SUM `financial_summary`, you get wrong totals (double/triple counting)
- If you take MAX of `candidate_financials`, you get wrong totals (just one quarter)

### Common Joins

```sql
-- Get candidate with their display name and financials
SELECT
    pp.display_name,
    c.party,
    c.state,
    c.district,
    fs.total_receipts,
    fs.cash_on_hand
FROM candidates c
JOIN political_persons pp ON c.person_id = pp.person_id
JOIN financial_summary fs ON c.candidate_id = fs.candidate_id
WHERE fs.cycle = 2026;

-- Get quarterly breakdown for a candidate
SELECT
    c.name,
    cf.report_type,
    cf.coverage_end_date,
    cf.total_receipts
FROM candidates c
JOIN candidate_financials cf ON c.candidate_id = cf.candidate_id
WHERE c.candidate_id = 'H6TX22126'
ORDER BY cf.coverage_end_date;

-- Look up candidate from committee
SELECT c.*
FROM committee_designations cd
JOIN candidates c ON cd.candidate_id = c.candidate_id
WHERE cd.committee_id = 'C00123456';
```

### Notification System Tables

| Table | Purpose |
|-------|---------|
| `user_candidate_follows` | Which candidates a user follows (has `notification_enabled` flag) |
| `notification_queue` | Pending/sent/failed email notifications |
| `data_refresh_log` | Tracks when data was last updated |

### Update Pipeline (GitHub Actions)

The `incremental-update.yml` workflow runs these in order:

1. `incremental_update.py` → updates `candidates` + `financial_summary`
2. `update_quarterly_financials.py` → updates `candidate_financials`
3. `detect_new_filings.py` → creates entries in `notification_queue`
4. `send_notifications.py` → sends emails, updates queue status
