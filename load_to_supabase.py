import json
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def load_json_file(filename):
    """Load and return JSON data from file."""
    print(f"Loading {filename}...")
    with open(filename, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records from {filename}")
    return data

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

def transform_candidates(candidates_data):
    """Transform candidate JSON to database format."""
    transformed = []

    for candidate in candidates_data:
        # Get cycle from cycles array - use the LATEST cycle (2026 for our data)
        # Incumbents may have multiple cycles, we want the most recent
        cycles = candidate.get('cycles', [])
        cycle = max(cycles) if cycles else None

        transformed.append({
            'candidate_id': candidate['candidate_id'],
            'name': candidate['name'],
            'party': candidate.get('party_full'),
            'state': candidate.get('state'),
            'district': candidate.get('district'),
            'office': candidate.get('office'),  # Already 'H' or 'S'
            'cycle': cycle
        })
    return transformed
    transformed = []
    
def transform_financials(financials_data):
    """Transform financial JSON to database format."""
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
            'report_year': record.get('report_year'),
            'report_type': record.get('report_type')
        })
    
    return transformed

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

def main():
    start_time = datetime.now()
    print("=== Starting Supabase Data Load ===\n")
    
    # Verify credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return
    
    all_errors = []
    total_inserted = 0
    
    # Load and insert candidates
    print("\n--- Loading Candidates ---")
    candidates_data = load_json_file('candidates_2026.json')
    candidates_transformed = transform_candidates(candidates_data)
    candidates_inserted, candidate_errors = insert_batch('candidates', candidates_transformed, on_conflict='candidate_id')
    all_errors.extend(candidate_errors)
    total_inserted += candidates_inserted

    print(f"\nCandidates: {candidates_inserted}/{len(candidates_transformed)} inserted")

    # Load and insert financials
    print("\n--- Loading Financial Data ---")
    financials_data = load_json_file('financials_2026.json')
    financials_transformed = transform_financials(financials_data)
    financials_inserted, financial_errors = insert_batch('financial_summary', financials_transformed, on_conflict='candidate_id,cycle,coverage_end_date')
    all_errors.extend(financial_errors)
    total_inserted += financials_inserted
    
    print(f"\nFinancials: {financials_inserted}/{len(financials_transformed)} inserted")
    
    # Calculate duration and status
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(all_errors) == 0 else 'partial' if total_inserted > 0 else 'failed'
    
    # Log the refresh
    print("\n--- Logging Refresh ---")
    log_refresh(2026, total_inserted, all_errors, status, duration)
    
    # Final summary
    print("\n=== Load Complete ===")
    print(f"Total records inserted: {total_inserted}")
    print(f"Total errors: {len(all_errors)}")
    print(f"Duration: {duration} seconds")
    print(f"Status: {status}")
    
    if all_errors:
        print("\nErrors encountered:")
        for error in all_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

if __name__ == "__main__":
    main()