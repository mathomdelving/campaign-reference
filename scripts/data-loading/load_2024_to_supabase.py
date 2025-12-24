#!/usr/bin/env python3
"""
Load 2024 FEC data into Supabase
Ensures schema consistency with 2026 data
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def load_json_file(filename):
    """Load and return JSON data from file."""
    print(f"Loading {filename}...")
    with open(filename, 'r') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data):,} records from {filename}")
    return data

def insert_batch(table_name, records, batch_size=1000, on_conflict=None):
    """Insert records into Supabase in batches using UPSERT."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    # Add on_conflict parameter for upsert
    if on_conflict:
        url += f"?on_conflict={on_conflict}"

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
                print(f"  Batch {i//batch_size + 1}: {inserted:,}/{total:,} records")
            else:
                error_msg = f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text[:200]}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} error: {str(e)[:200]}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)

    return inserted, errors

def transform_candidates(candidates_data):
    """Transform candidate JSON to database format (extract only required fields)."""
    transformed = []

    for candidate in candidates_data:
        # Keep office as single-character code ('H', 'S', 'P')
        # Database schema expects VARCHAR(1), not full names

        transformed.append({
            'candidate_id': candidate['candidate_id'],
            'name': candidate['name'],
            'party': candidate.get('party'),  # Short form like 'DEM', 'REP'
            'office': candidate.get('office'),  # Keep as 'H', 'S', 'P'
            'state': candidate.get('state'),
            'district': candidate.get('district'),  # '00', '01', etc.
            'incumbent_challenge': candidate.get('incumbent_challenge')  # 'I', 'C', 'O'
        })

    return transformed

def transform_financial_summary(financials_data):
    """Transform financial summary to database format."""
    transformed = []

    for record in financials_data:
        transformed.append({
            'candidate_id': record['candidate_id'],
            'cycle': record['cycle'],
            'total_receipts': record.get('total_receipts'),
            'total_disbursements': record.get('total_disbursements'),
            'cash_on_hand': record.get('cash_on_hand'),
            'coverage_start_date': record.get('coverage_start_date'),
            'coverage_end_date': record.get('coverage_end_date'),
            'report_year': record.get('last_report_year'),
            'report_type': record.get('last_report_type')
        })

    return transformed

