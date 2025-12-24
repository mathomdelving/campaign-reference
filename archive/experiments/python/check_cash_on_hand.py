#!/usr/bin/env python3
"""
Quick script to check if cash_on_hand data exists in database
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

def check_cycle_cash(cycle, candidate_ids):
    """Check cash_on_hand for specific candidates in a cycle"""

    print(f"\n{'='*80}")
    print(f"CHECKING CYCLE {cycle}")
    print('='*80)

    for candidate_id in candidate_ids:
        # Get financial data
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'candidate_id': f'eq.{candidate_id}',
                'cycle': f'eq.{cycle}',
                'select': 'candidate_id,cycle,total_receipts,total_disbursements,cash_on_hand'
            },
            headers=headers
        )

        data = response.json()

        if data and len(data) > 0:
            record = data[0]
            print(f"\n✓ {candidate_id}:")
            print(f"  Total Receipts: ${record['total_receipts']:,.2f}")
            print(f"  Total Disbursements: ${record['total_disbursements']:,.2f}")
            print(f"  Cash on Hand: ${record['cash_on_hand']:,.2f}")
        else:
            print(f"\n✗ {candidate_id}: No data found")

# Test candidates who definitely ran in 2022
print("="*80)
print("CASH ON HAND INVESTIGATION")
print("="*80)

# 2022 Senate winners
check_cycle_cash(2022, [
    'S2PA00420',  # Fetterman (PA - won)
    'S8GA00296',  # Warnock (GA - won)
    'H0AZ02224',  # Kelly (AZ - won special)
])

# 2024 Senate winners
check_cycle_cash(2024, [
    'S4MI00355',  # Slotkin (MI - won)
    'S6MD00163',  # Alsobrooks (MD - won)
])

# 2026 current fundraisers
check_cycle_cash(2026, [
    'S0GA00248',  # Ossoff
    'H0AZ02224',  # Kelly
])

print(f"\n{'='*80}")
print("INVESTIGATION COMPLETE")
print('='*80)
