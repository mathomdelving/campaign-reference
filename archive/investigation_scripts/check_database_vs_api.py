#!/usr/bin/env python3
"""
Compare what we have in database vs what FEC API returns
to understand correct field mapping
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

candidate_id = 'H0CA25154'  # Christy Smith
cycle = 2022

print("="*80)
print("CHRISTY SMITH 2022 - DATABASE vs FEC API COMPARISON")
print("="*80)

# 1. Check our financial_summary table (from bulk import)
print("\n[1] OUR DATABASE (financial_summary table - from bulk import):")
print("-"*80)
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/financial_summary",
    params={
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}',
        'select': '*'
    },
    headers=headers_query
)

db_data = response.json()
if db_data:
    print(json.dumps(db_data[0], indent=2))
else:
    print("NO DATA FOUND")

# 2. Check FEC API /totals/ endpoint
print("\n[2] FEC API /candidate/{id}/totals/ endpoint:")
print("-"*80)
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
    params={
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 1
    },
    timeout=30
)

totals_data = response.json().get('results', [])
if totals_data:
    print(f"receipts: ${totals_data[0].get('receipts', 0):,.2f}")
    print(f"disbursements: ${totals_data[0].get('disbursements', 0):,.2f}")
    print(f"cash_on_hand_end_period: ${totals_data[0].get('last_cash_on_hand_end_period', 0):,.2f}")
    print(f"\nAll fields with 'receipt' in name:")
    for key, value in totals_data[0].items():
        if 'receipt' in key.lower() and value and value != 0:
            print(f"  {key}: {value}")
    print(f"\nAll fields with 'contribution' in name:")
    for key, value in totals_data[0].items():
        if 'contribution' in key.lower() and value and value != 0:
            print(f"  {key}: {value}")

# 3. Check FEC API /reports/ endpoint - get ALL reports for the cycle
print("\n[3] FEC API /committee/{id}/reports/ endpoint (ALL reports for cycle):")
print("-"*80)

# First get committee
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
    params={'api_key': FEC_API_KEY, 'per_page': 20},
    timeout=30
)
committees = response.json().get('results', [])
if committees:
    committee_id = committees[0]['committee_id']
    print(f"Committee: {committee_id} - {committees[0].get('name')}")

    # Get ALL reports
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
    print(f"\nTotal reports found: {len(reports)}")
    print(f"\nReport breakdown:")
    for report in reports:
        print(f"\n  Report Type: {report.get('report_type')} | Coverage: {report.get('coverage_start_date', '')[:10]} to {report.get('coverage_end_date', '')[:10]}")

        # Check all possible receipt/contribution fields
        for field in ['total_receipts_period', 'total_receipts_ytd', 'receipts_period', 'receipts_ytd',
                      'total_contributions_period', 'total_contributions_ytd',
                      'net_contributions_period', 'net_contributions_ytd']:
            value = report.get(field)
            if value is not None:
                print(f"    {field}: {value}")

        # Check disbursements
        for field in ['total_disbursements_period', 'total_disbursements_ytd']:
            value = report.get(field)
            if value is not None:
                print(f"    {field}: {value}")

        # Check cash
        cash_end = report.get('cash_on_hand_end_period')
        if cash_end:
            print(f"    cash_on_hand_end_period: {cash_end}")

print("\n" + "="*80)
print("ANALYSIS NEEDED:")
print("="*80)
print("1. Which field from /reports/ matches 'receipts' from /totals/?")
print("2. Do we need to sum multiple reports, or use a specific report type?")
print("3. What's the difference between 'contributions' and 'receipts'?")
