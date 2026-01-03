#!/usr/bin/env python3
"""
Load Cycle Data to Supabase

Loads JSON files from collect_cycle_data.py into Supabase tables.
Handles any election cycle (2018, 2020, 2022, 2024, 2026).

FOLLOWS 2-STEP WORKFLOW:
  Step 1: collect_cycle_data.py → JSON files
  Step 2: This script → JSON files to Supabase

Usage:
  python3 load_cycle_to_supabase.py --cycle 2020
  python3 load_cycle_to_supabase.py --cycle 2018 --dry-run
  python3 load_cycle_to_supabase.py --cycle 2022 --quarterly-only

Tables Updated:
  - candidates (upsert by candidate_id)
  - financial_summary (upsert by candidate_id, cycle, coverage_end_date)
  - candidate_financials (upsert by candidate_id, cycle, coverage_end_date)
"""

import json
import os
import sys
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY in environment")
    sys.exit(1)


def load_json_file(filename):
    """Load JSON data from file."""
    if not os.path.exists(filename):
        print(f"  File not found: {filename}")
        return None

    with open(filename, 'r') as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} records from {filename}")
    return data


def upsert_batch(table_name, records, on_conflict, batch_size=500, dry_run=False):
    """Upsert records into Supabase in batches."""
    if dry_run:
        print(f"  [DRY RUN] Would upsert {len(records)} records to {table_name}")
        return len(records), []

    url = f"{SUPABASE_URL}/rest/v1/{table_name}?on_conflict={on_conflict}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    total = len(records)
    inserted = 0
    errors = []

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]

        try:
            response = requests.post(url, headers=headers, json=batch)

            if response.status_code in [200, 201, 204]:
                inserted += len(batch)
                if (i // batch_size + 1) % 5 == 0 or i + batch_size >= total:
                    print(f"    Upserted {inserted}/{total} records")
            else:
                error_msg = f"Batch {i//batch_size + 1}: {response.status_code} - {response.text[:200]}"
                print(f"    ERROR: {error_msg}")
                errors.append(error_msg)

            time.sleep(0.1)  # Small delay between batches

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1}: {str(e)}"
            print(f"    ERROR: {error_msg}")
            errors.append(error_msg)

    return inserted, errors


def transform_candidates(candidates_data, cycle):
    """Transform candidate JSON to database format."""
    transformed = []

    for candidate in candidates_data:
        transformed.append({
            'candidate_id': candidate['candidate_id'],
            'name': candidate.get('name'),
            'party': candidate.get('party_full'),
            'state': candidate.get('state'),
            'district': candidate.get('district'),
            'office': candidate.get('office'),
            'incumbent_challenge': candidate.get('incumbent_challenge'),
            'updated_at': datetime.now().isoformat()
        })

    return transformed


def transform_financials(financials_data, cycle):
    """Transform financial summary JSON to database format."""
    transformed = []

    for record in financials_data:
        # Extract report_year from coverage_end_date if not present
        report_year = record.get('last_report_year')
        if not report_year and record.get('coverage_end_date'):
            try:
                report_year = int(record['coverage_end_date'][:4])
            except:
                pass

        transformed.append({
            'candidate_id': record['candidate_id'],
            'cycle': cycle,
            'total_receipts': record.get('total_receipts'),
            'total_disbursements': record.get('total_disbursements'),
            'cash_on_hand': record.get('cash_on_hand'),
            'coverage_start_date': record.get('coverage_start_date'),
            'coverage_end_date': record.get('coverage_end_date'),
            'report_year': report_year,
            'report_type': record.get('last_report_type'),
            'updated_at': datetime.now().isoformat()
        })

    return transformed


def transform_quarterly(quarterly_data, cycle):
    """Transform quarterly financials JSON to candidate_financials format."""
    transformed = []

    for record in quarterly_data:
        # Parse filing_id - handle both numeric and string formats
        filing_id = record.get('filing_id')
        if isinstance(filing_id, str) and filing_id.startswith('FEC-'):
            try:
                filing_id = int(filing_id.replace('FEC-', ''))
            except ValueError:
                filing_id = None

        # Extract report_year from coverage_end_date
        report_year = None
        if record.get('coverage_end_date'):
            try:
                report_year = int(record['coverage_end_date'][:4])
            except:
                pass

        transformed.append({
            'candidate_id': record['candidate_id'],
            'committee_id': record.get('committee_id'),
            'name': record.get('name'),
            'party': record.get('party'),
            'state': record.get('state'),
            'district': record.get('district'),
            'office': record.get('office'),
            'cycle': cycle,
            'report_type': record.get('report_type'),
            'report_year': report_year,
            'coverage_start_date': record.get('coverage_start_date'),
            'coverage_end_date': record.get('coverage_end_date'),
            'total_receipts': record.get('total_receipts'),
            'total_disbursements': record.get('total_disbursements'),
            'cash_beginning': record.get('cash_beginning'),
            'cash_ending': record.get('cash_ending'),
            'cash_on_hand': record.get('cash_ending'),  # Map cash_ending to cash_on_hand
            'filing_id': filing_id,
            'is_amendment': record.get('is_amendment', False),
            'updated_at': datetime.now().isoformat()
        })

    return transformed


