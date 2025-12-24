"""
Enhanced FEC Filing Fetcher - All Report Types
===============================================

This script fetches ALL filing types for candidates, including:
- Quarterly reports (Q1, Q2, Q3, YE)
- Pre-election reports (12P, 12G, 12R, 12S)
- Post-election reports (30G, 30R, 30S)
- Monthly reports (M2-M12)

It replaces the limited quarterly-only fetcher with comprehensive filing data.

USAGE:
    python fetch_all_filings.py --cycle 2026 [--limit 10]

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
BASE_URL = "https://api.open.fec.gov/v1"

if not FEC_API_KEY:
    print("ERROR: FEC_API_KEY not found in .env file!")
    exit(1)


def fetch_candidates_from_db(cycle, limit=None):
    """Fetch candidates from Supabase database with pagination."""
    all_candidates = []
    offset = 0
    batch_size = 1000  # Supabase max limit

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }

    while True:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        params = {
            'cycle': f'eq.{cycle}',
            'select': 'candidate_id,name,party,state,district,office',
            'limit': batch_size,
            'offset': offset
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            batch = response.json()

            if not batch:
                break

            all_candidates.extend(batch)

            # If user specified a limit, stop when we reach it
            if limit and len(all_candidates) >= limit:
                return all_candidates[:limit]

            # If we got fewer than batch_size, we've reached the end
            if len(batch) < batch_size:
                break

            offset += batch_size

        except Exception as e:
            print(f"Error fetching candidates from database: {e}")
            break

    return all_candidates


def fetch_all_filings(candidate_id, cycle):
    """
    Fetch ALL filings for a candidate, including quarterly, pre/post election.

    Filing Types Included:
    - Q1, Q2, Q3, YE (quarterly)
    - 12P, 12G, 12R, 12S (12-day pre-election)
    - 30G, 30R, 30S (30-day post-election)
    - M2-M12 (monthly, for presidential candidates)
    - TER (termination)
    """
    try:
        # Step 1: Get candidate's committees
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': 10
        }, timeout=10)

        time.sleep(0.5)  # Rate limit

        if not committees_response.ok:
            return []

        committees = committees_response.json().get('results', [])
        all_filings = []

        # Step 2: For each committee, get ALL filings
        for committee in committees:
            committee_id = committee.get('committee_id')

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',  # House/Senate candidate reports
                'sort': '-coverage_end_date',
                'per_page': 50  # Get more filings to cover all types
            }, timeout=10)

            time.sleep(0.5)  # Rate limit

            if filings_response.ok:
                filings = filings_response.json().get('results', [])

                for filing in filings:
                    report_type = filing.get('report_type_full', '')
                    report_code = filing.get('report_type', '')

                    # Only skip if no financial data
                    receipts = filing.get('total_receipts')
                    disbursements = filing.get('total_disbursements')

                    if receipts is None and disbursements is None:
                        continue

                    all_filings.append({
                        'committee_id': committee_id,
                        'filing_id': filing.get('file_number'),
                        'report_type': report_type,
                        'coverage_start_date': filing.get('coverage_start_date'),
                        'coverage_end_date': filing.get('coverage_end_date'),
                        'total_receipts': receipts,
                        'total_disbursements': disbursements,
                        'cash_beginning': filing.get('cash_on_hand_beginning_period'),
                        'cash_ending': filing.get('cash_on_hand_end_period'),
                        'is_amendment': filing.get('is_amended', False)
                    })

        return all_filings

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching filings for {candidate_id}: {e}")
        return []


def calculate_quarter(coverage_end_date, report_type, report_code):
    """
    Calculate quarter label based on coverage end date and report type.

    Returns:
    - 'Q1', 'Q2', 'Q3', 'Q4' for quarterly reports
    - '12P', '12G', etc. for pre-election reports
    - '30G', '30R', etc. for post-election reports
    - 'M2'-'M12' for monthly reports
    - 'YE' for year-end
    - 'TER' for termination
    """
    # Use report code if available (more reliable)
    if report_code:
        code_upper = report_code.upper()

        # Pre-election reports
        if code_upper in ['12P', '12G', '12R', '12S', '12C']:
            return code_upper

        # Post-election reports
        if code_upper in ['30G', '30R', '30S']:
            return code_upper

        # Monthly reports
        if code_upper.startswith('M') and len(code_upper) <= 3:
            return code_upper

        # Year-end
        if code_upper in ['YE', 'YEAR-END']:
            return 'YE'

        # Termination
        if code_upper in ['TER', 'TERMINATION']:
            return 'TER'

    # Fall back to parsing report_type text
    if report_type:
        type_upper = report_type.upper()

        if 'APRIL' in type_upper or 'Q1' in type_upper:
            return 'Q1'
        elif 'JULY' in type_upper or 'Q2' in type_upper:
            return 'Q2'
        elif 'OCTOBER' in type_upper or 'Q3' in type_upper:
            return 'Q3'
        elif 'YEAR-END' in type_upper or 'Q4' in type_upper:
            return 'YE'
        elif 'PRE-PRIMARY' in type_upper or '12 DAY PRE-PRIMARY' in type_upper:
            return '12P'
        elif 'PRE-GENERAL' in type_upper or '12 DAY PRE-GENERAL' in type_upper:
            return '12G'
        elif 'PRE-RUNOFF' in type_upper:
            return '12R'
        elif 'PRE-SPECIAL' in type_upper:
            return '12S'
        elif 'POST-GENERAL' in type_upper or '30 DAY POST-GENERAL' in type_upper:
            return '30G'
        elif 'POST-RUNOFF' in type_upper:
            return '30R'
        elif 'POST-SPECIAL' in type_upper:
            return '30S'
        elif 'TERMINATION' in type_upper:
            return 'TER'

    # Last resort: parse from coverage end date (month)
    if coverage_end_date:
        try:
            month = int(coverage_end_date.split('-')[1])
            if month <= 3:
                return 'Q1'
            elif month <= 6:
                return 'Q2'
            elif month <= 9:
                return 'Q3'
            else:
                return 'Q4'
        except:
            pass

    return None  # Unknown quarter


def save_to_database(filings, cycle):
    """Save filings to quarterly_financials table."""
    if not filings:
        print("  No filings to save")
        return 0

    # Use candidate_id, filing_id for uniqueness (simpler than the 4-column constraint)
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    # Batch insert (1000 at a time)
    batch_size = 1000
    inserted = 0

    for i in range(0, len(filings), batch_size):
        batch = filings[i:i + batch_size]

        try:
            response = requests.post(url, headers=headers, json=batch)

            if response.status_code in [200, 201, 204]:
                inserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: {inserted}/{len(filings)} filings saved")
            else:
                print(f"    Batch {i//batch_size + 1} failed: {response.status_code} - {response.text[:200]}")

        except Exception as e:
            print(f"    Batch {i//batch_size + 1} error: {str(e)}")

    return inserted


def main():
    parser = argparse.ArgumentParser(description='Fetch all FEC filings for candidates')
    parser.add_argument('--cycle', type=int, default=2026, help='Election cycle year (e.g., 2026)')
    parser.add_argument('--limit', type=int, help='Limit number of candidates to process (for testing)')
    parser.add_argument('--save-json', action='store_true', help='Save results to JSON file')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("FEC ALL FILINGS FETCHER")
    print("="*80)
    print(f"Cycle: {args.cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\nERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    # Fetch candidates from database
    print(f"\nFetching candidates for {args.cycle}...")
    candidates = fetch_candidates_from_db(args.cycle, args.limit)

    if not candidates:
        print("  No candidates found")
        return

    print(f"  Found {len(candidates)} candidates")

    if args.limit:
        print(f"  (Limited to {args.limit} for testing)")

    # Fetch filings for each candidate
    print(f"\nFetching filings...")
    print("="*80)

    all_filings = []
    candidates_with_filings = 0

    for idx, candidate in enumerate(candidates):
        candidate_id = candidate['candidate_id']
        name = candidate.get('name', 'Unknown')

        print(f"[{idx+1}/{len(candidates)}] {name} ({candidate_id})...", end=" ")

        filings = fetch_all_filings(candidate_id, args.cycle)

        if filings:
            candidates_with_filings += 1

            # Add candidate metadata to each filing
            for filing in filings:
                filing['candidate_id'] = candidate_id
                filing['name'] = name
                filing['party'] = candidate.get('party')
                filing['state'] = candidate.get('state')
                filing['district'] = candidate.get('district')
                filing['office'] = candidate.get('office')
                filing['cycle'] = args.cycle

            all_filings.extend(filings)
            print(f"✓ {len(filings)} filings")
        else:
            print("✓ (no filings)")

        # Save every 10 candidates to avoid losing progress
        if (idx + 1) % 10 == 0 and all_filings:
            print(f"\n  💾 Saving {len(all_filings)} filings to database...")
            inserted = save_to_database(all_filings, args.cycle)
            print(f"  ✓ Saved {inserted} filings\n")
            all_filings = []  # Clear after saving

    # Save remaining filings
    if all_filings:
        print(f"\n  💾 Saving final {len(all_filings)} filings to database...")
        inserted = save_to_database(all_filings, args.cycle)
        print(f"  ✓ Saved {inserted} filings")

    # Optional: save to JSON
    if args.save_json:
        json_file = f"all_filings_{args.cycle}.json"
        with open(json_file, 'w') as f:
            json.dump(all_filings, f, indent=2)
        print(f"\n✓ Saved to {json_file}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Candidates processed: {len(candidates)}")
    print(f"Candidates with filings: {candidates_with_filings}")
    print(f"Total filings collected: {len(all_filings) if args.save_json else 'saved to database'}")
    print("="*80)


if __name__ == "__main__":
    main()
