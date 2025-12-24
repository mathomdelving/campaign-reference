#!/usr/bin/env python3
"""
TEST SCRIPT: Verify collection logic works correctly on sample candidates
Tests across all cycles before running full 30-50 hour collection
"""

import requests
import os
from dotenv import load_dotenv
import time
import json

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

RATE_LIMIT_DELAY = 4.0

# Test candidates across cycles
TEST_CANDIDATES = {
    2024: 'H2AZ02311',  # Kirsten Engel (AZ-02) - FIXED ID
    2022: 'H0CA25154',  # Christy Smith (CA-27) - CRITICAL TEST
    2020: 'H0IA02156',  # Rita Hart (IA-02) - FIXED ID
    2018: 'H8IA01094',  # Abby Finkenauer (IA-01)
}


def find_candidate_in_fec(candidate_id, cycle):
    """Find specific candidate in FEC API"""

    try:
        response = requests.get(
            'https://api.open.fec.gov/v1/candidates/',
            params={
                'api_key': FEC_API_KEY,
                'candidate_id': candidate_id,
                # Don't filter by election_year - just get the candidate
                'per_page': 10
            },
            timeout=30
        )
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            results = response.json().get('results', [])
            if results:
                return results[0]
    except Exception as e:
        print(f"    Error: {e}")

    return None


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
    """Get ALL committees for a candidate (no cycle filter!)"""

    try:
        response = requests.get(
            f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
            params={
                'api_key': FEC_API_KEY,
                'per_page': 100
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
    """Get ALL reports for a committee in a cycle (with pagination!)"""

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

    # Insert filings
    if filings:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/quarterly_financials",
            headers=headers_upsert,
            json=filings
        )

        if response.status_code in [200, 201]:
            return len(filings)
        else:
            print(f"      Error storing filings: {response.status_code}")
            print(f"      {response.text[:200]}")

    return 0


def verify_in_database(candidate_id, cycle):
    """Verify candidate and filings are in database"""

    # Check candidate
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/candidates",
        params={'candidate_id': f'eq.{candidate_id}', 'select': 'name,party,state'},
        headers=headers_query
    )

    candidate_exists = len(r.json()) > 0

    # Check filings
    r2 = requests.get(
        f"{SUPABASE_URL}/rest/v1/quarterly_financials",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}',
            'select': 'count'
        },
        headers={**headers_query, 'Prefer': 'count=exact'}
    )

    filing_count = int(r2.headers.get('Content-Range', '0/0').split('/')[-1])

    return candidate_exists, filing_count


def test_candidate(candidate_id, cycle, name):
    """Test full collection process for one candidate"""

    print(f"\n{'='*100}")
    print(f"Testing: {name} ({candidate_id}) - Cycle {cycle}")
    print('='*100)

    # Step 1: Find in FEC API
    print(f"\n[1] Searching FEC API...")
    candidate = find_candidate_in_fec(candidate_id, cycle)

    if not candidate:
        print(f"    ❌ Not found in FEC API for cycle {cycle}")
        return False

    print(f"    ✓ Found: {candidate['name']}")

    # Step 2: Store candidate
    print(f"\n[2] Storing candidate metadata...")
    if upsert_candidate(candidate):
        print(f"    ✓ Candidate stored")
    else:
        print(f"    ❌ Failed to store candidate")
        return False

    # Step 3: Get committees
    print(f"\n[3] Getting ALL committees...")
    committees = get_all_committees(candidate_id)
    print(f"    ✓ Found {len(committees)} committees")

    if not committees:
        print(f"    ⚠️  No committees found")
        return False

    for comm in committees:
        print(f"      - {comm['committee_id']}: {comm.get('name', 'N/A')}")

    # Step 4: Get all reports for each committee
    print(f"\n[4] Collecting ALL reports for cycle {cycle}...")
    total_reports = 0
    total_stored = 0

    for committee in committees:
        committee_id = committee['committee_id']
        reports = get_all_reports(committee_id, cycle)

        if reports:
            print(f"    Committee {committee_id}: {len(reports)} reports")

            # Store filings
            stored = store_filings(candidate, committee_id, reports, cycle)
            total_stored += stored
            total_reports += len(reports)

            # Show sample reports
            for report in reports[:3]:
                print(f"      - {report.get('report_type')}: {report.get('coverage_end_date')} - Receipts: ${report.get('total_receipts', 0):,.0f}")

    print(f"\n    ✓ Total reports found: {total_reports}")
    print(f"    ✓ Filings stored: {total_stored}")

    # Step 5: Verify in database
    print(f"\n[5] Verifying in database...")
    candidate_exists, filing_count = verify_in_database(candidate_id, cycle)

    if candidate_exists:
        print(f"    ✓ Candidate in database")
    else:
        print(f"    ❌ Candidate NOT in database")

    print(f"    ✓ Filings in database: {filing_count}")

    success = candidate_exists and filing_count > 0

    if success:
        print(f"\n✅ SUCCESS - {name} fully collected")
    else:
        print(f"\n❌ FAILED - {name} not properly stored")

    return success


def main():
    print("="*100)
    print("COLLECTION SCRIPT TEST")
    print("="*100)
    print("\nTesting collection logic on 4 candidates across 4 cycles")
    print("This will verify:")
    print("- Candidate metadata collection")
    print("- Committee discovery")
    print("- Report/filing collection (with pagination)")
    print("- Database storage")
    print("\nIMPORTANT: Each API call has 4 second delay (respects 1,000/hour limit)")
    print("="*100)

    results = []

    for cycle, candidate_id in TEST_CANDIDATES.items():
        # Find name
        names = {
            'H2AZ02311': 'Kirsten Engel',
            'H0CA25154': 'Christy Smith',
            'H0IA02156': 'Rita Hart',
            'H8IA01094': 'Abby Finkenauer'
        }

        name = names.get(candidate_id, 'Unknown')
        success = test_candidate(candidate_id, cycle, name)
        results.append((name, cycle, success))

    # Summary
    print(f"\n{'='*100}")
    print("TEST SUMMARY")
    print('='*100)

    for name, cycle, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name} ({cycle})")

    passed = sum(1 for _, _, s in results if s)
    print(f"\n{passed}/4 tests passed")

    if passed == 4:
        print("\n✅ ALL TESTS PASSED - Script is ready for full collection")
        print("You can now run: python3 collect_all_filings_complete.py")
    else:
        print("\n⚠️  Some tests failed - investigate before running full collection")


if __name__ == '__main__':
    main()
