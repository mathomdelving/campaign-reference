# FEC Bulk Import - Quick Start

## 30-Second Version

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download files from https://www.fec.gov/data/browse-data/?tab=bulk-data
#    - cn26.zip (Candidates)
#    - weball26.zip (Financials)

# 3. Extract
mkdir fec_bulk_data
unzip cn26.zip -d fec_bulk_data/
unzip weball26.zip -d fec_bulk_data/

# 4. Update paths in bulk_import_fec.py (lines 285-290)

# 5. Run
python bulk_import_fec.py
```

---

## What Gets Imported

| FEC File | Size | Your Table | Records | What It Contains |
|----------|------|------------|---------|------------------|
| `cn26.zip` | ~50 MB | `candidates` | ~5,000 | Candidate names, parties, states, districts |
| `weball26.zip` | ~30 MB | `financial_summary` | ~2,900 | Total raised, spent, cash on hand |

**Note:** Quarterly breakdowns (`quarterly_financials`) require using your existing API script.

---

## Configuration (bulk_import_fec.py)

```python
# Line 285: Set your cycle
CYCLE = 2026  # Change to 2024, 2022, etc.

# Lines 290-294: Point to your files
CANDIDATE_MASTER_FILE = 'fec_bulk_data/cn.txt'
WEBALLCANDS_FILE = 'fec_bulk_data/weball.txt'
```

---

## Expected Output

```
================================================================================
FEC BULK DATA IMPORT
================================================================================

--- Processing Candidate Master File ---
Loaded 8,432 raw candidate records
Filtered to 5,185 candidates for 2026 (House/Senate only)
✓ Candidates: 5185/5185 inserted

--- Processing All Candidates Summary File ---
Loaded 5,432 raw financial records
Filtered to 2,880 records with financial data
✓ Financials: 2880/2880 inserted

Total records inserted: 8,065
Duration: 45 seconds
Status: success
```

---

## Common File Names by Cycle

| Cycle | Candidate File | Financial File |
|-------|----------------|----------------|
| 2026 | `cn26.zip` → `cn.txt` | `weball26.zip` → `weball.txt` |
| 2024 | `cn24.zip` → `cn.txt` | `weball24.zip` → `weball.txt` |
| 2022 | `cn22.zip` → `cn.txt` | `weball22.zip` → `weball.txt` |
| 2020 | `cn20.zip` → `cn.txt` | `weball20.zip` → `weball.txt` |

---

## Validation Queries

```sql
-- Check what got imported
SELECT cycle, office, COUNT(*)
FROM candidates
GROUP BY cycle, office;

-- Check financial totals
SELECT cycle,
       COUNT(*) as candidates,
       SUM(total_receipts) as total_raised,
       SUM(cash_on_hand) as total_cash
FROM financial_summary
GROUP BY cycle;

-- View recent import logs
SELECT * FROM data_refresh_log
ORDER BY refreshed_at DESC
LIMIT 5;
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "File not found" | Check paths match extracted filenames (`cn.txt` vs `cn26.txt`) |
| "ModuleNotFoundError: pandas" | Run `pip install -r requirements.txt` |
| "Fewer records than expected" | Normal - script filters to H/S offices and records with financial data |
| Need quarterly data | Use existing `fetch_fec_data.py` + `load_to_supabase.py` |

---

## Next Steps

1. Import completes → Verify with SQL queries above
2. Test frontend (http://localhost:5173)
3. For quarterly trends, run: `python fetch_fec_data.py`
4. Schedule daily updates via GitHub Actions (already configured)

---

**Full Documentation:** See `BULK_IMPORT_GUIDE.md`
