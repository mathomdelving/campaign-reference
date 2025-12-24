#!/usr/bin/env python3
"""Check what the raw FEC API actually returns for reports"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

# Check one of Christy Smith's committees
committee_id = 'C00725101'  # FLIP FORWARD PAC
cycle = 2022

print(f"Checking reports for committee {committee_id} in cycle {cycle}")
print("="*80)

response = requests.get(
    f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
    params={
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'per_page': 3,
        'sort': '-coverage_end_date'
    },
    timeout=30
)

data = response.json()
reports = data.get('results', [])

print(f"\nFound {len(reports)} reports")
print("\nFirst report details:")
print("="*80)

if reports:
    report = reports[0]
    print(json.dumps(report, indent=2))

    print("\n" + "="*80)
    print("Key fields:")
    print("="*80)
    print(f"Report Type: {report.get('report_type')}")
    print(f"Coverage End: {report.get('coverage_end_date')}")
    print(f"total_receipts: {report.get('total_receipts')}")
    print(f"total_disbursements: {report.get('total_disbursements')}")
    print(f"cash_on_hand_end_period: {report.get('cash_on_hand_end_period')}")

    print("\nALL numeric fields in report:")
    for key, value in report.items():
        if isinstance(value, (int, float)) and value != 0:
            print(f"  {key}: {value}")
