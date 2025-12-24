#!/usr/bin/env python3
"""
Systematically investigate FEC data structure to find the CORRECT mapping
Compare /totals/ endpoint with ALL report data to understand the relationship
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

candidate_id = 'H0CA25154'  # Christy Smith
cycle = 2022

print("="*100)
print("SYSTEMATIC INVESTIGATION: Christy Smith 2022")
print("="*100)

# 1. Get /totals/ endpoint (source of truth)
print("\n[1] FEC API /candidate/{id}/totals/ - THE SOURCE OF TRUTH")
print("-"*100)

response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
    params={'api_key': FEC_API_KEY, 'cycle': cycle},
    timeout=30
)

totals = response.json().get('results', [])
if totals:
    total = totals[0]
    print(f"\nKey fields from /totals/:")
    print(f"  receipts: ${total.get('receipts', 0):,.2f}")
    print(f"  disbursements: ${total.get('disbursements', 0):,.2f}")
    print(f"  last_cash_on_hand_end_period: ${total.get('last_cash_on_hand_end_period', 0):,.2f}")
    print(f"  coverage_end_date: {total.get('coverage_end_date')}")
    print(f"  last_report_type_full: {total.get('last_report_type_full')}")
    print(f"  last_report_year: {total.get('last_report_year')}")

    print(f"\nAll fields from /totals/ endpoint:")
    for key in sorted(total.keys()):
        if total[key] and total[key] != 0:
            print(f"  {key}: {total[key]}")

# 2. Get committee
print(f"\n[2] Get Committee for Candidate")
print("-"*100)

response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
    params={'api_key': FEC_API_KEY},
    timeout=30
)

committees = response.json().get('results', [])
if committees:
    committee_id = committees[0]['committee_id']
    print(f"Committee: {committee_id} - {committees[0].get('name')}")

# 3. Get ALL reports and analyze
print(f"\n[3] ALL REPORTS for committee {committee_id} in cycle {cycle}")
print("-"*100)

response = requests.get(
    f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
    params={
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 100,
        'sort': '-coverage_end_date'
    },
    timeout=30
)

reports = response.json().get('results', [])

print(f"\nTotal reports: {len(reports)}")
print(f"\nDetailed breakdown (sorted by coverage_end_date DESC):")
print("-"*100)

for i, report in enumerate(reports, 1):
    print(f"\n[Report {i}] Type: {report.get('report_type')} | Coverage: {report.get('coverage_start_date', '')[:10]} to {report.get('coverage_end_date', '')[:10]}")
    print(f"  Report year: {report.get('report_year')}")
    print(f"  Amendment indicator: {report.get('amendment_indicator')}")
    print(f"  Most recent: {report.get('most_recent')}")

    # Show period vs ytd
    print(f"  Receipts:")
    print(f"    total_receipts_period: ${float(report.get('total_receipts_period', 0) or 0):,.2f}")
    print(f"    total_receipts_ytd: ${float(report.get('total_receipts_ytd', 0) or 0):,.2f}")

    print(f"  Disbursements:")
    print(f"    total_disbursements_period: ${float(report.get('total_disbursements_period', 0) or 0):,.2f}")
    print(f"    total_disbursements_ytd: ${float(report.get('total_disbursements_ytd', 0) or 0):,.2f}")

    print(f"  Cash:")
    print(f"    cash_on_hand_end_period: ${float(report.get('cash_on_hand_end_period', 0) or 0):,.2f}")

# 4. Analysis
print(f"\n[4] ANALYSIS")
print("-"*100)

expected_receipts = totals[0].get('receipts', 0)
expected_disbursements = totals[0].get('disbursements', 0)
expected_cash = totals[0].get('last_cash_on_hand_end_period', 0)
expected_coverage_end = totals[0].get('coverage_end_date', '')

print(f"\nTarget from /totals/:")
print(f"  Receipts: ${expected_receipts:,.2f}")
print(f"  Disbursements: ${expected_disbursements:,.2f}")
print(f"  Cash: ${expected_cash:,.2f}")
print(f"  Coverage end date: {expected_coverage_end}")

print(f"\nSearching for matching report...")

for report in reports:
    r_ytd = report.get('total_receipts_ytd', 0) or 0
    d_ytd = report.get('total_disbursements_ytd', 0) or 0
    c = report.get('cash_on_hand_end_period', 0) or 0

    # Check if this matches
    r_match = abs(r_ytd - expected_receipts) < 100
    d_match = abs(d_ytd - expected_disbursements) < 100
    c_match = abs(c - expected_cash) < 100

    if r_match or d_match or c_match:
        print(f"\n✓ POTENTIAL MATCH:")
        print(f"  Report type: {report.get('report_type')}")
        print(f"  Coverage: {report.get('coverage_end_date', '')[:10]}")
        print(f"  Receipts YTD: ${r_ytd:,.2f} {'✓' if r_match else '✗'}")
        print(f"  Disbursements YTD: ${d_ytd:,.2f} {'✓' if d_match else '✗'}")
        print(f"  Cash: ${c:,.2f} {'✓' if c_match else '✗'}")
        print(f"  Most recent: {report.get('most_recent')}")
        print(f"  Amendment: {report.get('amendment_indicator')}")

print(f"\n[5] HYPOTHESIS")
print("-"*100)
print("Possible explanations for /totals/ vs /reports/ differences:")
print("1. /totals/ may aggregate across multiple committees")
print("2. /totals/ may use a specific report (last filed, most recent, specific type)")
print("3. /totals/ may include adjustments or corrections")
print("4. YTD values reset at year boundaries")
print("\nNext step: Check if we need to look at candidate-level totals vs committee-level reports")
