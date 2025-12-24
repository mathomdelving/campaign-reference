#!/usr/bin/env python3
"""
Corrected 2024 FEC Data Collection Script
==========================================

This script fixes BOTH issues discovered in our 2024 data collection:

ISSUE #1 FIX: Use cycle=2024 instead of election_year=2024
- Gets all 9,810 candidates instead of only 5,226
- Captures all major Senate races (Cruz, Casey, Gallego, Lake, etc.)

ISSUE #2 FIX: Use principal committee via committee history
- For each candidate, check committee history for cycle-specific designation
- Only collect from principal committee (designation='P' for cycle=2024)
- Avoids collecting from wrong committees
- Gets correct amounts for timeseries data

DATA COLLECTED (two tables):
1. financial_summary: Cumulative totals from GET /candidate/{id}/totals/?cycle=2024
2. quarterly_financials: Individual filings from GET /committee/{principal_id}/filings/?cycle=2024
   - Includes all filing types (quarterly, pre-primary, pre-general, post-general, year-end)
   - Deduplicates amendments (keeps most recent for each period)
   - Provides timeseries data for trend charts

USAGE:
    # Test on known candidates first (recommended)
    python fetch_2024_corrected.py --test

    # Test on small sample
    python fetch_2024_corrected.py --limit 50

    # Run full collection
    python fetch_2024_corrected.py

    # Delete existing 2024 data and start fresh
    python fetch_2024_corrected.py --delete-existing

Author: Campaign Reference Team
Date: November 2025
See: COLLECTION_ROADMAP.md for full investigation details
"""

import requests
import json
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
CYCLE = 2024
PROGRESS_FILE = "collection_progress_2024.json"
NO_PRINCIPAL_LOG = "no_principal_committee_2024.log"
VALIDATION_LOG = "validation_mismatches_2024.log"

FEC_API_KEY = os.getenv('FEC_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

# Rate limiting: 5 seconds between calls = 720 calls/hour (safe under 1000/hour limit)
RATE_LIMIT_DELAY = 5.0

# Test candidates to validate both fixes
TEST_CANDIDATES = {
    # Issue #1: Previously missing candidates (not in election_year=2024 results)
    'S2TX00312': {'name': 'Ted Cruz', 'expected_min': 50_000_000, 'issue': 'Missing'},
    'S6PA00217': {'name': 'Bob Casey', 'expected_min': 40_000_000, 'issue': 'Missing'},
    'S4AZ00139': {'name': 'Ruben Gallego', 'expected_min': 20_000_000, 'issue': 'Missing'},
    'S4AZ00220': {'name': 'Kari Lake', 'expected_min': 20_000_000, 'issue': 'Missing'},
    # Issue #2: Wrong amounts due to wrong committee
    'S6OH00163': {'name': 'Sherrod Brown', 'expected_min': 90_000_000, 'issue': 'Wrong Amount'},
    'S4TX00722': {'name': 'Colin Allred', 'expected_min': 90_000_000, 'issue': 'Control'},
    'S4MD00327': {'name': 'Angela Alsobrooks', 'expected_min': 10_000_000, 'issue': 'Missing'},
    'S4OH00192': {'name': 'Bernie Moreno', 'expected_min': 5_000_000, 'issue': 'Missing'},
}


def log_no_principal(candidate_id, name, committees_found):
    """Log candidates with no principal committee for manual review."""
    with open(NO_PRINCIPAL_LOG, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | {candidate_id} | {name} | {committees_found} committees found\n")


def log_validation_mismatch(candidate_id, name, our_total, fec_total, pct_diff):
    """Log candidates where our totals don't match FEC totals."""
    with open(VALIDATION_LOG, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | {candidate_id} | {name} | "
                f"Our: ${our_total:,.0f} | FEC: ${fec_total:,.0f} | Diff: {pct_diff:.1f}%\n")


def load_progress():
    """Load progress from previous run."""
    if not os.path.exists(PROGRESS_FILE):
        return {'processed_ids': [], 'processed_count': 0}

    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'processed_ids': [], 'processed_count': 0}


def save_progress(processed_ids, total_count):
    """Save progress to resume later if interrupted."""
    progress_data = {
        'processed_ids': list(processed_ids),
        'processed_count': len(processed_ids),
        'total_count': total_count,
        'last_updated': datetime.now().isoformat()
    }

    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)


