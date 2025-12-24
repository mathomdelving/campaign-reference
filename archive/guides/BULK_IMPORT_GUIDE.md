# FEC Bulk Data Import Guide

This guide walks you through importing historical FEC data using bulk CSV files instead of API calls.

## Why Use Bulk Import?

✅ **Much faster** - No API rate limits
✅ **Historical data** - Access data back to 1980
✅ **Complete datasets** - Get all records at once
✅ **Cost effective** - Free downloads from FEC

---

## Quick Start (5 Steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This adds `pandas` to your existing dependencies.

### 2. Download FEC Bulk Data Files

Visit: **https://www.fec.gov/data/browse-data/?tab=bulk-data**

Download these files for your target cycle (e.g., 2026):

| File | Description | Table |
|------|-------------|-------|
| `cn26.zip` | Candidate Master | → `candidates` |
| `weball26.zip` | All Candidates Summary | → `financial_summary` |

**For historical cycles:**
- 2024: `cn24.zip`, `weball24.zip`
- 2022: `cn22.zip`, `weball22.zip`
- etc. back to 1980

### 3. Extract the ZIP Files

```bash
# Create directory for bulk data
mkdir fec_bulk_data

# Extract files
unzip cn26.zip -d fec_bulk_data/
unzip weball26.zip -d fec_bulk_data/
```

You should now have:
- `fec_bulk_data/cn.txt` (or `cn26.txt`)
- `fec_bulk_data/weball.txt` (or `weball26.txt`)

### 4. Configure the Import Script

Open `bulk_import_fec.py` and update these lines (around line 285):

```python
CYCLE = 2026  # Change to 2024, 2022, etc. for historical data

# Update these paths to match your extracted files
CANDIDATE_MASTER_FILE = 'fec_bulk_data/cn.txt'
WEBALLCANDS_FILE = 'fec_bulk_data/weball.txt'
```

### 5. Run the Import

```bash
python bulk_import_fec.py
```

You'll see output like:
```
================================================================================
FEC BULK DATA IMPORT
================================================================================

--- Processing Candidate Master File ---
File: fec_bulk_data/cn.txt
Loaded 8,432 raw candidate records
Filtered to 5,185 candidates for 2026 (House/Senate only)
Transformed 5,185 candidate records

Upserted batch 1: 1000/5185 records
Upserted batch 2: 2000/5185 records
...

✓ Candidates: 5185/5185 inserted

--- Processing All Candidates Summary File ---
...
✓ Financials: 2880/2880 inserted

================================================================================
IMPORT COMPLETE
================================================================================
Total records inserted: 8065
Duration: 45 seconds
Status: success
```

---

## Advanced Usage

### Import Multiple Cycles at Once

Edit `bulk_import_fec.py` to loop through multiple cycles:

```python
# In main() function, replace CYCLE = 2026 with:
for CYCLE in [2020, 2022, 2024, 2026]:
    print(f"\n\nImporting cycle {CYCLE}...")
    CANDIDATE_MASTER_FILE = f'fec_bulk_data/cn{str(CYCLE)[2:]}.txt'
    WEBALLCANDS_FILE = f'fec_bulk_data/weball{str(CYCLE)[2:]}.txt'

    # ... rest of import logic
```

### Import Only Candidates (No Financials)

Comment out the financial import section:

```python
# # Import Financial Summaries
# if os.path.exists(WEBALLCANDS_FILE):
#     ...
```

### Import Only Specific States

Add filtering in `transform_candidate_master()`:

```python
# After line 170, add:
df = df[df['CAND_OFFICE_ST'].isin(['VA', 'NC', 'GA'])]  # Virginia, NC, Georgia only
```

---

## Understanding the Data Files

### Candidate Master File (`cn.txt`)

**File Format:** Pipe-delimited (|)
**Encoding:** Latin-1
**Size:** ~50 MB (uncompressed)

**Key Columns:**
- `CAND_ID` - Unique candidate ID (e.g., "H6VA07124")
- `CAND_NAME` - Full name (Last, First)
- `CAND_PTY_AFFILIATION` - Party code (DEM, REP, IND)
- `CAND_OFFICE` - Office (H=House, S=Senate, P=President)
- `CAND_OFFICE_ST` - State (2-letter)
- `CAND_OFFICE_DISTRICT` - District number (for House)

**Example Row:**
```
H6VA07124|VINDMAN, EUGENE|DEM|2026|VA|H|07|C|C|C00844415|...
```

### All Candidates Summary (`weball.txt`)

**File Format:** Pipe-delimited (|)
**Encoding:** Latin-1
**Size:** ~30 MB (uncompressed)

**Key Columns:**
- `CAND_ID` - Matches candidate master
- `TTL_RECEIPTS` - Total money raised (cumulative)
- `TTL_DISB` - Total money spent (cumulative)
- `COH_COP` - Cash on hand (end of period)
- `CVG_END_DT` - Coverage end date (MM/DD/YYYY)

