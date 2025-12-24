#!/usr/bin/env python3
"""
FINAL VERIFICATION before multi-day collection
Ensure we're getting the RIGHT data that matches FEC totals
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

def test_candidate(candidate_id, cycle, name):
    """Test that we can get accurate totals for a candidate"""

    print(f"\n{'='*80}")
    print(f"{name} ({candidate_id}) - Cycle {cycle}")
    print('='*80)

    # 1. Get FEC API /totals/ endpoint (ground truth)
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
        params={'api_key': FEC_API_KEY, 'cycle': cycle, 'per_page': 1},
        timeout=30
    )

    totals = response.json().get('results', [])
    if not totals:
        print("❌ No totals found in FEC API")
        return False

    expected_receipts = totals[0].get('receipts', 0)
    expected_disbursements = totals[0].get('disbursements', 0)
    expected_cash = totals[0].get('last_cash_on_hand_end_period', 0)

    print(f"\n[GROUND TRUTH] FEC API /totals/ endpoint:")
    print(f"  Receipts:      ${expected_receipts:>15,.2f}")
    print(f"  Disbursements: ${expected_disbursements:>15,.2f}")
    print(f"  Cash on Hand:  ${expected_cash:>15,.2f}")

    # 2. Get ALL committees for this candidate
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
        params={'api_key': FEC_API_KEY, 'per_page': 20},
        timeout=30
    )

    committees = response.json().get('results', [])
    print(f"\n[COMMITTEES] Found {len(committees)} committee(s):")
    for comm in committees:
        print(f"  {comm['committee_id']}: {comm.get('name', 'N/A')} (Type: {comm.get('committee_type')}, Designation: {comm.get('designation')})")

    # 3. For each committee, get the FINAL report (YE or 30G) and check if totals match
    print(f"\n[REPORTS] Checking final reports from each committee:")

    all_found_receipts = []
    all_found_disbursements = []
    all_found_cash = []

    for committee in committees:
        committee_id = committee['committee_id']

        response = requests.get(
            f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
            params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'per_page': 20,
                'sort': '-coverage_end_date'
            },
            timeout=30
        )

        reports = response.json().get('results', [])

        if not reports:
            print(f"  {committee_id}: No reports found")
            continue

        # Find the report with MAXIMUM YTD values (represents cycle total)
        # Different report types (30G, YE, Q3, etc.) have different YTD values
        max_receipts = 0
        max_disbursements = 0
        max_cash = 0
        max_report_type = None

        for report in reports:
            r_ytd = float(report.get('total_receipts_ytd', 0) or 0)
            d_ytd = float(report.get('total_disbursements_ytd', 0) or 0)
            c = float(report.get('cash_on_hand_end_period', 0) or 0)

            if r_ytd > max_receipts:
                max_receipts = r_ytd
                max_report_type = report.get('report_type')
            if d_ytd > max_disbursements:
                max_disbursements = d_ytd
            if c > max_cash:
                max_cash = c

        all_found_receipts.append(max_receipts)
        all_found_disbursements.append(max_disbursements)
        all_found_cash.append(max_cash)

        print(f"  {committee_id} ({len(reports)} reports, max from {max_report_type}): R=${max_receipts:,.0f}, D=${max_disbursements:,.0f}, C=${max_cash:,.0f}")

    # 4. Compare with expected
    print(f"\n[COMPARISON]")

    # The highest receipt/disbursement should be close to the totals endpoint
    max_receipts = max(all_found_receipts) if all_found_receipts else 0
    max_disbursements = max(all_found_disbursements) if all_found_disbursements else 0
    max_cash = max(all_found_cash) if all_found_cash else 0

    receipt_diff = abs(max_receipts - expected_receipts)
    disbursement_diff = abs(max_disbursements - expected_disbursements)
    cash_diff = abs(max_cash - expected_cash)

    print(f"  Expected Receipts:      ${expected_receipts:>15,.2f}")
    print(f"  Found (highest):        ${max_receipts:>15,.2f}")
    print(f"  Difference:             ${receipt_diff:>15,.2f}")
    print()
    print(f"  Expected Disbursements: ${expected_disbursements:>15,.2f}")
    print(f"  Found (highest):        ${max_disbursements:>15,.2f}")
    print(f"  Difference:             ${disbursement_diff:>15,.2f}")
    print()
    print(f"  Expected Cash:          ${expected_cash:>15,.2f}")
    print(f"  Found (highest):        ${max_cash:>15,.2f}")
    print(f"  Difference:             ${cash_diff:>15,.2f}")

    # Allow 5% variance
    receipt_ok = receipt_diff < (expected_receipts * 0.05) if expected_receipts > 0 else receipt_diff == 0
    disbursement_ok = disbursement_diff < (expected_disbursements * 0.05) if expected_disbursements > 0 else disbursement_diff == 0
    cash_ok = cash_diff < 100  # $100 tolerance

    if receipt_ok and disbursement_ok and cash_ok:
        print(f"\n✅ PASS - Numbers match within tolerance")
        return True
    else:
        print(f"\n❌ FAIL - Numbers don't match")
        if not receipt_ok:
            print(f"  ❌ Receipts off by ${receipt_diff:,.2f}")
        if not disbursement_ok:
            print(f"  ❌ Disbursements off by ${disbursement_diff:,.2f}")
        if not cash_ok:
            print(f"  ❌ Cash off by ${cash_diff:,.2f}")
        return False


# Test with our 4 sample candidates
print("="*80)
print("FINAL VERIFICATION - Do our numbers match FEC totals?")
print("="*80)

test_cases = [
    ('H2AZ02311', 2024, 'Kirsten Engel'),
    ('H0CA25154', 2022, 'Christy Smith'),
    ('H0IA02156', 2020, 'Rita Hart'),
    ('H8IA01094', 2018, 'Abby Finkenauer')
]

results = []
for candidate_id, cycle, name in test_cases:
    success = test_candidate(candidate_id, cycle, name)
    results.append((name, success))

print(f"\n{'='*80}")
print("FINAL VERIFICATION SUMMARY")
print('='*80)

for name, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")

passed = sum(1 for _, s in results if s)
print(f"\n{passed}/{len(results)} tests passed")

if passed == len(results):
    print("\n✅✅✅ ALL VERIFIED - Safe to proceed with multi-day collection")
else:
    print("\n❌ VERIFICATION FAILED - Do NOT proceed until issues resolved")
