#!/usr/bin/env python3
"""
Party Committee Data Collector - Following the Ironclad 2-Step Workflow

Collects monthly filing data for major party committees:
- DCCC (C00000935) - Democratic Congressional Campaign Committee
- DSCC (C00042366) - Democratic Senatorial Campaign Committee
- NRCC (C00075820) - National Republican Congressional Committee
- NRSC (C00027466) - National Republican Senatorial Committee

These committees file MONTHLY (not quarterly like candidates) using Form F3X.

FOLLOWS 2-STEP WORKFLOW:
  Step 1: This script collects data → Saves to JSON files
  Step 2: Use load_party_committee_data.py to load JSON → Supabase

Usage:
  python3 scripts/collect_party_committee_data.py --cycle 2022
  python3 scripts/collect_party_committee_data.py --cycle 2024
  python3 scripts/collect_party_committee_data.py --cycles 2022,2024,2026

Output Files:
  - party_committee_filings_{cycle}.json
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
    print("Please create a .env file with your API key.")
    exit(1)

# Party committees to collect
PARTY_COMMITTEES = {
    "C00000935": {
        "name": "DCCC",
        "full_name": "Democratic Congressional Campaign Committee",
        "party": "DEM",
        "chamber": "house"
    },
    "C00042366": {
        "name": "DSCC",
        "full_name": "Democratic Senatorial Campaign Committee",
        "party": "DEM",
        "chamber": "senate"
    },
    "C00075820": {
        "name": "NRCC",
        "full_name": "National Republican Congressional Committee",
        "party": "REP",
        "chamber": "house"
    },
    "C00027466": {
        "name": "NRSC",
        "full_name": "National Republican Senatorial Committee",
        "party": "REP",
        "chamber": "senate"
    },
}


class Progress:
    """Progress tracker that can resume from interruptions."""
    def __init__(self, cycles):
        self.cycles = cycles
        cycle_str = "_".join(str(c) for c in sorted(cycles))
        self.progress_file = f"progress_party_committees_{cycle_str}.json"
        self.data = self._load()

    def _load(self):
        """Load progress from previous run if it exists."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_committees': [],
            'filings': [],
            'errors': []
        }

    def save(self):
        """Save current progress."""
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def is_completed(self, committee_id, cycle):
        """Check if a committee/cycle combo is already done."""
        key = f"{committee_id}_{cycle}"
        return key in self.data['completed_committees']

    def mark_completed(self, committee_id, cycle):
        """Mark a committee/cycle combo as completed."""
        key = f"{committee_id}_{cycle}"
        if key not in self.data['completed_committees']:
            self.data['completed_committees'].append(key)

    def add_filing(self, filing):
        """Add a filing record."""
        self.data['filings'].append(filing)

    def add_error(self, committee_id, cycle, error_msg):
        """Track an error."""
        self.data['errors'].append({
            'committee_id': committee_id,
            'cycle': cycle,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        })


