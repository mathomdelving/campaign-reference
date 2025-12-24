#!/usr/bin/env python3
"""
Comprehensive Data Audit: Review all financial data we have and identify gaps
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

def audit_cycle(cycle):
    """Comprehensive audit of data for a cycle"""

    print(f"\n{'='*80}")
    print(f"CYCLE {cycle} - DATA AUDIT")
    print('='*80)

    # Get all financial records for this cycle
    PAGE_SIZE = 1000
    from_offset = 0
    all_records = []

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'cycle': f'eq.{cycle}',
                'select': 'candidate_id,total_receipts,total_disbursements,cash_on_hand',
                'limit': PAGE_SIZE,
                'offset': from_offset
            },
            headers=headers
        )

        page = response.json()
        if not page or len(page) == 0:
            break

        all_records.extend(page)

        if len(page) < PAGE_SIZE:
            break

        from_offset += PAGE_SIZE

    print(f"\n📊 TOTAL RECORDS: {len(all_records)}")

    # Analyze the data
    complete_data = 0
    missing_receipts = 0
    missing_disbursements = 0
    missing_cash = 0
    all_zeros = 0

    receipts_values = []
    disbursements_values = []
    cash_values = []

    for record in all_records:
        receipts = record.get('total_receipts') or 0
        disbursements = record.get('total_disbursements') or 0
        cash = record.get('cash_on_hand') or 0

        receipts_values.append(receipts)
        disbursements_values.append(disbursements)
        cash_values.append(cash)

        if receipts == 0 and disbursements == 0 and cash == 0:
            all_zeros += 1
        else:
            if receipts > 0 and disbursements > 0 and cash > 0:
                complete_data += 1
            if receipts == 0:
                missing_receipts += 1
            if disbursements == 0:
                missing_disbursements += 1
            if cash == 0:
                missing_cash += 1

    print(f"\n✅ COMPLETE DATA (all 3 metrics > 0): {complete_data} ({complete_data/len(all_records)*100:.1f}%)")
    print(f"⚠️  MISSING CASH ON HAND: {missing_cash} ({missing_cash/len(all_records)*100:.1f}%)")
    print(f"⚠️  MISSING RECEIPTS: {missing_receipts} ({missing_receipts/len(all_records)*100:.1f}%)")
    print(f"⚠️  MISSING DISBURSEMENTS: {missing_disbursements} ({missing_disbursements/len(all_records)*100:.1f}%)")
    print(f"⚠️  ALL ZEROS (no data): {all_zeros} ({all_zeros/len(all_records)*100:.1f}%)")

    # Show top fundraisers
    sorted_by_receipts = sorted(all_records, key=lambda x: x.get('total_receipts') or 0, reverse=True)[:5]

    print(f"\n🏆 TOP 5 FUNDRAISERS:")
    for i, record in enumerate(sorted_by_receipts, 1):
        receipts = record.get('total_receipts') or 0
        disbursements = record.get('total_disbursements') or 0
        cash = record.get('cash_on_hand') or 0

        print(f"  {i}. {record['candidate_id']}")
        print(f"     Receipts: ${receipts:,.0f} | Disbursements: ${disbursements:,.0f} | Cash: ${cash:,.0f}")

    # Statistical summary
    non_zero_receipts = [r for r in receipts_values if r > 0]
    non_zero_disbursements = [d for d in disbursements_values if d > 0]
    non_zero_cash = [c for c in cash_values if c > 0]

    print(f"\n📈 STATISTICAL SUMMARY:")
    print(f"  Total Receipts:")
    print(f"    - Non-zero records: {len(non_zero_receipts)}/{len(all_records)}")
    print(f"    - Average (non-zero): ${sum(non_zero_receipts)/len(non_zero_receipts):,.0f}" if non_zero_receipts else "    - No data")
    print(f"    - Max: ${max(receipts_values):,.0f}")

    print(f"  Total Disbursements:")
    print(f"    - Non-zero records: {len(non_zero_disbursements)}/{len(all_records)}")
    print(f"    - Average (non-zero): ${sum(non_zero_disbursements)/len(non_zero_disbursements):,.0f}" if non_zero_disbursements else "    - No data")
    print(f"    - Max: ${max(disbursements_values):,.0f}")

    print(f"  Cash on Hand:")
    print(f"    - Non-zero records: {len(non_zero_cash)}/{len(all_records)}")
    print(f"    - Average (non-zero): ${sum(non_zero_cash)/len(non_zero_cash):,.0f}" if non_zero_cash else "    - No data")
    print(f"    - Max: ${max(cash_values):,.0f}")


def check_candidate_metadata():
    """Check if we have candidate metadata for all financial records"""

    print(f"\n{'='*80}")
    print("CANDIDATE METADATA COMPLETENESS")
    print('='*80)

    # Get all unique candidate_ids from financial_summary
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={
            'select': 'candidate_id',
            'limit': 10000
        },
        headers=headers
    )

    financial_ids = set([r['candidate_id'] for r in response.json()])

    # Get all candidate_ids from candidates table
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/candidates",
        params={
            'select': 'candidate_id',
            'limit': 20000
        },
        headers=headers
    )

    candidate_ids = set([r['candidate_id'] for r in response.json()])

    print(f"\n✓ Unique candidates with financial data: {len(financial_ids)}")
    print(f"✓ Candidates in metadata table: {len(candidate_ids)}")

    missing = financial_ids - candidate_ids

    if missing:
        print(f"\n⚠️  MISSING METADATA for {len(missing)} candidates")
        print(f"   Sample IDs: {list(missing)[:10]}")
    else:
        print(f"\n✅ All candidates with financial data have metadata")


def main():
    print("="*80)
    print("COMPREHENSIVE DATA AUDIT - CAMPAIGN REFERENCE")
    print("="*80)
    print("\nChecking data completeness for all cycles...")

    # Audit each cycle
    cycles = [2026, 2024, 2022, 2020, 2018]

    for cycle in cycles:
        audit_cycle(cycle)

    # Check metadata completeness
    check_candidate_metadata()

    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print('='*80)

    print("\n📋 SUMMARY:")
    print("   This audit shows the completeness of our dataset for:")
    print("   - Total Receipts (total raised)")
    print("   - Total Disbursements (total spent)")
    print("   - Cash on Hand (ending cash position)")
    print("\n   Any gaps identified above need to be filled to have a complete dataset.")


if __name__ == '__main__':
    main()
