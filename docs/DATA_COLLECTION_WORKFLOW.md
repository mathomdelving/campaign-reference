# ⚠️ CRITICAL: DATA COLLECTION WORKFLOW

**Last Updated:** November 19, 2025
**Status:** MANDATORY READING FOR ALL DATA COLLECTION

---

## 🚨 THE GOLDEN RULE

**NEVER, EVER upload data directly to Supabase without saving to JSON first.**

This is NOT optional. This is NOT a suggestion. This is an ABSOLUTE REQUIREMENT for data integrity.

---

## ✅ CORRECT 2-STEP WORKFLOW

### Step 1: Collection → JSON Files
```bash
# Use the CANONICAL robust collection script
python3 scripts/collect_cycle_data.py --cycle 2024 --max-retries 3
```

**What it creates:**
- `candidates_{cycle}.json` - All candidate metadata
- `financials_{cycle}.json` - Financial summary data
- `quarterly_financials_{cycle}.json` - Quarterly financial reports
- `failures_{cycle}.json` - Any persistent failures (only if errors remain after retries)
- `no_data_{cycle}.json` - Transparency file for candidates with no financial activity

**Why this matters:**
- ✅ Human review before upload
- ✅ Backup of raw data
- ✅ Recovery if upload fails
- ✅ Audit trail
- ✅ Can be re-uploaded if needed
- ✅ Automatic retry of failures with exponential backoff
- ✅ Historical committee designations (not current state)

**CRITICAL DATA INTEGRITY RULE:**
- ✅ **All committees MUST map to a candidate**
- ✅ **If a candidate does not exist, create it BEFORE loading committee data**
- ✅ **This ensures proper query flow:** `political_person → candidates → quarterly_financials → committees`

### Step 2: JSON Files → Supabase
```bash
# After reviewing JSON files, load to database
python3 scripts/data-loading/load_to_supabase.py
```

**What it does:**
- Reads the JSON files you just created
- Uploads to Supabase with proper error handling
- Respects database constraints
- Provides clear success/failure reporting

---

## ❌ WHAT NOT TO DO

### NEVER Use Direct Upload Scripts

The script `collect_fec_cycle_data.py` was archived because it violates the 2-step workflow:

```bash
# ❌ WRONG - DO NOT USE
python3 scripts/collect_fec_cycle_data.py --cycle 2024
```

**Why this is dangerous:**
- No human review before upload
- No backup if something goes wrong
- Uploaded bad data directly to production
- Created committee designation failures (Nov 18-19, 2025 incident)
- Violates data integrity principles

**Location of archived script:**
```
archive/collect_fec_cycle_data_BROKEN_UPLOADS_DIRECTLY.py
```

This script is kept only for historical reference. DO NOT USE IT.

---

## 📋 Why The 2-Step Workflow Exists

### Real Incident (November 18-19, 2025)

An overnight script uploaded data directly to Supabase without saving to JSON first:

**What went wrong:**
1. Script tried to set PostgreSQL generated columns (`is_principal`, `is_authorized`)
2. All 54,300 committee designation inserts failed silently
3. Failures not logged properly
4. Return values not checked
5. Bad data made it to production database

**Impact:**
- Missing candidates in District View (CA-27 2022)
- Frontend couldn't filter by principal committees
- Hours of debugging and data cleanup
- Loss of trust in data collection process

**What saved us:**
- Script failed fast (only 4 bad records uploaded)
- Existing quarterly_financials data was from proper JSON-based uploads
- Damage was minimal because we caught it early

**Lesson learned:**
**IF THE DATA HAD BEEN SAVED TO JSON FIRST, THIS NEVER WOULD HAVE HAPPENED.**

---

## 🎯 Proper Workflow Example

```bash
# 1. Collection (Step 1)
cd /Users/benjaminnelson/Desktop/campaign-reference
python3 scripts/data-collection/fetch_fec_data.py

# 2. Review the JSON files
ls -lh *.json
head -20 candidates_2026.json
head -20 financials_2026.json
head -20 quarterly_financials_2026.json

# 3. Verify data looks correct
python3 -c "import json; print(f'{len(json.load(open(\"candidates_2026.json\")))} candidates')"

# 4. Load to Supabase (Step 2)
python3 scripts/data-loading/load_to_supabase.py

# 5. Verify in database
# (Check Supabase dashboard or run queries)
```

---

## 📂 File Locations

### Collection Scripts (Step 1 - Save to JSON)
```
scripts/data-collection/
├── fetch_fec_data.py          ← ✅ USE THIS for collection
└── README.md
```

### Loading Scripts (Step 2 - Load JSON to DB)
```
scripts/data-loading/
├── load_to_supabase.py                    ← ✅ USE THIS for upload
├── load_quarterly_data.py                 ← For quarterly data only
└── backfill_committee_designations.py     ← For missing designations
```

### Archived (DO NOT USE)
```
archive/
└── collect_fec_cycle_data_BROKEN_UPLOADS_DIRECTLY.py  ← ❌ NEVER USE
```

---

## 🛡️ Enforcement

To prevent future incidents:

1. **Documentation Updated:** This file, collection-guide.md, and scripts/README.md all emphasize the 2-step workflow
2. **Script Archived:** Direct-upload script moved to `archive/` with clear warning in filename
3. **Code Review Required:** Any new collection scripts must be reviewed for workflow compliance
4. **Testing Required:** All collection scripts must have tests that verify JSON output
5. **This Document:** Must be read before any data collection activity

---

## ✅ Checklist Before Running Collection

Before running ANY data collection script:

- [ ] Does the script save to JSON files first?
- [ ] Have I reviewed the JSON output structure?
- [ ] Am I using scripts from `scripts/data-collection/` (not root)?
- [ ] Will I manually review JSON files before uploading?
- [ ] Am I using `load_to_supabase.py` for the upload step?
- [ ] Have I read this entire document?

If you answered "NO" to ANY of these, STOP and review this document again.

---

## 🆘 If You Accidentally Upload Directly

If you realize you've uploaded data directly to Supabase without saving to JSON first:

1. **STOP THE SCRIPT IMMEDIATELY** (Ctrl+C)
2. **Do NOT continue or resume**
3. **Assess damage:**
   - Check `created_at` timestamps in Supabase
   - Count records uploaded since script started
   - Verify data integrity
4. **Document the incident:**
   - What script was run?
   - When did it start?
   - How many records were uploaded?
   - What data looks wrong?
5. **Recovery options:**
   - Delete bad records if identifiable by timestamp
   - Re-run proper 2-step workflow
   - UPSERT with correct data if possible

---

## 📚 Additional Reading

- **Collection Guide:** `docs/guides/collection-guide.md`
- **Scripts README:** `scripts/README.md`
- **Database Schema:** `docs/data/database-schema.md`
- **Incident Report:** `docs/history/data-integrity-2025-11-19.md` (if created)

---

## 🎓 Summary

**THE RULE:**
1. Collect → JSON
2. Review JSON
3. Load JSON → Supabase

**NEVER skip step 2 (review).**
**NEVER go directly from collection to Supabase.**
**ALWAYS save to JSON first.**

This workflow exists for a reason. Follow it.

---

**Questions?** Review this document again. It's all here.

**Still have questions?** Review the incident from November 18-19, 2025. That's why this document exists.