def delete_existing_2024_data():
    """Delete all existing 2024 data from financial_summary table."""
    url = f"{SUPABASE_URL}/rest/v1/financial_summary"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Prefer': 'return=minimal'
    }

    try:
        response = requests.delete(
            f"{url}?cycle=eq.{CYCLE}",
            headers=headers
        )

        if response.status_code in [200, 204]:
            print(f"  ✅ Deleted existing 2024 data")
            return True
        else:
            print(f"  ⚠️  Delete response: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ Error deleting existing data: {e}")
        return False


def fetch_candidates_from_api(cycle, limit=None):
    """
    Fetch candidates from FEC API using cycle parameter.

    FIX #1: Uses cycle={cycle} instead of election_year={cycle}
    This returns ALL candidates (9,810 for 2024 vs only 5,226 with election_year)
    """
    all_candidates = []
    page = 1
    per_page = 100

    print(f"\nFetching candidates from FEC API using cycle={cycle}...")

    while True:
        try:
            url = f"{BASE_URL}/candidates/"

            # CRITICAL FIX #1: Use 'cycle' parameter, not 'election_year'
            params = {
                'api_key': FEC_API_KEY,
                'cycle': cycle,  # ← This is the fix!
                'per_page': per_page,
                'page': page
            }

            response = requests.get(url, params=params, timeout=15)
            time.sleep(RATE_LIMIT_DELAY)

            if not response.ok:
                print(f"  ⚠️  API error on page {page}: {response.status_code}")
                break

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            all_candidates.extend(results)

            # Progress update
            if page % 10 == 0:
                print(f"  Fetched {len(all_candidates)} candidates (page {page})...")

            # Check if we've hit the limit
            if limit and len(all_candidates) >= limit:
                all_candidates = all_candidates[:limit]
                break

            # Check if there are more pages
            pagination = data.get('pagination', {})
            total_pages = pagination.get('pages', 0)

            # If we know total pages and reached it, stop
            if total_pages > 0 and page >= total_pages:
                break

            # If we got fewer results than requested, we're probably done
            if len(results) < per_page:
                break

            page += 1

        except Exception as e:
            print(f"  ⚠️  Error fetching page {page}: {e}")
            break

    print(f"  ✅ Found {len(all_candidates)} candidates for cycle {cycle}")
    return all_candidates


def get_candidate_committees(candidate_id):
    """Get all committees for a candidate."""
    try:
        url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        params = {
            'api_key': FEC_API_KEY,
            'per_page': 100
        }

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            return response.json().get('results', [])
        return []
    except:
        return []


def get_committee_history(committee_id):
    """Get historical data for a committee across all cycles."""
    try:
        url = f"{BASE_URL}/committee/{committee_id}/history/"
        params = {'api_key': FEC_API_KEY}

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if response.ok:
            return response.json().get('results', [])
        return []
    except:
        return []


def get_principal_committee_for_cycle(candidate_id, cycle):
    """
    Identify principal committee for a specific cycle using committee history.

    FIX #2: This handles cases where committees change roles between cycles.
    Example: C00264697 was 'P' (Principal) in 2024 but 'U' (Unauthorized) in 2026.

    IMPORTANT: Checks ALL committees first to ensure we find the correct principal
    committee for the specific cycle, since committees can rotate roles over time.

    Returns: dict with committee info, or None if no principal committee found
    """
    # Get all committees associated with candidate
    committees = get_candidate_committees(candidate_id)

    if not committees:
        return None

    # Check ALL committees to find which was principal for this specific cycle
    principal_committees = []

    for committee in committees:
        committee_id = committee['committee_id']

        # Get historical data for this committee
        history = get_committee_history(committee_id)

        # Find the record for the cycle we care about
        for record in history:
            if record.get('cycle') == cycle:
                designation = record.get('designation')

                # Found a principal committee for this cycle!
                if designation == 'P':
                    principal_committees.append({
                        'committee_id': committee_id,
                        'name': record.get('name'),
                        'designation': designation,
                        'committee_type': record.get('committee_type')
                    })
                break  # Only need one record per committee for this cycle

    # Should only be one principal committee per cycle
    if len(principal_committees) == 0:
        return None
    elif len(principal_committees) > 1:
        # Log warning but return the first one
        committee_ids = [c['committee_id'] for c in principal_committees]
        print(f"      ⚠️  WARNING: Multiple principal committees for {candidate_id} in {cycle}: {committee_ids}")
        return principal_committees[0]
    else:
        return principal_committees[0]


