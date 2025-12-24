#!/usr/bin/env python3
"""
Load ONLY the 2024 financial_summary data
"""

import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def transform_financial_summary(financials_data):
    """Transform financial summary to database format."""
    transformed = []

    for record in financials_data:
        transformed.append({
            'candidate_id': record['candidate_id'],
            'cycle': record['cycle'],
            'total_receipts': record.get('total_receipts'),
            'total_disbursements': record.get('total_disbursements'),
            'cash_on_hand': record.get('cash_on_hand'),
            'coverage_start_date': record.get('coverage_start_date'),
            'coverage_end_date': record.get('coverage_end_date'),
            'report_year': record.get('last_report_year'),
            'report_type': record.get('last_report_type')
        })

    return transformed

def insert_batch(table_name, records, batch_size=1000):
    """Insert records into Supabase in batches."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    total = len(records)
    inserted = 0
    errors = []

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]

        try:
            response = requests.post(url, headers=headers, json=batch)

            if response.status_code in [200, 201, 204]:
                inserted += len(batch)
                print(f"  Batch {i//batch_size + 1}: {inserted:,}/{total:,} records")
            else:
                error_msg = f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text[:200]}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} error: {str(e)[:200]}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)

    return inserted, errors

def main():
    print("="*70)
    print("LOADING 2024 FINANCIAL SUMMARY")
    print("="*70)

    # Load data
    print("\nLoading financials_2024.json...")
    with open('financials_2024.json', 'r') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data):,} records")

    # Transform
    print("\nTransforming data...")
    transformed = transform_financial_summary(data)
    print(f"✓ Transformed {len(transformed):,} records")

    # Insert
    print(f"\nInserting {len(transformed):,} financial summaries...")
    inserted, errors = insert_batch('financial_summary', transformed)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total inserted: {inserted:,}/{len(transformed):,}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nFirst 3 errors:")
        for error in errors[:3]:
            print(f"  - {error}")
    else:
        print("\n✅ SUCCESS! All 2024 financial summaries loaded.")

if __name__ == "__main__":
    main()
