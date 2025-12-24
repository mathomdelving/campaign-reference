"""
Bulk Import FEC Data from CSV Files
====================================

This script imports FEC bulk data files (downloaded from https://www.fec.gov/data/browse-data/?tab=bulk-data)
into your Supabase database. It reuses the existing batch insert logic from load_to_supabase.py.

USAGE:
    1. Download FEC bulk files (e.g., cn26.zip, weball26.zip) and extract them
    2. Update the file paths in the main() function
    3. Run: python bulk_import_fec.py

SUPPORTED FILES:
    - Candidate Master (cn.txt) -> candidates table
    - All Candidates Summary (weball.txt) -> financial_summary table
    - [Future] Committee Filings -> quarterly_financials table

"""

import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


# ============================================================================
# REUSABLE BATCH INSERT (from load_to_supabase.py)
# ============================================================================

def insert_batch(table_name, records, batch_size=1000, on_conflict=None):
    """Insert records into Supabase in batches using UPSERT."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    # Add on_conflict parameter for upsert
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
                print(f"Upserted batch {i//batch_size + 1}: {inserted}/{total} records")
            else:
                error_msg = f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}"
                print(error_msg)
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} error: {str(e)}"
            print(error_msg)
            errors.append(error_msg)

    return inserted, errors


def log_refresh(cycle, records_updated, errors, status, duration):
    """Log the data refresh operation."""
    url = f"{SUPABASE_URL}/rest/v1/data_refresh_log"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    log_entry = {
        'cycle': cycle,
        'records_updated': records_updated,
        'errors': '\n'.join(errors) if errors else None,
        'status': status,
        'duration_seconds': duration
    }

    try:
        response = requests.post(url, headers=headers, json=log_entry)
        if response.status_code in [200, 201]:
            print("Refresh logged successfully")
        else:
            print(f"Failed to log refresh: {response.text}")
    except Exception as e:
        print(f"Error logging refresh: {str(e)}")


# ============================================================================
# FEC BULK FILE COLUMN MAPPINGS
# ============================================================================

# FEC Candidate Master file (cn.txt) column names
# Source: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/
CANDIDATE_MASTER_COLUMNS = [
    'CAND_ID',           # Candidate ID
    'CAND_NAME',         # Candidate Name
    'CAND_PTY_AFFILIATION',  # Party Code (3-letter)
    'CAND_ELECTION_YR',  # Election Year
    'CAND_OFFICE_ST',    # State
    'CAND_OFFICE',       # Office (H/S/P)
    'CAND_OFFICE_DISTRICT',  # District
    'CAND_ICI',          # Incumbent/Challenger/Open
    'CAND_STATUS',       # Status
    'CAND_PCC',          # Principal Campaign Committee
    'CAND_ST1',          # Mailing Address
    'CAND_ST2',          # Mailing Address 2
    'CAND_CITY',         # City
    'CAND_ST',           # State (mailing)
    'CAND_ZIP'           # ZIP
]

# FEC All Candidates Summary (weball.txt) column names
# Source: https://www.fec.gov/campaign-finance-data/all-candidates-file-description/
WEBALLCANDS_COLUMNS = [
    'CAND_ID',           # Candidate ID
    'CAND_NAME',         # Candidate Name
    'CAND_ICI',          # Incumbent/Challenger/Open
    'PTY_CD',            # Party Code
    'CAND_PTY_AFFILIATION',  # Party Affiliation
    'TTL_RECEIPTS',      # Total Receipts
    'TRANS_FROM_AUTH',   # Transfers from Authorized Committees
    'TTL_DISB',          # Total Disbursements
    'TRANS_TO_AUTH',     # Transfers to Authorized Committees
    'COH_BOP',           # Cash on Hand Beginning of Period
    'COH_COP',           # Cash on Hand Close of Period
    'CAND_CONTRIB',      # Candidate Contributions
    'CAND_LOANS',        # Candidate Loans
    'OTHER_LOANS',       # Other Loans
    'CAND_LOAN_REPAY',   # Candidate Loan Repayments
    'OTHER_LOAN_REPAY',  # Other Loan Repayments
    'DEBTS_OWED_BY',     # Debts Owed By
    'TTL_INDIV_CONTRIB', # Total Individual Contributions
    'CAND_OFFICE_ST',    # State
    'CAND_OFFICE_DISTRICT',  # District
    'SPEC_ELECTION',     # Special Election Status
    'PRIM_ELECTION',     # Primary Election Status
    'RUN_ELECTION',      # Runoff Election Status
    'GEN_ELECTION',      # General Election Status
    'GEN_ELECTION_PRECENT',  # General Election Percentage
    'OTHER_POL_CMTE_CONTRIB',  # Contributions from Other Political Committees
    'POL_PTY_CONTRIB',   # Political Party Contributions
    'CVG_END_DT',        # Coverage End Date
    'INDIV_REFUNDS',     # Individual Refunds
    'CMTE_REFUNDS'       # Committee Refunds
]

# Party code mapping (3-letter to full name)
PARTY_MAPPING = {
    'DEM': 'DEMOCRATIC PARTY',
    'REP': 'REPUBLICAN PARTY',
    'IND': 'INDEPENDENT',
    'LIB': 'LIBERTARIAN PARTY',
    'GRE': 'GREEN PARTY',
    'CON': 'CONSTITUTION PARTY',
    'UNK': None,
    '': None
}


# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

def transform_candidate_master(csv_path, cycle):
    """
    Transform FEC Candidate Master CSV to candidates table format.

    Args:
        csv_path: Path to cn.txt file (pipe-delimited)
        cycle: Election cycle year (e.g., 2026)

    Returns:
        List of dicts ready for database insert
    """
    print(f"\n--- Processing Candidate Master File ---")
    print(f"File: {csv_path}")

    # Read pipe-delimited file
    df = pd.read_csv(
        csv_path,
        delimiter='|',
        names=CANDIDATE_MASTER_COLUMNS,
        dtype=str,  # Read all as strings to avoid type issues
        encoding='latin1'  # FEC files use latin1 encoding
    )

    print(f"Loaded {len(df)} raw candidate records")

    # Filter to specific cycle and relevant offices (House/Senate)
    df = df[
        (df['CAND_ELECTION_YR'] == str(cycle)) &
        (df['CAND_OFFICE'].isin(['H', 'S']))
    ]

    print(f"Filtered to {len(df)} candidates for {cycle} (House/Senate only)")

    # Transform to database schema
    transformed = []
    for _, row in df.iterrows():
        # Map party code to full name
        party_code = row['CAND_PTY_AFFILIATION'].strip() if pd.notna(row['CAND_PTY_AFFILIATION']) else ''
        party_full = PARTY_MAPPING.get(party_code, party_code if party_code else None)

        # Handle district (pad with zeros for House, None for Senate)
        district = None
        if row['CAND_OFFICE'] == 'H' and pd.notna(row['CAND_OFFICE_DISTRICT']):
            district = row['CAND_OFFICE_DISTRICT'].strip().zfill(2)  # '1' -> '01'

        transformed.append({
            'candidate_id': row['CAND_ID'].strip(),
            'name': row['CAND_NAME'].strip() if pd.notna(row['CAND_NAME']) else None,
            'party': party_full,
            'state': row['CAND_OFFICE_ST'].strip() if pd.notna(row['CAND_OFFICE_ST']) else None,
            'district': district,
            'office': row['CAND_OFFICE'].strip() if pd.notna(row['CAND_OFFICE']) else None,
            'cycle': cycle
        })

    print(f"Transformed {len(transformed)} candidate records")
    return transformed


def transform_weballcands(csv_path, cycle):
    """
    Transform FEC All Candidates Summary CSV to financial_summary table format.

    Args:
        csv_path: Path to weball.txt file (pipe-delimited)
        cycle: Election cycle year (e.g., 2026)

    Returns:
        List of dicts ready for database insert
    """
    print(f"\n--- Processing All Candidates Summary File ---")
    print(f"File: {csv_path}")

    # Read pipe-delimited file
    df = pd.read_csv(
        csv_path,
        delimiter='|',
        names=WEBALLCANDS_COLUMNS,
        dtype=str,  # Read all as strings initially
        encoding='latin1'
    )

    print(f"Loaded {len(df)} raw financial records")

    # Convert numeric columns
    numeric_cols = ['TTL_RECEIPTS', 'TTL_DISB', 'COH_COP']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Filter out records with no financial data
    df = df[df['TTL_RECEIPTS'].notna() | df['TTL_DISB'].notna()]

    print(f"Filtered to {len(df)} records with financial data")

    # Transform to database schema
    transformed = []
    for _, row in df.iterrows():
        # Handle district (pad with zeros)
        district = None
        if pd.notna(row['CAND_OFFICE_DISTRICT']):
            district_str = str(row['CAND_OFFICE_DISTRICT']).strip()
            if district_str and district_str != '00':
                district = district_str.zfill(2)

        # Parse coverage end date (format: MM/DD/YYYY or YYYYMMDD)
        coverage_end_date = None
        if pd.notna(row['CVG_END_DT']):
            try:
                date_str = str(row['CVG_END_DT']).strip()
                if '/' in date_str:  # MM/DD/YYYY
                    coverage_end_date = datetime.strptime(date_str, '%m/%d/%Y').date().isoformat()
                elif len(date_str) == 8:  # YYYYMMDD
                    coverage_end_date = datetime.strptime(date_str, '%Y%m%d').date().isoformat()
            except:
                pass  # Invalid date, leave as None

        transformed.append({
            'candidate_id': row['CAND_ID'].strip(),
            'cycle': cycle,
            'total_receipts': float(row['TTL_RECEIPTS']) if pd.notna(row['TTL_RECEIPTS']) else None,
            'total_disbursements': float(row['TTL_DISB']) if pd.notna(row['TTL_DISB']) else None,
            'cash_on_hand': float(row['COH_COP']) if pd.notna(row['COH_COP']) else None,
            'coverage_start_date': None,  # Not available in summary file
            'coverage_end_date': coverage_end_date,
            'report_year': cycle,
            'report_type': None  # Not available in summary file
        })

    print(f"Transformed {len(transformed)} financial records")
    return transformed


# ============================================================================
# MAIN IMPORT FUNCTION
# ============================================================================

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("FEC BULK DATA IMPORT")
    print("=" * 80)

    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return

    # ========================================================================
    # CONFIGURATION: Update these paths to your downloaded FEC files
    # ========================================================================

    CYCLE = 2026  # Change this to import different cycles (2024, 2022, etc.)

    # Download from: https://www.fec.gov/data/browse-data/?tab=bulk-data
    # Example: cn26.zip (extract to get cn.txt)
    CANDIDATE_MASTER_FILE = 'fec_bulk_data/cn.txt'  # Actual extracted filename

    # Example: weball26.zip (extract to get weball.txt)
    WEBALLCANDS_FILE = 'fec_bulk_data/weball26.txt'  # Actual extracted filename

    # ========================================================================

    all_errors = []
    total_inserted = 0

    # Import Candidates
    if os.path.exists(CANDIDATE_MASTER_FILE):
        try:
            candidates = transform_candidate_master(CANDIDATE_MASTER_FILE, CYCLE)
            if candidates:
                candidates_inserted, candidate_errors = insert_batch(
                    'candidates',
                    candidates,
                    on_conflict='candidate_id'
                )
                all_errors.extend(candidate_errors)
                total_inserted += candidates_inserted
                print(f"\n✓ Candidates: {candidates_inserted}/{len(candidates)} inserted")
            else:
                print("\n⚠ No candidates to insert")
        except Exception as e:
            error_msg = f"Error processing candidates: {str(e)}"
            print(f"\n✗ {error_msg}")
            all_errors.append(error_msg)
    else:
        print(f"\n⚠ Candidate file not found: {CANDIDATE_MASTER_FILE}")
        print(f"   Download from: https://www.fec.gov/files/bulk-downloads/2026/cn26.zip")

    # Import Financial Summaries
    if os.path.exists(WEBALLCANDS_FILE):
        try:
            financials = transform_weballcands(WEBALLCANDS_FILE, CYCLE)
            if financials:
                financials_inserted, financial_errors = insert_batch(
                    'financial_summary',
                    financials,
                    on_conflict='candidate_id,cycle,coverage_end_date'
                )
                all_errors.extend(financial_errors)
                total_inserted += financials_inserted
                print(f"\n✓ Financials: {financials_inserted}/{len(financials)} inserted")
            else:
                print("\n⚠ No financials to insert")
        except Exception as e:
            error_msg = f"Error processing financials: {str(e)}"
            print(f"\n✗ {error_msg}")
            all_errors.append(error_msg)
    else:
        print(f"\n⚠ Financial file not found: {WEBALLCANDS_FILE}")
        print(f"   Download from: https://www.fec.gov/files/bulk-downloads/2026/weball26.zip")

    # Calculate duration and status
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(all_errors) == 0 else 'partial' if total_inserted > 0 else 'failed'

    # Log the refresh
    print("\n--- Logging Refresh ---")
    log_refresh(CYCLE, total_inserted, all_errors, status, duration)

    # Final summary
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Total records inserted: {total_inserted}")
    print(f"Total errors: {len(all_errors)}")
    print(f"Duration: {duration} seconds")
    print(f"Status: {status}")

    if all_errors:
        print("\nErrors encountered:")
        for error in all_errors[:10]:  # Show first 10 errors
            print(f"  - {error}")


if __name__ == "__main__":
    main()
