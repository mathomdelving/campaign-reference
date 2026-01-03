#!/usr/bin/env python3
"""
ROBUST FEC Cycle Data Collector - Ironclad Edition

This is an enhanced version with comprehensive error handling:
✓ Tracks failures separately from "no data" cases
✓ Automatically retries failed candidates
✓ Survives restarts by persisting failure state
✓ Distinguishes between legitimate "no financial data" vs actual errors
✓ Includes HISTORICAL committee designation fields (P, A, J, D, etc.)
✓ Uses /committee/{id}/history/ to get contemporaneous designations for the target cycle

Key Features:
1. DUAL TRACKING: Separate tracking for "failed" vs "no_data"
2. AUTO-RETRY: Failed candidates automatically retried at end
3. RESUME-SAFE: Can restart from crashes without losing progress
4. DETAILED LOGGING: Every error categorized and logged
5. HISTORICAL DESIGNATIONS: Captures designation from target cycle, not current state

FOLLOWS 2-STEP WORKFLOW:
  Step 1: This script collects data → Saves to JSON files
  Step 2: Use load_to_supabase.py to load JSON → Supabase

Usage:
  python3 fetch_cycle_data_robust.py --cycle 2022
  python3 fetch_cycle_data_robust.py --cycle 2024

Output Files:
  - candidates_{cycle}.json
  - financials_{cycle}.json
  - quarterly_financials_{cycle}.json
  - failures_{cycle}.json  ← NEW! Tracks all errors
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

class RobustProgress:
    """
    Enhanced progress tracker that distinguishes between:
    - processed: Successfully attempted (data or no data)
    - failed: Errors that need retry
    - no_data: Candidates with legitimately no financial data
    """
    def __init__(self, cycle):
        self.cycle = cycle
        self.progress_file = f"progress_{cycle}_robust.json"
        self.data = self._load()

    def _load(self):
        """Load progress from previous run if it exists"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'last_processed_index': 0,
            'financials': [],
            'quarterly_financials': [],
            'failed_candidates': [],  # NEW: Track failures
            'no_data_candidates': [],  # NEW: Track legitimate "no data"
            'retry_count': 0  # NEW: Track how many retry passes we've done
        }

    def save(self):
        """Save current progress"""
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_financial(self, record):
        """Add a successful financial record"""
        self.data['financials'].append(record)

    def add_quarterly(self, record):
        """Add a quarterly financial record"""
        self.data['quarterly_financials'].append(record)

    def mark_failed(self, candidate_id, name, error_type, error_msg):
        """Mark a candidate as failed (needs retry)"""
        failure = {
            'candidate_id': candidate_id,
            'name': name,
            'error_type': error_type,
            'error_msg': error_msg,
            'timestamp': datetime.now().isoformat(),
            'retry_count': self.data.get('retry_count', 0)
        }
        # Don't add duplicates
        existing = [f for f in self.data['failed_candidates']
                   if f['candidate_id'] == candidate_id]
        if not existing:
            self.data['failed_candidates'].append(failure)

    def mark_no_data(self, candidate_id, name):
        """Mark a candidate as legitimately having no data"""
        if candidate_id not in self.data['no_data_candidates']:
            self.data['no_data_candidates'].append({
                'candidate_id': candidate_id,
                'name': name,
                'timestamp': datetime.now().isoformat()
            })

    def increment_index(self):
        """Move to next candidate"""
        self.data['last_processed_index'] += 1

    def clear_failures(self):
        """Clear failed candidates list (called before retry pass)"""
        self.data['failed_candidates'] = []

    def increment_retry_count(self):
        """Increment retry pass counter"""
        self.data['retry_count'] = self.data.get('retry_count', 0) + 1


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
            # For candidate fetching, this is critical - retry once
            if page == 1:
                print("  Retrying in 10 seconds...")
                time.sleep(10)
                continue
            break

    print(f"\n  Total {('House' if office == 'H' else 'Senate')} candidates: {len(all_candidates)}")
    return all_candidates


