#!/usr/bin/env python3
"""
Test backfill on 4 specific candidates across 4 cycles
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_supabase = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}


def find_candidate(name_search, cycle):
    """Search for a candidate by name"""
    url = 'https://api.open.fec.gov/v1/candidates/search/'
    response = requests.get(url, params={
        'api_key': FEC_API_KEY,
        'q': name_search,
        'per_page': 10
    }, timeout=30)

    results = response.json().get('results', [])

    # Find candidate with matching cycle
    for cand in results:
        if cycle in cand.get('election_years', []):
            return cand['candidate_id'], cand['name']

    # If no exact cycle match, return first result
    if results:
        return results[0]['candidate_id'], results[0]['name']

    return None, None


def get_database_data(candidate_id, cycle):
    """Get current data from our database"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}',
            'select': 'candidate_id,cycle,total_receipts,total_disbursements,cash_on_hand'
        },
        headers=headers_query
    )

    data = response.json()
    if data and len(data) > 0:
        return data[0]
    return None


def get_fec_cash(candidate_id, cycle):
    """Get cash_on_hand from FEC API (mimics backfill script logic)"""

    # Step 1: Get ALL committees (no cycle filter)
    url = f"https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/"
    response = requests.get(url, params={
        'api_key': FEC_API_KEY,
        'per_page': 20
    }, timeout=30)
    time.sleep(0.5)

    committees = response.json().get('results', [])

    if not committees:
        return None, "No committees found"

    # Step 2: For each committee, look for reports in this cycle
    for committee in committees:
        committee_id = committee['committee_id']

        # Get reports for this cycle
        url = f"https://api.open.fec.gov/v1/committee/{committee_id}/reports/"
        response = requests.get(url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': 20,
            'sort': '-coverage_end_date'
        }, timeout=30)
        time.sleep(0.5)

        reports = response.json().get('results', [])

        if not reports:
            continue

        # Look for year-end (YE) report
        for report in reports:
            if report.get('report_type') == 'YE':
                cash = report.get('cash_on_hand_end_period')
                if cash is not None:
                    return cash, f"YE report - Committee {committee_id}"

        # Fallback to most recent report
        for report in reports:
            cash = report.get('cash_on_hand_end_period')
            if cash is not None:
                return cash, f"{report.get('report_type')} report - Committee {committee_id}"

    return None, "No reports with cash data found"


def update_database(candidate_id, cycle, cash_on_hand):
    """Update cash_on_hand in database"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}'
        },
        headers=headers_supabase,
        json={'cash_on_hand': cash_on_hand}
    )
    return response.status_code in [200, 204]


def test_candidate(name, cycle):
    """Test full backfill process for one candidate"""

    print(f"\n{'='*100}")
    print(f"{name} - Cycle {cycle}")
    print('='*100)

    # Step 1: Find candidate ID
    print(f"\n[1] Searching FEC API for '{name}'...")
    candidate_id, full_name = find_candidate(name, cycle)

    if not candidate_id:
        print(f"❌ Candidate not found in FEC API")
        return False

    print(f"✓ Found: {full_name} ({candidate_id})")

    # Step 2: Check our database
    print(f"\n[2] Checking our database (financial_summary table)...")
    db_data = get_database_data(candidate_id, cycle)

    if not db_data:
        print(f"❌ No data in our database for cycle {cycle}")
        return False

    print(f"✓ Database record found:")
    print(f"    Total Receipts:    ${db_data['total_receipts']:>15,.2f}")
    print(f"    Total Disbursed:   ${db_data['total_disbursements']:>15,.2f}")
    print(f"    Cash on Hand:      ${db_data['cash_on_hand']:>15,.2f}")

    # Step 3: Get cash from FEC API
    print(f"\n[3] Fetching cash_on_hand from FEC API...")
    fec_cash, source = get_fec_cash(candidate_id, cycle)

    if fec_cash is None:
        print(f"⚠️  {source}")
        return False

    print(f"✓ Found cash_on_hand: ${fec_cash:,.2f}")
    print(f"  Source: {source}")

    # Step 4: Update if needed
    if db_data['cash_on_hand'] == fec_cash:
        print(f"\n[4] ✓ Database already up to date")
        return True

    print(f"\n[4] Updating database...")
    print(f"    ${db_data['cash_on_hand']:,.2f} → ${fec_cash:,.2f}")

    success = update_database(candidate_id, cycle, fec_cash)

    if success:
        print(f"✅ SUCCESS - Database updated")

        # Verify
        verify = get_database_data(candidate_id, cycle)
        if verify and verify['cash_on_hand'] == fec_cash:
            print(f"✓ Verified: Database now shows ${verify['cash_on_hand']:,.2f}")
            return True
        else:
            print(f"❌ Verification failed")
            return False
    else:
        print(f"❌ FAILED - Update unsuccessful")
        return False


def main():
    print("="*100)
    print("BACKFILL TEST - 4 Candidates Across 4 Cycles")
    print("="*100)
    print("\nThis will test the complete backfill process:")
    print("1. Find candidate in FEC API")
    print("2. Check our database (financial_summary table)")
    print("3. Fetch cash_on_hand from FEC API")
    print("4. Update database")
    print("5. Verify update")

    tests = [
        ("Engel", 2024),
        ("Smith", 2022),
        ("Hart", 2020),
        ("Finkenauer", 2018)
    ]

    results = []

    for name, cycle in tests:
        success = test_candidate(name, cycle)
        results.append((name, cycle, success))
        time.sleep(1)

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
        print("\n✅ ALL TESTS PASSED - Ready for overnight backfill")
    else:
        print("\n⚠️  Some tests failed - investigate before running full backfill")


if __name__ == '__main__':
    main()
