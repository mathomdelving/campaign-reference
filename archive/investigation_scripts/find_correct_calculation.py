#!/usr/bin/env python3
"""
Test different methods to calculate cycle totals from reports
Find which method matches the /totals/ endpoint
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

candidate_id = 'H0CA25154'  # Christy Smith
cycle = 2022

print("="*100)
print("FINDING THE CORRECT CALCULATION METHOD")
print("="*100)

# Get ground truth from /totals/
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
    params={'api_key': FEC_API_KEY, 'cycle': cycle},
    timeout=30
)

totals = response.json().get('results', [])[0]
expected_receipts = totals.get('receipts')
expected_disbursements = totals.get('disbursements')
expected_cash = totals.get('last_cash_on_hand_end_period')

print(f"\n[GROUND TRUTH] /candidate/{candidate_id}/totals/ for cycle {cycle}")
print(f"  Receipts: ${expected_receipts:,.2f}")
print(f"  Disbursements: ${expected_disbursements:,.2f}")
print(f"  Cash: ${expected_cash:,.2f}")
print(f"  Coverage: {totals.get('coverage_start_date')} to {totals.get('coverage_end_date')}")

# Get all reports
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
    params={'api_key': FEC_API_KEY},
    timeout=30
)
committees = response.json().get('results', [])
committee_id = committees[0]['committee_id']

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

print(f"\n[REPORTS] {len(reports)} reports found for committee {committee_id}")

# METHOD 1: Sum all _period amounts
print(f"\n{'='*100}")
print("METHOD 1: Sum all total_receipts_period amounts")
print('='*100)

sum_receipts_period = 0
sum_disbursements_period = 0

for report in reports:
    if report.get('most_recent'):  # Only use most recent versions (skip amendments)
        r_p = float(report.get('total_receipts_period', 0) or 0)
        d_p = float(report.get('total_disbursements_period', 0) or 0)
        sum_receipts_period += r_p
        sum_disbursements_period += d_p

print(f"  Sum of receipts_period: ${sum_receipts_period:,.2f}")
print(f"  Expected: ${expected_receipts:,.2f}")
print(f"  Difference: ${abs(sum_receipts_period - expected_receipts):,.2f}")
print(f"  Match: {'✓' if abs(sum_receipts_period - expected_receipts) < 100 else '✗'}")

# METHOD 2: Use the highest YTD value
print(f"\n{'='*100}")
print("METHOD 2: Use highest total_receipts_ytd value")
print('='*100)

max_receipts_ytd = 0
max_disbursements_ytd = 0

for report in reports:
    if report.get('most_recent'):
        r_ytd = float(report.get('total_receipts_ytd', 0) or 0)
        d_ytd = float(report.get('total_disbursements_ytd', 0) or 0)
        if r_ytd > max_receipts_ytd:
            max_receipts_ytd = r_ytd
        if d_ytd > max_disbursements_ytd:
            max_disbursements_ytd = d_ytd

print(f"  Max receipts_ytd: ${max_receipts_ytd:,.2f}")
print(f"  Expected: ${expected_receipts:,.2f}")
print(f"  Difference: ${abs(max_receipts_ytd - expected_receipts):,.2f}")
print(f"  Match: {'✓' if abs(max_receipts_ytd - expected_receipts) < 100 else '✗'}")

# METHOD 3: Use YE report's YTD
print(f"\n{'='*100}")
print("METHOD 3: Use Year-End (YE) report's YTD")
print('='*100)

ye_receipts_ytd = None
ye_disbursements_ytd = None

for report in reports:
    if report.get('report_type') == 'YE' and report.get('most_recent') and report.get('report_year') == cycle:
        ye_receipts_ytd = float(report.get('total_receipts_ytd', 0) or 0)
        ye_disbursements_ytd = float(report.get('total_disbursements_ytd', 0) or 0)
        break

if ye_receipts_ytd:
    print(f"  YE receipts_ytd: ${ye_receipts_ytd:,.2f}")
    print(f"  Expected: ${expected_receipts:,.2f}")
    print(f"  Difference: ${abs(ye_receipts_ytd - expected_receipts):,.2f}")
    print(f"  Match: {'✓' if abs(ye_receipts_ytd - expected_receipts) < 100 else '✗'}")
else:
    print("  No YE report found")

# METHOD 4: Sum period amounts from 2022 reports + YE 2021 YTD
print(f"\n{'='*100}")
print("METHOD 4: Sum 2022 period amounts + 2021 year-end YTD")
print('='*100)

sum_2022_period = 0
ye_2021_ytd = 0

for report in reports:
    if not report.get('most_recent'):
        continue

    if report.get('report_year') == 2022:
        r_p = float(report.get('total_receipts_period', 0) or 0)
        sum_2022_period += r_p
    elif report.get('report_type') == 'YE' and report.get('report_year') == 2021:
        ye_2021_ytd = float(report.get('total_receipts_ytd', 0) or 0)

total_method4 = sum_2022_period + ye_2021_ytd

print(f"  Sum of 2022 period amounts: ${sum_2022_period:,.2f}")
print(f"  Plus 2021 YE YTD: ${ye_2021_ytd:,.2f}")
print(f"  Total: ${total_method4:,.2f}")
print(f"  Expected: ${expected_receipts:,.2f}")
print(f"  Difference: ${abs(total_method4 - expected_receipts):,.2f}")
print(f"  Match: {'✓' if abs(total_method4 - expected_receipts) < 100 else '✗'}")

# SUMMARY
print(f"\n{'='*100}")
print("SUMMARY")
print('='*100)

methods = [
    ("Sum all _period", sum_receipts_period),
    ("Max _ytd", max_receipts_ytd),
    ("YE _ytd", ye_receipts_ytd if ye_receipts_ytd else 0),
    ("2022 period + 2021 YE", total_method4)
]

best_match = None
best_diff = float('inf')

for method_name, value in methods:
    diff = abs(value - expected_receipts)
    if diff < best_diff:
        best_diff = diff
        best_match = method_name

    print(f"{method_name:25} ${value:>15,.2f}  Diff: ${diff:>12,.2f}  {'✓ MATCH' if diff < 100 else ''}")

print(f"\n{'='*100}")
print(f"✓ BEST MATCH: {best_match} (diff: ${best_diff:,.2f})")
print('='*100)