def fetch_committee_reports(committee_id, cycle, retry_count=0):
    """
    Fetch all reports for a party committee for a given cycle.
    Uses the /committee/{id}/reports/ endpoint which returns F3X data.

    Returns: (reports_list, error_msg)
    """
    url = f"{BASE_URL}/committee/{committee_id}/reports/"
    all_reports = []
    page = 1
    per_page = 100

    while True:
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': per_page,
            'page': page,
            'sort': '-coverage_end_date'
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            # Handle rate limit
            if response.status_code == 429:
                if retry_count < 3:
                    wait_time = 60 * (2 ** retry_count)
                    print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    return fetch_committee_reports(committee_id, cycle, retry_count + 1)
                else:
                    return ([], f"Rate limit persists after {retry_count} retries")

            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            all_reports.extend(results)

            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break

            page += 1
            time.sleep(0.5)  # Rate limiting between pages

        except requests.exceptions.Timeout as e:
            return ([], f"Timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            return ([], f"Request error: {str(e)}")

    return (all_reports, None)


def process_report(raw_report, committee_info, cycle):
    """Convert raw FEC report to our standard format."""
    coverage_end = raw_report.get('coverage_end_date')
    if coverage_end:
        coverage_end = coverage_end[:10]  # Just date part

    coverage_start = raw_report.get('coverage_start_date')
    if coverage_start:
        coverage_start = coverage_start[:10]

    # Get period values (not YTD)
    total_receipts = raw_report.get('total_receipts_period')
    total_disbursements = raw_report.get('total_disbursements_period')

    # Handle string values that may come from API
    if isinstance(total_receipts, str):
        total_receipts = float(total_receipts) if total_receipts else 0
    if isinstance(total_disbursements, str):
        total_disbursements = float(total_disbursements) if total_disbursements else 0

    return {
        'committee_id': raw_report.get('committee_id'),
        'committee_name': committee_info['name'],
        'committee_full_name': committee_info['full_name'],
        'party': committee_info['party'],
        'chamber': committee_info['chamber'],
        'cycle': cycle,
        'report_type': raw_report.get('report_type'),
        'report_type_full': raw_report.get('report_type_full'),
        'coverage_start_date': coverage_start,
        'coverage_end_date': coverage_end,
        'total_receipts': float(total_receipts or 0),
        'total_disbursements': float(total_disbursements or 0),
        'cash_on_hand_beginning': float(raw_report.get('cash_on_hand_beginning_period') or 0),
        'cash_on_hand_end': float(raw_report.get('cash_on_hand_end_period') or 0),
        'debts_owed': float(raw_report.get('debts_owed_by_committee') or 0),
        'individual_contributions': float(raw_report.get('total_individual_contributions_period') or 0),
        'other_committee_contributions': float(raw_report.get('other_political_committee_contributions_period') or 0),
        'independent_expenditures': float(raw_report.get('independent_expenditures_period') or 0),
        'coordinated_expenditures': float(raw_report.get('coordinated_expenditures_by_party_committee_period') or 0),
        'file_number': raw_report.get('file_number'),
        'receipt_date': raw_report.get('receipt_date'),
        'is_amended': raw_report.get('is_amended', False),
        'pdf_url': raw_report.get('pdf_url'),
    }


def main():
    parser = argparse.ArgumentParser(description='Party committee data collector')
    parser.add_argument('--cycle', type=int, help='Single election cycle (e.g., 2024)')
    parser.add_argument('--cycles', type=str, help='Multiple cycles comma-separated (e.g., 2022,2024,2026)')
    args = parser.parse_args()

    # Parse cycles
    if args.cycles:
        cycles = [int(c.strip()) for c in args.cycles.split(',')]
    elif args.cycle:
        cycles = [args.cycle]
    else:
        cycles = [2022, 2024, 2026]  # Default: 2022-present

    print("\n" + "=" * 60)
    print("PARTY COMMITTEE DATA COLLECTOR")
    print(f"Cycles: {', '.join(str(c) for c in cycles)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n⚠️  FOLLOWING 2-STEP WORKFLOW:")
    print("  Step 1: Collect data → JSON files (this script)")
    print("  Step 2: Review JSON → Load to Supabase (separate)")

    # Initialize progress tracker
    progress = Progress(cycles)

    if progress.data['filings']:
        print(f"\n✓ Resuming: Already have {len(progress.data['filings'])} filings")

    # Collect data
    print(f"\n\nCollecting reports for {len(PARTY_COMMITTEES)} committees...")
    print("=" * 60)

    total_collected = 0

    for committee_id, info in PARTY_COMMITTEES.items():
        print(f"\n{info['name']} ({committee_id}):")

        for cycle in cycles:
            if progress.is_completed(committee_id, cycle):
                print(f"  {cycle}: Already collected, skipping")
                continue

            print(f"  {cycle}: Fetching...", end=" ")

            reports, error = fetch_committee_reports(committee_id, cycle)

            if error:
                print(f"❌ Error: {error}")
                progress.add_error(committee_id, cycle, error)
                continue

            # Filter out amended reports (keep only most recent)
            non_amended = [r for r in reports if not r.get('is_amended')]

            # Process and store
            for raw_report in non_amended:
                # Skip if no coverage date
                if not raw_report.get('coverage_end_date'):
                    continue

                processed = process_report(raw_report, info, cycle)
                progress.add_filing(processed)

            progress.mark_completed(committee_id, cycle)
            progress.save()

            print(f"✓ {len(non_amended)} reports")
            total_collected += len(non_amended)

            time.sleep(1)  # Rate limiting between cycles

    # Save final output
    print(f"\n\n{'=' * 60}")
    print("SAVING OUTPUT FILES")
    print("=" * 60)

    cycle_str = "_".join(str(c) for c in sorted(cycles))
    output_file = f"party_committee_filings_{cycle_str}.json"

    output_data = {
        'collected_at': datetime.now().isoformat(),
        'cycles': cycles,
        'committees': list(PARTY_COMMITTEES.keys()),
        'total_filings': len(progress.data['filings']),
        'filings': progress.data['filings']
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Saved {output_file}: {len(progress.data['filings'])} filings")

    # Save errors if any
    if progress.data['errors']:
        errors_file = f"party_committee_errors_{cycle_str}.json"
        with open(errors_file, 'w') as f:
            json.dump(progress.data['errors'], f, indent=2)
        print(f"⚠️  Saved {errors_file}: {len(progress.data['errors'])} errors")

    # Cleanup progress file
    if os.path.exists(progress.progress_file):
        os.remove(progress.progress_file)
        print(f"✓ Cleaned up {progress.progress_file}")

    # Summary
    print(f"\n{'=' * 60}")
    print("COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Total filings collected: {len(progress.data['filings'])}")

    # By committee
    print("\nBy committee:")
    for committee_id, info in PARTY_COMMITTEES.items():
        count = sum(1 for f in progress.data['filings'] if f['committee_id'] == committee_id)
        print(f"  {info['name']}: {count} filings")

    # By cycle
    print("\nBy cycle:")
    for cycle in cycles:
        count = sum(1 for f in progress.data['filings'] if f['cycle'] == cycle)
        print(f"  {cycle}: {count} filings")

    # Sample latest filings
    if progress.data['filings']:
        print("\nLatest filings:")
        sorted_filings = sorted(
            progress.data['filings'],
            key=lambda x: x['coverage_end_date'] or '',
            reverse=True
        )[:4]
        for f in sorted_filings:
            print(f"  {f['committee_name']} - {f['coverage_end_date']} - ${f['total_receipts']:,.0f} raised")

    print(f"\n✅ COLLECTION COMPLETE!")
    print(f"\n📋 NEXT STEPS:")
    print(f"  1. Review {output_file} to verify data looks correct")
    print(f"  2. Run: python3 scripts/data-loading/load_party_committee_data.py")
    print()


if __name__ == "__main__":
    main()
