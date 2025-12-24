#!/usr/bin/env python3
"""
Monitor the progress of cash_on_hand backfill
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

def check_progress():
    """Check how many records have been backfilled"""

    print("\n" + "="*80)
    print(f"BACKFILL PROGRESS CHECK - {time.strftime('%I:%M:%S %p')}")
    print("="*80)

    cycles = [2024, 2022, 2020, 2018]
    total_updated = 0

    for cycle in cycles:
        # Get total records
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/financial_summary',
            params={
                'cycle': f'eq.{cycle}',
                'select': 'count',
                'limit': 1
            },
            headers={**headers, 'Prefer': 'count=exact'}
        )
        total = int(response.headers.get('Content-Range', '').split('/')[-1])

        # Get records with cash > 0
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/financial_summary',
            params={
                'cycle': f'eq.{cycle}',
                'cash_on_hand': 'gt.0',
                'select': 'count',
                'limit': 1
            },
            headers={**headers, 'Prefer': 'count=exact'}
        )
        updated = int(response.headers.get('Content-Range', '').split('/')[-1])

        total_updated += updated
        percent = (updated / total * 100) if total > 0 else 0

        status = "✅" if updated == total else "⏳"
        print(f"\n{status} Cycle {cycle}: {updated}/{total} records ({percent:.1f}%)")

    print(f"\n📊 TOTAL PROGRESS: {total_updated}/7280 records updated")
    print("="*80)

if __name__ == '__main__':
    check_progress()
