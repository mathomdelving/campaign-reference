"""
Fix missing cash_on_hand for candidates that should have data
"""
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"
CYCLE = 2026

def fetch_candidate_financials(candidate_id, cycle=CYCLE):
    """Fetch financial totals for a candidate"""
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]
        else:
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("FIX MISSING CASH ON HAND - Starting...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Load existing financials
    print("\nLoading financials_2026.json...")
    with open('financials_2026.json', 'r') as f:
        financials = json.load(f)

    # Find all records with None cash_on_hand
    missing = [f for f in financials if f.get('cash_on_hand') is None]
    print(f"Found {len(missing)} candidates with missing cash_on_hand\n")

    # Update them
    updated_count = 0
    still_missing = 0

    for i, record in enumerate(missing, 1):
        candidate_id = record['candidate_id']
        name = record['name']

        print(f"  [{i}/{len(missing)}] {name:40} ({candidate_id})... ", end='', flush=True)

        # Fetch from FEC
        financial_data = fetch_candidate_financials(candidate_id)

        if financial_data:
            cash_on_hand = financial_data.get('last_cash_on_hand_end_period')

            if cash_on_hand is not None:
                record['cash_on_hand'] = cash_on_hand
                updated_count += 1
                print(f"✓ ${cash_on_hand:,.0f}")
            else:
                still_missing += 1
                print("✓ (no cash data)")
        else:
            still_missing += 1
            print("✗ (no data)")

        # Rate limit
        time.sleep(1.5)

    # Save updated data
    print(f"\nSaving updated financials...")
    with open('financials_2026.json', 'w') as f:
        json.dump(financials, f, indent=2)

    print("\n" + "="*60)
    print(f"Updated: {updated_count} candidates")
    print(f"Still missing: {still_missing} candidates")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == '__main__':
    main()
