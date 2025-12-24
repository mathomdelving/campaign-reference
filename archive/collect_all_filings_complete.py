#!/usr/bin/env python3
"""
COMPREHENSIVE FEC DATA COLLECTION
Collects ALL candidates and ALL their filings for complete timeseries data

This is the ONE script that gets us everything we need:
- All candidates (metadata)
- All filings/reports (quarterly, monthly, pre/post election, etc.)
- Standardized across all cycles (2018-2026)

Output:
- candidates table: candidate metadata
- quarterly_financials table: every filing with timeseries data
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

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

RATE_LIMIT_DELAY = 4.0  # 4 seconds = 900 calls/hour (safely under 1,000/hour limit)
# CRITICAL: FEC allows 1,000 API CALLS per hour (not 1,000 records!)
# Each call can return 100 records via pagination
# This collection will take 30-50 HOURS due to rate limiting

PROGRESS_FILE = 'collection_progress.json'


def load_progress():
    """Load progress from previous run"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_progress(progress):
    """Save progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def get_all_candidates(cycle, office=None):
    """Get ALL candidates for a cycle from FEC API (with pagination)"""

    print(f"\n  Fetching ALL candidates for {cycle}...")

    candidates = []
    page = 1

    while True:
        params = {
            'api_key': FEC_API_KEY,
            'election_year': cycle,
            'per_page': 100,
            'page': page
        }

        if office:
            params['office'] = office

        try:
            response = requests.get(
                'https://api.open.fec.gov/v1/candidates/',
                params=params,
                timeout=30
            )
            time.sleep(RATE_LIMIT_DELAY)

            if not response.ok:
                print(f"    Error fetching page {page}: {response.status_code}")
                break

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            candidates.extend(results)

            if page % 10 == 0:
                print(f"    Page {page}: {len(candidates)} candidates so far...")

            # Check if there are more pages
            pagination = data.get('pagination', {})
            if not pagination.get('pages') or page >= pagination['pages']:
                break

            page += 1

        except Exception as e:
            print(f"    Error on page {page}: {e}")
            break

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

    try:
        response = requests.get(
            f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
            params={
                'api_key': FEC_API_KEY,
                'per_page': 20
            },
            timeout=30
        )
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            return response.json().get('results', [])

    except Exception as e:
        pass

    return []


def get_all_reports(committee_id, cycle):
    """Get ALL reports for a committee in a cycle"""

    reports = []
    page = 1

    while True:
        try:
            response = requests.get(
                f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
                params={
                    'api_key': FEC_API_KEY,
                    'cycle': cycle,
                    'per_page': 100,
                    'page': page,
                    'sort': '-coverage_end_date'
                },
                timeout=30
            )
            time.sleep(RATE_LIMIT_DELAY)

            if not response.ok:
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

        except Exception as e:
            break

    return reports


def store_filings(candidate, committee_id, reports, cycle):
    """Store filings in quarterly_financials table"""

    if not reports:
        return 0

    filings = []

    for report in reports:
        # Extract financial data using PERIOD amounts (not YTD)
        # VERIFIED: Sum of all _period amounts = cycle total from /totals/ endpoint
        # - total_receipts_period = activity during THIS filing period
        # - total_receipts_ytd = cumulative from Jan 1 of calendar year (not what we want)
        # For timeseries visualization and accurate cycle totals, use _period amounts
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


def process_cycle(cycle):
    """Process all candidates and filings for a cycle"""

    print(f"\n{'='*80}")
    print(f"PROCESSING CYCLE {cycle}")
    print('='*80)

    # Load progress
    progress = load_progress()
    cycle_key = str(cycle)

    if cycle_key not in progress:
        progress[cycle_key] = {
            'started': datetime.now().isoformat(),
            'candidates_processed': 0,
            'filings_collected': 0,
            'processed_ids': []
        }

    # Get ALL candidates for this cycle
    candidates = get_all_candidates(cycle)

    print(f"\n  Processing {len(candidates)} candidates...")

    candidates_added = 0
    filings_added = 0

    for i, candidate in enumerate(candidates, 1):
        candidate_id = candidate['candidate_id']

        # Skip if already processed
        if candidate_id in progress[cycle_key]['processed_ids']:
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
        progress[cycle_key]['processed_ids'].append(candidate_id)
        progress[cycle_key]['candidates_processed'] = i
        progress[cycle_key]['filings_collected'] = filings_added

        # Save progress every 25 candidates
        if i % 25 == 0:
            save_progress(progress)
            print(f"    Progress: {i}/{len(candidates)} candidates, {filings_added} filings")

    progress[cycle_key]['completed'] = datetime.now().isoformat()
    save_progress(progress)

    print(f"\n  ✅ Cycle {cycle} complete:")
    print(f"     Candidates: {candidates_added}")
    print(f"     Filings: {filings_added}")


def main():
    print("="*80)
    print("COMPREHENSIVE FEC DATA COLLECTION")
    print("="*80)
    print("\nThis will collect ALL candidates and ALL filings for:")
    print("- Cycles: 2018, 2020, 2022, 2024, 2026")
    print("- Data: Every quarterly, monthly, and special report")
    print("\nIMPORTANT:")
    print("- FEC API Limit: 1,000 CALLS per hour (not 1,000 records)")
    print("- Rate: 1 call every 4 seconds = 900 calls/hour")
    print("- Each call can return 100 records with pagination")
    print("\nEstimated: 30,000-50,000 total API calls needed")
    print("Duration: 30-50 HOURS (will run over multiple days)")
    print("="*80)

    start_time = datetime.now()

    cycles = [2026, 2024, 2022, 2020, 2018]

    for cycle in cycles:
        process_cycle(cycle)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 3600

    print(f"\n{'='*80}")
    print("COLLECTION COMPLETE")
    print('='*80)
    print(f"Duration: {duration:.1f} hours")
    print("\nNext: Verify data completeness")


if __name__ == '__main__':
    main()
