"""
Incremental FEC Data Update Script

This script checks for new FEC filings since the last update and only refreshes
data for candidates with new activity. Much faster than full data pull.

Usage:
    python incremental_update.py              # Normal incremental update
    python incremental_update.py --lookback 7 # Check last 7 days
    python incremental_update.py --force-full # Force full refresh
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BASE_URL = "https://api.open.fec.gov/v1"
CYCLE = 2026

# Validate environment variables
if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("ERROR: Missing required environment variables")
    print("Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
    sys.exit(1)


def get_last_update_time():
    """Get the timestamp of the last successful data update"""
    url = f"{SUPABASE_URL}/rest/v1/data_refresh_log"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'order': 'fetch_date.desc',
        'limit': 1,
        'status': 'eq.success'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        logs = response.json()
        if logs:
            last_update = logs[0].get('fetch_date')
            print(f"Last successful update: {last_update}")
            return last_update

    # Default to checking last 24 hours if no log found
    return (datetime.now() - timedelta(days=1)).isoformat()


def get_recent_filings(since_date, max_pages=10):
    """
    Fetch all filings received since the given date

    Args:
        since_date: ISO format date string (YYYY-MM-DD)
        max_pages: Maximum number of pages to fetch (safety limit)

    Returns:
        List of filing records
    """
    print(f"\n=== Fetching Recent Filings ===")
    print(f"Looking for filings since: {since_date}")

    all_filings = []
    page = 1

    while page <= max_pages:
        url = f"{BASE_URL}/filings/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': CYCLE,
            'form_type': 'F3',  # House/Senate candidate reports
            'min_receipt_date': since_date,
            'sort': '-receipt_date',
            'per_page': 100,
            'page': page
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            all_filings.extend(results)
            print(f"  Page {page}: {len(results)} filings")

            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break

            page += 1
            time.sleep(0.5)  # Rate limiting

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching page {page}: {e}")
            break

    print(f"\nTotal recent filings: {len(all_filings)}")
    return all_filings


def extract_candidate_ids_from_filings(filings):
    """
    Extract unique candidate IDs from filings

    Note: Some filings may not have candidate_id directly, so we use committee_id
    and will need to look up the candidate for that committee
    """
    candidate_ids = set()
    committee_ids = set()

    for filing in filings:
        candidate_id = filing.get('candidate_id')
        committee_id = filing.get('committee_id')

        if candidate_id:
            candidate_ids.add(candidate_id)
        elif committee_id:
            committee_ids.add(committee_id)

    print(f"\nFound {len(candidate_ids)} direct candidate IDs")
    print(f"Found {len(committee_ids)} committee IDs (need to resolve to candidates)")

    # Resolve committee IDs to candidate IDs
    for committee_id in committee_ids:
        candidate_id = get_candidate_id_for_committee(committee_id)
        if candidate_id:
            candidate_ids.add(candidate_id)

    print(f"Total unique candidates to update: {len(candidate_ids)}")
    return list(candidate_ids)


def get_candidate_id_for_committee(committee_id):
    """Look up which candidate a committee belongs to"""
    url = f"{BASE_URL}/committee/{committee_id}/"
    params = {'api_key': FEC_API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            candidate_id = results[0].get('candidate_ids', [])
            if candidate_id:
                return candidate_id[0]

        time.sleep(0.5)

    except requests.exceptions.RequestException:
        pass

    return None


def fetch_candidate_info(candidate_id):
    """Fetch candidate basic info"""
    url = f"{BASE_URL}/candidate/{candidate_id}/"
    params = {'api_key': FEC_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]

    except requests.exceptions.RequestException as e:
        print(f"    Error fetching candidate info: {e}")

    return None


def fetch_candidate_financials(candidate_id):
    """Fetch candidate financial totals"""
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': CYCLE
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]

    except requests.exceptions.RequestException as e:
        print(f"    Error fetching financials: {e}")

    return None


def update_candidates_in_supabase(candidate_ids):
    """
    Update candidate and financial data in Supabase for given candidate IDs

    Returns:
        Number of candidates updated successfully
    """
    print(f"\n=== Updating {len(candidate_ids)} Candidates ===")

    updated_candidates = 0
    updated_financials = 0
    errors = []

    for idx, candidate_id in enumerate(candidate_ids, 1):
        print(f"  [{idx}/{len(candidate_ids)}] {candidate_id}...", end=" ")

        # Fetch candidate info
        candidate_info = fetch_candidate_info(candidate_id)
        time.sleep(0.5)

        if not candidate_info:
            print("✗ (no candidate info)")
            errors.append(f"{candidate_id}: No candidate info found")
            continue

        # Fetch financial data
        financial_data = fetch_candidate_financials(candidate_id)
        time.sleep(0.5)

        if not financial_data:
            print("✗ (no financial data)")
            errors.append(f"{candidate_id}: No financial data found")
            continue

        # Update candidate record
        candidate_record = {
            'candidate_id': candidate_id,
            'name': candidate_info.get('name'),
            'party': candidate_info.get('party_full'),
            'state': candidate_info.get('state'),
            'district': candidate_info.get('district'),
            'office': candidate_info.get('office'),
            'cycle': CYCLE
        }

        if upsert_candidate(candidate_record):
            updated_candidates += 1

        # Update financial record
        financial_record = {
            'candidate_id': candidate_id,
            'cycle': CYCLE,
            'total_receipts': financial_data.get('receipts'),
            'total_disbursements': financial_data.get('disbursements'),
            'cash_on_hand': financial_data.get('last_cash_on_hand_end_period'),
            'coverage_start_date': financial_data.get('coverage_start_date'),
            'coverage_end_date': financial_data.get('coverage_end_date'),
            'report_year': financial_data.get('last_report_year'),
            'report_type': financial_data.get('last_report_type_full')
        }

        if upsert_financial(financial_record):
            updated_financials += 1
            print(f"✓ (${financial_data.get('receipts', 0):,.0f} raised)")
        else:
            print("✗ (update failed)")
            errors.append(f"{candidate_id}: Failed to update")

    print(f"\nUpdated: {updated_candidates} candidates, {updated_financials} financial records")

    return updated_candidates + updated_financials, errors


def upsert_candidate(record):
    """Upsert a single candidate record"""
    url = f"{SUPABASE_URL}/rest/v1/candidates?on_conflict=candidate_id"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    try:
        response = requests.post(url, headers=headers, json=record)
        return response.status_code in [200, 201, 204]
    except:
        return False


def upsert_financial(record):
    """Upsert a single financial record"""
    url = f"{SUPABASE_URL}/rest/v1/financial_summary?on_conflict=candidate_id,cycle,coverage_end_date"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    try:
        response = requests.post(url, headers=headers, json=record)
        return response.status_code in [200, 201, 204]
    except:
        return False


def log_refresh(records_updated, errors, status, duration, update_type='incremental'):
    """Log the refresh operation"""
    url = f"{SUPABASE_URL}/rest/v1/data_refresh_log"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    log_entry = {
        'fetch_date': datetime.now().isoformat(),
        'cycle': CYCLE,
        'records_updated': records_updated,
        'errors': '\n'.join(errors[:10]) if errors else None,  # First 10 errors
        'status': status,
        'duration_seconds': duration
    }

    try:
        response = requests.post(url, headers=headers, json=log_entry)
        if response.status_code in [200, 201]:
            print("✓ Refresh logged successfully")
        else:
            print(f"✗ Failed to log refresh: {response.status_code}")
    except Exception as e:
        print(f"✗ Error logging refresh: {e}")


def main():
    start_time = datetime.now()

    print("\n" + "="*70)
    print("FEC INCREMENTAL DATA UPDATE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Parse command line arguments
    lookback_days = None
    force_full = '--force-full' in sys.argv

    for arg in sys.argv[1:]:
        if arg.startswith('--lookback'):
            try:
                lookback_days = int(sys.argv[sys.argv.index(arg) + 1])
            except:
                pass

    # Determine lookback date
    if lookback_days:
        since_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        print(f"Mode: Custom lookback ({lookback_days} days)")
    elif force_full:
        print(f"Mode: FULL REFRESH - This will take 17-18 hours!")
        print("Use the original fetch_fec_data.py script instead.")
        sys.exit(0)
    else:
        last_update = get_last_update_time()
        since_date = datetime.fromisoformat(last_update.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        print(f"Mode: Incremental update since last refresh")

    # Step 1: Get recent filings
    recent_filings = get_recent_filings(since_date)

    if not recent_filings:
        print("\n✓ No new filings found - data is up to date!")
        duration = int((datetime.now() - start_time).total_seconds())
        log_refresh(0, [], 'success', duration, 'incremental')
        return

    # Step 2: Extract candidate IDs
    candidate_ids = extract_candidate_ids_from_filings(recent_filings)

    if not candidate_ids:
        print("\n✓ No candidates to update")
        duration = int((datetime.now() - start_time).total_seconds())
        log_refresh(0, [], 'success', duration, 'incremental')
        return

    # Step 3: Update candidates
    records_updated, errors = update_candidates_in_supabase(candidate_ids)

    # Calculate stats
    duration = int((datetime.now() - start_time).total_seconds())
    status = 'success' if len(errors) == 0 else 'partial' if records_updated > 0 else 'failed'

    # Log the refresh
    print(f"\n=== Logging Update ===")
    log_refresh(records_updated, errors, status, duration, 'incremental')

    # Final summary
    print("\n" + "="*70)
    print("UPDATE COMPLETE")
    print(f"Duration: {duration} seconds")
    print(f"Records updated: {records_updated}")
    print(f"Errors: {len(errors)}")
    print(f"Status: {status.upper()}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
