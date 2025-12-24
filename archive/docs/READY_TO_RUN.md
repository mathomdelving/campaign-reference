# Political Pole - Ready to Run Overnight Collection! 🏁

**Status:** ✅ Validated and ready to go!
**Time:** October 22, 2025
**Estimated Runtime:** 6-8 hours

---

## ✅ What We've Completed

1. **Updated fetch_fec_data.py** - Now collects both summary AND quarterly filings data
2. **Tested on 3 candidates** - Vindman, Wahls, Miller-Meeks all returned quarterly data successfully!
3. **Created database schema** - New `quarterly_financials` table designed and SQL file ready

### Test Results:
- Vindman: 3 quarterly filings (Q1, Q2, Q3 2025) ✅
- Wahls: 3 quarterly filings ✅
- Miller-Meeks: 10 filings (includes amendments) ✅
- **Total test records:** 16 quarterly filings

---

## 🎯 Next Steps (Tonight Before Sleep)

### Step 1: Create the Quarterly Table in Supabase (2 minutes)

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy and paste the entire contents of `create_quarterly_table.sql` (shown below)
6. Click "Run" (green play button)
7. You should see "Success. No rows returned"

```sql
-- Copy everything from create_quarterly_table.sql:
-- (The full SQL is in the file, or see below)
```

<details>
<summary>Click to expand full SQL</summary>

```sql
CREATE TABLE IF NOT EXISTS quarterly_financials (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),
  cycle INTEGER NOT NULL,
  quarter VARCHAR(10),
  report_year INTEGER,
  report_type VARCHAR(100),
  coverage_start_date DATE,
  coverage_end_date DATE,
  total_receipts DECIMAL(15,2),
  total_disbursements DECIMAL(15,2),
  cash_beginning DECIMAL(15,2),
  cash_ending DECIMAL(15,2),
  filing_id BIGINT,
  is_amendment BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(candidate_id, cycle, coverage_end_date, filing_id)
);

CREATE INDEX IF NOT EXISTS idx_qf_candidate ON quarterly_financials(candidate_id);
CREATE INDEX IF NOT EXISTS idx_qf_cycle ON quarterly_financials(cycle);
CREATE INDEX IF NOT EXISTS idx_qf_quarter ON quarterly_financials(quarter, report_year);
CREATE INDEX IF NOT EXISTS idx_qf_committee ON quarterly_financials(committee_id);
CREATE INDEX IF NOT EXISTS idx_qf_timeseries ON quarterly_financials(candidate_id, cycle, coverage_end_date);
CREATE INDEX IF NOT EXISTS idx_qf_filing ON quarterly_financials(filing_id);

COMMENT ON TABLE quarterly_financials IS 'Individual quarterly FEC filings for timeseries analysis';
```

</details>

### Step 2: Start the Overnight Collection (1 minute)

In your terminal, run:

```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
python3 fetch_fec_data.py
```

**What will happen:**
- Loads existing `candidates_2026.json` (5,185 candidates)
- For each candidate:
  - Fetches summary totals (for backwards compatibility)
  - Fetches quarterly filings (NEW - for timeseries)
- Saves progress every 50 candidates
- Takes 6-8 hours (4 second delay between requests for rate limiting)

**Output files:**
- `financials_2026.json` - Updated summary totals
- `quarterly_financials_2026.json` - NEW quarterly timeseries data
- `progress.json` - Resume capability (if interrupted)

### Step 3: Let it Run Overnight

- Leave your computer on or use `nohup` (see below)
- Check back in the morning
- Progress saves every 50 candidates, so it's safe to interrupt if needed

---

## 🚀 Alternative: Run in Background with nohup

If you want to close your terminal and let it run:

```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
nohup python3 fetch_fec_data.py > fetch_output.log 2>&1 &
```

Then you can:
- Close your terminal
- Check progress anytime with: `tail -f fetch_output.log`
- See if it's still running: `ps aux | grep fetch_fec_data`

---

## 📊 What Happens Tomorrow Morning

When the collection finishes (or when you wake up), we'll:

1. **Load quarterly data to Supabase** (~5 minutes)
   - Run `load_to_supabase.py` (we'll update it tomorrow)
   - Loads quarterly_financials_2026.json to database

2. **Update frontend branding** (~30 minutes)
   - Add Political Pole name and RedBull Racing colors
   - Navy Blue (#121F45), Blue (#223971), Red (#CC1E4A), Yellow (#FFC906)

3. **Build the 4 use-case views** (~4-5 hours)
   - District race comparison
   - Candidate profile with timeseries
   - Multi-candidate comparison
   - Leaderboard with filters

---

## 🎨 Political Pole Branding

### Colors:
- **Navy Blue:** `#121F45` - Primary background, headers
- **Blue:** `#223971` - Secondary backgrounds, borders
- **Red:** `#CC1E4A` - Accents, CTAs, important metrics
- **Yellow:** `#FFC906` - Highlights, warnings, standout data
- **White:** `#FFFFFF` - Text on dark backgrounds, cards

### Party Colors (Keep Standard):
- **Democrats:** `#2563EB` (Blue)
- **Republicans:** `#DC2626` (Red)
- **Independents:** `#7C3AED` (Purple)
- **Others:** `#6B7280` (Gray)

---

## ⚠️ Troubleshooting

### If the script hits rate limits:
- It automatically waits and retries (exponential backoff)
- Progress is saved every 50 candidates
- You can resume by just running the script again

### If you need to stop and resume:
1. Press `Ctrl+C` to stop
2. Check `progress.json` - it has your last position
3. Run `python3 fetch_fec_data.py` again - it will resume

### If something goes wrong:
- Check `progress.json` to see last successful candidate
- Delete `progress.json` to start over from scratch
- The script is idempotent - safe to run multiple times

---

##  Expected Results

After overnight collection, you should have:

**financials_2026.json:**
- ~2,800-3,000 candidate summary records (same as before)
- Cumulative totals for each candidate

**quarterly_financials_2026.json (NEW!):**
- Estimated 6,000-10,000 quarterly filing records
- Each candidate with activity will have 2-5 quarterly filings
- Example breakdown:
  - Q1 2025: ~2,000 candidates filed
  - Q2 2025: ~2,500 candidates filed
  - Q3 2025: ~2,800 candidates filed
  - Q4 2025: (not yet filed, data collection in Oct 2025)

---

## 🎯 Tomorrow's Plan

1. **Morning (8am):** Check if collection finished
2. **Load data to Supabase** (~5 min)
3. **Update load_to_supabase.py** for quarterly data
4. **Build Political Pole UI** with:
   - Navigation bar with logo/branding
   - 4 distinct views (District, Candidate, Comparison, Leaderboard)
   - Quarterly timeseries charts
   - RedBull Racing color scheme throughout

---

## 🏁 Ready to Start!

**Checklist:**
- ✅ `fetch_fec_data.py` updated and tested
- ✅ Test validated on 3 candidates
- ✅ `create_quarterly_table.sql` created
- ⬜ Create quarterly table in Supabase (Step 1 above)
- ⬜ Start overnight collection (Step 2 above)

**Once you complete Steps 1 & 2, you're done for tonight!**

Sleep well, and tomorrow morning we'll have beautiful quarterly timeseries data ready to visualize! 🏎️💨

---

*Generated by Claude Code - October 22, 2025*
