#!/usr/bin/env python3
"""
Fix Historical Committee Designations

Problem: The collection script captured CURRENT committee designations,
not the historical designations from the 2022 cycle.

Solution: Use /committee/{id}/history/ to get the correct designation
for each committee during the 2022 cycle.

Usage:
  python3 fix_historical_designations.py --cycle 2022
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
BASE_URL = "https://api.open.fec.gov/v1"

if not FEC_API_KEY:
    print("ERROR: FEC_API_KEY not found in .env file!")
    exit(1)


def get_historical_designation(committee_id, cycle):
    """
    Get the committee designation for a specific cycle from history endpoint.
    Returns: (designation, designation_full) or (None, None) if not found
    """
    url = f"{BASE_URL}/committee/{committee_id}/history/"

    try:
        response = requests.get(url, params={'api_key': FEC_API_KEY}, timeout=30)

        if not response.ok:
            print(f"    ⚠️  API error for {committee_id}: HTTP {response.status_code}")
            return (None, None)

        history = response.json().get('results', [])

        # Find the record for our cycle
        for record in history:
            if record.get('cycle') == cycle:
                return (record.get('designation'), record.get('designation_full'))

        # If no exact cycle match, try to find closest earlier cycle
        earlier_records = [r for r in history if r.get('cycle', 0) <= cycle]
        if earlier_records:
            # Sort by cycle descending, take the most recent before our target cycle
            earlier_records.sort(key=lambda x: x.get('cycle', 0), reverse=True)
            record = earlier_records[0]
            return (record.get('designation'), record.get('designation_full'))

        return (None, None)

    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Request error for {committee_id}: {e}")
        return (None, None)


def main():
    parser = argparse.ArgumentParser(description='Fix historical committee designations')
    parser.add_argument('--cycle', type=int, required=True, help='Election cycle (e.g., 2022)')
    args = parser.parse_args()

    cycle = args.cycle
    input_file = f"quarterly_financials_{cycle}.json"
    output_file = f"quarterly_financials_{cycle}_fixed.json"

    print("\n" + "="*60)
    print("FIX HISTORICAL COMMITTEE DESIGNATIONS")
    print(f"Cycle: {cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Load the data
    print(f"\n📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        filings = json.load(f)

    print(f"   Total filings: {len(filings):,}")

    # Get unique committees
    committees = set(f.get('committee_id') for f in filings if f.get('committee_id'))
    print(f"   Unique committees: {len(committees):,}")

    # Build designation lookup
    print(f"\n🔍 Fetching historical designations from FEC API...")
    print(f"   (This will take ~{len(committees) * 4 / 60:.0f} minutes with 4-second delays)")

    designation_lookup = {}
    corrections_needed = 0

    for idx, committee_id in enumerate(sorted(committees), 1):
        if idx % 50 == 0:
            print(f"   Progress: {idx}/{len(committees)} committees...")

        historical_des, historical_des_full = get_historical_designation(committee_id, cycle)

        if historical_des:
            designation_lookup[committee_id] = {
                'designation': historical_des,
                'designation_full': historical_des_full
            }

            # Check if this differs from current designation in our data
            current_filings = [f for f in filings if f.get('committee_id') == committee_id]
            if current_filings:
                current_des = current_filings[0].get('designation')
                if current_des != historical_des:
                    corrections_needed += 1
                    print(f"   ✏️  {committee_id}: {current_des} → {historical_des}")

        # Rate limit - 4 seconds to stay under FEC's 1,000/hour limit
        time.sleep(4)

    print(f"\n   Found historical designations for {len(designation_lookup):,} committees")
    print(f"   Corrections needed: {corrections_needed} committees")

    # Apply corrections
    print(f"\n✏️  Applying corrections...")
    corrections_applied = 0

    for filing in filings:
        committee_id = filing.get('committee_id')
        if committee_id in designation_lookup:
            old_des = filing.get('designation')
            new_des = designation_lookup[committee_id]['designation']
            new_des_full = designation_lookup[committee_id]['designation_full']

            if old_des != new_des:
                filing['designation'] = new_des
                filing['designation_full'] = new_des_full
                corrections_applied += 1

    print(f"   Applied {corrections_applied:,} designation corrections")

    # Save corrected data
    print(f"\n💾 Saving corrected data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(filings, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print("CORRECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total filings: {len(filings):,}")
    print(f"Committees checked: {len(committees):,}")
    print(f"Corrections applied: {corrections_applied:,}")

    # Show designation breakdown
    designation_counts = {}
    for filing in filings:
        des = filing.get('designation', 'NONE')
        designation_counts[des] = designation_counts.get(des, 0) + 1

    print(f"\nCORRECTED DESIGNATION BREAKDOWN:")
    for des in sorted(designation_counts.keys()):
        count = designation_counts[des]
        pct = count / len(filings) * 100
        print(f"  {des:5} {count:6,} ({pct:5.1f}%)")

    print(f"\n✅ COMPLETE!")
    print(f"\nOriginal file: {input_file} (preserved)")
    print(f"Corrected file: {output_file}")
    print(f"\nNext steps:")
    print(f"  1. Review the corrected file")
    print(f"  2. Replace original: mv {output_file} {input_file}")
    print(f"  3. Upload to Supabase")
    print()


if __name__ == "__main__":
    main()
