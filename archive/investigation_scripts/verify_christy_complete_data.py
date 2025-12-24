#!/usr/bin/env python3
"""Verify Christy Smith 2022 has correct data"""

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

print("="*80)
print("CHRISTY SMITH 2022 - ALL FILINGS (sorted by total_receipts DESC)")
print("="*80)

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/quarterly_financials",
    params={
        'candidate_id': 'eq.H0CA25154',
        'cycle': 'eq.2022',
        'select': 'report_type,coverage_end_date,total_receipts,total_disbursements,cash_ending',
        'order': 'total_receipts.desc',
        'limit': 20
    },
    headers=headers_query
)

filings = response.json()

print(f"\nTotal filings found: {len(filings)}")
print(f"\nTop filings by receipts:")
print("-"*80)

for filing in filings:
    print(f"{filing['report_type']:6} | End: {filing['coverage_end_date']} | Receipts: ${filing['total_receipts']:>13,.2f} | Disbursed: ${filing['total_disbursements']:>13,.2f}")

print("\n" + "="*80)
print("EXPECTED (from FEC API /totals/):")
print("="*80)
print("Receipts: $3,949,504.79")
print("Disbursed: $4,067,086.96")
print("Cash: $51,825.48")

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)
highest_receipt = filings[0]['total_receipts'] if filings else 0
print(f"Highest receipt filing: ${highest_receipt:,.2f}")
print(f"Expected from API: $3,949,504.79")
print(f"Difference: ${3949504.79 - highest_receipt:,.2f}")

if highest_receipt > 3900000:
    print("✅ DATA LOOKS CORRECT!")
else:
    print("❌ Still missing data - highest receipt should be ~$4M")
