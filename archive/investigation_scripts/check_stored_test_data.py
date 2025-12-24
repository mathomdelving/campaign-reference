#!/usr/bin/env python3
"""Check what data was actually stored for our test candidates"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

test_candidates = [
    ('H2AZ02311', 2024, 'Kirsten Engel'),
    ('H0CA25154', 2022, 'Christy Smith'),
    ('H0IA02156', 2020, 'Rita Hart'),
    ('H8IA01094', 2018, 'Abby Finkenauer')
]

for candidate_id, cycle, name in test_candidates:
    print(f"\n{'='*80}")
    print(f"{name} ({candidate_id}) - Cycle {cycle}")
    print('='*80)

    # Get filings from quarterly_financials
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/quarterly_financials",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}',
            'select': 'committee_id,report_type,coverage_end_date,total_receipts,total_disbursements,cash_ending',
            'order': 'coverage_end_date.desc',
            'limit': 5
        },
        headers=headers_query
    )

    filings = response.json()

    print(f"\nTop 5 filings stored:")
    for filing in filings:
        print(f"  {filing['report_type']:6} | End: {filing['coverage_end_date']} | Committee: {filing['committee_id']}")
        print(f"         Receipts: ${filing['total_receipts']:>12,.2f} | Disbursed: ${filing['total_disbursements']:>12,.2f} | Cash: ${filing['cash_ending']:>12,.2f}")

    # Also check /totals/ endpoint for comparison
    import time
    time.sleep(0.5)
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
        params={
            'api_key': os.environ.get('FEC_API_KEY'),
            'cycle': cycle,
            'per_page': 1
        },
        timeout=30
    )

    totals = response.json().get('results', [])
    if totals:
        print(f"\nFEC API /totals/ for comparison:")
        print(f"  Total Receipts: ${totals[0].get('receipts', 0):>12,.2f}")
        print(f"  Total Disbursed: ${totals[0].get('disbursements', 0):>12,.2f}")
        print(f"  Cash on Hand: ${totals[0].get('last_cash_on_hand_end_period', 0):>12,.2f}")
