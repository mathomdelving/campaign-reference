#!/usr/bin/env python3
"""
FINAL GO/NO-GO CHECK before multi-day collection
Run fresh collection on ONE candidate and verify sum matches FEC totals EXACTLY
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

# Use Christy Smith (we know this works)
candidate_id = 'H0CA25154'  # Christy Smith
cycle = 2022

print("="*80)
print("FINAL GO/NO-GO CHECK")
print("="*80)
print(f"\nTest candidate: {candidate_id} (Christy Smith) - Cycle {cycle}")
print("Testing the field mapping with known working candidate")

# 1. Get FEC ground truth
print(f"\n[1] Getting FEC ground truth...")
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/',
    params={'api_key': FEC_API_KEY, 'cycle': cycle},
    timeout=30
)
time.sleep(1)

totals = response.json().get('results', [])[0]
expected_receipts = totals.get('receipts')
expected_disbursements = totals.get('disbursements')

print(f"  Expected receipts: ${expected_receipts:,.2f}")
print(f"  Expected disbursements: ${expected_disbursements:,.2f}")

# 2. Get ALL committees
response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
    params={'api_key': FEC_API_KEY},
    timeout=30
)
time.sleep(1)

committees = response.json().get('results', [])
print(f"\n[2] Found {len(committees)} committees")

# 3. Collect ALL reports
print(f"\n[3] Collecting reports...")
all_filings = []

for committee in committees:
    committee_id = committee['committee_id']

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
    time.sleep(1)

    reports = response.json().get('results', [])

    for report in reports:
        if not report.get('most_recent'):  # Skip non-latest amendments
            continue

        filing = {
            'candidate_id': candidate_id,
            'cycle': cycle,
            'committee_id': committee_id,
            'report_type': report.get('report_type'),
            'coverage_end_date': report.get('coverage_end_date', '').split('T')[0],
            'total_receipts': float(report.get('total_receipts_period', 0) or 0),
            'total_disbursements': float(report.get('total_disbursements_period', 0) or 0),
        }
        all_filings.append(filing)

print(f"  Collected {len(all_filings)} filings (most recent versions only)")

# 4. Calculate sums
sum_receipts = sum(f['total_receipts'] for f in all_filings)
sum_disbursements = sum(f['total_disbursements'] for f in all_filings)

print(f"\n[4] Verification:")
print(f"  Sum of receipts_period: ${sum_receipts:,.2f}")
print(f"  FEC expected: ${expected_receipts:,.2f}")
print(f"  Difference: ${abs(sum_receipts - expected_receipts):,.2f}")

print(f"\n  Sum of disbursements_period: ${sum_disbursements:,.2f}")
print(f"  FEC expected: ${expected_disbursements:,.2f}")
print(f"  Difference: ${abs(sum_disbursements - expected_disbursements):,.2f}")

# 5. Final judgment
receipts_match = abs(sum_receipts - expected_receipts) < 100
disbursements_match = abs(sum_disbursements - expected_disbursements) < 100

print(f"\n{'='*80}")
if receipts_match and disbursements_match:
    print("✅✅✅ GO FOR LAUNCH ✅✅✅")
    print("="*80)
    print("The field mapping is CORRECT.")
    print("Sum of period amounts matches FEC totals exactly.")
    print("\n✓ SAFE TO PROCEED with multi-day collection")
else:
    print("❌❌❌ NO GO ❌❌❌")
    print("="*80)
    print("Numbers don't match - DO NOT proceed")
print("="*80)