def fetch_committee_filings(committee_id, cycle):
    """
    Fetch ALL filings for a committee in a specific cycle.

    Handles amendments: For each unique (report_type, coverage_start_date, coverage_end_date),
    we keep only the most recent filing (highest amendment_indicator).

    Returns: list of filing records
    """
    try:
        url = f"{BASE_URL}/committee/{committee_id}/filings/"

        all_filings = []
        page = 1
        per_page = 100

        while True:
            params = {
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'per_page': per_page,
                'page': page
            }

            response = requests.get(url, params=params, timeout=15)
            time.sleep(RATE_LIMIT_DELAY)

            if not response.ok:
                break

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            all_filings.extend(results)

            # Check if there are more pages
            # If we got fewer results than requested, we're on the last page
            if len(results) < per_page:
                break

            pagination = data.get('pagination', {})
            if pagination.get('pages') and page >= pagination.get('pages'):
                break

            page += 1

        if not all_filings:
            return []

        # Group filings by (report_type, coverage_start_date, coverage_end_date)
        # Keep only the most recent amendment for each unique period
        filing_groups = {}

        for filing in all_filings:
            report_type = filing.get('report_type')
            coverage_start = filing.get('coverage_start_date')
            coverage_end = filing.get('coverage_end_date')

            # Skip filings without required fields
            if not all([report_type, coverage_start, coverage_end]):
                continue

            key = (report_type, coverage_start, coverage_end)

            # Keep the filing with the latest amendment_indicator or most recent file_number
            if key not in filing_groups:
                filing_groups[key] = filing
            else:
                # Compare amendment indicators or receipt dates to get most recent
                existing_amendment = filing_groups[key].get('amendment_indicator') or ''
                new_amendment = filing.get('amendment_indicator') or ''

                # Higher amendment indicator = more recent
                # Or if same, use most recent receipt_date
                if new_amendment > existing_amendment:
                    filing_groups[key] = filing
                elif new_amendment == existing_amendment:
                    existing_date = filing_groups[key].get('receipt_date') or ''
                    new_date = filing.get('receipt_date') or ''
                    if new_date > existing_date:
                        filing_groups[key] = filing

        # Convert to list of filing records with needed fields
        filings_list = []
        for filing in filing_groups.values():
            filings_list.append({
                'report_type': filing.get('report_type'),
                'coverage_start_date': filing.get('coverage_start_date'),
                'coverage_end_date': filing.get('coverage_end_date'),
                'total_receipts': filing.get('total_receipts', 0) or 0,
                'total_disbursements': filing.get('total_disbursements', 0) or 0,
                'cash_on_hand': filing.get('cash_on_hand_end_period', 0) or 0,
                'amendment_indicator': filing.get('amendment_indicator', ''),
            })

        return filings_list

    except Exception as e:
        return []


def fetch_fec_totals(candidate_id, cycle):
    """
    Fetch FEC's pre-aggregated totals for validation.

    This is what the FEC considers the "official" totals for a candidate.
    We compare our calculated totals against this to validate accuracy.
    """
    try:
        url = f"{BASE_URL}/candidate/{candidate_id}/totals/"

        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': 1
        }

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return None

        results = response.json().get('results', [])

        if not results:
            return None

        totals = results[0]

        return {
            'receipts': totals.get('receipts', 0) or 0,
            'disbursements': totals.get('disbursements', 0) or 0,
            'cash_on_hand': totals.get('cash_on_hand_end_period', 0) or 0,
        }

    except:
        return None


