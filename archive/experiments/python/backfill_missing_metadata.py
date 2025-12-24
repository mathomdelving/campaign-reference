#!/usr/bin/env python3
"""
Backfill missing candidate metadata
Fetch metadata for candidates who have financial data but no candidate record
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

RATE_LIMIT_DELAY = 0.5


def get_missing_candidates():
    """Find all candidate_ids with financial data but no metadata"""

    print("Finding candidates with missing metadata...")

    # Get all unique candidate_ids from financial_summary
    PAGE_SIZE = 1000
    from_offset = 0
    financial_ids = set()

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'select': 'candidate_id',
                'limit': PAGE_SIZE,
                'offset': from_offset
            },
            headers=headers_query
        )

        page = response.json()
        if not page or len(page) == 0:
            break

        financial_ids.update([r['candidate_id'] for r in page])

        if len(page) < PAGE_SIZE:
            break

        from_offset += PAGE_SIZE

    print(f"  Found {len(financial_ids)} unique candidates with financial data")

    # Get all candidate_ids from candidates table
    from_offset = 0
    candidate_ids = set()

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/candidates",
            params={
                'select': 'candidate_id',
                'limit': PAGE_SIZE,
                'offset': from_offset
            },
            headers=headers_query
        )

        page = response.json()
        if not page or len(page) == 0:
            break

        candidate_ids.update([r['candidate_id'] for r in page])

        if len(page) < PAGE_SIZE:
            break

        from_offset += PAGE_SIZE

    print(f"  Found {len(candidate_ids)} candidates in metadata table")

    # Find missing
    missing = financial_ids - candidate_ids

    print(f"  {len(missing)} candidates missing metadata")

    return list(missing)


def fetch_candidate_from_fec(candidate_id):
    """Fetch candidate metadata from FEC API"""

    try:
        url = 'https://api.open.fec.gov/v1/candidates/'
        params = {
            'api_key': FEC_API_KEY,
            'candidate_id': candidate_id,
            'per_page': 1
        }

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return None

        data = response.json()
        if data.get('results') and len(data['results']) > 0:
            return data['results'][0]

        return None

    except Exception as e:
        return None


def backfill_metadata(missing_ids):
    """Fetch and insert missing candidate metadata"""

    print(f"\n{'='*80}")
    print(f"BACKFILLING METADATA FOR {len(missing_ids)} CANDIDATES")
    print('='*80)

    added = 0
    errors = 0
    not_found = 0

    for i, candidate_id in enumerate(missing_ids, 1):
        try:
            # Fetch from FEC API
            candidate = fetch_candidate_from_fec(candidate_id)

            if not candidate:
                not_found += 1
                continue

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
                    print(f"  Progress: {added} added, {not_found} not found, {i}/{len(missing_ids)} processed")
            else:
                errors += 1

        except Exception as e:
            errors += 1
            continue

    print(f"\n✅ Added {added} candidates")
    print(f"⚠️  {not_found} not found in FEC API")
    if errors > 0:
        print(f"❌ {errors} errors")


def main():
    print("="*80)
    print("CANDIDATE METADATA BACKFILL")
    print("="*80)

    # Find missing candidates
    missing_ids = get_missing_candidates()

    if not missing_ids:
        print("\n✅ No missing metadata - all candidates are complete!")
        return

    # Backfill the metadata
    backfill_metadata(missing_ids)

    print(f"\n{'='*80}")
    print("BACKFILL COMPLETE")
    print('='*80)


if __name__ == '__main__':
    main()
