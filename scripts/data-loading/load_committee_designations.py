#!/usr/bin/env python3
"""
Committee Designations Loader

Loads committee designation JSON files to Supabase database.

STEP 2 OF 2-STEP WORKFLOW:
  Step 1: fetch_committee_designations.py collects data → JSON files
  Step 2: This script loads JSON → Supabase

Usage:
  python3 scripts/data-loading/load_committee_designations.py --cycles 2022,2024,2026
"""

import json
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    exit(1)

def load_json_file(filename):
    """Load and return JSON data from file."""
    if not os.path.exists(filename):
        print(f"ERROR: File {filename} not found!")
        print(f"  Run fetch_committee_designations.py first to collect data")
        return None

    print(f"Loading {filename}...")
    with open(filename, 'r') as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} records from {filename}")
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
                print(f"  Upserted batch {i//batch_size + 1}: {inserted}/{total} records")
            else:
                error_msg = f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}"
                print(f"  {error_msg}")
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} error: {str(e)}"
            print(f"  {error_msg}")
            errors.append(error_msg)

    return inserted, errors

def transform_designations(designations_data):
    """Transform designation JSON to database format.

    IMPORTANT: Does NOT include generated columns (is_principal, is_authorized, etc.)
    These are computed automatically by PostgreSQL.
    """
    transformed = []

    for record in designations_data:
        # Only include columns that are NOT generated
        transformed.append({
            'committee_id': record['committee_id'],
            'cycle': record['cycle'],
            'candidate_id': record.get('candidate_id'),
            'candidate_name': record.get('candidate_name'),
            'office': record.get('office'),
            'designation': record['designation'],
            'designation_full': record.get('designation_full'),
            'committee_type': record.get('committee_type'),
            'committee_type_full': record.get('committee_type_full')
            # DO NOT include: is_principal, is_authorized, is_joint_fundraising, is_leadership_pac
            # These are generated columns and will be computed by PostgreSQL
        })

    return transformed

def main():
    parser = argparse.ArgumentParser(description='Load committee designations to Supabase')
    parser.add_argument('--cycles', type=str, default='2022,2024,2026',
                        help='Comma-separated list of cycles (default: 2022,2024,2026)')
    args = parser.parse_args()

    cycles = [int(c.strip()) for c in args.cycles.split(',')]

    print("\n" + "="*60)
    print("COMMITTEE DESIGNATIONS LOADER")
    print(f"Cycles: {cycles}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    all_errors = []
    total_inserted = 0

    for cycle in cycles:
        print(f"\n--- Loading Cycle {cycle} ---")

        # Load JSON file
        filename = f"committee_designations_{cycle}.json"
        designations_data = load_json_file(filename)

        if not designations_data:
            print(f"  Skipping cycle {cycle} - no data file found")
            continue

        # Transform to database format
        designations_transformed = transform_designations(designations_data)

        # Insert to database
        designations_inserted, designation_errors = insert_batch(
            'committee_designations',
            designations_transformed,
            on_conflict='committee_id,cycle'
        )

        all_errors.extend(designation_errors)
        total_inserted += designations_inserted

        print(f"\n  Cycle {cycle}: {designations_inserted}/{len(designations_transformed)} records inserted")

    # Final summary
    print("\n" + "="*60)
    print("LOAD COMPLETE")
    print("="*60)
    print(f"Total records inserted: {total_inserted}")
    print(f"Total errors: {len(all_errors)}")

    if all_errors:
        print("\nErrors encountered:")
        for error in all_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more errors")
    else:
        print("\n✅ All committee designations loaded successfully!")
        print("\n📋 NEXT STEPS:")
        print("  1. Verify data in Supabase dashboard")
        print("  2. Test frontend filtering by principal committees")
        print("  3. Check that generated columns (is_principal, is_authorized) are populated")

if __name__ == "__main__":
    main()
