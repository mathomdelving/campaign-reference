"""
Fix Financial Import - Reimport with Candidate Validation
==========================================================

This script re-imports financial data for cycles where the import failed,
but validates that candidates exist before inserting financials.

"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_valid_candidates(cycle):
    """Fetch all candidate IDs for a given cycle from database."""
    url = f"{SUPABASE_URL}/rest/v1/candidates"
    params = {
        'cycle': f'eq.{cycle}',
        'select': 'candidate_id'
    }
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.ok:
        candidates = response.json()
        return set(c['candidate_id'] for c in candidates)
    return set()


def insert_batch(table_name, records, batch_size=1000, on_conflict=None):
    """Insert records into Supabase in batches using UPSERT."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    if on_conflict:
        url += f"?on_conflict={on_conflict}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
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
                print(f"  Upserted batch {i//batch_size + 1}: {inserted}/{total} records")
            else:
                error_msg = f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}"
                print(f"  {error_msg}")
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} error: {str(e)}"
            print(f"  {error_msg}")
            errors.append(error_msg)

    return inserted, errors


def import_financials_for_cycle(cycle):
    """Import financial data for a cycle, validating candidates exist."""
    print(f"\n{'='*80}")
    print(f"IMPORTING FINANCIALS FOR {cycle}")
    print('='*80)

    # Get valid candidate IDs
    print(f"\nFetching valid candidate IDs for {cycle}...")
    valid_candidates = get_valid_candidates(cycle)
    print(f"  Found {len(valid_candidates)} valid candidates")

    # Read financial file
    weball_file = f'fec_bulk_data/weball_{cycle}.txt'

    if not os.path.exists(weball_file):
        print(f"  ✗ File not found: {weball_file}")
        return 0, []

    print(f"\nReading financial data from {weball_file}...")

    # Column names for weball file
    WEBALLCANDS_COLUMNS = [
        'CAND_ID', 'CAND_NAME', 'CAND_ICI', 'PTY_CD', 'CAND_PTY_AFFILIATION',
        'TTL_RECEIPTS', 'TRANS_FROM_AUTH', 'TTL_DISB', 'TRANS_TO_AUTH',
        'COH_BOP', 'COH_COP', 'CAND_CONTRIB', 'CAND_LOANS', 'OTHER_LOANS',
        'CAND_LOAN_REPAY', 'OTHER_LOAN_REPAY', 'DEBTS_OWED_BY', 'TTL_INDIV_CONTRIB',
        'CAND_OFFICE_ST', 'CAND_OFFICE_DISTRICT', 'SPEC_ELECTION', 'PRIM_ELECTION',
        'RUN_ELECTION', 'GEN_ELECTION', 'GEN_ELECTION_PRECENT', 'OTHER_POL_CMTE_CONTRIB',
        'POL_PTY_CONTRIB', 'CVG_END_DT', 'INDIV_REFUNDS', 'CMTE_REFUNDS'
    ]

    df = pd.read_csv(
        weball_file,
        delimiter='|',
        names=WEBALLCANDS_COLUMNS,
        dtype=str,
        encoding='latin1'
    )

    print(f"  Loaded {len(df)} raw records")

    # Convert numeric columns
    numeric_cols = ['TTL_RECEIPTS', 'TTL_DISB', 'COH_COP']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Filter to records with financial data AND valid candidates
    df = df[df['TTL_RECEIPTS'].notna() | df['TTL_DISB'].notna()]
    print(f"  Filtered to {len(df)} records with financial data")

    # Filter to only valid candidates
    df = df[df['CAND_ID'].str.strip().isin(valid_candidates)]
    print(f"  Filtered to {len(df)} records with valid candidate IDs")

    if len(df) == 0:
        print("  ⚠ No records to import")
        return 0, []

    # Transform to database schema
    transformed = []
    for _, row in df.iterrows():
        # Parse coverage end date
        coverage_end_date = None
        if pd.notna(row['CVG_END_DT']):
            try:
                date_str = str(row['CVG_END_DT']).strip()
                if '/' in date_str:  # MM/DD/YYYY
                    coverage_end_date = datetime.strptime(date_str, '%m/%d/%Y').date().isoformat()
                elif len(date_str) == 8:  # YYYYMMDD
                    coverage_end_date = datetime.strptime(date_str, '%Y%m%d').date().isoformat()
            except:
                pass

        transformed.append({
            'candidate_id': row['CAND_ID'].strip(),
            'cycle': cycle,
            'total_receipts': float(row['TTL_RECEIPTS']) if pd.notna(row['TTL_RECEIPTS']) else None,
            'total_disbursements': float(row['TTL_DISB']) if pd.notna(row['TTL_DISB']) else None,
            'cash_on_hand': float(row['COH_COP']) if pd.notna(row['COH_COP']) else None,
            'coverage_start_date': None,
            'coverage_end_date': coverage_end_date,
            'report_year': cycle,
            'report_type': None
        })

    print(f"\n  Inserting {len(transformed)} financial records...")
    inserted, errors = insert_batch(
        'financial_summary',
        transformed,
        on_conflict='candidate_id,cycle,coverage_end_date'
    )

    print(f"\n  ✓ Inserted: {inserted}/{len(transformed)} records")
    if errors:
        print(f"  ✗ Errors: {len(errors)}")
        for error in errors[:3]:
            print(f"      {error}")

    return inserted, errors


def main():
    print("="*80)
    print("FIX FINANCIAL IMPORT - Reimport with Candidate Validation")
    print("="*80)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\nERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    cycles = [2024, 2022, 2020, 2018]

    total_inserted = 0
    total_errors = 0

    for cycle in cycles:
        inserted, errors = import_financials_for_cycle(cycle)
        total_inserted += inserted
        total_errors += len(errors)

    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Total financial records inserted: {total_inserted}")
    print(f"Total errors: {total_errors}")
    print("="*80)


if __name__ == "__main__":
    main()
