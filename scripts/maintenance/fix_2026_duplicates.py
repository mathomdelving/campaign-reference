#!/usr/bin/env python3
"""
Fix duplicate candidates in 2026 financial_summary.

Problem: Some committees are linked to both House (H*) and Senate (S*) candidate_ids,
causing duplicate entries in financial_summary with identical data.

Solution: Delete the House financial_summary entry for candidates who are
running for Senate in 2026 (keeping only the Senate entry).
"""

import os
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Headers for Supabase API calls
HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

def get_financial_summary_2026():
    """Fetch all 2026 financial_summary entries with pagination."""
    all_data = []
    offset = 0
    limit = 1000

    while True:
        url = f"{SUPABASE_URL}/rest/v1/financial_summary"
        params = {
            'cycle': 'eq.2026',
            'select': 'candidate_id,total_receipts,total_disbursements,cash_on_hand',
            'offset': offset,
            'limit': limit
        }

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            batch = response.json()
            if not batch:
                break
            all_data.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        else:
            print(f"Error fetching financial_summary: {response.status_code} - {response.text}")
            break

    return all_data

def get_candidates():
    """Fetch all candidates with their names, with pagination."""
    all_data = []
    offset = 0
    limit = 1000

    while True:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        params = {
            'select': 'candidate_id,name,office,state',
            'offset': offset,
            'limit': limit
        }

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            batch = response.json()
            if not batch:
                break
            all_data.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        else:
            print(f"Error fetching candidates: {response.status_code} - {response.text}")
            break

    return {c['candidate_id']: c for c in all_data}

def find_duplicates(financials, candidates):
    """
    Find duplicate entries where:
    - Same total_receipts appears for both H* and S* candidate_ids
    - These represent the same person running for different offices
    """
    # Group financials by total_receipts (our key indicator of duplicates)
    receipts_map = defaultdict(list)

    for f in financials:
        key = f['total_receipts']
        if key and key > 0:  # Ignore zero/null entries
            receipts_map[key].append(f['candidate_id'])

    duplicates = []

    for receipts, cand_ids in receipts_map.items():
        if len(cand_ids) >= 2:
            # Check if we have both H* and S* candidate_ids
            house_ids = [c for c in cand_ids if c.startswith('H')]
            senate_ids = [c for c in cand_ids if c.startswith('S')]

            if house_ids and senate_ids:
                # Get candidate names to verify they're the same person
                for h_id in house_ids:
                    for s_id in senate_ids:
                        h_cand = candidates.get(h_id, {})
                        s_cand = candidates.get(s_id, {})

                        # Extract last name for comparison
                        h_name = h_cand.get('name', '')
                        s_name = s_cand.get('name', '')

                        # Simple last name match (names are in "LASTNAME, FIRSTNAME" format)
                        h_last = h_name.split(',')[0].strip().upper() if h_name else ''
                        s_last = s_name.split(',')[0].strip().upper() if s_name else ''

                        if h_last and s_last and h_last == s_last:
                            duplicates.append({
                                'house_id': h_id,
                                'senate_id': s_id,
                                'house_name': h_name,
                                'senate_name': s_name,
                                'state': s_cand.get('state'),
                                'total_receipts': receipts
                            })

    return duplicates

def delete_financial_summary(candidate_id, cycle=2026):
    """Delete a financial_summary entry for a specific candidate and cycle."""
    url = f"{SUPABASE_URL}/rest/v1/financial_summary"
    params = {
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}'
    }

    response = requests.delete(url, headers=HEADERS, params=params)
    return response.status_code in [200, 204]

def main():
    print("=" * 60)
    print("FIX 2026 DUPLICATE FINANCIAL ENTRIES")
    print("=" * 60)

    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    print("\n1. Fetching 2026 financial_summary data...")
    financials = get_financial_summary_2026()
    print(f"   Found {len(financials)} entries")

    print("\n2. Fetching candidate data...")
    candidates = get_candidates()
    print(f"   Found {len(candidates)} candidates")

    print("\n3. Identifying duplicates...")
    duplicates = find_duplicates(financials, candidates)
    print(f"   Found {len(duplicates)} duplicate pairs")

    if not duplicates:
        print("\nNo duplicates found. Database is clean!")
        return

    print("\n4. Duplicate pairs to fix:")
    print("-" * 60)

    for i, dup in enumerate(duplicates, 1):
        print(f"\n   {i}. {dup['house_name']}")
        print(f"      House:  {dup['house_id']} -> DELETE")
        print(f"      Senate: {dup['senate_id']} -> KEEP")
        print(f"      State:  {dup['state']}")
        print(f"      Total Receipts: ${dup['total_receipts']:,.2f}")

    print("\n" + "=" * 60)
    print("5. Deleting House entries (keeping Senate entries)...")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for dup in duplicates:
        house_id = dup['house_id']
        house_name = dup['house_name']

        if delete_financial_summary(house_id, 2026):
            print(f"   ✓ Deleted: {house_id} ({house_name})")
            success_count += 1
        else:
            print(f"   ✗ Failed:  {house_id} ({house_name})")
            error_count += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   Deleted: {success_count}")
    print(f"   Errors:  {error_count}")
    print("\nDone! Each candidate should now appear only once on the leaderboard.")

if __name__ == "__main__":
    main()
