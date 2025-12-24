# Investigation Scripts Archive

This folder contains scripts that were created during the investigation and debugging phase of the FEC data collection project. These scripts helped us determine the correct field mappings and validation approaches.

## Archived: November 5, 2025

### Key Findings from Investigation

**Critical Discovery:**
- FEC `/reports/` endpoint uses `total_receipts_period` and `total_disbursements_period` (NOT `_ytd`)
- Sum of all `_period` amounts = FEC `/totals/` endpoint (verified with $0.00 difference)
- YTD fields reset at calendar year boundaries (not suitable for 2-year election cycles)

**Final Configuration:**
- Rate limit: 4 seconds between API calls (900 calls/hour, under 1,000 limit)
- Pagination: Fetches ALL candidates across all pages (no 1,000 candidate limit)
- Data structure: Compatible with existing 2026 quarterly_financials table

## Archived Scripts

### Field Mapping Investigation
- `find_correct_calculation.py` - Tested different calculation methods, found correct approach
- `investigate_fec_structure.py` - Systematic analysis of FEC API structure
- `check_database_vs_api.py` - Compared database vs API field mappings
- `check_raw_report_data.py` - Examined raw FEC API report responses

### Verification Scripts
- `final_go_no_go.py` - Final verification before multi-day collection (PASSED ✓)
- `final_verification.py` - Verified data accuracy across test candidates
- `verify_christy_complete_data.py` - Specific verification for Christy Smith 2022
- `verify_data_structure.py` - Confirmed compatibility with 2026 data
- `verify_period_sum.py` - Verified period sums match FEC totals
- `check_stored_test_data.py` - Checked data stored in database
- `check_latest_filings.py` - Examined most recent database entries

### Test Scripts
- `test_four_candidates.py` - Tested collection across 4 cycles
- `test_principal_committee_filter.py` - Investigated committee filtering
- `test_specific_candidates_cash.py` - Tested cash_on_hand retrieval
- `test_backfill_sample.py` - Sample backfill testing
- `verify_test_candidates.py` - Candidate verification script
- `find_christy_committee.py` - Committee discovery debugging

### Backfill Scripts (Deprecated)
- `backfill_cash_complete.py` - Early attempt at backfilling cash (superseded by comprehensive collection)

## Active Scripts (Kept in Root)

- `collect_all_filings_complete.py` - **PRODUCTION SCRIPT** - Comprehensive FEC data collection
- `test_collection_script.py` - Test script for validation before full runs
- `import_fec_bulk_data.py` - Bulk data import utility (if needed)

## Notes

These scripts represent the investigation process that led to the correct implementation. They are preserved for reference but are no longer actively used. The final, correct implementation is in `collect_all_filings_complete.py`.
