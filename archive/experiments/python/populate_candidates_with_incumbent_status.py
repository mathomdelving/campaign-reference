#!/usr/bin/env python3
"""
Populate candidates table with all candidates from financial_summary
and fetch their incumbent_challenge status from FEC API
"""

import requests
import os
from dotenv import load_dotenv
import time
import json
from datetime import datetime

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

print("=" * 80)
print("POPULATING CANDIDATES TABLE WITH INCUMBENT STATUS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Step 1: Get all unique candidate_ids from financial_summary
print("\n[1/3] Fetching unique candidates from financial_summary...")
all_candidate_ids = set()

for cycle in [2026, 2024, 2022, 2020, 2018]:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={'cycle': f'eq.{cycle}', 'select': 'candidate_id', 'limit': 3000},
        headers=headers_query
    )
    cycle_ids = set([r['candidate_id'] for r in response.json()])
    all_candidate_ids.update(cycle_ids)
    print(f"  Cycle {cycle}: {len(cycle_ids)} candidates")

candidate_ids_list = sorted(list(all_candidate_ids))
print(f"\n  ✓ Total unique candidates: {len(candidate_ids_list)}")

# Step 2: Fetch metadata from FEC API for each candidate
print(f"\n[2/3] Fetching candidate metadata from FEC API...")
print(f"  (This will take ~{len(candidate_ids_list) * 0.5 / 60:.0f} minutes with rate limiting)")

candidates_to_upsert = []
success_count = 0
error_count = 0
not_found_count = 0

for idx, candidate_id in enumerate(candidate_ids_list):
    try:
        # Fetch candidate from FEC API
        response = requests.get(
            'https://api.open.fec.gov/v1/candidates/',
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

            candidates_to_upsert.append({
                'candidate_id': candidate.get('candidate_id'),
                'name': candidate.get('name'),
                'party': candidate.get('party'),
                'office': candidate.get('office'),
                'state': candidate.get('state'),
                'district': candidate.get('district'),
                'incumbent_challenge': candidate.get('incumbent_challenge')
            })

            success_count += 1

            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(candidate_ids_list)} ({success_count} found, {not_found_count} not found, {error_count} errors)")
        else:
            not_found_count += 1
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(candidate_ids_list)} ({success_count} found, {not_found_count} not found, {error_count} errors)")

        # Rate limiting
        time.sleep(0.5)

    except Exception as e:
        error_count += 1
        print(f"  ❌ Error fetching {candidate_id}: {str(e)}")
        time.sleep(1)
        continue

print(f"\n  ✓ Successfully fetched: {success_count}")
print(f"  ⚠️  Not found: {not_found_count}")
print(f"  ❌ Errors: {error_count}")

# Step 3: Upsert candidates to database
print(f"\n[3/3] Upserting {len(candidates_to_upsert)} candidates to database...")

batch_size = 100
upserted_count = 0

for i in range(0, len(candidates_to_upsert), batch_size):
    batch = candidates_to_upsert[i:i + batch_size]

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/candidates",
            headers=headers_supabase,
            json=batch
        )

        if response.status_code in [200, 201]:
            upserted_count += len(batch)
            print(f"  ✓ Batch {i//batch_size + 1}/{(len(candidates_to_upsert)-1)//batch_size + 1}: Upserted {len(batch)} candidates (total: {upserted_count}/{len(candidates_to_upsert)})")
        else:
            print(f"  ❌ Batch {i//batch_size + 1} error: {response.status_code} - {response.text[:200]}")

        time.sleep(0.3)

    except Exception as e:
        print(f"  ❌ Error upserting batch: {str(e)}")
        continue

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total upserted: {upserted_count}")
print("=" * 80)