def log_refresh(cycle, records_updated, errors, status, duration):
    """Log the data refresh operation."""
    url = f"{SUPABASE_URL}/rest/v1/data_refresh_log"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    log_entry = {
        'fetch_date': datetime.now().isoformat(),
        'cycle': cycle,
        'records_updated': records_updated,
        'errors': '\n'.join(errors[:10]) if errors else None,
        'status': status,
        'duration_seconds': duration
    }

    try:
        response = requests.post(url, headers=headers, json=log_entry)
        if response.status_code in [200, 201]:
            print("  Refresh logged successfully")
        else:
            print(f"  Failed to log refresh: {response.status_code}")
    except Exception as e:
        print(f"  Error logging refresh: {e}")


def main():
    parser = argparse.ArgumentParser(description='Load cycle data to Supabase')
    parser.add_argument('--cycle', type=int, required=True, help='Election cycle (e.g., 2020, 2018)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--quarterly-only', action='store_true', help='Only load quarterly data')
    parser.add_argument('--skip-quarterly', action='store_true', help='Skip quarterly data')
    args = parser.parse_args()

    cycle = args.cycle
    dry_run = args.dry_run

    start_time = datetime.now()

    print("\n" + "=" * 60)
    print("LOAD CYCLE DATA TO SUPABASE")
    print(f"Cycle: {cycle}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_errors = []
    total_inserted = 0

    # Load candidates (unless quarterly-only)
    if not args.quarterly_only:
        print(f"\n--- Loading Candidates ---")
        candidates_file = f"candidates_{cycle}.json"
        candidates_data = load_json_file(candidates_file)

        if candidates_data:
            candidates_transformed = transform_candidates(candidates_data, cycle)
            inserted, errors = upsert_batch(
                'candidates',
                candidates_transformed,
                'candidate_id',
                dry_run=dry_run
            )
            all_errors.extend(errors)
            total_inserted += inserted
            print(f"  Result: {inserted} candidates")

    # Load financial summary (unless quarterly-only)
    if not args.quarterly_only:
        print(f"\n--- Loading Financial Summary ---")
        financials_file = f"financials_{cycle}.json"
        financials_data = load_json_file(financials_file)

        if financials_data:
            financials_transformed = transform_financials(financials_data, cycle)
            inserted, errors = upsert_batch(
                'financial_summary',
                financials_transformed,
                'candidate_id,cycle,coverage_end_date',
                dry_run=dry_run
            )
            all_errors.extend(errors)
            total_inserted += inserted
            print(f"  Result: {inserted} financial records")

    # Load quarterly financials (unless skip-quarterly)
    if not args.skip_quarterly:
        print(f"\n--- Loading Quarterly Financials ---")
        quarterly_file = f"quarterly_financials_{cycle}.json"
        quarterly_data = load_json_file(quarterly_file)

        if quarterly_data:
            quarterly_transformed = transform_quarterly(quarterly_data, cycle)
            inserted, errors = upsert_batch(
                'candidate_financials',
                quarterly_transformed,
                'candidate_id,cycle,coverage_end_date',
                dry_run=dry_run
            )
            all_errors.extend(errors)
            total_inserted += inserted
            print(f"  Result: {inserted} quarterly records")

    # Calculate duration and status
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(all_errors) == 0 else 'partial' if total_inserted > 0 else 'failed'

    # Log refresh (unless dry run)
    if not dry_run:
        print(f"\n--- Logging Refresh ---")
        log_refresh(cycle, total_inserted, all_errors, status, duration)

    # Final summary
    print("\n" + "=" * 60)
    print("LOAD COMPLETE")
    print("=" * 60)
    print(f"Total records upserted: {total_inserted}")
    print(f"Errors: {len(all_errors)}")
    print(f"Duration: {duration} seconds")
    print(f"Status: {status.upper()}")

    if all_errors:
        print(f"\nFirst 5 errors:")
        for error in all_errors[:5]:
            print(f"  - {error[:100]}")

    if dry_run:
        print(f"\n[DRY RUN] No changes were made to the database")


if __name__ == "__main__":
    main()
