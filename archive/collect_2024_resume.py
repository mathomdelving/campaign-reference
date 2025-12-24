#!/usr/bin/env python3
"""
RESUME 2024 CYCLE COLLECTION
With improved rate limit handling and retry logic
"""

import requests
import os
from dotenv import load_dotenv
import time
import json
from datetime import datetime

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

RATE_LIMIT_DELAY = 4.0  # 4 seconds between calls
MAX_RETRIES = 5  # Maximum number of retries for rate limit errors
BACKOFF_MULTIPLIER = 2  # Exponential backoff multiplier


def make_fec_request_with_retry(url, params, max_retries=MAX_RETRIES):
    """Make FEC API request with retry logic for rate limiting"""

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            # Always sleep after request to respect rate limit
            time.sleep(RATE_LIMIT_DELAY)

            # Success
            if response.ok:
                return response

            # Rate limit error - wait and retry
            if response.status_code == 429:
                wait_time = RATE_LIMIT_DELAY * (BACKOFF_MULTIPLIER ** attempt)
                print(f"    ⚠️  Rate limit hit (429). Waiting {wait_time:.0f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue

            # Other error - log and return
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
    """Get ALL candidates for a cycle with improved error handling"""

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
    """Insert or update candidate in database"""

    record = {
        'candidate_id': candidate['candidate_id'],
        'name': candidate['name'],
        'party': candidate.get('party'),
        'state': candidate.get('state'),
        'office': candidate.get('office'),
        'district': candidate.get('district'),
        'incumbent_challenge': candidate.get('incumbent_challenge')
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/candidates",
        headers=headers_upsert,
        json=[record]
    )

    return response.status_code in [200, 201]


def get_all_committees(candidate_id):
    """Get ALL committees for a candidate"""

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
    """Get ALL reports for a committee in a cycle"""

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


def store_filings(candidate, committee_id, reports, cycle):
    """Store filings in quarterly_financials table"""

    if not reports:
        return 0

    filings = []

    for report in reports:
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
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/quarterly_financials",
            headers=headers_upsert,
            json=filings
        )

        if response.status_code in [200, 201]:
            return len(filings)

    return 0


def process_2024_cycle():
    """Process 2024 cycle with resume capability"""

    cycle = 2024

    print(f"\n{'='*80}")
    print(f"RESUMING 2024 CYCLE COLLECTION")
    print('='*80)

    # Get ALL candidates (will retry through rate limits)
    candidates = get_all_candidates(cycle, start_page=1)

    # Load existing progress to skip already processed candidates
    progress_file = 'collection_progress.json'
    processed_ids = []

    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            if '2024' in progress:
                processed_ids = progress['2024'].get('processed_ids', [])

    print(f"\n  Total candidates: {len(candidates)}")
    print(f"  Already processed: {len(processed_ids)}")
    print(f"  Remaining: {len(candidates) - len(processed_ids)}")

    candidates_added = 0
    filings_added = 0

    for i, candidate in enumerate(candidates, 1):
        candidate_id = candidate['candidate_id']

        # Skip if already processed
        if candidate_id in processed_ids:
            continue

        # Store candidate metadata
        if upsert_candidate(candidate):
            candidates_added += 1

        # Get all committees
        committees = get_all_committees(candidate_id)

        # Get all reports for each committee
        for committee in committees:
            committee_id = committee['committee_id']
            reports = get_all_reports(committee_id, cycle)

            # Store filings
            count = store_filings(candidate, committee_id, reports, cycle)
            filings_added += count

        # Update progress
        processed_ids.append(candidate_id)

        # Save progress and log every 25 candidates
        if i % 25 == 0:
            # Update progress file
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
            else:
                progress = {}

            if '2024' not in progress:
                progress['2024'] = {'started': datetime.now().isoformat()}

            progress['2024']['processed_ids'] = processed_ids
            progress['2024']['candidates_processed'] = len(processed_ids)
            progress['2024']['filings_collected'] = filings_added
            progress['2024']['last_updated'] = datetime.now().isoformat()

            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)

            print(f"    Progress: {len(processed_ids)}/{len(candidates)} candidates, {filings_added} filings")

    # Final save
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}

    progress['2024'] = {
        'started': progress.get('2024', {}).get('started', datetime.now().isoformat()),
        'completed': datetime.now().isoformat(),
        'processed_ids': processed_ids,
        'candidates_processed': len(processed_ids),
        'filings_collected': filings_added
    }

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"\n  ✅ Cycle 2024 complete:")
    print(f"     New candidates added: {candidates_added}")
    print(f"     New filings added: {filings_added}")
    print(f"     Total candidates processed: {len(processed_ids)}")


if __name__ == '__main__':
    print("="*80)
    print("2024 CYCLE COLLECTION WITH IMPROVED RATE LIMIT HANDLING")
    print("="*80)
    print("\nFeatures:")
    print("✅ Automatic retry with exponential backoff for 429 errors")
    print("✅ Resumes from where previous collection stopped")
    print("✅ Progress saved every 25 candidates")
    print("\nEstimated duration: 8-12 hours")
    print("="*80)
    print()

    start_time = datetime.now()

    try:
        process_2024_cycle()
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted. Progress has been saved.")
        print("Run this script again to resume from where you left off.")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 3600

    print(f"\n{'='*80}")
    print("COLLECTION COMPLETE")
    print('='*80)
    print(f"Duration: {duration:.1f} hours")