def fetch_candidate_financials(candidate_id, cycle, retry_count=0):
    """
    Fetch financial totals with enhanced error tracking
    Returns: (data, error_type, error_msg)
    - data: Financial data dict or None
    - error_type: "rate_limit", "timeout", "network", "server", or None
    - error_msg: Detailed error message or None
    """
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        # Handle rate limit specifically
        if response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT HIT! Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return fetch_candidate_financials(candidate_id, cycle, retry_count + 1)
            else:
                error_msg = f"Rate limit persists after {retry_count} retries"
                print(f"\n  ❌ {error_msg}")
                return (None, "rate_limit", error_msg)

        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            return (results[0], None, None)
        else:
            # No results = legitimate "no data", not an error
            return (None, None, None)

    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout after 30s: {str(e)}"
        print(f"\n  ⚠️  TIMEOUT: {error_msg}")
        return (None, "timeout", error_msg)

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"\n  ⚠️  CONNECTION ERROR: {error_msg}")
        return (None, "network", error_msg)

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {response.status_code}: {str(e)}"
        print(f"\n  ⚠️  HTTP ERROR: {error_msg}")
        return (None, "server", error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"\n  ⚠️  ERROR: {error_msg}")
        return (None, "network", error_msg)


def fetch_committee_quarterly_filings(candidate_id, cycle, retry_count=0):
    """
    Fetch quarterly filings for a candidate's committee(s)
    Returns: (filings_list, error_type, error_msg)
    - filings_list: List of filing dicts or []
    - error_type: "rate_limit", "timeout", "network", "server", or None
    - error_msg: Detailed error message or None
    """
    try:
        # Step 1: Get committee(s) for this candidate
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle
        }, timeout=30)

        # Handle rate limit
        if committees_response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_committee_quarterly_filings(candidate_id, cycle, retry_count + 1)
            else:
                error_msg = f"Rate limit persists after {retry_count} retries"
                return ([], "rate_limit", error_msg)

        if not committees_response.ok:
            error_msg = f"Committee fetch failed: HTTP {committees_response.status_code}"
            return ([], "server", error_msg)

        # Rate limit after committees call (targeting 6000 req/hour)
        time.sleep(0.1)

        committees = committees_response.json().get('results', [])
        all_filings = []

        # Step 2: For each committee, get filings
        for committee in committees:
            committee_id = committee.get('committee_id')
            committee_type = committee.get('committee_type')
            committee_type_full = committee.get('committee_type_full')

            # Get HISTORICAL designation for this cycle (not current designation!)
            # Use /committee/{id}/history/ to get the designation during the target cycle
            history_url = f"{BASE_URL}/committee/{committee_id}/history/"
            history_response = requests.get(history_url, params={
                'api_key': FEC_API_KEY
            }, timeout=30)

            # Rate limit after history call (targeting 6000 req/hour)
            time.sleep(0.1)

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

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',  # House/Senate candidate reports
                'sort': '-coverage_end_date',
                'per_page': 20  # Get up to 20 filings (covers multiple quarters + amendments)
            }, timeout=30)

            # Rate limit after filings call (targeting 6000 req/hour)
            time.sleep(0.1)

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
                        'is_amendment': filing.get('is_amended', False),
                        'designation': designation,
                        'designation_full': designation_full,
                        'committee_type': committee_type,
                        'committee_type_full': committee_type_full
                    })

        return (all_filings, None, None)

    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout: {str(e)}"
        return ([], "timeout", error_msg)

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        return ([], "network", error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        return ([], "network", error_msg)


def process_candidate(candidate, cycle, progress):
    """
    Process a single candidate and track results
    Returns: success (bool)
    """
    candidate_id = candidate.get('candidate_id')
    name = candidate.get('name', 'Unknown')

    print(f"  {name} ({candidate_id})...", end=" ")

    has_data = False
    has_error = False

    # Fetch summary data (totals) - 1 API call
    financial_data, fin_error_type, fin_error_msg = fetch_candidate_financials(candidate_id, cycle)
    time.sleep(0.1)  # Rate limit: targeting 6000 req/hour

    if fin_error_type:
        # This is an actual error - mark for retry
        progress.mark_failed(candidate_id, name, f"financials_{fin_error_type}", fin_error_msg)
        has_error = True
    elif financial_data:
        # Success - we got financial data
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
        progress.add_financial(combined)
        has_data = True

    # Fetch quarterly filings - makes 2+ API calls internally with 4s delays between each
    filings, qtr_error_type, qtr_error_msg = fetch_committee_quarterly_filings(candidate_id, cycle)

    if qtr_error_type:
        # This is an actual error - mark for retry
        progress.mark_failed(candidate_id, name, f"quarterly_{qtr_error_type}", qtr_error_msg)
        has_error = True
    elif filings:
        # Success - we got quarterly data
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
                'designation': filing.get('designation'),
                'designation_full': filing.get('designation_full'),
                'committee_type': filing.get('committee_type'),
                'committee_type_full': filing.get('committee_type_full'),
                'cycle': cycle
            }
            progress.add_quarterly(quarterly_record)
        has_data = True
        print(f"✓ ({len(filings)} quarterly filings)")

    # Determine final status
    if has_error:
        print("❌ FAILED (will retry)")
        return False
    elif has_data:
        if not filings:
            print("✓ (summary only, no quarterly)")
        return True
    else:
        # No data AND no errors = legitimate "no data"
        progress.mark_no_data(candidate_id, name)
        print("✓ (no financial data)")
        return True


