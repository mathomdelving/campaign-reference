#!/usr/bin/env python3
"""
FEC CYCLE DATA COLLECTION - PRODUCTION SCRIPT

Collects comprehensive FEC campaign finance data for any election cycle.

Features:
- Automatic retry with exponential backoff for rate limit (429) errors
- Resume capability (automatically skips already-processed candidates)
- Progress tracking (saved every 25 candidates)
- Handles timeouts and network errors gracefully
- Can be safely interrupted and resumed

Usage:
    python3 scripts/collect_fec_cycle_data.py --cycle 2024
    python3 scripts/collect_fec_cycle_data.py --cycle 2016,2014,2012

Environment Variables Required:
    FEC_API_KEY - Your FEC API key
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_KEY - Your Supabase service key

Data Collected:
    - candidates: Candidate metadata (name, party, state, office, etc.)
    - quarterly_financials: All filings with financial data
      (receipts, disbursements, cash on hand per report period)

Rate Limiting:
    - FEC API: 1,000 calls per hour
    - Script: 4 seconds between calls (900 calls/hour, safely under limit)
    - Retry: Up to 5 attempts with exponential backoff on 429 errors

Estimated Duration:
    - ~5-8 hours per cycle with 2,000-5,000 candidates
    - Depends on number of candidates and committees

Author: Claude Code
Date: November 2025
"""

import requests
import os
import sys
import argparse
from dotenv import load_dotenv
import time
import json
from datetime import datetime

load_dotenv()