**Example Row:**
```
H6VA07124|VINDMAN, EUGENE|C|DEM|DEMOCRATIC PARTY|8265432.18|0.00|5123456.78|...
```

---

## How the Script Works

### 1. Data Transformation

The script automatically handles:

✅ **Party code mapping** - Converts "DEM" → "DEMOCRATIC PARTY"
✅ **District padding** - Converts "7" → "07" for consistency
✅ **Date parsing** - Handles MM/DD/YYYY and YYYYMMDD formats
✅ **Null handling** - Converts empty strings to proper NULL values
✅ **Type conversion** - Ensures numeric fields are proper floats

### 2. Batch Upserts

- Processes 1,000 records per batch
- Uses `on_conflict` to update existing records
- Logs all operations to `data_refresh_log` table

### 3. Deduplication

**Candidates:** Deduplicated by `candidate_id`
**Financials:** Deduplicated by `(candidate_id, cycle, coverage_end_date)`

---

## Quarterly Data (Advanced)

⚠️ **Note:** The `quarterly_financials` table requires per-quarter breakdowns, which are **not available in the summary files**.

**Two options:**

### Option A: Use Your Existing API Script

Your `fetch_fec_data.py` already fetches quarterly data via the API:

```bash
# After bulk importing candidates/financials, fetch quarterly data
python fetch_fec_data.py  # Fetches quarterly filings for all candidates
python load_to_supabase.py  # Loads quarterly_financials.json
```

### Option B: Process Individual Filing Data (Advanced)

Download committee-level filing data:
- `cm26.zip` - Committee master
- Committee filing records (more complex parsing)

This requires additional transformation logic (contact for implementation).

---

## Troubleshooting

### Error: "File not found"

**Problem:** Script can't find the CSV files

**Solution:**
```bash
# Check your file paths
ls -la fec_bulk_data/

# Update paths in bulk_import_fec.py to match actual filenames
# Some FEC files are named cn.txt, others cn26.txt
```

### Error: "UnicodeDecodeError"

**Problem:** File encoding issue

**Solution:** The script uses `encoding='latin1'` which should work. If it doesn't:
```python
# Try utf-8 instead (line 177, 248)
df = pd.read_csv(csv_path, delimiter='|', encoding='utf-8')
```

### Error: "Invalid date format"

**Problem:** FEC date formats vary by year

**Solution:** Check the date format in your file:
```bash
# View a sample row
head -5 fec_bulk_data/weball.txt
```

Then update the date parsing logic (line 257-268).

### Warning: "Fewer records than expected"

**Cause:** Filtering removed records

**Check:**
- Filter by cycle year (line 170)
- Filter by office type (H/S only, line 171)
- Filter for financial data existence (line 245)

This is **normal** - not all candidates have filed financial reports yet.

---

## Data Validation

After import, verify data quality:

### Check Record Counts

```sql
-- Candidates by cycle
SELECT cycle, office, COUNT(*)
FROM candidates
WHERE cycle = 2026
GROUP BY cycle, office;

-- Financials by cycle
SELECT cycle, COUNT(*),
       SUM(total_receipts),
       SUM(total_disbursements)
FROM financial_summary
WHERE cycle = 2026
GROUP BY cycle;
```

### Check for Missing Data

```sql
-- Candidates without financials
SELECT c.candidate_id, c.name, c.state, c.district
FROM candidates c
LEFT JOIN financial_summary f ON c.candidate_id = f.candidate_id AND c.cycle = f.cycle
WHERE c.cycle = 2026 AND f.candidate_id IS NULL;
```

### Verify Data Freshness

```sql
-- Check when data was last updated
SELECT * FROM data_refresh_log
ORDER BY refreshed_at DESC
LIMIT 5;
```

---

## Performance Tips

### Large Imports (Multiple Cycles)

- Import one cycle at a time
- Use `batch_size=500` for slower connections
- Run during off-peak hours

### Memory Usage

The script loads entire files into memory via pandas. For very large files:

```python
# Process in chunks (add to transform functions)
chunk_size = 10000
for chunk in pd.read_csv(csv_path, delimiter='|', chunksize=chunk_size):
    # Process chunk
    ...
```

---

## Next Steps

After bulk import:

1. ✅ Verify data with SQL queries above
2. ✅ Test frontend to ensure data displays correctly
3. ✅ Set up daily API updates (your existing `fetch_fec_data.py`)
4. ✅ Consider scheduling quarterly bulk refreshes

---

## Support & Resources

- **FEC Bulk Data:** https://www.fec.gov/data/browse-data/?tab=bulk-data
- **FEC Data Dictionaries:** https://www.fec.gov/campaign-finance-data/data-dictionaries/
- **File Descriptions:** https://www.fec.gov/campaign-finance-data/
- **API Documentation:** https://api.open.fec.gov/developers/

---

**Questions?** Check the existing docs in `/docs/` or review the inline comments in `bulk_import_fec.py`.
