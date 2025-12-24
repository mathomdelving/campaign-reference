#!/usr/bin/env python3
"""
FEC Historical Cycle Data Collection Script - TEMPLATE
=======================================================

⚠️  THIS IS A TEMPLATE FILE - DO NOT MODIFY DIRECTLY ⚠️

When collecting data for a new cycle, COPY this file to scripts/data-collection/
and work with the copy. This ensures the template remains pristine for future use.

Example:
    cp scripts/templates/fetch_historical_cycle_TEMPLATE.py scripts/data-collection/fetch_2020.py
    python3 scripts/data-collection/fetch_2020.py --cycle 2020

See scripts/templates/README.md for detailed instructions.

============================================

Flexible script to collect any historical election cycle (2018, 2020, 2022, etc.)

FEATURES:
1. ✅ Uses cycle parameter to get all candidates for that cycle
2. ✅ Uses /committee/{id}/history/ to identify principal committee for the cycle
3. ✅ Captures ALL filing types (quarterly, pre-primary, pre-general, post-general, year-end)
4. ✅ Deduplicates amendments (keeps most recent for each period)
5. ✅ Saves to JSON files first (quality control before Supabase upload)

USAGE:
    python3 fetch_historical_cycle.py --cycle 2022
    python3 fetch_historical_cycle.py --cycle 2020 --dry-run

DATA COLLECTED:
- candidates_{cycle}.json: All candidate metadata
- financials_{cycle}.json: Summary totals from /candidate/{id}/totals/
- quarterly_financials_{cycle}.json: ALL filings from principal committee

Once validated, load to Supabase using load_2024_to_supabase.py (adapt for cycle).

Author: Campaign Reference Team
Date: November 2025
"""

import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

# CYCLE and PROGRESS_FILE will be set in main() based on command-line arguments
#
# ⚠️  CRITICAL: Python default parameters are evaluated at FUNCTION DEFINITION time,
# not at call time. This means that default parameters like `cycle=CYCLE` will capture
# the value of CYCLE when the function is DEFINED (None), not when main() sets it.
#
# SOLUTION: Always pass CYCLE explicitly when calling functions. Do not rely on defaults.
# Example:
#   ❌ BAD:  fetch_candidate_financials(candidate_id)  # Uses cycle=None
#   ✅ GOOD: fetch_candidate_financials(candidate_id, CYCLE)  # Uses correct cycle
#
CYCLE = None
PROGRESS_FILE = None

if not FEC_API_KEY:
    print("ERROR: FEC_API_KEY not found in .env file!")
    print("Please create a .env file with your API key.")
    exit(1)

