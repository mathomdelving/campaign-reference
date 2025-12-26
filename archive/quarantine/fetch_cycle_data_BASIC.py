# NOTE: This is the non-robust version. Use scripts/collect_cycle_data.py instead.
#!/usr/bin/env python3
"""
FEC Cycle Data Collector

Collects comprehensive campaign finance data for ANY election cycle:
- Candidates (House + Senate)
- Financial summaries
- Quarterly financial reports

FOLLOWS 2-STEP WORKFLOW:
  Step 1: This script collects data → Saves to JSON files
  Step 2: Use load_to_supabase.py to load JSON → Supabase

Usage:
  python3 fetch_cycle_data.py --cycle 2022
  python3 fetch_cycle_data.py --cycle 2024

Output Files:
  - candidates_{cycle}.json
  - financials_{cycle}.json
  - quarterly_financials_{cycle}.json
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

def load_progress(cycle):
    """Load progress from previous run if it exists"""
    progress_file = f"progress_{cycle}.json"
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'last_processed_index': 0, 'financials': [], 'quarterly_financials': []}

def save_progress(cycle, index, financials, quarterly_financials):
    """Save current progress"""
    progress_file = f"progress_{cycle}.json"
    progress = {
        'last_processed_index': index,
        'financials': financials,
        'quarterly_financials': quarterly_financials,
        'last_updated': datetime.now().isoformat()
    }
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def fetch_candidates(office, cycle):
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
            response = requests.get(url, params=params, timeout=30)
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

def fetch_candidate_financials(candidate_id, cycle, retry_count=0):
    """Fetch financial totals with retry logic for rate limits"""
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

def fetch_committee_quarterly_filings(candidate_id, cycle, retry_count=0):
    """
    Fetch quarterly filings for a candidate's committee(s)
    Returns list of quarterly reports with financial data
    NOTE: This function makes 2+ API calls (committees + filings for each committee)
    """
    try:
        # Step 1: Get committee(s) for this candidate
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle
        }, timeout=10)

        # Handle rate limit
        if committees_response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_committee_quarterly_filings(candidate_id, cycle, retry_count + 1)
            else:
                return []

        if not committees_response.ok:
            return []

        # Rate limit after committees call
        time.sleep(4)

        committees = committees_response.json().get('results', [])
        all_filings = []

        # Step 2: For each committee, get filings
        for committee in committees:
            committee_id = committee.get('committee_id')

            # Get HISTORICAL designation for this cycle (not current designation!)
            # Use /committee/{id}/history/ to get the designation during the target cycle
            history_url = f"{BASE_URL}/committee/{committee_id}/history/"
            try:
                history_response = requests.get(history_url, params={
                    'api_key': FEC_API_KEY
                }, timeout=30)

                # Rate limit after history call
                time.sleep(4)

                # Default to current designation if history call fails
                designation = committee.get('designation')
                designation_full = committee.get('designation_full')

                if history_response.ok:
                    history = history_response.json().get('results', [])
                    # Find the record for our target cycle
                    for record in history:
                        if record.get('cycle') == cycle:
                            designation = record.get('designation')
                            designation_full = record.get('designation_full')
                            break
                    else:
                        # If no exact match, find most recent cycle <= target cycle
                        earlier_records = [r for r in history if r.get('cycle', 0) <= cycle]
                        if earlier_records:
                            earlier_records.sort(key=lambda x: x.get('cycle', 0), reverse=True)
                            designation = earlier_records[0].get('designation')
                            designation_full = earlier_records[0].get('designation_full')
            except:
                # If history lookup fails, use current designation as fallback
                designation = committee.get('designation')
                designation_full = committee.get('designation_full')

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',  # House/Senate candidate reports
                'sort': '-coverage_end_date',
                'per_page': 20  # Get up to 20 filings (covers multiple quarters + amendments)
            }, timeout=10)

            # Rate limit after filings call
            time.sleep(4)

            if filings_response.ok:
                filings = filings_response.json().get('results', [])

                # COLLECT ALL REPORT TYPES (not just quarterly!)
                # This includes:
                # - Quarterly: Q1, Q2, Q3, Q4, APRIL QUARTERLY, JULY QUARTERLY, OCTOBER QUARTERLY
                # - Pre-election: PRE-PRIMARY, PRE-GENERAL, PRE-CONVENTION, PRE-RUN-OFF, PRE-SPECIAL
                # - Post-election: POST-GENERAL, POST-PRIMARY, POST-RUN-OFF, POST-SPECIAL
                # - Other: YEAR-END, MID-YEAR REPORT
                # We're already filtering by form_type='F3' (House/Senate reports), so we get all relevant filings
                # ONLY exclude TERMINATION reports (candidates who shut down)

                for filing in filings:
                    report_type = filing.get('report_type_full', '')

                    # Skip termination reports only
                    if 'TERMINATION' in report_type.upper():
                        continue

                    receipts = filing.get('total_receipts')
                    disbursements = filing.get('total_disbursements')

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
        print(f"\n    Error fetching quarterly filings for {candidate_id}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Collect FEC campaign finance data for a cycle')
    parser.add_argument('--cycle', type=int, required=True, help='Election cycle (e.g., 2022, 2024, 2026)')
    args = parser.parse_args()

    cycle = args.cycle

    print("\n" + "="*60)
    print("FEC CYCLE DATA COLLECTOR")
    print(f"Cycle: {cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n⚠️  FOLLOWING 2-STEP WORKFLOW:")
    print("  Step 1: Collect data → JSON files (this script)")
    print("  Step 2: Review JSON → Load to Supabase (separate)")

    # Load previous progress if it exists
    progress = load_progress(cycle)
    start_index = progress['last_processed_index']
    financials = progress['financials']
    quarterly_financials = progress.get('quarterly_financials', [])

    if start_index > 0:
        print(f"\n✓ Resuming from candidate #{start_index + 1}")
        print(f"✓ Already have {len(financials)} summary records")
        print(f"✓ Already have {len(quarterly_financials)} quarterly records")

    # Load or fetch candidates
    candidates_file = f"candidates_{cycle}.json"
    if os.path.exists(candidates_file):
        print(f"\n✓ Loading existing candidates from {candidates_file}")
        with open(candidates_file, 'r') as f:
            all_candidates = json.load(f)
    else:
        print("\n\nSTEP 1: Fetching candidates...")
        house_candidates = fetch_candidates('H', cycle)
        senate_candidates = fetch_candidates('S', cycle)
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
    print(f"\n\nSTEP 2: Fetching financial data (summary + quarterly)...")
    print(f"{'='*60}")
    print(f"Rate limit: 1,000 requests/hour (FEC API limit)")
    print(f"Processing with 4 second delay between EACH API call")
    print(f"Each candidate: 3+ API calls (totals + committees + filings)")
    print(f"  = ~12-16 seconds per candidate minimum")
    print(f"Estimated time: Several hours for {len(all_candidates)} candidates")
    print(f"{'='*60}\n")

    total = len(all_candidates)
    save_frequency = 50

    for idx in range(start_index, total):
        candidate = all_candidates[idx]
        candidate_id = candidate.get('candidate_id')
        name = candidate.get('name', 'Unknown')

        print(f"  [{idx+1}/{total}] {name} ({candidate_id})...", end=" ")

        # Fetch summary data (totals) - 1 API call
        financial_data = fetch_candidate_financials(candidate_id, cycle)
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
                'cash_on_hand': financial_data.get('last_cash_on_hand_end_period'),
                'coverage_start_date': financial_data.get('coverage_start_date'),
                'coverage_end_date': financial_data.get('coverage_end_date'),
                'last_report_year': financial_data.get('last_report_year'),
                'last_report_type': financial_data.get('last_report_type_full'),
                'cycle': cycle
            }
            financials.append(combined)

        # Fetch quarterly filings - makes 2+ API calls internally with 4s delays between each
        filings = fetch_committee_quarterly_filings(candidate_id, cycle)

        if filings:
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
                    'cycle': cycle
                }
                quarterly_financials.append(quarterly_record)
            print(f"✓ ({len(filings)} quarterly filings)")
        else:
            print("✓ (no quarterly data)")

        if (idx + 1) % save_frequency == 0:
            save_progress(cycle, idx + 1, financials, quarterly_financials)
            print(f"\n  💾 Progress saved: {len(financials)} summary, {len(quarterly_financials)} quarterly (processed {idx + 1}/{total})\n")

    # Save final output files
    financials_file = f"financials_{cycle}.json"
    with open(financials_file, 'w') as f:
        json.dump(financials, f, indent=2)

    quarterly_file = f"quarterly_financials_{cycle}.json"
    with open(quarterly_file, 'w') as f:
        json.dump(quarterly_financials, f, indent=2)

    # Clean up progress file
    progress_file = f"progress_{cycle}.json"
    if os.path.exists(progress_file):
        os.remove(progress_file)

    print(f"\n{'='*60}")
    print(f"✓ Saved financial data to {financials_file}")
    print(f"  Candidates with financial summary: {len(financials)}/{total}")
    print(f"\n✓ Saved quarterly data to {quarterly_file}")
    print(f"  Total quarterly filings: {len(quarterly_financials)}")
    print(f"{'='*60}")

    print("\nSUMMARY:")
    candidates_with_money = [f for f in financials if f.get('total_receipts', 0) and f.get('total_receipts', 0) > 0]
    print(f"  Candidates who have raised money: {len(candidates_with_money)}")

    if candidates_with_money:
        total_raised = sum(f.get('total_receipts', 0) for f in candidates_with_money)
        print(f"  Total money raised: ${total_raised:,.2f}")

    # Quarterly summary
    candidates_with_quarterly = len(set(q['candidate_id'] for q in quarterly_financials))
    print(f"  Candidates with quarterly data: {candidates_with_quarterly}")

    print("\n✅ COLLECTION COMPLETE!")
    print(f"\n📋 NEXT STEP:")
    print(f"  1. Review the JSON files to verify data looks correct")
    print(f"  2. Load to Supabase: python3 scripts/data-loading/load_to_supabase.py")
    print()

if __name__ == "__main__":
    main()