# API Configuration
FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Validate environment variables
if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("ERROR: Missing required environment variables")
    print("Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
    sys.exit(1)

# Supabase headers
headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

# Rate limiting configuration
RATE_LIMIT_DELAY = 4.0  # 4 seconds = 900 calls/hour
MAX_RETRIES = 5  # Maximum retries for rate limit errors
BACKOFF_MULTIPLIER = 2  # Exponential backoff multiplier

# Progress tracking
PROGRESS_FILE = 'collection_progress.json'


def make_fec_request_with_retry(url, params, max_retries=MAX_RETRIES):
    """
    Make FEC API request with automatic retry logic for rate limiting.

    Handles:
    - 429 (rate limit) errors with exponential backoff
    - Network timeouts and connection errors
    - Other HTTP errors

    Returns:
        Response object if successful, None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            # Always respect rate limit
            time.sleep(RATE_LIMIT_DELAY)

            # Success
            if response.ok:
                return response

            # Rate limit error - wait and retry
            if response.status_code == 429:
                wait_time = RATE_LIMIT_DELAY * (BACKOFF_MULTIPLIER ** attempt)
                print(f"    ⚠️  Rate limit (429). Waiting {wait_time:.0f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue

            # Other error - log and return
            if response.status_code not in [404]:  # 404 is normal for candidates without committees
                print(f"    Error: {response.status_code}")
            return response

        except Exception as e:
            print(f"    Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RATE_LIMIT_DELAY * (BACKOFF_MULTIPLIER ** attempt))
                continue
            return None

    print(f"    ❌ Failed after {max_retries} attempts")
    return None


def get_all_candidates(cycle, start_page=1):
    """
    Fetch ALL candidates for a cycle from FEC API with pagination.

    Args:
        cycle: Election year (e.g., 2024, 2022, 2020)
        start_page: Page number to start from (for resuming)

    Returns:
        List of candidate dictionaries
    """
    print(f"\n  Fetching ALL candidates for {cycle} (starting from page {start_page})...")

    candidates = []
    page = start_page

    while True:
        params = {
            'api_key': FEC_API_KEY,
            'election_year': cycle,
            'per_page': 100,
            'page': page
        }

        response = make_fec_request_with_retry(
            'https://api.open.fec.gov/v1/candidates/',
            params
        )

        if not response or not response.ok:
            print(f"    Stopping at page {page} due to persistent errors")
            break

        data = response.json()
        results = data.get('results', [])

        if not results:
            break

        candidates.extend(results)

        if page % 10 == 0:
            print(f"    Page {page}: {len(candidates)} candidates so far...")

        # Check pagination
        pagination = data.get('pagination', {})
        if not pagination.get('pages') or page >= pagination['pages']:
            break

        page += 1

    print(f"  ✓ Found {len(candidates)} total candidates")
    return candidates


def upsert_candidate(candidate):
    """
    Insert or update candidate in database.
    Uses merge-duplicates to handle updates gracefully.

    Returns:
        True if successful, False otherwise
    """
    record = {
        'candidate_id': candidate['candidate_id'],
        'name': candidate['name'],
        'party': candidate.get('party'),
        'state': candidate.get('state'),
        'office': candidate.get('office'),
        'district': candidate.get('district'),
        'incumbent_challenge': candidate.get('incumbent_challenge')
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/candidates",
            headers=headers_upsert,
            json=[record]
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"    Error upserting candidate {candidate['candidate_id']}: {e}")
        return False


def get_committee_designation(committee_id, cycle):
    """
    Get committee designation for a specific cycle from history endpoint.

    Returns:
        Designation code (e.g., 'P' for Principal, 'A' for Authorized, 'U' for Unauthorized)
    """
    response = make_fec_request_with_retry(
        f'https://api.open.fec.gov/v1/committee/{committee_id}/history/',
        params={
            'api_key': FEC_API_KEY,
            'per_page': 100
        }
    )

    if response and response.ok:
        history = response.json().get('results', [])
        # Find designation for this specific cycle
        for record in history:
            if record.get('cycle') == cycle:
                return record.get('designation')

    return None


def get_all_committees(candidate_id):
    """
    Get all committees associated with a candidate.

    Returns:
        List of committee dictionaries
    """
    response = make_fec_request_with_retry(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
        params={
            'api_key': FEC_API_KEY,
            'per_page': 20
        }
    )

    if response and response.ok:
        return response.json().get('results', [])

    return []


def get_all_reports(committee_id, cycle):
    """
    Get all financial reports for a committee in a specific cycle.

    Returns:
        List of report dictionaries
    """
    reports = []
    page = 1

    while True:
        response = make_fec_request_with_retry(
            f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
            params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'per_page': 100,
                'page': page,
                'sort': '-coverage_end_date'
            }
        )

        if not response or not response.ok:
            break

        data = response.json()
        results = data.get('results', [])

        if not results:
            break

        reports.extend(results)

        # Check pagination
        pagination = data.get('pagination', {})
        if not pagination.get('pages') or page >= pagination['pages']:
            break

        page += 1

    return reports


def upsert_committee_designation(committee_id, cycle, designation, committee_name, committee_type, candidate_id):
    """
    Upsert committee designation data to committee_designations table.
    Uses normalized table structure (not inline column).
    """
    if not designation:
        return False

    # Map designation codes to names
    designation_names = {
        'P': 'Principal campaign committee',
        'A': 'Authorized by a candidate',
        'U': 'Unauthorized',
        'B': 'Lobbyist/Registrant PAC',
        'D': 'Leadership PAC',
        'J': 'Joint fundraiser'
    }

    # Map committee types
    committee_type_names = {
        'H': 'House',
        'S': 'Senate',
        'P': 'Presidential',
        'X': 'Non-qualified',
        'Y': 'Qualified',
        'Z': 'National Party Nonfederal',
        'N': 'PAC - Nonqualified',
        'Q': 'PAC - Qualified',
        'O': 'Independent Expenditure (Super PAC)',
        'V': 'Hybrid PAC',
        'W': 'Single Candidate Independent Expenditure'
    }

    # NOTE: Do NOT include generated columns (is_principal, is_authorized, is_joint_fundraising, is_leadership_pac)
    # PostgreSQL computes these automatically based on designation value
    record = {
        'committee_id': committee_id,
        'cycle': cycle,
        'designation': designation,
        'designation_name': designation_names.get(designation),
        'committee_type': committee_type,
        'committee_type_name': committee_type_names.get(committee_type),
        'committee_name': committee_name,
        'candidate_id': candidate_id,
        'source': 'fec_api'
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/committee_designations?on_conflict=committee_id,cycle",
            headers=headers_upsert,
            json=[record]
        )

        if response.status_code in [200, 201]:
            return True
        else:
            print(f"    ⚠️  Failed to store designation for {committee_id}: {response.status_code}")
            print(f"       Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"    ⚠️  Exception storing designation for {committee_id}: {str(e)[:200]}")
        return False


def store_filings(candidate, committee_id, reports, cycle):
    """
    Store financial reports in quarterly_financials table.
    Uses PERIOD amounts (not YTD) for accurate timeseries data.

    Returns:
        Number of filings successfully stored
    """
    if not reports:
        return 0

    filings = []

    for report in reports:
        # Use PERIOD amounts for accurate per-quarter data
        receipts_period = float(report.get('total_receipts_period', 0) or 0)
        disbursements_period = float(report.get('total_disbursements_period', 0) or 0)

        filing = {
            'candidate_id': candidate['candidate_id'],
            'name': candidate['name'],
            'party': candidate.get('party_full', candidate.get('party')),
            'state': candidate.get('state'),
            'district': candidate.get('district'),
            'office': candidate.get('office'),
            'cycle': cycle,
            'committee_id': committee_id,
            'filing_id': report.get('report_key'),
            'report_type': report.get('report_type'),
            'coverage_start_date': report.get('coverage_start_date', '').split('T')[0] if report.get('coverage_start_date') else None,
            'coverage_end_date': report.get('coverage_end_date', '').split('T')[0] if report.get('coverage_end_date') else None,
            'total_receipts': receipts_period,
            'total_disbursements': disbursements_period,
            'cash_beginning': float(report.get('cash_on_hand_beginning_period', 0) or 0),
            'cash_ending': float(report.get('cash_on_hand_end_period', 0) or 0),
            'is_amendment': report.get('amendment_indicator') == 'A'
        }

        filings.append(filing)

    # Batch insert
    if filings:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/quarterly_financials?on_conflict=candidate_id,cycle,report_type,coverage_start_date,coverage_end_date",
                headers=headers_upsert,
                json=filings
            )

            if response.status_code in [200, 201]:
                return len(filings)
            else:
                print(f"    ❌ Failed to store filings: {response.status_code} - {response.text[:200]}")
                return -1  # Return -1 to indicate failure
        except Exception as e:
            print(f"    ❌ Exception storing filings: {e}")
            return -1  # Return -1 to indicate failure

    return 0  # No filings to store (success)


def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def process_cycle(cycle):
    """
    Process all candidates and filings for a single cycle.
    Automatically resumes from where it left off if interrupted.

    Args:
        cycle: Election year (e.g., 2024, 2022, 2020)
    """
    print(f"\n{'='*80}")
    print(f"PROCESSING CYCLE {cycle}")
    print('='*80)

    # Get ALL candidates (will retry through rate limits)
    candidates = get_all_candidates(cycle, start_page=1)

    # Load existing progress to skip already-processed candidates
    progress = load_progress()
    cycle_key = str(cycle)

    if cycle_key not in progress:
        progress[cycle_key] = {
            'started': datetime.now().isoformat(),
            'processed_ids': [],
            'failed_candidates': []
        }

    processed_ids = progress[cycle_key].get('processed_ids', [])
    failed_candidates = progress[cycle_key].get('failed_candidates', [])

    print(f"\n  Total candidates: {len(candidates)}")
    print(f"  Already processed: {len(processed_ids)}")
    if failed_candidates:
        print(f"  Failed (will retry): {len(failed_candidates)}")
    print(f"  Remaining: {len(candidates) - len(processed_ids)}")

    if len(candidates) == len(processed_ids) and len(failed_candidates) == 0:
        print(f"\n  ✅ Cycle {cycle} already complete!")
        return

    candidates_added = 0
    filings_added = 0
    candidates_failed = 0

    for i, candidate in enumerate(candidates, 1):
        candidate_id = candidate['candidate_id']

        # Skip if already processed
        if candidate_id in processed_ids:
            continue

        # Store candidate metadata
        if upsert_candidate(candidate):
            candidates_added += 1

        # Track if this candidate had any failures
        had_failure = False

        # Get all committees
        committees = get_all_committees(candidate_id)

        # Get all reports for each committee
        for committee in committees:
            committee_id = committee['committee_id']
            committee_name = committee.get('name', '')
            committee_type = committee.get('committee_type', '')

            # Get designation for this committee in this cycle
            designation = get_committee_designation(committee_id, cycle)

            # Store designation in committee_designations table
            if designation:
                designation_success = upsert_committee_designation(
                    committee_id,
                    cycle,
                    designation,
                    committee_name,
                    committee_type,
                    candidate_id
                )
                if not designation_success:
                    # Mark for retry if designation storage fails
                    had_failure = True
                    print(f"    ⚠️  Designation storage failed for {candidate_id}, will retry")

            # Get reports
            reports = get_all_reports(committee_id, cycle)

            # Store filings (quarterly_financials table - no inline designation)
            count = store_filings(candidate, committee_id, reports, cycle)

            if count == -1:
                # Failure storing filings
                had_failure = True
                print(f"    ⚠️  Will retry {candidate_id} in next run")
            elif count > 0:
                filings_added += count

        # Only mark as processed if no failures occurred
        if had_failure:
            candidates_failed += 1
            if candidate_id not in failed_candidates:
                failed_candidates.append(candidate_id)
        else:
            processed_ids.append(candidate_id)
            # Remove from failed list if it was there
            if candidate_id in failed_candidates:
                failed_candidates.remove(candidate_id)

        # Save progress and log every 25 candidates
        if (len(processed_ids) + len(failed_candidates)) % 25 == 0:
            progress[cycle_key]['processed_ids'] = processed_ids
            progress[cycle_key]['failed_candidates'] = failed_candidates
            progress[cycle_key]['candidates_processed'] = len(processed_ids)
            progress[cycle_key]['candidates_failed'] = len(failed_candidates)
            progress[cycle_key]['filings_collected'] = filings_added
            progress[cycle_key]['last_updated'] = datetime.now().isoformat()
            save_progress(progress)

            print(f"    Progress: {len(processed_ids)}/{len(candidates)} candidates, {filings_added} filings, {len(failed_candidates)} failed")

    # Final save
    progress[cycle_key]['completed'] = datetime.now().isoformat()
    progress[cycle_key]['processed_ids'] = processed_ids
    progress[cycle_key]['failed_candidates'] = failed_candidates
    progress[cycle_key]['candidates_processed'] = len(processed_ids)
    progress[cycle_key]['candidates_failed'] = len(failed_candidates)
    progress[cycle_key]['filings_collected'] = filings_added
    save_progress(progress)

    print(f"\n  ✅ Cycle {cycle} complete:")
    print(f"     New candidates added: {candidates_added}")
    print(f"     New filings added: {filings_added}")
    print(f"     Total candidates processed: {len(processed_ids)}")

    if failed_candidates:
        print(f"\n  ⚠️  {len(failed_candidates)} candidates failed to store filings:")
        for failed_id in failed_candidates[:10]:
            print(f"     - {failed_id}")
        if len(failed_candidates) > 10:
            print(f"     ... and {len(failed_candidates) - 10} more")
        print(f"\n  To retry failed candidates, run the script again:")
        print(f"     python3 scripts/collect_fec_cycle_data.py --cycle {cycle}")
    else:
        print(f"     No failures!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Collect FEC campaign finance data for election cycles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect single cycle
  python3 scripts/collect_fec_cycle_data.py --cycle 2024

  # Collect multiple cycles
  python3 scripts/collect_fec_cycle_data.py --cycle 2016,2014,2012

  # Run in background
  nohup python3 -u scripts/collect_fec_cycle_data.py --cycle 2024 > collection.log 2>&1 &
        """
    )

    parser.add_argument(
        '--cycle',
        required=True,
        help='Election cycle(s) to collect (e.g., 2024 or 2016,2014,2012)'
    )

    args = parser.parse_args()

    # Parse cycles
    cycles = [int(c.strip()) for c in args.cycle.split(',')]

    print("="*80)
    print("FEC CAMPAIGN FINANCE DATA COLLECTION")
    print("="*80)
    print(f"\nCycles to process: {', '.join(map(str, cycles))}")
    print("\nFeatures:")
    print("✅ Automatic retry with exponential backoff for rate limit errors")
    print("✅ Resumes from where previous collection stopped")
    print("✅ Progress saved every 25 candidates")
    print("\nRate limiting: 4 seconds between calls (900 calls/hour)")
    print("Estimated: 5-8 hours per cycle")
    print("="*80)
    print()

    start_time = datetime.now()

    try:
        for cycle in cycles:
            process_cycle(cycle)
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted. Progress has been saved.")
        print("Run this script again to resume from where you left off.")
        sys.exit(0)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 3600

    print(f"\n{'='*80}")
    print("COLLECTION COMPLETE")
    print('='*80)
    print(f"Duration: {duration:.1f} hours")
    print(f"Cycles processed: {', '.join(map(str, cycles))}")


if __name__ == '__main__':
    main()