def load_progress():
    """Load progress from previous run if it exists"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_processed_index': 0, 'financials': [], 'quarterly_financials': []}

def save_progress(index, financials, quarterly_financials):
    """Save current progress"""
    progress = {
        'last_processed_index': index,
        'financials': financials,
        'quarterly_financials': quarterly_financials,
        'last_updated': datetime.now().isoformat()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def fetch_candidates(office, cycle=CYCLE):
    """
    Fetch candidates for a specific office and cycle.

    ⚠️  WARNING: Do not rely on the default cycle=CYCLE parameter!
    Always pass the cycle explicitly when calling this function.
    See module-level comment for details on Python default parameter gotcha.
    """
    print(f"\n{'='*60}")
    print(f"Fetching {('House' if office == 'H' else 'Senate')} candidates for {cycle}...")
    print(f"{'='*60}")
    
    all_candidates = []
    page = 1
    
    while True:
        url = f"{BASE_URL}/candidates/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'office': office,
            'per_page': 100,
            'page': page,
            'sort': 'name'
        }
        
        try:
            print(f"  Fetching page {page}...", end=" ")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print("No more results.")
                break
            
            all_candidates.extend(results)
            print(f"✓ Got {len(results)} candidates")
            
            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break
            
            page += 1
            time.sleep(0.25)
            
        except requests.exceptions.RequestException as e:
            print(f"\n  ERROR fetching page {page}: {e}")
            break
    
    print(f"\n  Total {('House' if office == 'H' else 'Senate')} candidates: {len(all_candidates)}")
    return all_candidates

def fetch_candidate_financials(candidate_id, cycle=CYCLE, retry_count=0):
    """
    Fetch financial totals with retry logic for rate limits.

    ⚠️  WARNING: Do not rely on the default cycle=CYCLE parameter!
    Always pass the cycle explicitly when calling this function.
    See module-level comment for details on Python default parameter gotcha.
    """
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        # Handle rate limit specifically
        if response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT HIT! Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return fetch_candidate_financials(candidate_id, cycle, retry_count + 1)
            else:
                print(f"\n  ❌ Rate limit persists after {retry_count} retries. Skipping.")
                return None

        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching financials for {candidate_id}: {e}")
        return None

def get_committee_history(committee_id):
    """Get historical data for a committee across all cycles"""
    try:
        url = f"{BASE_URL}/committee/{committee_id}/history/"
        response = requests.get(url, params={'api_key': FEC_API_KEY}, timeout=10)
        time.sleep(4)

        if response.ok:
            return response.json().get('results', [])
        return []
    except:
        return []


def get_principal_committee_for_cycle(candidate_id, cycle):
    """
    Identify principal committee for a specific cycle using committee history.

    This handles cases where committees change roles between cycles.
    Example: C00264697 was 'P' (Principal) in 2024 but 'U' (Unauthorized) in 2026.

    Returns: committee_id of principal committee for that cycle, or None
    """
    # Get all committees associated with candidate
    committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
    committees_response = requests.get(committees_url, params={
        'api_key': FEC_API_KEY,
        'per_page': 100
    }, timeout=10)
    time.sleep(4)

    if not committees_response.ok:
        return None

    committees = committees_response.json().get('results', [])

    # Check ALL committees to find which was principal for this specific cycle
    for committee in committees:
        committee_id = committee['committee_id']

        # Get historical data for this committee
        history = get_committee_history(committee_id)

        # Find the record for the cycle we care about
        for record in history:
            if record.get('cycle') == cycle and record.get('designation') == 'P':
                return committee_id

    return None


def fetch_committee_quarterly_filings(candidate_id, cycle=CYCLE, retry_count=0):
    """
    Fetch ALL filings for a candidate's PRINCIPAL committee for the cycle.

    ⚠️  WARNING: Do not rely on the default cycle=CYCLE parameter!
    Always pass the cycle explicitly when calling this function.
    See module-level comment for details on Python default parameter gotcha.

    FIXES:
    1. Uses committee history to identify principal committee for the cycle
    2. Captures ALL filing types (F3 regular + F3N 48-hour notices)
    3. Deduplicates amendments CORRECTLY (with proper amendment order)

    Returns list of filing records with financial data
    """
    try:
        # Step 1: Find principal committee for this cycle
        principal_committee_id = get_principal_committee_for_cycle(candidate_id, cycle)

        if not principal_committee_id:
            return []

        # Step 2: Get ALL F3 and F3N filings from principal committee
        all_filings = []

        # Fetch F3 (regular reports) and F3N (48-hour notices)
        for form_type in ['F3', 'F3N']:
            page = 1

            while True:
                filings_url = f"{BASE_URL}/committee/{principal_committee_id}/filings/"
                filings_response = requests.get(filings_url, params={
                    'api_key': FEC_API_KEY,
                    'cycle': cycle,
                    'form_type': form_type,
                    'sort': '-coverage_end_date',
                    'per_page': 100,
                    'page': page
                }, timeout=30)

                time.sleep(4)

                if not filings_response.ok:
                    break

                data = filings_response.json()
                filings = data.get('results', [])

                if not filings:
                    break

                all_filings.extend(filings)

                # IMPORTANT: Use pagination metadata, not result count!
                # Checking len(filings) < 100 is WRONG - can stop early or loop forever
                pagination = data.get('pagination', {})
                total_pages = pagination.get('pages', 1)

                if page >= total_pages:
                    break

                page += 1

        # Step 3: Deduplicate amendments - keep most recent for each period
        # Group by (report_type, coverage_start_date, coverage_end_date)
        filing_groups = {}

        # Amendment order mapping (FEC uses: blank/N/NEW for original, then A, B, C...)
        amendment_order_map = {
            '': 0, 'N': 0, 'NEW': 0,
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7,
            'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13
        }

        for filing in all_filings:
            report_type = filing.get('report_type_full', '')
            coverage_start = filing.get('coverage_start_date')
            coverage_end = filing.get('coverage_end_date')

            # Skip if missing required fields
            if not all([report_type, coverage_start, coverage_end]):
                continue

            key = (report_type, coverage_start, coverage_end)

            # Keep the filing with the latest amendment_indicator
            if key not in filing_groups:
                filing_groups[key] = filing
            else:
                # Compare amendment indicators using proper ordering
                existing_amendment = filing_groups[key].get('amendment_indicator', '').upper()
                new_amendment = filing.get('amendment_indicator', '').upper()

                existing_order = amendment_order_map.get(existing_amendment, 0)
                new_order = amendment_order_map.get(new_amendment, 0)

                # Higher order = more recent amendment
                if new_order > existing_order:
                    filing_groups[key] = filing
                elif new_order == existing_order:
                    # If same amendment level, use most recent receipt_date
                    existing_date = filing_groups[key].get('receipt_date', '')
                    new_date = filing.get('receipt_date', '')
                    if new_date > existing_date:
                        filing_groups[key] = filing

        # Step 4: Convert to our format
        deduplicated_filings = []
        for filing in filing_groups.values():
            deduplicated_filings.append({
                'committee_id': principal_committee_id,
                'filing_id': filing.get('file_number'),
                'report_type': filing.get('report_type_full', ''),
                'coverage_start_date': filing.get('coverage_start_date'),
                'coverage_end_date': filing.get('coverage_end_date'),
                'total_receipts': filing.get('total_receipts', 0) or 0,
                'total_disbursements': filing.get('total_disbursements', 0) or 0,
                'cash_beginning': filing.get('cash_on_hand_beginning_period', 0) or 0,
                'cash_ending': filing.get('cash_on_hand_end_period', 0) or 0,
                'is_amendment': filing.get('amendment_indicator', '') != ''
            })

        return deduplicated_filings

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching filings for {candidate_id}: {e}")
        return []

def main():
    global CYCLE, PROGRESS_FILE

    import argparse
    parser = argparse.ArgumentParser(description='FEC Historical Cycle Data Collection Script')
    parser.add_argument('--cycle', type=int, required=True,
                       help='Election cycle to collect (e.g., 2022, 2020, 2018)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test on first 50 candidates only (does not save files)')
    args = parser.parse_args()

    # Set global variables based on command-line arguments
    CYCLE = args.cycle
    PROGRESS_FILE = f"progress_{CYCLE}_simple.json"

    print("\n" + "="*60)
    print(f"FEC DATA FETCHER - Collecting {CYCLE} Cycle")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("MODE: DRY RUN (first 50 candidates, no file save)")
    print("="*60)
    
    # Load previous progress if it exists
    progress = load_progress()
    start_index = progress['last_processed_index']
    financials = progress['financials']
    quarterly_financials = progress.get('quarterly_financials', [])

    if start_index > 0:
        print(f"\n✓ Resuming from candidate #{start_index + 1}")
        print(f"✓ Already have {len(financials)} summary records")
        print(f"✓ Already have {len(quarterly_financials)} quarterly records")
    
    # Load or fetch candidates
    candidates_file = f"candidates_{CYCLE}.json"

    if args.dry_run:
        # DRY RUN: Only fetch first 50 candidates (1 page)
        print("\n⚠️  DRY RUN MODE: Fetching only first 50 candidates (not using cached file)")
        print("\nSTEP 1: Fetching candidates (limited to 50)...")

        # Fetch just 1 page (100 candidates) from House
        url = f"{BASE_URL}/candidates/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': CYCLE,
            'office': 'H',
            'per_page': 50,
            'page': 1,
            'sort': 'name'
        }
        response = requests.get(url, params=params)
        all_candidates = response.json().get('results', [])[:50]

        print(f"✓ Fetched {len(all_candidates)} candidates for dry run")

    elif os.path.exists(candidates_file):
        print(f"\n✓ Loading existing candidates from {candidates_file}")
        with open(candidates_file, 'r') as f:
            all_candidates = json.load(f)
    else:
        print("\nSTEP 1: Fetching candidates...")
        # IMPORTANT: Must pass CYCLE explicitly (see warning at top of file)
        house_candidates = fetch_candidates('H', CYCLE)
        senate_candidates = fetch_candidates('S', CYCLE)
        all_candidates = house_candidates + senate_candidates

        print(f"\n{'='*60}")
        print(f"TOTAL CANDIDATES: {len(all_candidates)}")
        print(f"  House: {len(house_candidates)}")
        print(f"  Senate: {len(senate_candidates)}")
        print(f"{'='*60}")

        with open(candidates_file, 'w') as f:
            json.dump(all_candidates, f, indent=2)
        print(f"\n✓ Saved candidates to {candidates_file}")
    
    # Fetch financial data with progress tracking
    print(f"\nSTEP 2: Fetching financial data (summary + quarterly)...")
    print(f"{'='*60}")
    print(f"Rate limit: 1,000 requests/hour (FEC API limit)")
    print(f"Processing with 4 second delay between EACH API call")
    print(f"Each candidate: 3 API calls (totals + committees + filings)")
    print(f"  = 12 seconds per candidate minimum")
    print(f"  = ~300 candidates/hour = ~17-18 hours for 5,185 candidates")
    print(f"Estimated completion time: Tomorrow afternoon/evening")
    print(f"{'='*60}\n")

    total = len(all_candidates)
    save_frequency = 50

    # Track failed candidates for retry
    failed_candidates = []

    for idx in range(start_index, total):
        candidate = all_candidates[idx]
        candidate_id = candidate.get('candidate_id')
        name = candidate.get('name', 'Unknown')

        print(f"  [{idx+1}/{total}] {name} ({candidate_id})...", end=" ")

        try:
            # Fetch summary data (totals) - 1 API call
            # IMPORTANT: Must pass CYCLE explicitly (see warning at top of file)
            financial_data = fetch_candidate_financials(candidate_id, CYCLE)
            time.sleep(4)  # Rate limit: 4 seconds after totals call

            if financial_data:
                combined = {
                    'candidate_id': candidate_id,
                    'name': name,
                    'party': candidate.get('party_full'),
                    'state': candidate.get('state'),
                    'district': candidate.get('district'),
                    'office': candidate.get('office_full'),
                    'total_receipts': financial_data.get('receipts'),
                    'total_disbursements': financial_data.get('disbursements'),
                    'cash_on_hand': financial_data.get('last_cash_on_hand_end_period'),  # FIXED: Use correct field name
                    'coverage_start_date': financial_data.get('coverage_start_date'),
                    'coverage_end_date': financial_data.get('coverage_end_date'),
                    'last_report_year': financial_data.get('last_report_year'),
                    'last_report_type': financial_data.get('last_report_type_full'),
                    'cycle': CYCLE
                }
                financials.append(combined)

            # Fetch quarterly filings - makes 2+ API calls internally with 4s delays between each
            # IMPORTANT: Must pass CYCLE explicitly (see warning at top of file)
            filings = fetch_committee_quarterly_filings(candidate_id, CYCLE)

            if filings:
                # VALIDATION: Compare sum of filings vs API totals
                if financial_data:
                    filings_total_receipts = sum(f['total_receipts'] for f in filings)
                    api_total_receipts = financial_data.get('receipts', 0)

                    if api_total_receipts > 0:
                        pct_diff = abs(filings_total_receipts - api_total_receipts) / api_total_receipts * 100

                        # Log significant mismatches for review
                        if pct_diff > 5:
                            print(f"\n    ⚠️  VALIDATION: Filing sum ${filings_total_receipts:,.0f} vs API ${api_total_receipts:,.0f} ({pct_diff:.1f}% diff)")

                for filing in filings:
                    quarterly_record = {
                        'candidate_id': candidate_id,
                        'name': name,
                        'party': candidate.get('party_full'),
                        'state': candidate.get('state'),
                        'district': candidate.get('district'),
                        'office': candidate.get('office_full'),
                        'committee_id': filing['committee_id'],
                        'filing_id': filing['filing_id'],
                        'report_type': filing['report_type'],
                        'coverage_start_date': filing['coverage_start_date'],
                        'coverage_end_date': filing['coverage_end_date'],
                        'total_receipts': filing['total_receipts'],
                        'total_disbursements': filing['total_disbursements'],
                        'cash_beginning': filing['cash_beginning'],
                        'cash_ending': filing['cash_ending'],
                        'is_amendment': filing['is_amendment'],
                        'cycle': CYCLE
                    }
                    quarterly_financials.append(quarterly_record)
                print(f"✓ ({len(filings)} filings)")
            else:
                print("✓ (no filing data)")

        except Exception as e:
            # Catch ANY unexpected error processing this candidate
            print(f"❌ FAILED: {str(e)[:80]}")
            failed_candidates.append({
                'candidate_id': candidate_id,
                'name': name,
                'error': str(e),
                'index': idx
            })
            # Continue to next candidate instead of crashing

        if (idx + 1) % save_frequency == 0:
            save_progress(idx + 1, financials, quarterly_financials)
            print(f"\n  💾 Progress saved: {len(financials)} summary, {len(quarterly_financials)} quarterly (processed {idx + 1}/{total})\n")

            # Also save failed candidates log
            if failed_candidates and not args.dry_run:
                with open(f"failed_candidates_{CYCLE}.json", 'w') as f:
                    json.dump(failed_candidates, f, indent=2)
    
    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - Files NOT saved")
        print(f"{'='*60}")
    else:
        financials_file = f"financials_{CYCLE}.json"
        with open(financials_file, 'w') as f:
            json.dump(financials, f, indent=2)

        quarterly_file = f"quarterly_financials_{CYCLE}.json"
        with open(quarterly_file, 'w') as f:
            json.dump(quarterly_financials, f, indent=2)

        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    if not args.dry_run:
        print(f"\n{'='*60}")
        print(f"✓ Saved financial data to {financials_file}")
        print(f"  Candidates with financial summary: {len(financials)}/{total}")
        print(f"\n✓ Saved quarterly data to {quarterly_file}")
        print(f"  Total quarterly filings: {len(quarterly_financials)}")
        print(f"{'='*60}")

    print("\nSUMMARY:")
    candidates_with_money = [f for f in financials if f.get('total_receipts', 0) > 0]
    print(f"  Candidates who have raised money: {len(candidates_with_money)}")

    if candidates_with_money:
        total_raised = sum(f.get('total_receipts', 0) for f in candidates_with_money)
        print(f"  Total money raised: ${total_raised:,.2f}")

    # Quarterly summary
    candidates_with_quarterly = len(set(q['candidate_id'] for q in quarterly_financials))
    print(f"  Candidates with quarterly data: {candidates_with_quarterly}")

    if failed_candidates:
        print(f"\n⚠️  {len(failed_candidates)} candidates failed during processing:")
        for fc in failed_candidates[:10]:  # Show first 10
            print(f"     - {fc['name']} ({fc['candidate_id']}): {fc['error'][:60]}")
        if len(failed_candidates) > 10:
            print(f"     ... and {len(failed_candidates) - 10} more")
        if not args.dry_run:
            print(f"\n  Failed candidates saved to: failed_candidates_{CYCLE}.json")
            print("  You can retry these later if needed.")

    if args.dry_run:
        print("\n✓ DRY RUN COMPLETE!")
        print(f"  Processed {total} candidates")
        print(f"  Ready for full run: python3 {__file__}")
    else:
        print("\n✓ DATA COLLECTION COMPLETE!")
        print(f"  Check your files:")
        print(f"    - {candidates_file}")
        print(f"    - {financials_file}")
        print(f"    - {quarterly_file}")
    print()

if __name__ == "__main__":
    main()