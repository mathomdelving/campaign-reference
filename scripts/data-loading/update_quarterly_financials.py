"""
Quarterly Financials Update Script

This script fetches quarterly financial reports from the FEC API and updates
the candidate_financials table with individual quarter breakdown data.

This is separate from incremental_update.py which updates cumulative totals
in financial_summary for the leaderboard.

Usage:
    python update_quarterly_financials.py              # Normal update (last 7 days)
    python update_quarterly_financials.py --lookback 30  # Check last 30 days
    python update_quarterly_financials.py --cycle 2024   # Specific cycle
    python update_quarterly_financials.py --dry-run      # Preview without writing
"""

import requests
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
DEFAULT_CYCLE = 2026

# Validate environment variables
if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("ERROR: Missing required environment variables")
    print("Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
    sys.exit(1)


def retry_request(func, *args, **kwargs):
    """Retry a request with exponential backoff for rate limiting (429)"""
    max_retries = 5
    base_wait = 2

    for attempt in range(max_retries):
        try:
            response = func(*args, **kwargs)
            if response.status_code == 429:
                wait_time = base_wait * (2 ** attempt)
                print(f"    ⚠️  Rate limited (429). Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            return response
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = base_wait * (2 ** attempt)
                print(f"    ⚠️  Connection error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise e
    return None


def get_candidate_id_from_committee(committee_id):
    """Look up candidate_id from committee_id using committee_designations"""
    url = f"{SUPABASE_URL}/rest/v1/committee_designations"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    params = {
        'committee_id': f'eq.{committee_id}',
        'select': 'candidate_id',
        'limit': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and data[0].get('candidate_id'):
                return data[0]['candidate_id']
    except Exception as e:
        pass

    return None


def get_candidate_info(candidate_id):
    """Get candidate info from our database"""
    url = f"{SUPABASE_URL}/rest/v1/candidates"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    params = {
        'candidate_id': f'eq.{candidate_id}',
        'limit': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]
    except Exception as e:
        print(f"    Error fetching candidate {candidate_id}: {e}")

    return None


def fetch_quarterly_reports(since_date, cycle=DEFAULT_CYCLE, max_pages=50):
    """
    Fetch quarterly financial reports from FEC API.

    Returns reports with form_type F3 (House/Senate campaign reports)
    which contain quarterly financial breakdowns.
    """
    print(f"\n=== Fetching Quarterly Reports ===")
    print(f"Since: {since_date}")
    print(f"Cycle: {cycle}")

    all_reports = []
    page = 1

    while page <= max_pages:
        url = f"{BASE_URL}/reports/house-senate/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'min_receipt_date': since_date,
            'sort': '-receipt_date',
            'per_page': 100,
            'page': page,
            'is_amended': False  # Only get original filings, not amendments
        }

        try:
            response = retry_request(requests.get, url, params=params)
            if not response or response.status_code != 200:
                print(f"  Error fetching page {page}: {response.status_code if response else 'No response'}")
                break

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            all_reports.extend(results)
            print(f"  Page {page}: {len(results)} reports (total: {len(all_reports)})")

            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break

            page += 1
            time.sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"\nTotal reports fetched: {len(all_reports)}")
    return all_reports


def transform_report_to_record(report, candidate_info, candidate_id):
    """Transform an FEC report into a candidate_financials record"""

    # Map report type to readable format
    report_type = report.get('report_type_full') or report.get('report_type') or 'Unknown'

    # Get coverage dates - strip time portion if present
    coverage_start = report.get('coverage_start_date')
    coverage_end = report.get('coverage_end_date')

    if coverage_start and 'T' in coverage_start:
        coverage_start = coverage_start.split('T')[0]
    if coverage_end and 'T' in coverage_end:
        coverage_end = coverage_end.split('T')[0]

    # Calculate report year from coverage end date
    report_year = None
    if coverage_end:
        try:
            report_year = int(coverage_end[:4])
        except:
            pass

    # Parse filing_id - strip "FEC-" prefix if present and convert to integer
    raw_filing_id = report.get('fec_file_id')
    filing_id = None
    if raw_filing_id:
        if isinstance(raw_filing_id, str) and raw_filing_id.startswith('FEC-'):
            try:
                filing_id = int(raw_filing_id.replace('FEC-', ''))
            except ValueError:
                filing_id = None
        elif isinstance(raw_filing_id, (int, float)):
            filing_id = int(raw_filing_id)

    record = {
        'candidate_id': candidate_id,
        'committee_id': report.get('committee_id'),
        'name': candidate_info.get('name') if candidate_info else report.get('candidate_name'),
        'party': candidate_info.get('party') if candidate_info else None,
        'state': candidate_info.get('state') if candidate_info else None,
        'district': candidate_info.get('district') if candidate_info else None,
        'office': candidate_info.get('office') if candidate_info else None,
        'person_id': candidate_info.get('person_id') if candidate_info else None,
        'cycle': report.get('cycle'),
        'report_type': report_type,
        'report_year': report_year,
        'coverage_start_date': coverage_start,
        'coverage_end_date': coverage_end,
        'total_receipts': report.get('total_receipts_period'),  # Period amount, not YTD
        'total_disbursements': report.get('total_disbursements_period'),  # Period amount
        'cash_beginning': report.get('cash_on_hand_beginning_period'),
        'cash_ending': report.get('cash_on_hand_end_period'),
        'cash_on_hand': report.get('cash_on_hand_end_period'),
        'filing_id': filing_id,
        'is_amendment': report.get('is_amended', False),
        'updated_at': datetime.now().isoformat()
    }

    return record


def upsert_quarterly_record(record, dry_run=False):
    """Upsert a quarterly financial record"""
    if dry_run:
        return True

    url = f"{SUPABASE_URL}/rest/v1/candidate_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    # Use candidate_id + cycle + coverage_end_date as unique key
    params = {
        'on_conflict': 'candidate_id,cycle,coverage_end_date'
    }

    try:
        response = requests.post(url, headers=headers, json=record, params=params)
        if response.status_code not in [200, 201, 204]:
            print(f"    Upsert failed ({response.status_code}): {response.text[:200]}")
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"    Error upserting record: {e}")
        return False


def check_existing_record(candidate_id, cycle, coverage_end_date):
    """Check if a record already exists"""
    url = f"{SUPABASE_URL}/rest/v1/candidate_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    params = {
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}',
        'coverage_end_date': f'eq.{coverage_end_date}',
        'select': 'id,updated_at'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
    except:
        pass

    return None


