"""
Quick script to re-fetch ONLY the financial summary data with corrected cash_on_hand field.
This avoids re-fetching candidates and quarterly data which would take hours.
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
    print("UPDATE CASH ON HAND - Starting...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Load existing financials
    print("\nLoading financials_2026.json...")
    with open('financials_2026.json', 'r') as f:
        financials = json.load(f)

    print(f"Found {len(financials)} financial records")

    # Check how many have cash_on_hand
    with_cash = [f for f in financials if f.get('cash_on_hand')]
    print(f"Currently have cash_on_hand: {len(with_cash)}/{len(financials)}")

    # Update each record
    print(f"\nUpdating cash_on_hand for {len(financials)} candidates...")
    print(f"Rate limit: ~1.9 seconds per candidate = ~{len(financials) * 1.9 / 60:.1f} minutes total\n")

    updated_count = 0
    has_cash_count = 0

    for idx, record in enumerate(financials):
        candidate_id = record['candidate_id']
        name = record.get('name', 'Unknown')

        print(f"  [{idx+1}/{len(financials)}] {name[:30]:30} ({candidate_id})...", end=" ")

        # Fetch fresh data
        financial_data = fetch_candidate_financials(candidate_id)
        time.sleep(1.5)  # Rate limit - with 7000/hour limit, can do ~1.9s per request

        if financial_data:
            # Update the cash_on_hand field with correct field name
            new_cash = financial_data.get('last_cash_on_hand_end_period')
            old_cash = record.get('cash_on_hand')

            if new_cash != old_cash:
                record['cash_on_hand'] = new_cash
                updated_count += 1

                if new_cash:
                    has_cash_count += 1
                    print(f"✓ ${new_cash:,.0f}")
                else:
                    print("✓ (no cash data)")
            else:
                print("✓ (unchanged)")
        else:
            print("✗ (no data)")

    # Save updated file
    print(f"\n{'='*60}")
    print("Saving updated financials_2026.json...")
    with open('financials_2026.json', 'w') as f:
        json.dump(financials, f, indent=2)

    print(f"\n✓ Updated {updated_count} records")
    print(f"✓ {has_cash_count} candidates now have cash_on_hand data")
    print(f"{'='*60}")
    print("\nNext step: Run load_to_supabase.py to update the database")

if __name__ == "__main__":
    main()
