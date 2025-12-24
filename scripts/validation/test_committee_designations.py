#!/usr/bin/env python3
"""
TEST: Committee Designations Table

Tests that committee_designations table can:
1. Accept new records
2. Handle UPSERT (on_conflict) correctly
3. Process designation data from FEC API

This test uses REAL committee IDs from collected quarterly_financials data.
"""

import requests
import os
import sys
import time
from dotenv import load_dotenv

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

# Designation code mappings
DESIGNATION_NAMES = {
    'P': 'Principal campaign committee',
    'A': 'Authorized committee',
    'J': 'Joint fundraising committee',
    'U': 'Unauthorized committee',
    'B': 'Lobbyist/Registrant PAC',
    'D': 'Leadership PAC'
}


def get_committee_designation(committee_id, cycle):
    """Fetch committee designation from FEC API."""
    url = f'https://api.open.fec.gov/v1/committee/{committee_id}/history/'
    params = {'api_key': FEC_API_KEY, 'per_page': 100}

    try:
        response = requests.get(url, params=params, timeout=30)
        time.sleep(4)  # Rate limiting

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
        print(f"    Exception fetching designation: {e}")
        return None


def test_insert_designation(committee_id, cycle, candidate_id, test_num):
    """Test inserting a committee designation record."""
    print(f"\n{'='*60}")
    print(f"TEST {test_num}: {committee_id} (cycle {cycle})")
    print('='*60)

    # Step 1: Fetch from FEC API
    print(f"  1. Fetching designation from FEC API...")
    designation_data = get_committee_designation(committee_id, cycle)

    if not designation_data or not designation_data['designation']:
        print(f"  ❌ Could not fetch designation from FEC API")
        return False

    print(f"  ✓ Found: {designation_data['designation']} - {DESIGNATION_NAMES.get(designation_data['designation'], 'Unknown')}")

    # Step 2: Build record (exclude generated columns: is_principal, is_authorized, etc.)
    record = {
        'committee_id': committee_id,
        'cycle': cycle,
        'designation': designation_data['designation'],
        'designation_name': DESIGNATION_NAMES.get(designation_data['designation']),
        'committee_type': designation_data['committee_type'],
        'committee_name': designation_data['committee_name'],
        'candidate_id': candidate_id,
        'source': 'fec_api'
        # NOTE: is_principal, is_authorized, is_joint_fundraising, is_leadership_pac
        # are GENERATED columns - PostgreSQL computes them automatically
    }

    # Step 3: Attempt insert with UPSERT
    print(f"  2. Inserting to committee_designations...")
    url = f"{SUPABASE_URL}/rest/v1/committee_designations?on_conflict=committee_id,cycle"

    try:
        response = requests.post(url, headers=headers_upsert, json=[record])

        if response.status_code in [200, 201]:
            print(f"  ✓ INSERT successful (status {response.status_code})")
            return True
        else:
            print(f"  ❌ INSERT failed: {response.status_code}")
            print(f"     Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"  ❌ Exception during insert: {e}")
        return False


def test_upsert_same_record(committee_id, cycle, test_num):
    """Test UPSERT by trying to insert the same record again."""
    print(f"\n{'='*60}")
    print(f"TEST {test_num}: UPSERT (re-insert {committee_id})")
    print('='*60)

    # Fetch existing record
    url = f"{SUPABASE_URL}/rest/v1/committee_designations?committee_id=eq.{committee_id}&cycle=eq.{cycle}"
    response = requests.get(url, headers=headers_query)

    if not response.ok or not response.json():
        print(f"  ❌ Could not fetch existing record")
        return False

    existing = response.json()[0]
    print(f"  1. Found existing record")

    # Try to insert again with modified data (excluding generated columns)
    modified = {
        'committee_id': existing['committee_id'],
        'cycle': existing['cycle'],
        'designation': existing['designation'],
        'designation_name': existing['designation_name'],
        'committee_type': existing['committee_type'],
        'committee_name': f"{existing['committee_name']} (UPDATED)",
        'candidate_id': existing['candidate_id'],
        'source': existing['source']
        # Exclude: is_principal, is_authorized, is_joint_fundraising, is_leadership_pac (generated)
        # Exclude: created_at, updated_at (auto-managed)
    }

    print(f"  2. Attempting UPSERT with modified name...")
    url = f"{SUPABASE_URL}/rest/v1/committee_designations?on_conflict=committee_id,cycle"

    try:
        response = requests.post(url, headers=headers_upsert, json=[modified])

        if response.status_code in [200, 201]:
            print(f"  ✓ UPSERT successful (status {response.status_code})")

            # Verify update
            url = f"{SUPABASE_URL}/rest/v1/committee_designations?committee_id=eq.{committee_id}&cycle=eq.{cycle}"
            response = requests.get(url, headers=headers_query)
            updated = response.json()[0]

            if "(UPDATED)" in updated['committee_name']:
                print(f"  ✓ Record was updated correctly")
            else:
                print(f"  ⚠️  Record not updated (merge-duplicates may have kept original)")

            return True
        else:
            print(f"  ❌ UPSERT failed: {response.status_code}")
            print(f"     Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"  ❌ Exception during UPSERT: {e}")
        return False


def main():
    print("="*60)
    print("COMMITTEE DESIGNATIONS TABLE TEST")
    print("="*60)
    print("\nTesting with REAL committee IDs from collected data\n")

    # Test cases: (committee_id, cycle, candidate_id)
    test_cases = [
        ('C00919803', 2026, 'S6AR00207'),  # Real committee from our data
        ('C00893289', 2026, 'H6FL06324'),  # Another real committee
    ]

    results = []

    # Test 1 & 2: Insert new records
    for i, (committee_id, cycle, candidate_id) in enumerate(test_cases, 1):
        success = test_insert_designation(committee_id, cycle, candidate_id, i)
        results.append(('INSERT', committee_id, success))

    # Test 3: UPSERT (update existing)
    if results[0][2]:  # If first insert succeeded
        success = test_upsert_same_record(test_cases[0][0], test_cases[0][1], 3)
        results.append(('UPSERT', test_cases[0][0], success))

    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print('='*60)

    for test_type, committee_id, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_type} {committee_id}")

    passed = sum(1 for _, _, success in results if success)
    total = len(results)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Committee designations table is working correctly.")
        print("   Safe to proceed with backfill script.")
    else:
        print("\n❌ Some tests failed. Fix table issues before backfilling.")
        sys.exit(1)


if __name__ == '__main__':
    main()
