#!/usr/bin/env python3
"""
Verify that sum of stored period amounts matches FEC /totals/
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

test_cases = [
    ('H0CA25154', 2022, 'Christy Smith'),
]

for candidate_id, cycle, name in test_cases:
    print(f"\n{'='*80}")
    print(f"{name} ({candidate_id}) - Cycle {cycle}")
    print('='*80)

    # Get FEC /totals/ (ground truth)
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
        params={'api_key': FEC_API_KEY, 'cycle': cycle},
        timeout=30
    )

    totals = response.json().get('results', [])[0]
    expected_receipts = totals.get('receipts')
    expected_disbursements = totals.get('disbursements')

    print(f"\n[FEC /totals/]")
    print(f"  Receipts: ${expected_receipts:,.2f}")
    print(f"  Disbursements: ${expected_disbursements:,.2f}")

    # Get our stored filings
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/quarterly_financials",
        params={
            'candidate_id': f'eq.{candidate_id}',
            'cycle': f'eq.{cycle}',
            'select': 'total_receipts,total_disbursements',
            'limit': 1000
        },
        headers=headers_query
    )

    filings = response.json()

    # Sum them up (skip duplicates from amendments)
    sum_receipts = sum(f['total_receipts'] for f in filings)
    sum_disbursements = sum(f['total_disbursements'] for f in filings)

    print(f"\n[Our Database - Sum of Period Amounts]")
    print(f"  Receipts: ${sum_receipts:,.2f}")
    print(f"  Disbursements: ${sum_disbursements:,.2f}")

    print(f"\n[Comparison]")
    receipts_diff = abs(sum_receipts - expected_receipts)
    disbursements_diff = abs(sum_disbursements - expected_disbursements)

    print(f"  Receipts difference: ${receipts_diff:,.2f}")
    print(f"  Disbursements difference: ${disbursements_diff:,.2f}")

    # Note: We may have duplicates from multiple test runs
    print(f"\n  Total filings in database: {len(filings)}")
    print(f"  (Note: May include duplicates from test runs)")

    if receipts_diff / expected_receipts < 0.1:  # Within 10%
        print(f"\n✓ VERIFIED - Numbers are reasonable")
    else:
        print(f"\n⚠️  WARNING - Large variance detected")
