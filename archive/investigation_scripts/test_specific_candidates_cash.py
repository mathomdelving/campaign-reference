#!/usr/bin/env python3
"""
Test specific candidates to see what year-end cash data is actually available
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

def test_candidate_reports(candidate_id, name, cycle):
    """Test what reports are available for a specific candidate"""

    print(f"\n{'='*80}")
    print(f"{name} ({candidate_id}) - Cycle {cycle}")
    print('='*80)

    # Get committees
    url = f"https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 10
    }

    response = requests.get(url, params=params, timeout=15)
    committees = response.json().get('results', [])

    print(f"\nCommittees in cycle {cycle}: {len(committees)}")
    for comm in committees:
        print(f"  - {comm['committee_id']}: {comm.get('name', 'N/A')}")

    if not committees:
        print("❌ No committees found!")
        return

    # Check reports for primary committee
    committee_id = committees[0]['committee_id']
    print(f"\nChecking reports for committee: {committee_id}")

    # Get ALL reports for this committee in this cycle
    url = f"https://api.open.fec.gov/v1/committee/{committee_id}/reports/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 20,
        'sort': '-coverage_end_date'
    }

    response = requests.get(url, params=params, timeout=15)
    reports = response.json().get('results', [])

    print(f"\nTotal reports found: {len(reports)}")

    # Group by report type
    by_type = {}
    for report in reports:
        rtype = report.get('report_type', 'UNKNOWN')
        if rtype not in by_type:
            by_type[rtype] = []
        by_type[rtype].append(report)

    print(f"\nReport types available:")
    for rtype, reps in sorted(by_type.items()):
        print(f"  {rtype}: {len(reps)} reports")

    # Show year-end reports specifically
    year_end_reports = by_type.get('YE', [])
    if year_end_reports:
        print(f"\n✅ YEAR-END REPORTS FOUND: {len(year_end_reports)}")
        for ye in year_end_reports[:3]:
            print(f"  Coverage: {ye.get('coverage_start_date')} to {ye.get('coverage_end_date')}")
            print(f"  Cash on hand: ${ye.get('cash_on_hand_end_period', 0):,.2f}")
    else:
        print(f"\n⚠️  NO YEAR-END REPORTS - Checking other report types for cash...")

        # Check for Q4 reports (which would have year-end cash)
        for rtype in ['12P', 'Q4', '30G', 'M12']:
            if rtype in by_type:
                print(f"\n  Found {rtype} reports:")
                for rep in by_type[rtype][:2]:
                    print(f"    Coverage: {rep.get('coverage_end_date')}")
                    print(f"    Cash: ${rep.get('cash_on_hand_end_period', 0):,.2f}")


# Test 2024 cycle candidates
print("="*80)
print("TESTING 2024 CYCLE - Should have year-end 2023 data")
print("="*80)

test_candidate_reports('S4MI00355', 'Elissa Slotkin (MI Senate winner)', 2024)
test_candidate_reports('S4TX00722', 'Colin Allred (TX Senate)', 2024)
test_candidate_reports('S6NY00082', 'Chuck Schumer (NY Senate incumbent)', 2024)

# Test 2022 cycle candidates
print("\n" + "="*80)
print("TESTING 2022 CYCLE - Should have year-end 2021 data")
print("="*80)

test_candidate_reports('S2PA00420', 'John Fetterman (PA Senate winner)', 2022)
test_candidate_reports('S0GA00559', 'Raphael Warnock (GA Senate winner)', 2022)
test_candidate_reports('S0AZ00350', 'Mark Kelly (AZ Senate winner)', 2022)

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