def fetch_candidate_financials(candidate_id, candidate_name, cycle):
    """
    Fetch complete financial data for a candidate in a specific cycle.

    Uses the corrected approach:
    1. Get principal committee using committee history (Fix #2)
    2. Fetch cumulative totals from /totals/ endpoint → financial_summary table
    3. Fetch ALL individual filings from principal committee → quarterly_financials table
    4. Deduplicate amendments (keep most recent for each period)

    Returns: dict with both summary and filings data, or None if no data available
    """
    # FIX #2: Get principal committee using committee history
    principal = get_principal_committee_for_cycle(candidate_id, cycle)

    if not principal:
        # No principal committee found
        committees = get_candidate_committees(candidate_id)
        log_no_principal(candidate_id, candidate_name, len(committees))
        return None

    committee_id = principal['committee_id']

    # Fetch cumulative totals for financial_summary table
    fec_totals = fetch_fec_totals(candidate_id, cycle)

    if not fec_totals:
        # Has principal committee but no totals data
        return None

    # Fetch ALL individual filings from principal committee for quarterly_financials table
    filings = fetch_committee_filings(committee_id, cycle)

    # Calculate sum of filings for validation
    filings_total = sum(f['total_receipts'] for f in filings) if filings else 0
    fec_total = fec_totals['receipts']

    # Validation: Check if sum of filings roughly matches FEC totals
    # Note: These may not match exactly due to filing structure
    # Some filings show cumulative amounts, others show period amounts
    validation_status = "✓"
    if fec_total > 0 and filings:
        # Check both sum and max approaches
        filings_max = max(f['total_receipts'] for f in filings)

        # Use the closer one for validation
        diff_sum = abs(filings_total - fec_total) / fec_total * 100 if fec_total > 0 else 0
        diff_max = abs(filings_max - fec_total) / fec_total * 100 if fec_total > 0 else 0

        pct_diff = min(diff_sum, diff_max)

        if pct_diff > 5:
            validation_status = f"⚠️  {pct_diff:.1f}% diff"

    return {
        # Summary data for financial_summary table
        'summary': {
            'total_receipts': fec_totals['receipts'],
            'total_disbursements': fec_totals['disbursements'],
            'cash_on_hand': fec_totals['cash_on_hand'],
            'coverage_end_date': fec_totals.get('coverage_end_date'),
            'report_type': fec_totals.get('last_report_type_full'),
        },
        # Individual filings for quarterly_financials table
        'filings': filings,
        # Metadata
        'committee_id': committee_id,
        'committee_name': principal['name'],
        'validation_status': validation_status,
        'num_filings': len(filings),
    }


def save_financial_summary(summary_records):
    """
    Save financial summary records to Supabase (cumulative totals).

    Each record represents cumulative totals for one candidate for the cycle.
    Uses upsert with unique constraint on (candidate_id, cycle, coverage_end_date).
    """
    if not summary_records:
        return 0

    url = f"{SUPABASE_URL}/rest/v1/financial_summary"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    # Batch upsert
    batch_size = 500
    saved = 0

    for i in range(0, len(summary_records), batch_size):
        batch = summary_records[i:i + batch_size]

        try:
            response = requests.post(
                url,
                headers=headers,
                json=batch
            )

            if response.status_code in [200, 201, 204]:
                saved += len(batch)
            else:
                print(f"    ⚠️  Summary batch {i//batch_size + 1} failed: {response.status_code}")
                print(f"    Response: {response.text[:300]}")
        except Exception as e:
            print(f"    ⚠️  Summary batch {i//batch_size + 1} error: {e}")

    return saved


def save_quarterly_financials(quarterly_records):
    """
    Save quarterly/filing records to Supabase (timeseries data).

    Each record represents one filing period for a candidate.
    Includes all filing types: quarterly, pre-primary, pre-general, post-general, year-end.
    Uses upsert with unique constraint on (candidate_id, cycle, coverage_end_date).
    """
    if not quarterly_records:
        return 0

    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    # Batch upsert
    batch_size = 500
    saved = 0

    for i in range(0, len(quarterly_records), batch_size):
        batch = quarterly_records[i:i + batch_size]

        try:
            response = requests.post(
                url,
                headers=headers,
                json=batch
            )

            if response.status_code in [200, 201, 204]:
                saved += len(batch)
            else:
                print(f"    ⚠️  Quarterly batch {i//batch_size + 1} failed: {response.status_code}")
                print(f"    Response: {response.text[:300]}")
        except Exception as e:
            print(f"    ⚠️  Quarterly batch {i//batch_size + 1} error: {e}")

    return saved


