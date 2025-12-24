#!/usr/bin/env python3
"""
Complete Cycle Data Collector

Collects ALL campaign finance data for a cycle:
1. Candidates (metadata)
2. Financial summaries (total raised, spent, cash)
3. Quarterly financials (all filings with committee IDs)
4. Committee designations (P, A, J, etc.)

FOLLOWS 2-STEP WORKFLOW:
  Collects everything → Saves to JSON files → Review → Load separately

Usage:
  python3 collect_complete_cycle_data.py --cycle 2022

Output Files:
  - candidates_{cycle}.json
  - financials_{cycle}.json
  - quarterly_financials_{cycle}.json
  - committee_designations_{cycle}.json  ← NEW!
"""

import subprocess
import sys
import os
import json
import argparse
from datetime import datetime

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ FAILED: {description}")
        return False

    print(f"\n✅ COMPLETED: {description}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Collect complete cycle data')
    parser.add_argument('--cycle', type=int, required=True, help='Election cycle (e.g., 2022, 2024, 2026)')
    args = parser.parse_args()

    cycle = args.cycle

    print("\n" + "="*60)
    print("COMPLETE CYCLE DATA COLLECTION")
    print(f"Cycle: {cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n⚠️  FOLLOWING 2-STEP WORKFLOW:")
    print("  Step 1: Collect ALL data → JSON files (this script)")
    print("  Step 2: Review JSON → Load to Supabase (separate)")

    # Step 1: Collect financial data using ROBUST cycle script
    print("\n\n" + "="*60)
    print("STEP 1: COLLECTING FINANCIAL DATA (ROBUST)")
    print("="*60)

    financial_cmd = [
        'python3',
        'scripts/data-collection/fetch_cycle_data_robust.py',
        '--cycle', str(cycle)
    ]

    if not run_command(financial_cmd, f"Financial data collection for {cycle}"):
        print("\n❌ Failed to collect financial data")
        sys.exit(1)

    # Step 2: Collect committee designations
    print("\n\n" + "="*60)
    print("STEP 2: COLLECTING COMMITTEE DESIGNATIONS")
    print("="*60)

    designation_cmd = [
        'python3',
        'scripts/data-collection/fetch_committee_designations.py',
        '--cycles', str(cycle)
    ]

    if not run_command(designation_cmd, f"Committee designations for {cycle}"):
        print("\n❌ Failed to collect committee designations")
        sys.exit(1)

    # Summary
    print("\n\n" + "="*60)
    print("COLLECTION COMPLETE!")
    print("="*60)

    # Check which files were created
    files_created = []
    expected_files = [
        f"candidates_{cycle}.json",
        f"financials_{cycle}.json",
        f"quarterly_financials_{cycle}.json",
        f"committee_designations_{cycle}.json"
    ]

    for filename in expected_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            files_created.append((filename, size))

            # Count records
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else "N/A"
                    print(f"  ✓ {filename}: {count} records ({size:,} bytes)")
            except:
                print(f"  ✓ {filename}: ({size:,} bytes)")

    print("\n📋 NEXT STEPS:")
    print("  1. Review the JSON files to verify data looks correct")
    print("  2. Load to Supabase:")
    print(f"     python3 scripts/data-loading/load_to_supabase.py")
    print(f"     python3 scripts/data-loading/load_committee_designations.py --cycles {cycle}")
    print()

if __name__ == "__main__":
    main()
