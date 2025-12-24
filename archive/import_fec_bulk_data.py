#!/usr/bin/env python3
"""
Import FEC Bulk Data Files
Complete import of ALL candidates and financial data from FEC bulk files

File formats:
- cn_YYYY.txt: Candidate metadata
- weball_YYYY.txt: Financial summaries (all candidates)

This will give us COMPLETE data much faster than API calls.
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

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

BULK_DATA_DIR = 'fec_bulk_data'

# Column mappings based on FEC documentation
CN_COLUMNS = {
    0: 'candidate_id',
    1: 'name',
    2: 'party',
    3: 'election_year',
    4: 'state',
    5: 'office',
    6: 'district',
    7: 'incumbent_challenge',
    8: 'candidate_status',
    9: 'committee_id'
}

WEBALL_COLUMNS = {
    0: 'candidate_id',
    1: 'name',
    2: 'incumbent_challenge',
    3: 'party_code',
    4: 'party',
    5: 'total_receipts',
    6: 'transfers_from_authorized',
    7: 'total_disbursements',
    8: 'transfers_to_authorized',
    9: 'beginning_cash',
    10: 'cash_on_hand',  # ending_cash
    11: 'contributions_from_candidate',
    17: 'total_individual_contributions',
    18: 'state',
    19: 'district'
}


def import_candidates(cycle):
    """Import candidate metadata from cn_YYYY.txt"""

    filename = f'{BULK_DATA_DIR}/cn_{cycle}.txt'

    if not os.path.exists(filename):
        print(f"⚠️  {filename} not found - skipping")
        return 0

    print(f"\n{'='*80}")
    print(f"Importing Candidates - Cycle {cycle}")
    print('='*80)

    candidates = []

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            try:
                fields = line.strip().split('|')

                # Extract fields
                candidate_id = fields[0]
                name = fields[1]
                party = fields[2] if len(fields) > 2 else None
                state = fields[4] if len(fields) > 4 else None
                office = fields[5] if len(fields) > 5 else None
                district = fields[6] if len(fields) > 6 else None
                incumbent_challenge = fields[7] if len(fields) > 7 else None

                # Create candidate record
                candidate = {
                    'candidate_id': candidate_id,
                    'name': name,
                    'party': party if party else None,
                    'state': state if state else None,
                    'office': office if office else None,
                    'district': district if district and district != '00' else None,
                    'incumbent_challenge': incumbent_challenge if incumbent_challenge else None
                }

                candidates.append(candidate)

                # Batch insert every 500 records
                if len(candidates) >= 500:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/candidates",
                        headers=headers_upsert,
                        json=candidates
                    )

                    if response.status_code not in [200, 201]:
                        print(f"❌ Error inserting batch: {response.status_code}")
                        print(response.text)
                    else:
                        print(f"  ✓ Inserted {len(candidates)} candidates (line {line_num})")

                    candidates = []

            except Exception as e:
                print(f"❌ Error on line {line_num}: {e}")
                continue

    # Insert remaining
    if candidates:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/candidates",
            headers=headers_upsert,
            json=candidates
        )

        if response.status_code in [200, 201]:
            print(f"  ✓ Inserted final {len(candidates)} candidates")

    print(f"✅ Candidate import complete for {cycle}")
    return line_num


def import_financials(cycle):
    """Import financial data from weball_YYYY.txt"""

    # Handle 2026 special case
    if cycle == 2026:
        filename = f'{BULK_DATA_DIR}/weball26.txt'
    else:
        filename = f'{BULK_DATA_DIR}/weball_{cycle}.txt'

    if not os.path.exists(filename):
        print(f"⚠️  {filename} not found - skipping")
        return 0

    print(f"\n{'='*80}")
    print(f"Importing Financial Data - Cycle {cycle}")
    print('='*80)

    financials = []

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            try:
                fields = line.strip().split('|')

                # Extract fields (column numbers from WEBALL_COLUMNS)
                candidate_id = fields[0]

                # Parse financial amounts (handle empty/invalid values)
                def parse_float(val):
                    try:
                        return float(val) if val and val.strip() else 0.0
                    except:
                        return 0.0

                total_receipts = parse_float(fields[5]) if len(fields) > 5 else 0.0
                total_disbursements = parse_float(fields[7]) if len(fields) > 7 else 0.0
                cash_on_hand = parse_float(fields[10]) if len(fields) > 10 else 0.0

                # Create financial record
                financial = {
                    'candidate_id': candidate_id,
                    'cycle': cycle,
                    'total_receipts': total_receipts,
                    'total_disbursements': total_disbursements,
                    'cash_on_hand': cash_on_hand
                }

                financials.append(financial)

                # Batch insert every 500 records
                if len(financials) >= 500:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/financial_summary",
                        headers=headers_upsert,
                        json=financials
                    )

                    if response.status_code not in [200, 201]:
                        print(f"❌ Error inserting batch: {response.status_code}")
                        print(response.text[:200])
                    else:
                        print(f"  ✓ Inserted {len(financials)} financial records (line {line_num})")

                    financials = []

            except Exception as e:
                print(f"❌ Error on line {line_num}: {e}")
                continue

    # Insert remaining
    if financials:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            headers=headers_upsert,
            json=financials
        )

        if response.status_code in [200, 201]:
            print(f"  ✓ Inserted final {len(financials)} financial records")
        else:
            print(f"❌ Error inserting final batch: {response.status_code}")
            print(response.text[:200])

    print(f"✅ Financial import complete for {cycle}")
    return line_num


def verify_import(cycle):
    """Verify data was imported correctly"""

    print(f"\n{'='*80}")
    print(f"Verification - Cycle {cycle}")
    print('='*80)

    # Check financial_summary count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/financial_summary",
        params={'cycle': f'eq.{cycle}', 'select': 'count', 'limit': 1},
        headers={**headers_query, 'Prefer': 'count=exact'}
    )

    count = int(response.headers.get('Content-Range', '0/0').split('/')[-1])
    print(f"  Financial records: {count}")

    # Check for Christy Smith 2022 specifically
    if cycle == 2022:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'candidate_id': 'eq.H0CA25154',
                'cycle': 'eq.2022',
                'select': 'total_receipts,total_disbursements,cash_on_hand'
            },
            headers=headers_query
        )

        data = response.json()
        if data:
            print(f"\n  ✓ Christy Smith 2022 verification:")
            print(f"    Receipts: ${data[0]['total_receipts']:,.2f}")
            print(f"    Disbursed: ${data[0]['total_disbursements']:,.2f}")
            print(f"    Cash: ${data[0]['cash_on_hand']:,.2f}")
        else:
            print(f"\n  ❌ Christy Smith 2022 NOT FOUND")


def main():
    print("="*80)
    print("FEC BULK DATA IMPORT")
    print("="*80)
    print("\nThis will import:")
    print("- Candidate metadata (cn_YYYY.txt)")
    print("- Financial summaries (weball_YYYY.txt)")
    print("\nFor cycles: 2018, 2020, 2022, 2024, 2026")

    cycles = [2026, 2024, 2022, 2020, 2018]

    for cycle in cycles:
        # Import candidates first
        import_candidates(cycle)

        # Then import financials
        import_financials(cycle)

        # Verify
        verify_import(cycle)

    print(f"\n{'='*80}")
    print("IMPORT COMPLETE")
    print('='*80)
    print("\nNext steps:")
    print("1. All candidate metadata and financial data should now be in database")
    print("2. Run comprehensive audit to verify completeness")
    print("3. Cash on hand data should be included from bulk files")


if __name__ == '__main__':
    main()
