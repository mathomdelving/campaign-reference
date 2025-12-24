#!/usr/bin/env python3
"""
BACKFILL COMMITTEE DESIGNATIONS

Uses existing quarterly_financials records to backfill committee_designations table.
Fetches designation from FEC API for each unique (committee_id, cycle) pair.

This is faster than re-collecting all candidates because:
- We already have the committee_id and cycle from quarterly_financials
- We only need to make ~3,000-5,000 API calls (not 50,000+)
- Rate limited to respect FEC API limits

Usage:
    python3 scripts/data-loading/backfill_committee_designations.py
    python3 scripts/data-loading/backfill_committee_designations.py --cycle 2026
"""

import requests
import os
import sys
import time
import argparse
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ ERROR: Missing required environment variables")
    sys.exit(1)

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

RATE_LIMIT_DELAY = 4.0  # 4 seconds between calls = 900 calls/hour

# FEC designation mappings
DESIGNATION_NAMES = {
    'P': 'Principal campaign committee',
    'A': 'Authorized by a candidate',
    'U': 'Unauthorized',
    'B': 'Lobbyist/Registrant PAC',
    'D': 'Leadership PAC',
    'J': 'Joint fundraiser'
}

COMMITTEE_TYPE_NAMES = {
    'H': 'House',
    'S': 'Senate',
    'P': 'Presidential',
    'X': 'Non-qualified',
    'Y': 'Qualified',
    'Z': 'National Party Nonfederal',
    'N': 'PAC - Nonqualified',
    'Q': 'PAC - Qualified',
    'O': 'Independent Expenditure (Super PAC)',
    'V': 'Hybrid PAC',
    'W': 'Single Candidate Independent Expenditure'
}


def get_unique_committees_from_quarterly(cycle=None):
    """Get unique (committee_id, cycle, candidate_id) from quarterly_financials."""
    print(f"\n  Fetching unique committees from quarterly_financials...")

    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?select=committee_id,cycle,candidate_id&limit=100000"
    if cycle:
        url += f"&cycle=eq.{cycle}"

    response = requests.get(url, headers=headers_query)

    if not response.ok:
        print(f"  ❌ Failed to fetch quarterly data: {response.status_code}")
        return []

    records = response.json()

    # Get unique combinations
    unique = {}
    for record in records:
        key = (record['committee_id'], record['cycle'])
        if key not in unique:
            unique[key] = record['candidate_id']

    print(f"  ✓ Found {len(unique)} unique committee-cycle combinations")
    return unique


def get_existing_designations(cycle=None):
    """Get committee_ids that already have designations stored."""
    url = f"{SUPABASE_URL}/rest/v1/committee_designations?select=committee_id,cycle&limit=100000"
    if cycle:
        url += f"&cycle=eq.{cycle}"

    response = requests.get(url, headers=headers_query)

    if not response.ok:
        return set()

    records = response.json()
    existing = {(r['committee_id'], r['cycle']) for r in records}

    if existing:
        print(f"  ✓ Found {len(existing)} existing designations (will skip)")

    return existing


def get_committee_designation_from_fec(committee_id, cycle):
    """Fetch committee designation from FEC API."""
    url = f'https://api.open.fec.gov/v1/committee/{committee_id}/history/'
    params = {'api_key': FEC_API_KEY, 'per_page': 100}

    try:
        response = requests.get(url, params=params, timeout=30)
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            history = response.json().get('results', [])
            for record in history:
                if record.get('cycle') == cycle:
                    return {
                        'designation': record.get('designation'),
                        'committee_type': record.get('committee_type'),
                        'committee_name': record.get('name')
                    }
        return None
    except Exception as e:
        print(f"    ⚠️  Exception fetching {committee_id}: {str(e)[:100]}")
        return None