def transform_quarterly_financials(quarterly_data):
    """Transform quarterly financials to database format."""
    transformed = []

    for record in quarterly_data:
        # Convert office full name to single-character code
        office = record.get('office', '')
        if office == 'House':
            office = 'H'
        elif office == 'Senate':
            office = 'S'
        elif office == 'President':
            office = 'P'

        # Convert party full name to short code
        party = record.get('party') or ''
        if party and 'DEMOCRATIC' in party:
            party = 'DEM'
        elif party and 'REPUBLICAN' in party:
            party = 'REP'
        elif party and 'LIBERTARIAN' in party:
            party = 'LIB'
        elif party and 'GREEN' in party:
            party = 'GRE'
        elif party and ('INDEPENDENT' in party or 'NONPARTISAN' in party):
            party = 'IND'
        elif not party:
            party = None
        # Leave others as-is (might be 3-letter codes already)

        transformed.append({
            'candidate_id': record['candidate_id'],
            'name': record['name'],
            'party': party,
            'state': record.get('state'),
            'district': record.get('district'),
            'office': office,
            'cycle': record['cycle'],
            'committee_id': record.get('committee_id'),
            'filing_id': record.get('filing_id'),
            'report_type': record.get('report_type'),
            'coverage_start_date': record.get('coverage_start_date'),
            'coverage_end_date': record.get('coverage_end_date'),
            'total_receipts': record.get('total_receipts'),
            'total_disbursements': record.get('total_disbursements'),
            'cash_beginning': record.get('cash_beginning'),
            'cash_ending': record.get('cash_ending'),
            'is_amendment': record.get('is_amendment')
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
        'cycle': cycle,
        'records_updated': records_updated,
        'errors': '\n'.join(errors[:10]) if errors else None,  # First 10 errors
        'status': status,
        'duration_seconds': duration
    }

    try:
        response = requests.post(url, headers=headers, json=log_entry)
        if response.status_code in [200, 201]:
            print("✓ Refresh logged successfully")
        else:
            print(f"⚠️  Failed to log refresh: {response.text[:200]}")
    except Exception as e:
        print(f"⚠️  Error logging refresh: {str(e)[:200]}")

def main():
    start_time = datetime.now()
    print("=" * 100)
    print("LOADING 2024 FEC DATA TO SUPABASE")
    print("=" * 100)

    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    all_errors = []
    total_inserted = 0

    # Step 1: Load and insert candidates
    print("\n1. LOADING CANDIDATES")
    print("-" * 100)
    candidates_data = load_json_file('candidates_2024.json')
    candidates_transformed = transform_candidates(candidates_data)

    print(f"Upserting {len(candidates_transformed):,} candidates (will merge with existing)...")
    candidates_inserted, candidate_errors = insert_batch(
        'candidates',
        candidates_transformed,
        on_conflict='candidate_id'  # UPSERT on candidate_id
    )
    all_errors.extend(candidate_errors)
    total_inserted += candidates_inserted

    if candidate_errors:
        print(f"⚠️  {len(candidate_errors)} errors during candidate load")
    else:
        print(f"✓ Candidates: {candidates_inserted:,}/{len(candidates_transformed):,} upserted")

    # Step 2: Load and insert financial summary
    print("\n2. LOADING FINANCIAL SUMMARY")
    print("-" * 100)
    financials_data = load_json_file('financials_2024.json')
    financials_transformed = transform_financial_summary(financials_data)

    print(f"Inserting {len(financials_transformed):,} financial summaries...")
    financials_inserted, financials_errors = insert_batch(
        'financial_summary',
        financials_transformed
    )
    all_errors.extend(financials_errors)
    total_inserted += financials_inserted

    if financials_errors:
        print(f"⚠️  {len(financials_errors)} errors during financial summary load")
    else:
        print(f"✓ Financial Summary: {financials_inserted:,}/{len(financials_transformed):,} upserted")

    # Step 3: Load and insert quarterly financials
    print("\n3. LOADING QUARTERLY FINANCIALS")
    print("-" * 100)
    quarterly_data = load_json_file('quarterly_financials_2024.json')
    quarterly_transformed = transform_quarterly_financials(quarterly_data)

    print(f"Upserting {len(quarterly_transformed):,} quarterly filings (will merge with existing)...")
    quarterly_inserted, quarterly_errors = insert_batch(
        'quarterly_financials',
        quarterly_transformed,
        batch_size=500,  # Smaller batches for larger records
        on_conflict='candidate_id,cycle,report_type,coverage_start_date,coverage_end_date'
    )
    all_errors.extend(quarterly_errors)
    total_inserted += quarterly_inserted

    if quarterly_errors:
        print(f"⚠️  {len(quarterly_errors)} errors during quarterly load")
    else:
        print(f"✓ Quarterly: {quarterly_inserted:,}/{len(quarterly_transformed):,} inserted")

    # Calculate duration and status
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(all_errors) == 0 else 'partial' if total_inserted > 0 else 'failed'

    # Log the refresh
    print("\n4. LOGGING REFRESH")
    print("-" * 100)
    log_refresh(2024, total_inserted, all_errors, status, duration)

    # Final summary
    print("\n" + "=" * 100)
    print("LOAD COMPLETE")
    print("=" * 100)
    print(f"Total records inserted: {total_inserted:,}")
    print(f"Total errors: {len(all_errors)}")
    print(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    print(f"Status: {status.upper()}")

    if all_errors:
        print("\n⚠️  ERRORS ENCOUNTERED:")
        for i, error in enumerate(all_errors[:5], 1):  # Show first 5 errors
            print(f"  {i}. {error[:150]}")
        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more errors")
    else:
        print("\n✅ ALL DATA LOADED SUCCESSFULLY!")
        print(f"\n2024 cycle data is now in Supabase:")
        print(f"  - {candidates_inserted:,} candidates")
        print(f"  - {financials_inserted:,} financial summaries")
        print(f"  - {quarterly_inserted:,} quarterly filings")

if __name__ == "__main__":
    main()
