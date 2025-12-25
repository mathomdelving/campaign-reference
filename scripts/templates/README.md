# Data Collection Script Templates

This directory contains **template scripts** that are known to work correctly. These should be used as starting points when collecting data for historical cycles.

## ⚠️ DO NOT MODIFY TEMPLATES DIRECTLY

Templates in this directory should remain unchanged. When you need to collect data for a specific cycle, **copy** the template to `scripts/data-collection/` and modify the copy.

---

## Available Templates

### `fetch_historical_cycle_TEMPLATE.py`

**Purpose**: Collect FEC data for any historical election cycle (2022, 2020, 2018, etc.)

**Features**:
- ✅ Fetches all candidates for a specific cycle
- ✅ Gets financial summary data from `/candidate/{id}/totals/`
- ✅ Gets quarterly filings from principal committees
- ✅ Uses committee history to handle committee designation changes
- ✅ Deduplicates amendments correctly
- ✅ Handles rate limits with exponential backoff
- ✅ Saves progress and can resume from interruptions

**Known Issues Fixed**:
- ✅ Python default parameter bug (see comments in script)
- ✅ All function calls explicitly pass `cycle` parameter
- ✅ Extensive documentation to prevent future issues

---

## How to Use for a New Cycle

### Example: Collecting 2020 Data

1. **Copy the template**:
   ```bash
   cp scripts/templates/fetch_historical_cycle_TEMPLATE.py scripts/data-collection/fetch_2020.py
   ```

2. **Test with dry run** (processes first 50 candidates only):
   ```bash
   cd /Users/benjaminnelson/Desktop/campaign-reference
   python3 scripts/data-collection/fetch_2020.py --cycle 2020 --dry-run
   ```

3. **Verify the output**:
   - Check that candidates are from the correct cycle
   - Verify that `last_report_year` matches expectations
   - Confirm quarterly data is being collected (should show "✓ (X filings)")

4. **Run full collection** (takes ~20-30 hours):
   ```bash
   nohup python3 scripts/data-collection/fetch_2020.py --cycle 2020 > collection_2020.log 2>&1 &
   ```

5. **Monitor progress**:
   ```bash
   # Check log
   tail -f collection_2020.log

   # Check progress file
   cat progress_2020_simple.json | python3 -m json.tool | head -20

   # Check if still running
   ps aux | grep fetch_2020
   ```

6. **After completion**, you'll have:
   - `candidates_2020.json` - All candidate metadata
   - `financials_2020.json` - Summary financial data
   - `quarterly_financials_2020.json` - Detailed quarterly filings

---

## Critical Reminders

### 1. **Python Default Parameter Gotcha**
The template includes extensive comments about this issue. TL;DR:
- ❌ **BAD**: `fetch_candidate_financials(candidate_id)`
- ✅ **GOOD**: `fetch_candidate_financials(candidate_id, CYCLE)`

Always pass `CYCLE` explicitly to all functions.

### 2. **Rate Limits**
- FEC API allows ~1,000 requests/hour
- Script uses 4-second delays between calls
- Each candidate requires 3+ API calls
- Expect ~20-30 hours for a full cycle (~6,700 candidates)

### 3. **Resumability**
If the script crashes or is interrupted:
- Progress is saved every 50 candidates to `progress_{cycle}_simple.json`
- Simply restart the same command - it will resume from where it left off
- Do NOT delete the progress file until collection is complete

### 4. **Data Validation**
After collection completes:
```bash
# Check how many candidates have 2020 data
python3 << 'EOF'
import json
data = json.load(open('financials_2020.json'))
correct_year = [f for f in data if f.get('last_report_year') == 2020]
print(f"Records with 2020 data: {len(correct_year)}/{len(data)}")
EOF

# Check quarterly data collected
wc -l quarterly_financials_2020.json
```

---

## Template Maintenance

When **critical bugs** are found and fixed in the template:

1. **Document the fix** in this README
2. **Update the template** with the fix
3. **Add comments** explaining the issue and solution
4. **Update version notes** below

### Version History

**v1.0** (November 13, 2025)
- Initial template created
- Fixed Python default parameter bug (cycle=CYCLE)
- Added comprehensive documentation
- All function calls explicitly pass cycle parameter
- Added warnings at module, function, and call-site levels

---

## Questions?

If you encounter issues:
1. Check the comments in the template script (extensive documentation)
2. Review this README
3. Look at successful past cycles (e.g., `scripts/data-collection/fetch_2024_simple.py`)
4. Check `FIXES_APPLIED.md` and other documentation in the project root