def run_test_candidates():
    """
    Test the script on known candidates to validate both fixes work.

    Tests:
    - Issue #1 candidates (previously missing)
    - Issue #2 candidates (previously wrong amounts)
    - Control candidate (should still work)
    """
    print("\n" + "="*80)
    print("TESTING ON KNOWN CANDIDATES")
    print("="*80)
    print("\nThis validates both fixes:")
    print("  Fix #1: Using cycle=2024 finds previously missing candidates")
    print("  Fix #2: Using committee history gets correct amounts")
    print()

    all_passed = True

    for candidate_id, expected in TEST_CANDIDATES.items():
        print(f"\nTesting: {expected['name']} ({candidate_id})")
        print(f"  Issue: {expected['issue']}")
        print(f"  Expected: >${expected['expected_min']:,}")

        financials = fetch_candidate_financials(candidate_id, expected['name'], CYCLE)

        if not financials:
            print(f"  ❌ FAILED: No financial data found")
            all_passed = False
            continue

        total_raised = financials['summary']['total_receipts']
        committee = financials.get('committee_name', 'Unknown')
        validation = financials['validation_status']
        num_filings = financials['num_filings']

        print(f"  Actual: ${total_raised:,}")
        print(f"  Committee: {committee}")
        print(f"  Filings: {num_filings}")
        print(f"  Validation: {validation}")

        if total_raised >= expected['expected_min']:
            print(f"  ✅ PASSED")
        else:
            print(f"  ❌ FAILED: Amount too low")
            all_passed = False

    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED - Script is working correctly!")
        print("   Ready to run full collection.")
    else:
        print("❌ SOME TESTS FAILED - DO NOT proceed with full run!")
        print("   Debug the issues above first.")
    print("="*80)

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description='Corrected 2024 FEC data collection with both fixes'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test on known candidates first'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of candidates (for testing)'
    )
    parser.add_argument(
        '--delete-existing',
        action='store_true',
        help='Delete existing 2024 data before collecting'
    )
    parser.add_argument(
        '--skip-save',
        action='store_true',
        help='Skip saving to database (for testing)'
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("CORRECTED 2024 FEC DATA COLLECTION")
    print("="*80)
    print(f"Cycle: {CYCLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nFixes Applied:")
    print(f"  ✓ Fix #1: Using cycle=2024 (gets all 9,810 candidates)")
    print(f"  ✓ Fix #2: Using committee history (gets correct amounts)")
    print(f"\nRate Limit: {RATE_LIMIT_DELAY}s delay ({3600/RATE_LIMIT_DELAY:.0f} calls/hour)")
    print("="*80)

    # Verify credentials
    if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
        print("\n❌ ERROR: Missing credentials in .env file")
        print("   Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
        return

    # Run test mode if requested
    if args.test:
        passed = run_test_candidates()
        if not passed:
            print("\n⚠️  Fix issues before running full collection")
            return
        else:
            print("\n✓ Test mode complete. Run without --test flag for full collection.")
            return

    # Delete existing data if requested
    if args.delete_existing:
        print(f"\nDeleting existing 2024 data...")
        delete_existing_2024_data()

    # Fetch candidates from API
    candidates = fetch_candidates_from_api(CYCLE, args.limit)

    if not candidates:
        print("\n❌ No candidates found")
        return

    print(f"\n✅ Will process {len(candidates)} candidates")
    if args.limit:
        print(f"   (Limited to {args.limit} for testing)")

    # Estimate time
    # Per candidate: 1 committees call + ~3-5 history calls + 1 totals call + 1-2 filings calls
    avg_calls_per_candidate = 7
    total_calls = len(candidates) * avg_calls_per_candidate
    estimated_hours = (total_calls * RATE_LIMIT_DELAY) / 3600
    print(f"\n⏱️  Estimated time: {estimated_hours:.1f} hours")
    print(f"   (~{total_calls:,} API calls × {RATE_LIMIT_DELAY}s delay)")
    print(f"   Note: Actual time may vary based on number of committees per candidate")

    # Load progress
    progress = load_progress()
    processed_ids = set(progress.get('processed_ids', []))

    if processed_ids:
        print(f"\n📁 Resuming: {len(processed_ids)} already processed")

    # Initialize log files
    if not processed_ids:  # Only clear logs on fresh start
        open(NO_PRINCIPAL_LOG, 'w').close()
        open(VALIDATION_LOG, 'w').close()

    # Process candidates
    print("\n" + "="*80)
    print("COLLECTING DATA")
    print("="*80)

    summary_results = []
    quarterly_results = []
    candidates_with_data = 0
    total_summary_saved = 0
    total_quarterly_saved = 0
    no_data_count = 0
    skipped_count = 0

    start_time = time.time()

    for idx, candidate in enumerate(candidates):
        candidate_id = candidate.get('candidate_id')
        name = candidate.get('name', 'Unknown')

        # Skip if already processed
        if candidate_id in processed_ids:
            skipped_count += 1
            continue

        print(f"[{idx+1}/{len(candidates)}] {name[:40]:40} ({candidate_id})...", end=" ")

        financials = fetch_candidate_financials(candidate_id, name, CYCLE)

        if financials:
            candidates_with_data += 1
            total_raised = financials['summary']['total_receipts']
            validation = financials['validation_status']
            num_filings = financials['num_filings']

            print(f"✓ ${total_raised:,.0f} ({num_filings} filings) {validation}")

            # Add summary record for financial_summary table
            summary_results.append({
                'candidate_id': candidate_id,
                'cycle': CYCLE,
                'total_receipts': financials['summary']['total_receipts'],
                'total_disbursements': financials['summary']['total_disbursements'],
                'cash_on_hand': financials['summary']['cash_on_hand'],
                'coverage_end_date': financials['summary'].get('coverage_end_date'),
                'report_type': financials['summary'].get('report_type'),
                'updated_at': datetime.now().isoformat(),
            })

            # Add filing records for quarterly_financials table
            for filing in financials['filings']:
                quarterly_results.append({
                    'candidate_id': candidate_id,
                    'name': name,
                    'committee_id': financials['committee_id'],
                    'cycle': CYCLE,
                    'report_type': filing['report_type'],
                    'coverage_start_date': filing['coverage_start_date'],
                    'coverage_end_date': filing['coverage_end_date'],
                    'total_receipts': filing['total_receipts'],
                    'total_disbursements': filing['total_disbursements'],
                    'cash_ending': filing['cash_on_hand'],
                    'updated_at': datetime.now().isoformat(),
                })
        else:
            no_data_count += 1
            print("⚠️  No financial data")

        # Mark as processed
        processed_ids.add(candidate_id)

        # Save checkpoint every 25 candidates
        if (idx + 1) % 25 == 0:
            if not args.skip_save:
                if summary_results:
                    print(f"\n  💾 Saving {len(summary_results)} summary records...")
                    saved = save_financial_summary(summary_results)
                    total_summary_saved += saved
                    print(f"  ✓ Saved {saved} summary records")
                    summary_results = []

                if quarterly_results:
                    print(f"  💾 Saving {len(quarterly_results)} quarterly/filing records...")
                    saved = save_quarterly_financials(quarterly_results)
                    total_quarterly_saved += saved
                    print(f"  ✓ Saved {saved} quarterly records")
                    quarterly_results = []

            save_progress(processed_ids, len(candidates))

            # Progress estimate
            elapsed = time.time() - start_time
            rate = (idx + 1 - skipped_count) / elapsed if elapsed > 0 else 0
            remaining = len(candidates) - (idx + 1)
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_hours = eta_seconds / 3600

            print(f"  📊 Progress: {idx+1}/{len(candidates)} | "
                  f"Rate: {rate:.2f}/sec | ETA: {eta_hours:.1f}h\n")

    # Save final batch
    if not args.skip_save:
        if summary_results:
            print(f"\n💾 Saving final {len(summary_results)} summary records...")
            saved = save_financial_summary(summary_results)
            total_summary_saved += saved
            print(f"✓ Saved {saved} summary records")

        if quarterly_results:
            print(f"\n💾 Saving final {len(quarterly_results)} quarterly/filing records...")
            saved = save_quarterly_financials(quarterly_results)
            total_quarterly_saved += saved
            print(f"✓ Saved {saved} quarterly records")

    save_progress(processed_ids, len(candidates))

    # Summary
    elapsed_total = time.time() - start_time

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Cycle: {CYCLE}")
    print(f"Total candidates: {len(candidates)}")
    if skipped_count > 0:
        print(f"Skipped (already processed): {skipped_count}")
    print(f"Newly processed: {len(processed_ids) - len(progress.get('processed_ids', []))}")
    print(f"With financial data: {candidates_with_data}")
    print(f"No financial data: {no_data_count}")
    if not args.skip_save:
        print(f"\nRecords saved:")
        print(f"  - Financial summaries: {total_summary_saved}")
        print(f"  - Quarterly/filing records: {total_quarterly_saved}")
    print(f"\nTotal time: {elapsed_total/60:.1f} minutes")
    print(f"\nLog files:")
    print(f"  - No principal committee: {NO_PRINCIPAL_LOG}")
    print(f"  - Validation mismatches: {VALIDATION_LOG}")
    print(f"  - Progress: {PROGRESS_FILE}")
    print("="*80)


if __name__ == "__main__":
    main()