def main():
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("QUARTERLY FINANCIALS UPDATE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Parse arguments
    lookback_days = 7
    cycle = DEFAULT_CYCLE
    dry_run = '--dry-run' in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == '--lookback' and i + 1 < len(sys.argv):
            try:
                lookback_days = int(sys.argv[i + 1])
            except ValueError:
                pass
        elif arg == '--cycle' and i + 1 < len(sys.argv):
            try:
                cycle = int(sys.argv[i + 1])
            except ValueError:
                pass

    since_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    print(f"\nMode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Lookback: {lookback_days} days (since {since_date})")
    print(f"Cycle: {cycle}")

    # Fetch quarterly reports
    reports = fetch_quarterly_reports(since_date, cycle)

    if not reports:
        print("\nNo new quarterly reports found.")
        return

    # Process reports
    print(f"\n=== Processing {len(reports)} Reports ===")

    stats = {
        'processed': 0,
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    # Cache for candidate info and committee lookups
    candidate_cache = {}
    committee_to_candidate = {}

    for i, report in enumerate(reports):
        committee_id = report.get('committee_id')
        coverage_end = report.get('coverage_end_date')

        if not committee_id or not coverage_end:
            stats['skipped'] += 1
            continue

        # Look up candidate_id from committee_id (with caching)
        if committee_id not in committee_to_candidate:
            committee_to_candidate[committee_id] = get_candidate_id_from_committee(committee_id)

        candidate_id = report.get('candidate_id') or committee_to_candidate[committee_id]

        if not candidate_id:
            stats['skipped'] += 1
            continue

        # Get candidate info (with caching)
        if candidate_id not in candidate_cache:
            candidate_cache[candidate_id] = get_candidate_info(candidate_id)

        candidate_info = candidate_cache[candidate_id]

        if not candidate_info:
            # Skip if we don't have this candidate in our database
            stats['skipped'] += 1
            continue

        # Clean coverage_end for lookup
        coverage_end_clean = coverage_end.split('T')[0] if 'T' in coverage_end else coverage_end

        # Check if record exists
        existing = check_existing_record(candidate_id, cycle, coverage_end_clean)

        # Transform and upsert
        record = transform_report_to_record(report, candidate_info, candidate_id)

        if dry_run:
            action = "UPDATE" if existing else "INSERT"
            print(f"  [{action}] {candidate_info.get('name', 'Unknown')[:30]} - {record.get('report_type', 'Unknown')[:20]}")
            stats['processed'] += 1
            if existing:
                stats['updated'] += 1
            else:
                stats['inserted'] += 1
        else:
            if upsert_quarterly_record(record):
                stats['processed'] += 1
                if existing:
                    stats['updated'] += 1
                else:
                    stats['inserted'] += 1
            else:
                stats['errors'] += 1

        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(reports)}")

        time.sleep(0.1)  # Small delay to avoid overwhelming the database

    # Summary
    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("UPDATE COMPLETE")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Reports processed: {stats['processed']}")
    print(f"  New records inserted: {stats['inserted']}")
    print(f"  Existing records updated: {stats['updated']}")
    print(f"  Skipped (no candidate match): {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nDuration: {duration:.1f} seconds")

    if dry_run:
        print("\n⚠️  DRY RUN - No changes were made to the database")


if __name__ == "__main__":
    main()
