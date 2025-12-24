#!/usr/bin/env python3
"""
TEST SCRIPT: Verify backfill works correctly on a small sample
Shows before/after data to confirm we're collecting all 3 metrics correctly
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

# Test candidates - known winners and major candidates
TEST_CANDIDATES = {
    2024: [
        ('S4MI00355', 'Elissa Slotkin (MI-Sen winner)'),
        ('S4TX00722', 'Colin Allred (TX-Sen)'),
        ('S4MD00319', 'Angela Alsobrooks (MD-Sen winner)'),
        ('S4AZ00139', 'Ruben Gallego (AZ-Sen winner)'),
        ('S6FL00756', 'Rick Scott (FL-Sen incumbent)'),
    ],
    2022: [
        ('S0GA00559', 'Raphael Warnock (GA-Sen winner)'),
        ('S0AZ00350', 'Mark Kelly (AZ-Sen winner)'),
        ('S2PA00420', 'John Fetterman (PA-Sen winner)'),
        ('S6PA00274', 'Mehmet Oz (PA-Sen)'),
        ('S2GA00225', 'Herschel Walker (GA-Sen)'),
    ]
}


def get_database_data(candidate_id, cycle):
    """Get current data from our database"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}',
            'select': 'total_receipts,total_disbursements,cash_on_hand'
        },
        headers=headers_query
    )

    data = response.json()
    if data and len(data) > 0:
        return data[0]
    return None


def get_fec_data(candidate_id, cycle):
    """Get data from FEC API"""

    # Get ALL committees (no cycle filter!)
    url = f"https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/"
    response = requests.get(url, params={'api_key': FEC_API_KEY, 'per_page': 20}, timeout=30)
    time.sleep(0.5)

    committees = response.json().get('results', [])

    if not committees:
        return None

    # Get reports for first committee
    committee_id = committees[0]['committee_id']
    url = f"https://api.open.fec.gov/v1/committee/{committee_id}/reports/"
    response = requests.get(url, params={
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 20,
        'sort': '-coverage_end_date'
    }, timeout=30)
    time.sleep(0.5)

    reports = response.json().get('results', [])

    # Look for year-end report
    for report in reports:
        if report.get('report_type') == 'YE':
            return {
                'cash_on_hand': report.get('cash_on_hand_end_period'),
                'report_type': 'YE',
                'coverage_end': report.get('coverage_end_date')
            }

    # Fallback to most recent report
    if reports:
        return {
            'cash_on_hand': reports[0].get('cash_on_hand_end_period'),
            'report_type': reports[0].get('report_type'),
            'coverage_end': reports[0].get('coverage_end_date')
        }

    return None


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


def test_cycle(cycle):
    """Test backfill for a specific cycle"""

    print(f"\n{'='*100}")
    print(f"TESTING CYCLE {cycle}")
    print('='*100)

    results = []

    for candidate_id, name in TEST_CANDIDATES[cycle]:
        print(f"\n{name} ({candidate_id})")
        print("-" * 100)

        # Get current database data
        db_before = get_database_data(candidate_id, cycle)

        if db_before:
            print(f"DATABASE BEFORE:")
            print(f"  Total Raised:  ${db_before['total_receipts']:>15,.2f}")
            print(f"  Total Spent:   ${db_before['total_disbursements']:>15,.2f}")
            print(f"  Cash on Hand:  ${db_before['cash_on_hand']:>15,.2f}")
        else:
            print(f"❌ NO DATA IN DATABASE")
            continue

        # Get FEC data
        fec_data = get_fec_data(candidate_id, cycle)

        if fec_data and fec_data['cash_on_hand'] is not None:
            print(f"\nFEC API:")
            print(f"  Cash on Hand:  ${fec_data['cash_on_hand']:>15,.2f}")
            print(f"  Report Type:   {fec_data['report_type']}")
            print(f"  Coverage End:  {fec_data['coverage_end']}")

            # Update if different
            if db_before['cash_on_hand'] != fec_data['cash_on_hand']:
                success = update_database(candidate_id, cycle, fec_data['cash_on_hand'])

                if success:
                    print(f"\n✅ UPDATED cash_on_hand: ${db_before['cash_on_hand']:,.2f} → ${fec_data['cash_on_hand']:,.2f}")
                    results.append(('updated', name, db_before['cash_on_hand'], fec_data['cash_on_hand']))
                else:
                    print(f"\n❌ UPDATE FAILED")
                    results.append(('failed', name, None, None))
            else:
                print(f"\n✓ Already up to date")
                results.append(('unchanged', name, db_before['cash_on_hand'], fec_data['cash_on_hand']))
        else:
            print(f"\n⚠️  NO CASH DATA AVAILABLE FROM FEC")
            results.append(('no_data', name, None, None))

    # Summary
    print(f"\n{'='*100}")
    print(f"CYCLE {cycle} SUMMARY")
    print('='*100)

    updated = sum(1 for r in results if r[0] == 'updated')
    unchanged = sum(1 for r in results if r[0] == 'unchanged')
    no_data = sum(1 for r in results if r[0] == 'no_data')
    failed = sum(1 for r in results if r[0] == 'failed')

    print(f"Updated: {updated}")
    print(f"Already correct: {unchanged}")
    print(f"No FEC data: {no_data}")
    print(f"Failed: {failed}")


def main():
    print("="*100)
    print("BACKFILL TEST - Sample of 10 Candidates")
    print("="*100)
    print("\nThis will:")
    print("1. Show current database values (Total Raised, Total Spent, Cash on Hand)")
    print("2. Fetch year-end cash from FEC API")
    print("3. Update database if needed")
    print("4. Show results")

    test_cycle(2024)
    test_cycle(2022)

    print(f"\n{'='*100}")
    print("TEST COMPLETE")
    print('='*100)
    print("\n✓ If results look correct, we can run the full backfill overnight")
    print("✗ If results are wrong, we need to fix the script before proceeding")


if __name__ == '__main__':
    main()
