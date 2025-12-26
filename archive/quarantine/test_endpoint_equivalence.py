#!/usr/bin/env python3
"""
Test whether /reports/house-senate/ endpoint returns equivalent data
to the committee history approach.

This will test on Cortez Masto, Johnson, and several other major candidates
to ensure we don't lose any data by switching endpoints.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

def get_principal_committee_for_cycle(candidate_id, cycle):
    """Current approach: Use committee history to find principal committee"""
    print(f"\n  METHOD 1 (Committee History): {candidate_id}")

    # Get all committees
    committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
    committees_response = requests.get(committees_url, params={
        'api_key': FEC_API_KEY,
        'per_page': 100
    }, timeout=10)

    if not committees_response.ok:
        print(f"    ❌ Failed to get committees")
        return None, []

    committees = committees_response.json().get('results', [])
    print(f"    Found {len(committees)} total committees")

    # Check each committee's history
    principal_committee_id = None
    for committee in committees:
        committee_id = committee['committee_id']

        # Get history
        history_url = f"{BASE_URL}/committee/{committee_id}/history/"
        history_response = requests.get(history_url, params={'api_key': FEC_API_KEY}, timeout=10)

        if not history_response.ok:
            continue

        history = history_response.json().get('results', [])

        # Find principal for this cycle
        for record in history:
            if record.get('cycle') == cycle and record.get('designation') == 'P':
                principal_committee_id = committee_id
                print(f"    ✓ Principal committee: {committee_id}")
                break

        if principal_committee_id:
            break

    if not principal_committee_id:
        print(f"    ❌ No principal committee found")
        return None, []

    # Get filings from principal committee
    all_filings = []
    for form_type in ['F3', 'F3N']:
        page = 1
        while True:
            filings_url = f"{BASE_URL}/committee/{principal_committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': form_type,
                'per_page': 100,
                'page': page
            }, timeout=30)

            if not filings_response.ok:
                break

            data = filings_response.json()
            filings = data.get('results', [])

            if not filings:
                break

            all_filings.extend(filings)

            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break

            page += 1

    print(f"    ✓ Got {len(all_filings)} total filings (F3 + F3N)")
    return principal_committee_id, all_filings


def get_reports_direct(candidate_id, cycle):
    """New simpler approach: Direct reports by candidate_id"""
    print(f"\n  METHOD 2 (Direct Reports): {candidate_id}")

    url = f"{BASE_URL}/reports/house-senate/"
    params = {
        'api_key': FEC_API_KEY,
        'candidate_id': candidate_id,
        'cycle': cycle,
        'per_page': 100
    }

    all_reports = []
    page = 1

    while True:
        params['page'] = page
        response = requests.get(url, params=params, timeout=30)

        if not response.ok:
            print(f"    ❌ Failed to get reports")
            return []

        data = response.json()
        results = data.get('results', [])

        if not results:
            break

        all_reports.extend(results)

        pagination = data.get('pagination', {})
        if page >= pagination.get('pages', 1):
            break

        page += 1

    print(f"    ✓ Got {len(all_reports)} reports")
    return all_reports


def compare_results(candidate_name, candidate_id, cycle, committee_filings, direct_reports):
    """Compare the two approaches"""
    print(f"\n{'='*80}")
    print(f"COMPARISON: {candidate_name} ({candidate_id}) - {cycle}")
    print(f"{'='*80}")

    print(f"\nCount:")
    print(f"  Committee History Approach: {len(committee_filings)} filings")
    print(f"  Direct Reports Approach:    {len(direct_reports)} reports")

    if len(committee_filings) != len(direct_reports):
        print(f"  ⚠️  COUNT MISMATCH: {abs(len(committee_filings) - len(direct_reports))} difference")
    else:
        print(f"  ✓ Counts match")

    # Compare coverage periods
    committee_periods = set()
    for f in committee_filings:
        key = (f.get('coverage_start_date'), f.get('coverage_end_date'), f.get('report_type'))
        committee_periods.add(key)

    direct_periods = set()
    for r in direct_reports:
        key = (r.get('coverage_start_date'), r.get('coverage_end_date'), r.get('report_type'))
        direct_periods.add(key)

    missing_in_direct = committee_periods - direct_periods
    extra_in_direct = direct_periods - committee_periods

    print(f"\nCoverage Periods:")
    print(f"  Committee approach: {len(committee_periods)} unique periods")
    print(f"  Direct approach:    {len(direct_periods)} unique periods")

    if missing_in_direct:
        print(f"  ⚠️  MISSING in direct approach: {len(missing_in_direct)} periods")
        for period in list(missing_in_direct)[:3]:
            print(f"     - {period}")

    if extra_in_direct:
        print(f"  ⚠️  EXTRA in direct approach: {len(extra_in_direct)} periods")
        for period in list(extra_in_direct)[:3]:
            print(f"     - {period}")

    if not missing_in_direct and not extra_in_direct:
        print(f"  ✓ All periods match")

    # Compare total amounts
    committee_total = sum(f.get('total_receipts', 0) or 0 for f in committee_filings)
    direct_total = sum(r.get('total_receipts', 0) or 0 for r in direct_reports)

    print(f"\nTotal Receipts:")
    print(f"  Committee approach: ${committee_total:,.2f}")
    print(f"  Direct approach:    ${direct_total:,.2f}")

    if abs(committee_total - direct_total) > 1:
        pct_diff = abs(committee_total - direct_total) / max(committee_total, direct_total) * 100
        print(f"  ⚠️  AMOUNT MISMATCH: {pct_diff:.1f}% difference")
    else:
        print(f"  ✓ Amounts match")

    return {
        'candidate_name': candidate_name,
        'candidate_id': candidate_id,
        'committee_count': len(committee_filings),
        'direct_count': len(direct_reports),
        'count_match': len(committee_filings) == len(direct_reports),
        'periods_match': not missing_in_direct and not extra_in_direct,
        'amounts_match': abs(committee_total - direct_total) <= 1,
        'committee_total': committee_total,
        'direct_total': direct_total
    }


def main():
    # Test candidates - mix of major fundraisers and our problem cases
    test_candidates = [
        {'name': 'Catherine Cortez Masto', 'id': 'S6NV00200', 'cycle': 2022},
        {'name': 'Ron Johnson', 'id': 'S0WI00197', 'cycle': 2022},
        {'name': 'Raphael Warnock', 'id': 'S8GA00321', 'cycle': 2022},
        {'name': 'Mark Kelly', 'id': 'S0AZ00285', 'cycle': 2022},
        {'name': 'John Fetterman', 'id': 'S2PA00466', 'cycle': 2022},
    ]

    print("="*80)
    print("ENDPOINT EQUIVALENCE TEST")
    print("="*80)
    print("\nTesting whether /reports/house-senate/ returns the same data")
    print("as the committee history approach.")
    print("\nThis test will check:")
    print("  1. Number of filings returned")
    print("  2. Coverage periods (are all periods present?)")
    print("  3. Total amounts (do they sum to the same?)")
    print("="*80)

    results = []

    for candidate in test_candidates:
        print(f"\n\n{'#'*80}")
        print(f"# Testing: {candidate['name']}")
        print(f"{'#'*80}")

        # Method 1: Committee history approach
        committee_id, committee_filings = get_principal_committee_for_cycle(
            candidate['id'],
            candidate['cycle']
        )

        # Method 2: Direct reports approach
        direct_reports = get_reports_direct(
            candidate['id'],
            candidate['cycle']
        )

        # Compare
        result = compare_results(
            candidate['name'],
            candidate['id'],
            candidate['cycle'],
            committee_filings,
            direct_reports
        )
        results.append(result)

    # Final summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    all_match = all(r['count_match'] and r['periods_match'] and r['amounts_match'] for r in results)

    for r in results:
        status = "✓ MATCH" if (r['count_match'] and r['periods_match'] and r['amounts_match']) else "❌ MISMATCH"
        print(f"\n{r['candidate_name']} ({r['candidate_id']}): {status}")
        print(f"  Counts: {r['committee_count']} vs {r['direct_count']}")
        print(f"  Totals: ${r['committee_total']:,.0f} vs ${r['direct_total']:,.0f}")

    if all_match:
        print(f"\n{'='*80}")
        print("✅ CONCLUSION: Both endpoints return IDENTICAL data")
        print("   It is SAFE to use the simpler /reports/house-senate/ endpoint")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print("❌ CONCLUSION: Endpoints return DIFFERENT data")
        print("   DO NOT switch to simpler endpoint - data quality at risk")
        print("   Stick with committee history approach but fix retry logic")
        print(f"{'='*80}")

    # Save results
    with open('endpoint_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: endpoint_comparison_results.json")


if __name__ == "__main__":
    main()