def upsert_committee_designation(committee_id, cycle, designation_data, candidate_id):
    """Store committee designation (no generated columns)."""
    if not designation_data or not designation_data['designation']:
        return False

    # Do NOT include generated columns (is_principal, is_authorized, etc.)
    record = {
        'committee_id': committee_id,
        'cycle': cycle,
        'designation': designation_data['designation'],
        'designation_name': DESIGNATION_NAMES.get(designation_data['designation']),
        'committee_type': designation_data['committee_type'],
        'committee_type_name': COMMITTEE_TYPE_NAMES.get(designation_data['committee_type']),
        'committee_name': designation_data['committee_name'],
        'candidate_id': candidate_id,
        'source': 'fec_api'
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/committee_designations?on_conflict=committee_id,cycle",
            headers=headers_upsert,
            json=[record]
        )

        if response.status_code in [200, 201]:
            return True
        else:
            print(f"    ⚠️  Failed to store {committee_id}: {response.status_code}")
            print(f"       {response.text[:200]}")
            return False

    except Exception as e:
        print(f"    ⚠️  Exception storing {committee_id}: {str(e)[:100]}")
        return False


def backfill_cycle(cycle):
    """Backfill committee designations for a specific cycle."""
    print(f"\n{'='*80}")
    print(f"BACKFILLING CYCLE {cycle}")
    print('='*80)

    # Get unique committees from quarterly data
    unique_committees = get_unique_committees_from_quarterly(cycle)

    if not unique_committees:
        print(f"  ❌ No quarterly data found for cycle {cycle}")
        return

    # Get existing designations to skip
    existing = get_existing_designations(cycle)

    # Filter to only committees that need designations
    to_process = {k: v for k, v in unique_committees.items() if k not in existing}

    if not to_process:
        print(f"\n  ✅ All {len(unique_committees)} committees already have designations!")
        return

    print(f"\n  Processing {len(to_process)} committees (skipping {len(existing)} existing)")
    print(f"  Estimated time: {(len(to_process) * RATE_LIMIT_DELAY / 3600):.1f} hours")
    print()

    success_count = 0
    failed_count = 0
    no_designation_count = 0

    for i, ((committee_id, cycle_val), candidate_id) in enumerate(to_process.items(), 1):
        if i % 25 == 0:
            print(f"  Progress: {i}/{len(to_process)} ({success_count} success, {failed_count} failed, {no_designation_count} no designation)")

        # Fetch from FEC API
        designation_data = get_committee_designation_from_fec(committee_id, cycle_val)

        if not designation_data or not designation_data['designation']:
            no_designation_count += 1
            continue

        # Store in database
        if upsert_committee_designation(committee_id, cycle_val, designation_data, candidate_id):
            success_count += 1
        else:
            failed_count += 1

    print(f"\n  {'='*80}")
    print(f"  CYCLE {cycle} COMPLETE")
    print(f"  {'='*80}")
    print(f"    ✓ Success: {success_count}")
    print(f"    ⚠️  Failed: {failed_count}")
    print(f"    ℹ️  No designation: {no_designation_count}")
    print(f"    Total processed: {len(to_process)}")


def main():
    parser = argparse.ArgumentParser(description='Backfill committee designations from existing quarterly data')
    parser.add_argument('--cycle', type=int, help='Backfill specific cycle only')
    args = parser.parse_args()

    start_time = datetime.now()

    print("="*80)
    print("BACKFILL COMMITTEE DESIGNATIONS")
    print("="*80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nUsing existing quarterly_financials data to populate committee_designations")
    print("No data re-collection needed - just fetching designations from FEC API")

    if args.cycle:
        backfill_cycle(args.cycle)
    else:
        # Get all cycles from quarterly_financials
        url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?select=cycle&limit=100000"
        response = requests.get(url, headers=headers_query)

        if response.ok:
            cycles = sorted(set(r['cycle'] for r in response.json()), reverse=True)
            print(f"\nFound data for cycles: {', '.join(map(str, cycles))}")

            for cycle in cycles:
                backfill_cycle(cycle)
        else:
            print("❌ Failed to fetch cycles from quarterly_financials")
            sys.exit(1)

    duration = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*80}")
    print(f"BACKFILL COMPLETE")
    print(f"Duration: {duration/60:.1f} minutes ({duration/3600:.1f} hours)")
    print('='*80)


if __name__ == '__main__':
    main()
