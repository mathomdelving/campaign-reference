#!/usr/bin/env python3
"""
Reconciliation Script: Find and fix candidates with financial data but missing from appropriate cycles
This ensures special election senators and other edge cases are captured
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_supabase = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

def check_and_fix_cycle(cycle):
    """Check a cycle for orphaned financial records and fetch missing data"""

    print(f"\n{'='*80}")
    print(f"CHECKING CYCLE {cycle}")
    print('='*80)

    # Get ALL candidate_ids with financial data for this cycle (with pagination)
    PAGE_SIZE = 1000
    offset = 0
    financial_ids = set()

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'cycle': f'eq.{cycle}',
                'select': 'candidate_id',
                'limit': PAGE_SIZE,
                'offset': offset
            },
            headers=headers_query
        )
        page = response.json()
        if not page or len(page) == 0:
            break

        financial_ids.update([r['candidate_id'] for r in page])

        if len(page) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    print(f"\n✓ Found {len(financial_ids)} candidates with financial data")

    # Check which ones are missing from candidates table (with pagination)
    offset = 0
    candidate_ids = set()

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/candidates",
            params={
                'select': 'candidate_id',
                'limit': PAGE_SIZE,
                'offset': offset
            },
            headers=headers_query
        )
        page = response.json()
        if not page or len(page) == 0:
            break

        candidate_ids.update([r['candidate_id'] for r in page])

        if len(page) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    missing = financial_ids - candidate_ids

    if len(missing) == 0:
        print(f"✅ No missing candidates - all have metadata")
        return

    print(f"⚠️  Found {len(missing)} candidates with financial data but no metadata")
    print(f"   Sample IDs: {list(missing)[:5]}")

    # Fetch missing candidates from FEC and add them
    print(f"\n✓ Fetching metadata for {len(missing)} missing candidates...")

    added = 0
    errors = 0

    for candidate_id in missing:
        try:
            # Fetch from FEC API
            response = requests.get(
                f'https://api.open.fec.gov/v1/candidates/',
                params={
                    'api_key': FEC_API_KEY,
                    'candidate_id': candidate_id,
                    'per_page': 1
                },
                timeout=15
            )

            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                candidate = data['results'][0]

                # Add to candidates table
                record = {
                    'candidate_id': candidate['candidate_id'],
                    'name': candidate['name'],
                    'party': candidate.get('party'),
                    'office': candidate.get('office'),
                    'state': candidate.get('state'),
                    'district': candidate.get('district'),
                    'incumbent_challenge': candidate.get('incumbent_challenge')
                }

                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/candidates",
                    headers=headers_supabase,
                    json=[record]
                )

                if response.status_code in [200, 201]:
                    added += 1
                    if added % 50 == 0:
                        print(f"  Progress: {added}/{len(missing)}")
                else:
                    errors += 1

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            errors += 1
            continue

    print(f"\n✅ Added {added} candidates")
    if errors > 0:
        print(f"⚠️  {errors} errors")

def main():
    print("="*80)
    print("CANDIDATE RECONCILIATION - Finding and fixing missing candidate metadata")
    print("="*80)

    cycles = [2026, 2024, 2022, 2020, 2018]

    for cycle in cycles:
        check_and_fix_cycle(cycle)
        time.sleep(1)

    print("\n" + "="*80)
    print("RECONCILIATION COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
