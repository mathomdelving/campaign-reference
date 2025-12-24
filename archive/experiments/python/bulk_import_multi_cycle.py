"""
Multi-Cycle Bulk Import for FEC Data
=====================================

This script imports multiple election cycles at once by extracting and processing
FEC bulk data files sequentially.

USAGE:
    python bulk_import_multi_cycle.py

"""

import os
import zipfile
from datetime import datetime
from bulk_import_fec import (
    transform_candidate_master,
    transform_weballcands,
    insert_batch,
    log_refresh,
    SUPABASE_URL,
    SUPABASE_KEY
)

# Cycles to import
CYCLES = [2024, 2022, 2020, 2018]

def extract_cycle_files(cycle, data_dir='fec_bulk_data'):
    """Extract files for a specific cycle and return file paths."""
    print(f"\n{'='*80}")
    print(f"Extracting files for {cycle} cycle")
    print('='*80)

    # File names
    cn_zip = f'{data_dir}/cn{str(cycle)[2:]}.zip'
    weball_zip = f'{data_dir}/weball{str(cycle)[2:]}.zip'

    # Extract to cycle-specific filenames
    cn_txt = f'{data_dir}/cn_{cycle}.txt'
    weball_txt = f'{data_dir}/weball_{cycle}.txt'

    # Extract candidate master
    if os.path.exists(cn_zip):
        with zipfile.ZipFile(cn_zip, 'r') as zip_ref:
            # Extract cn.txt and rename to cn_CYCLE.txt
            zip_ref.extract('cn.txt', data_dir)
            extracted = f'{data_dir}/cn.txt'
            if os.path.exists(extracted):
                os.rename(extracted, cn_txt)
                print(f"✓ Extracted {cn_zip} → {cn_txt}")
    else:
        print(f"✗ File not found: {cn_zip}")
        cn_txt = None

    # Extract financial summary
    if os.path.exists(weball_zip):
        with zipfile.ZipFile(weball_zip, 'r') as zip_ref:
            # Extract weball.txt or weballXX.txt
            names = zip_ref.namelist()
            weball_file = [n for n in names if 'weball' in n.lower()][0]
            zip_ref.extract(weball_file, data_dir)
            extracted = f'{data_dir}/{weball_file}'
            if os.path.exists(extracted):
                os.rename(extracted, weball_txt)
                print(f"✓ Extracted {weball_zip} → {weball_txt}")
    else:
        print(f"✗ File not found: {weball_zip}")
        weball_txt = None

    return cn_txt, weball_txt


def import_cycle(cycle):
    """Import data for a single cycle."""
    print(f"\n{'#'*80}")
    print(f"# IMPORTING {cycle} CYCLE")
    print('#'*80)

    start_time = datetime.now()

    # Extract files
    cn_file, weball_file = extract_cycle_files(cycle)

    all_errors = []
    total_inserted = 0

    # Import Candidates
    if cn_file and os.path.exists(cn_file):
        print(f"\n--- Processing Candidates ({cycle}) ---")
        try:
            candidates = transform_candidate_master(cn_file, cycle)
            if candidates:
                candidates_inserted, candidate_errors = insert_batch(
                    'candidates',
                    candidates,
                    on_conflict='candidate_id'
                )
                all_errors.extend(candidate_errors)
                total_inserted += candidates_inserted
                print(f"✓ Candidates: {candidates_inserted}/{len(candidates)} inserted")
            else:
                print("⚠ No candidates to insert")
        except Exception as e:
            error_msg = f"Error processing candidates: {str(e)}"
            print(f"✗ {error_msg}")
            all_errors.append(error_msg)
    else:
        print(f"⚠ Candidate file not found for {cycle}")

    # Import Financial Summaries
    if weball_file and os.path.exists(weball_file):
        print(f"\n--- Processing Financials ({cycle}) ---")
        try:
            financials = transform_weballcands(weball_file, cycle)
            if financials:
                financials_inserted, financial_errors = insert_batch(
                    'financial_summary',
                    financials,
                    on_conflict='candidate_id,cycle,coverage_end_date'
                )
                all_errors.extend(financial_errors)
                total_inserted += financials_inserted
                print(f"✓ Financials: {financials_inserted}/{len(financials)} inserted")
            else:
                print("⚠ No financials to insert")
        except Exception as e:
            error_msg = f"Error processing financials: {str(e)}"
            print(f"✗ {error_msg}")
            all_errors.append(error_msg)
    else:
        print(f"⚠ Financial file not found for {cycle}")

    # Calculate duration and status
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(all_errors) == 0 else 'partial' if total_inserted > 0 else 'failed'

    # Log the refresh
    print(f"\n--- Logging {cycle} Refresh ---")
    log_refresh(cycle, total_inserted, all_errors, status, duration)

    # Summary
    print(f"\n{cycle} CYCLE SUMMARY:")
    print(f"  Records inserted: {total_inserted}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Duration: {duration} seconds")
    print(f"  Status: {status}")

    return total_inserted, len(all_errors)


def main():
    overall_start = datetime.now()

    print("="*80)
    print("MULTI-CYCLE FEC BULK DATA IMPORT")
    print("="*80)
    print(f"Cycles to import: {', '.join(map(str, CYCLES))}")

    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\nERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    # Track overall stats
    total_records = 0
    total_errors = 0

    # Import each cycle
    for cycle in CYCLES:
        records, errors = import_cycle(cycle)
        total_records += records
        total_errors += errors

    # Overall summary
    overall_duration = int((datetime.now() - overall_start).total_seconds())

    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Cycles imported: {', '.join(map(str, CYCLES))}")
    print(f"Total records: {total_records}")
    print(f"Total errors: {total_errors}")
    print(f"Total duration: {overall_duration} seconds")
    print(f"Average per cycle: {overall_duration // len(CYCLES)} seconds")
    print("="*80)


if __name__ == "__main__":
    main()
