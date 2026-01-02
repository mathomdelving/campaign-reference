#!/usr/bin/env python3
"""
Load Party Committee Filings to Supabase

STEP 2 of the 2-step workflow:
  Step 1: collect_party_committee_data.py → JSON files
  Step 2: This script → Load JSON to Supabase

Creates the party_committee_filings table if it doesn't exist.

Usage:
  python3 scripts/data-loading/load_party_committee_data.py
  python3 scripts/data-loading/load_party_committee_data.py --file party_committee_filings_2024.json

Environment:
  SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL
  SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY
"""

import json
import os
import sys
import glob
from datetime import datetime

# Find Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing Supabase credentials!")
    print("Set SUPABASE_URL and SUPABASE_KEY environment variables")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase-py not installed. Run: pip install supabase")
    sys.exit(1)


def find_json_file():
    """Find the most recent party committee filings JSON file."""
    patterns = [
        "party_committee_filings_*.json",
        "party_committee_filings.json"
    ]

    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    if not files:
        return None

    # Return most recently modified
    return max(files, key=os.path.getmtime)


def ensure_table_exists(supabase):
    """Check if table exists by trying a simple query."""
    try:
        result = supabase.table("party_committee_filings").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "does not exist" in str(e).lower() or "42P01" in str(e):
            return False
        # Other error - table might exist
        return True


def load_filings(supabase, filings):
    """Load filings to Supabase with upsert."""
    print(f"\nLoading {len(filings)} filings to Supabase...")

    # Process in batches
    batch_size = 100
    total_loaded = 0
    total_errors = 0

    for i in range(0, len(filings), batch_size):
        batch = filings[i:i + batch_size]

        # Convert to database format
        records = []
        for f in batch:
            record = {
                "committee_id": f["committee_id"],
                "committee_name": f["committee_name"],
                "committee_full_name": f.get("committee_full_name"),
                "party": f["party"],
                "chamber": f["chamber"],
                "cycle": f["cycle"],
                "report_type": f.get("report_type"),
                "report_type_full": f.get("report_type_full"),
                "coverage_start_date": f.get("coverage_start_date"),
                "coverage_end_date": f["coverage_end_date"],
                "total_receipts": f.get("total_receipts", 0),
                "total_disbursements": f.get("total_disbursements", 0),
                "cash_on_hand_beginning": f.get("cash_on_hand_beginning", 0),
                "cash_on_hand_end": f.get("cash_on_hand_end", 0),
                "debts_owed": f.get("debts_owed", 0),
                "individual_contributions": f.get("individual_contributions", 0),
                "other_committee_contributions": f.get("other_committee_contributions", 0),
                "independent_expenditures": f.get("independent_expenditures", 0),
                "coordinated_expenditures": f.get("coordinated_expenditures", 0),
                "file_number": f.get("file_number"),
                "receipt_date": f.get("receipt_date"),
                "is_amended": f.get("is_amended", False),
                "pdf_url": f.get("pdf_url"),
            }
            records.append(record)

        try:
            # Upsert based on unique constraint
            result = supabase.table("party_committee_filings").upsert(
                records,
                on_conflict="committee_id,cycle,coverage_end_date,file_number"
            ).execute()

            total_loaded += len(records)
            print(f"  Loaded batch {i // batch_size + 1}: {len(records)} records")

        except Exception as e:
            print(f"  ERROR in batch {i // batch_size + 1}: {e}")
            total_errors += len(records)

    return total_loaded, total_errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Load party committee filings to Supabase")
    parser.add_argument("--file", type=str, help="JSON file to load (default: auto-detect)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without loading")
    args = parser.parse_args()

    print("=" * 60)
    print("LOAD PARTY COMMITTEE FILINGS TO SUPABASE")
    print("=" * 60)

    # Find JSON file
    json_file = args.file or find_json_file()
    if not json_file:
        print("\nERROR: No party committee filings JSON file found!")
        print("Run collect_party_committee_data.py first to create the JSON file.")
        sys.exit(1)

    print(f"\nLoading from: {json_file}")

    # Load data
    with open(json_file, "r") as f:
        data = json.load(f)

    filings = data.get("filings", data if isinstance(data, list) else [])
    print(f"Found {len(filings)} filings in file")

    if args.dry_run:
        print("\n[DRY RUN] Would load the following:")
        # Show summary
        by_committee = {}
        for f in filings:
            name = f["committee_name"]
            by_committee[name] = by_committee.get(name, 0) + 1
        for name, count in sorted(by_committee.items()):
            print(f"  {name}: {count} filings")
        print("\nRun without --dry-run to actually load.")
        return

    # Connect to Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Check if table exists
    if not ensure_table_exists(supabase):
        print("\n⚠️  Table 'party_committee_filings' does not exist!")
        print("Please run the migration first:")
        print("  sql/migrations/002_create_party_committee_filings.sql")
        sys.exit(1)

    # Load data
    loaded, errors = load_filings(supabase, filings)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Loaded: {loaded} filings")
    if errors:
        print(f"✗ Errors: {errors} filings")
    else:
        print("✓ Zero errors!")

    # Verify
    print("\nVerifying in database...")
    result = supabase.table("party_committee_filings").select("committee_name", count="exact").execute()
    print(f"Total records in party_committee_filings: {result.count}")


if __name__ == "__main__":
    main()