def main():
    parser = argparse.ArgumentParser(description='Robust FEC campaign finance data collector')
    parser.add_argument('--cycle', type=int, required=True, help='Election cycle (e.g., 2022, 2024, 2026)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry passes for failed candidates')
    args = parser.parse_args()

    cycle = args.cycle
    max_retries = args.max_retries

    print("\n" + "="*60)
    print("ROBUST FEC CYCLE DATA COLLECTOR - IRONCLAD EDITION")
    print(f"Cycle: {cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n✅ ENHANCED FEATURES:")
    print("  • Tracks failures separately from 'no data' cases")
    print("  • Automatically retries failed candidates")
    print("  • Survives restarts without losing progress")
    print("  • Includes committee designation fields (P, A, J, D)")
    print("\n⚠️  FOLLOWING 2-STEP WORKFLOW:")
    print("  Step 1: Collect data → JSON files (this script)")
    print("  Step 2: Review JSON → Load to Supabase (separate)")

    # Load progress
    progress = RobustProgress(cycle)
    start_index = progress.data['last_processed_index']

    if start_index > 0:
        print(f"\n✓ Resuming from candidate #{start_index + 1}")
        print(f"✓ Already have {len(progress.data['financials'])} summary records")
        print(f"✓ Already have {len(progress.data['quarterly_financials'])} quarterly records")
        print(f"✓ {len(progress.data['failed_candidates'])} candidates need retry")
        print(f"✓ {len(progress.data['no_data_candidates'])} candidates with no data")

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

    # Main collection loop
    print(f"\n\nSTEP 2: Fetching financial data (summary + quarterly)...")
    print(f"{'='*60}")
    print(f"Rate limit: 7,000 requests/hour (targeting 6,000 to leave headroom)")
    print(f"Processing with 0.1 second delay between API calls")
    print(f"Each candidate: 3+ API calls (totals + committees + filings)")
    print(f"  = ~2 seconds per candidate")
    print(f"Estimated time: ~{len(all_candidates) * 2.5 / 3600:.1f} hours for {len(all_candidates)} candidates")
    print(f"{'='*60}\n")

    total = len(all_candidates)
    save_frequency = 50

    # Process remaining candidates
    for idx in range(start_index, total):
        candidate = all_candidates[idx]
        print(f"[{idx+1}/{total}] ", end="")

        process_candidate(candidate, cycle, progress)
        progress.increment_index()

        if (idx + 1) % save_frequency == 0:
            progress.save()
            print(f"\n  💾 Progress saved: {len(progress.data['financials'])} summary, "
                  f"{len(progress.data['quarterly_financials'])} quarterly, "
                  f"{len(progress.data['failed_candidates'])} failures "
                  f"(processed {idx + 1}/{total})\n")

    # Save after main loop
    progress.save()

    # RETRY FAILED CANDIDATES
    retry_pass = 0
    while progress.data['failed_candidates'] and retry_pass < max_retries:
        retry_pass += 1
        failed_list = progress.data['failed_candidates'].copy()

        print(f"\n\n{'='*60}")
        print(f"RETRY PASS #{retry_pass}: {len(failed_list)} failed candidates")
        print(f"{'='*60}\n")

        progress.clear_failures()
        progress.increment_retry_count()

        # Find full candidate objects for failed IDs
        failed_ids = {f['candidate_id'] for f in failed_list}
        retry_candidates = [c for c in all_candidates if c.get('candidate_id') in failed_ids]

        for idx, candidate in enumerate(retry_candidates):
            print(f"[RETRY {idx+1}/{len(retry_candidates)}] ", end="")
            process_candidate(candidate, cycle, progress)

            if (idx + 1) % 25 == 0:
                progress.save()
                print(f"\n  💾 Retry progress saved\n")

        progress.save()

        if not progress.data['failed_candidates']:
            print(f"\n✅ All failures resolved on retry pass #{retry_pass}!")
            break

    # Save final output files
    print(f"\n\n{'='*60}")
    print("SAVING FINAL OUTPUT FILES")
    print(f"{'='*60}")

    financials_file = f"financials_{cycle}.json"
    with open(financials_file, 'w') as f:
        json.dump(progress.data['financials'], f, indent=2)
    print(f"✓ Saved {financials_file}: {len(progress.data['financials'])} records")

    quarterly_file = f"quarterly_financials_{cycle}.json"
    with open(quarterly_file, 'w') as f:
        json.dump(progress.data['quarterly_financials'], f, indent=2)
    print(f"✓ Saved {quarterly_file}: {len(progress.data['quarterly_financials'])} records")

    # Save failures for manual review
    if progress.data['failed_candidates']:
        failures_file = f"failures_{cycle}.json"
        with open(failures_file, 'w') as f:
            json.dump(progress.data['failed_candidates'], f, indent=2)
        print(f"⚠️  Saved {failures_file}: {len(progress.data['failed_candidates'])} persistent failures")

    # Save no-data list for transparency
    no_data_file = f"no_data_{cycle}.json"
    with open(no_data_file, 'w') as f:
        json.dump(progress.data['no_data_candidates'], f, indent=2)
    print(f"✓ Saved {no_data_file}: {len(progress.data['no_data_candidates'])} candidates")

    # Clean up progress file
    if os.path.exists(progress.progress_file):
        os.remove(progress.progress_file)
        print(f"✓ Cleaned up {progress.progress_file}")

    # Final summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total candidates processed: {total}")
    print(f"  ✓ With financial data: {len(progress.data['financials'])}")
    print(f"  ✓ With quarterly data: {len(set(q['candidate_id'] for q in progress.data['quarterly_financials']))}")
    print(f"  • No financial data: {len(progress.data['no_data_candidates'])}")
    if progress.data['failed_candidates']:
        print(f"  ❌ Persistent failures: {len(progress.data['failed_candidates'])}")
        print(f"     (See {failures_file} for details)")
    else:
        print(f"  ✅ Zero failures - 100% success rate!")

    candidates_with_money = [f for f in progress.data['financials']
                            if f.get('total_receipts', 0) and f.get('total_receipts', 0) > 0]
    if candidates_with_money:
        total_raised = sum(f.get('total_receipts', 0) for f in candidates_with_money)
        print(f"\nMoney raised by {len(candidates_with_money)} candidates: ${total_raised:,.2f}")

    print("\n✅ COLLECTION COMPLETE!")
    print(f"\n📋 NEXT STEPS:")
    print(f"  1. Review the JSON files to verify data looks correct")
    print(f"  2. Load to Supabase:")
    print(f"     python3 scripts/data-loading/load_to_supabase.py")
    if progress.data['failed_candidates']:
        print(f"  3. Review {failures_file} and manually investigate failures")
    print()

if __name__ == "__main__":
    main()
