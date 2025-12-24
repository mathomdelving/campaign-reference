#!/bin/bash
# Archive investigation and test scripts

# Scripts to keep (actively used or important)
KEEP=(
  "collect_all_filings_complete.py"
  "test_collection_script.py"
  "import_fec_bulk_data.py"
)

# Investigation scripts to archive
ARCHIVE=(
  "backfill_cash_complete.py"
  "check_database_vs_api.py"
  "check_latest_filings.py"
  "check_raw_report_data.py"
  "check_stored_test_data.py"
  "final_go_no_go.py"
  "final_verification.py"
  "find_christy_committee.py"
  "find_correct_calculation.py"
  "investigate_fec_structure.py"
  "test_backfill_sample.py"
  "test_four_candidates.py"
  "test_principal_committee_filter.py"
  "test_specific_candidates_cash.py"
  "verify_christy_complete_data.py"
  "verify_data_structure.py"
  "verify_period_sum.py"
  "verify_test_candidates.py"
)

echo "Moving investigation scripts to archive/investigation_scripts/..."

for script in "${ARCHIVE[@]}"; do
  if [ -f "$script" ]; then
    mv "$script" archive/investigation_scripts/
    echo "  ✓ Archived: $script"
  fi
done

echo ""
echo "Keeping in root directory:"
for script in "${KEEP[@]}"; do
  if [ -f "$script" ]; then
    echo "  ✓ $script"
  fi
done

echo ""
echo "✅ Cleanup complete!"
