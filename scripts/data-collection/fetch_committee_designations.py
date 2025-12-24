#!/usr/bin/env python3
"""
Committee Designations Collector

Collects committee designation data (P = Principal, A = Authorized, etc.) for existing
quarterly_financials records.

FOLLOWS 2-STEP WORKFLOW:
  Step 1: This script collects data → Saves to JSON files
  Step 2: Use load_committee_designations.py to load JSON → Supabase

Usage:
  python3 scripts/data-collection/fetch_committee_designations.py --cycles 2022,2024,2026
"""

import requests
import json
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not FEC_API_KEY:
    print("ERROR: FEC_API_KEY not found in .env file!")
    exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY not found in .env file!")
    exit(1)

def fetch_committee_ids_from_supabase(cycle):
    """Fetch unique committee IDs from quarterly_financials for a cycle"""
    print(f"\nFetching committee IDs from Supabase for cycle {cycle}...")

    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }

    # Fetch unique committee IDs with candidate info
    params = {
        'select': 'committee_id,candidate_id,name,office',
        'cycle': f'eq.{cycle}'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        records = response.json()

        # Extract unique committees with their associated candidate info
        committees = {}
        for record in records:
            committee_id = record.get('committee_id')
            if committee_id and committee_id not in committees:
                committees[committee_id] = {
                    'committee_id': committee_id,
                    'candidate_id': record.get('candidate_id'),
                    'candidate_name': record.get('name'),
                    'office': record.get('office')
                }

        print(f"  Found {len(committees)} unique committees for cycle {cycle}")
        return list(committees.values())

    except requests.exceptions.RequestException as e:
        print(f"  ERROR fetching from Supabase: {e}")
        return []

def fetch_committee_info_from_fec(committee_id, cycle, retry_count=0):
    """Fetch committee information from FEC API"""
    url = f"https://api.open.fec.gov/v1/committee/{committee_id}/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        # Handle rate limit
        if response.status_code == 429:
            if retry_count < 5:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_committee_info_from_fec(committee_id, cycle, retry_count + 1)
            else:
                print(f"\n  ❌ Rate limit persists after {retry_count} retries")
                return None

        if response.status_code == 404:
            # Committee not found (normal for some cases)
            return None

        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            committee = results[0]
            return {
                'designation': committee.get('designation'),
                'designation_full': committee.get('designation_full'),
                'committee_type': committee.get('committee_type'),
                'committee_type_full': committee.get('committee_type_full')
            }

        return None

    except requests.exceptions.RequestException as e:
        print(f"\n  Error fetching committee {committee_id}: {e}")
        return None

def collect_designations_for_cycle(cycle):
    """Collect all committee designations for a cycle"""
    print(f"\n{'='*60}")
    print(f"COLLECTING COMMITTEE DESIGNATIONS FOR CYCLE {cycle}")
    print(f"{'='*60}")

    # Step 1: Get committee IDs from quarterly_financials
    committees = fetch_committee_ids_from_supabase(cycle)

    if not committees:
        print(f"  No committees found for cycle {cycle}")
        return []

    # Step 2: Fetch designation for each committee
    print(f"\nFetching designations from FEC API...")
    print(f"Rate limit: 1,000 calls/hour")
    print(f"Processing with 4 second delay between calls")
    print(f"Estimated time: {len(committees) * 4 / 60:.1f} minutes\n")

    designations = []
    save_frequency = 25

    for idx, committee in enumerate(committees):
        committee_id = committee['committee_id']
        candidate_id = committee['candidate_id']
        candidate_name = committee['candidate_name']
        office = committee['office']

        print(f"  [{idx+1}/{len(committees)}] {committee_id} ({candidate_name})...", end=" ")

        # Fetch committee info from FEC
        info = fetch_committee_info_from_fec(committee_id, cycle)

        if info and info.get('designation'):
            designation_record = {
                'committee_id': committee_id,
                'cycle': cycle,
                'candidate_id': candidate_id,
                'candidate_name': candidate_name,
                'office': office,
                'designation': info['designation'],
                'designation_full': info['designation_full'],
                'committee_type': info['committee_type'],
                'committee_type_full': info['committee_type_full']
            }
            designations.append(designation_record)
            print(f"✓ {info['designation']} - {info['designation_full']}")
        else:
            print("⚠️  Not found or no designation")

        # Rate limit: 4 seconds between calls
        time.sleep(4)

        # Save progress periodically
        if (idx + 1) % save_frequency == 0:
            filename = f"committee_designations_{cycle}_progress.json"
            with open(filename, 'w') as f:
                json.dump(designations, f, indent=2)
            print(f"\n  💾 Progress saved: {len(designations)} designations (processed {idx + 1}/{len(committees)})\n")

    return designations

def main():
    parser = argparse.ArgumentParser(description='Collect committee designations for FEC cycles')
    parser.add_argument('--cycles', type=str, default='2022,2024,2026',
                        help='Comma-separated list of cycles (default: 2022,2024,2026)')
    args = parser.parse_args()

    cycles = [int(c.strip()) for c in args.cycles.split(',')]

    print("\n" + "="*60)
    print("COMMITTEE DESIGNATIONS COLLECTOR")
    print(f"Cycles: {cycles}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n⚠️  FOLLOWING 2-STEP WORKFLOW:")
    print("  Step 1: Collecting → JSON files (this script)")
    print("  Step 2: Review JSON → Load to Supabase (separate script)")

    all_designations = {}

    for cycle in cycles:
        designations = collect_designations_for_cycle(cycle)
        all_designations[cycle] = designations

        # Save final file for this cycle
        filename = f"committee_designations_{cycle}.json"
        with open(filename, 'w') as f:
            json.dump(designations, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✓ Saved {len(designations)} designations to {filename}")
        print(f"{'='*60}")

        # Clean up progress file if it exists
        progress_file = f"committee_designations_{cycle}_progress.json"
        if os.path.exists(progress_file):
            os.remove(progress_file)

    # Print summary
    print("\n" + "="*60)
    print("COLLECTION COMPLETE!")
    print("="*60)

    for cycle in cycles:
        count = len(all_designations.get(cycle, []))
        print(f"  Cycle {cycle}: {count} designations")

    print(f"\n✓ Files created:")
    for cycle in cycles:
        print(f"    - committee_designations_{cycle}.json")

    print("\n📋 NEXT STEP:")
    print("  1. Review the JSON files to verify data looks correct")
    print("  2. Run: python3 scripts/data-loading/load_committee_designations.py")
    print()

if __name__ == "__main__":
    main()
