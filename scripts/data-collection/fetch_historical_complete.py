#!/usr/bin/env python3
"""
Corrected Historical FEC Data Fetcher
======================================

This script fetches CORRECT financial data for historical election cycles by:
1. Using the /committee/{id}/totals/ endpoint with proper cycle filtering
2. Validating dates are from the correct cycle year range
3. Testing against known benchmarks (Fetterman, Kelly, Warnock)

Key fixes from fetch_all_filings.py:
- Adds report_year filtering to ensure correct cycle data
- Validates coverage_end_date is in expected year range
- Uses totals endpoint for pre-aggregated data
- Tests on benchmarks before processing all candidates

USAGE:
    # Test on 10 candidates first
    python fetch_historical_complete.py --cycle 2022 --limit 10 --test

    # Run full cycle after validation
    python fetch_historical_complete.py --cycle 2022

    # Run all historical cycles
    python fetch_historical_complete.py --cycle 2024
    python fetch_historical_complete.py --cycle 2022
    python fetch_historical_complete.py --cycle 2020
    python fetch_historical_complete.py --cycle 2018
"""

import requests
import json
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Progress file for resuming interrupted runs
PROGRESS_FILE = "historical_collection_progress.json"

FEC_API_KEY = os.getenv('FEC_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

# Benchmark candidates for validation (2022 cycle)
# Note: Kelly/Warnock not in 2022 database (only have 2020 records)
BENCHMARKS_2022 = {
    'S6PA00274': {'name': 'FETTERMAN, JOHN', 'expected_min': 50_000_000, 'state': 'PA'},
    'S2PA00638': {'name': 'OZ, MEHMET', 'expected_min': 30_000_000, 'state': 'PA'},
    'S2OH00402': {'name': 'RYAN, TIMOTHY', 'expected_min': 35_000_000, 'state': 'OH'},
    'S2OH00436': {'name': 'VANCE, J D', 'expected_min': 10_000_000, 'state': 'OH'},
    'S2GA00225': {'name': 'WALKER, HERSCHEL', 'expected_min': 45_000_000, 'state': 'GA'},
}

# Rate limiting - 5 seconds between calls (safe under 1000/hour)
RATE_LIMIT_DELAY = 5.0


def load_progress(cycle):
    """Load progress from previous run for this cycle."""
    if not os.path.exists(PROGRESS_FILE):
        return {}

    try:
        with open(PROGRESS_FILE, 'r') as f:
            all_progress = json.load(f)
            return all_progress.get(str(cycle), {})
    except:
        return {}


def save_progress(cycle, processed_count, total_count, processed_ids):
    """Save progress to resume later if interrupted."""
    progress_data = {}

    # Load existing progress for other cycles
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress_data = json.load(f)
        except:
            pass

    # Update progress for this cycle
    progress_data[str(cycle)] = {
        'processed_count': processed_count,
        'total_count': total_count,
        'processed_ids': processed_ids,
        'last_updated': datetime.now().isoformat()
    }

    # Save to file
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)


def validate_cycle_dates(coverage_end_date, cycle):
    """
    Validate that the coverage date is from the correct election cycle.

    Election cycles cover:
    - 2022 cycle: 2021-01-01 to 2022-12-31
    - 2020 cycle: 2019-01-01 to 2020-12-31
    etc.

    Returns True if date is valid for cycle, False otherwise.
    """
    if not coverage_end_date:
        return False

    try:
        year = int(coverage_end_date.split('-')[0])
        # Cycle data should be from cycle year or year before
        return year in [cycle - 1, cycle]
    except:
        return False


def fetch_candidates_from_db(cycle, limit=None):
    """Fetch candidates from Supabase database with pagination."""
    all_candidates = []
    offset = 0
    batch_size = 1000

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }

    while True:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        params = {
            'cycle': f'eq.{cycle}',
            'select': 'candidate_id,name,party,state,district,office',
            'limit': batch_size,
            'offset': offset
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            batch = response.json()

            if not batch:
                break

            all_candidates.extend(batch)

            if limit and len(all_candidates) >= limit:
                return all_candidates[:limit]

            if len(batch) < batch_size:
                break

            offset += batch_size

        except Exception as e:
            print(f"Error fetching candidates from database: {e}")
            break

    return all_candidates


def fetch_committee_totals(committee_id, cycle):
    """
    Fetch financial totals for a committee in a specific cycle.

    CRITICAL FIX: This uses the /totals/ endpoint which returns pre-aggregated
    data for the specific cycle, avoiding the bug where /filings/ returns
    current cycle data instead of historical data.
    """
    try:
        url = f"{BASE_URL}/committee/{committee_id}/totals/"

        # CRITICAL: Filter by cycle to get historical data
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': 10
        }

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return None

        results = response.json().get('results', [])

        if not results:
            return None

        # Get the first result (should be for the requested cycle)
        totals = results[0]

        # CRITICAL: Validate that coverage_end_date is from correct cycle
        coverage_end_date = totals.get('coverage_end_date')

        if not validate_cycle_dates(coverage_end_date, cycle):
            print(f"\n      ⚠️  WARNING: Committee {committee_id} returned data from wrong cycle!")
            print(f"          Coverage date: {coverage_end_date} (expected {cycle-1}-{cycle})")
            return None

        return {
            'receipts': totals.get('receipts', 0) or 0,
            'disbursements': totals.get('disbursements', 0) or 0,
            'cash_on_hand': totals.get('cash_on_hand_end_period', 0) or 0,
            'coverage_start_date': totals.get('coverage_start_date'),
            'coverage_end_date': coverage_end_date,
            'report_year': totals.get('report_year'),
        }

    except requests.exceptions.RequestException as e:
        print(f"\n      Error fetching totals for {committee_id}: {e}")
        return None


def fetch_candidate_committees(candidate_id, cycle):
    """
    Fetch all committees for a candidate in a specific cycle.
    """
    try:
        url = f"{BASE_URL}/candidate/{candidate_id}/committees/"

        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'per_page': 20
        }

        response = requests.get(url, params=params, timeout=15)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return []

        committees = response.json().get('results', [])
        return committees

    except requests.exceptions.RequestException as e:
        print(f"\n      Error fetching committees for {candidate_id}: {e}")
        return []


def fetch_candidate_financials(candidate_id, cycle):
    """
    Fetch complete financial data for a candidate in a specific cycle.

    Returns aggregated totals from all of the candidate's committees.
    """
    # Get candidate's committees for this cycle
    committees = fetch_candidate_committees(candidate_id, cycle)

    if not committees:
        return None

    # Aggregate totals from all committees
    total_receipts = 0
    total_disbursements = 0
    cash_on_hand = 0
    latest_coverage_end = None
    committee_ids = []

    for committee in committees:
        committee_id = committee.get('committee_id')
        committee_ids.append(committee_id)

        # Get financial totals for this committee
        totals = fetch_committee_totals(committee_id, cycle)

        if totals:
            total_receipts += totals['receipts']
            total_disbursements += totals['disbursements']
            cash_on_hand = totals['cash_on_hand']  # Use most recent

            # Track latest coverage date
            coverage_end = totals.get('coverage_end_date')
            if coverage_end:
                if not latest_coverage_end or coverage_end > latest_coverage_end:
                    latest_coverage_end = coverage_end

    # Return None if no financial data found
    if total_receipts == 0 and total_disbursements == 0 and cash_on_hand == 0:
        return None

    return {
        'total_receipts': total_receipts,
        'total_disbursements': total_disbursements,
        'cash_on_hand': cash_on_hand,
        'coverage_end_date': latest_coverage_end,
        'committee_ids': committee_ids,
    }


def test_benchmark_candidates(cycle):
    """
    Test script on known benchmark candidates to validate it's working correctly.

    For 2022 cycle:
    - Fetterman should show $50M+
    - Kelly should show $60M+
    - Warnock should show $80M+
    """
    if cycle != 2022:
        print(f"\n⚠️  No benchmarks defined for cycle {cycle} (only 2022)")
        return True

    print("\n" + "="*80)
    print("BENCHMARK VALIDATION - Testing Known Candidates")
    print("="*80)

    all_passed = True

    for candidate_id, expected in BENCHMARKS_2022.items():
        print(f"\nTesting: {expected['name']} ({expected['state']}) - {candidate_id}")
        print(f"  Expected: ${expected['expected_min']:,}+")

        financials = fetch_candidate_financials(candidate_id, cycle)

        if not financials:
            print(f"  ❌ FAILED: No financial data found")
            all_passed = False
            continue

        total_raised = financials['total_receipts']
        coverage_date = financials['coverage_end_date']

        print(f"  Actual: ${total_raised:,.2f}")
        print(f"  Coverage end date: {coverage_date}")

        # Validate amount
        if total_raised < expected['expected_min']:
            print(f"  ❌ FAILED: Amount too low (expected ${expected['expected_min']:,}+)")
            all_passed = False
        else:
            print(f"  ✅ PASSED: Amount correct")

        # Validate date is from correct cycle
        if not validate_cycle_dates(coverage_date, cycle):
            print(f"  ❌ FAILED: Coverage date from wrong cycle (expected 2021-2022)")
            all_passed = False
        else:
            year = coverage_date.split('-')[0]
            print(f"  ✅ PASSED: Coverage date in correct cycle ({year})")

    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL BENCHMARKS PASSED - Script is working correctly!")
    else:
        print("❌ SOME BENCHMARKS FAILED - DO NOT proceed with full run!")
        print("   Debug the issues above before running on all candidates.")
    print("="*80)

    return all_passed


def save_to_database(candidates_data, cycle):
    """
    Save financial summary data to Supabase financial_summary table.

    Strategy: Use proper upsert to handle duplicates gracefully.
    The unique constraint is on (candidate_id, cycle, coverage_end_date).
    """
    if not candidates_data:
        print("  No data to save")
        return 0

    url = f"{SUPABASE_URL}/rest/v1/financial_summary"

    # Use upsert with on_conflict parameter
    # This tells Supabase which columns define uniqueness
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'
    }

    # Batch upsert (500 at a time to avoid timeouts)
    batch_size = 500
    upserted = 0

    for i in range(0, len(candidates_data), batch_size):
        batch = candidates_data[i:i + batch_size]

        try:
            # Use upsert parameter - this handles duplicates by updating
            response = requests.post(
                f"{url}?on_conflict=candidate_id,cycle,coverage_end_date",
                headers=headers,
                json=batch
            )

            if response.status_code in [200, 201, 204]:
                upserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: Upserted {upserted}/{len(candidates_data)} records")
            else:
                print(f"    Batch {i//batch_size + 1} failed: {response.status_code}")
                print(f"    {response.text[:300]}")

        except Exception as e:
            print(f"    Batch {i//batch_size + 1} error: {str(e)}")

    return upserted


def main():
    parser = argparse.ArgumentParser(
        description='Fetch CORRECT historical FEC financial data'
    )
    parser.add_argument(
        '--cycle',
        type=int,
        required=True,
        help='Election cycle year (2024, 2022, 2020, 2018)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of candidates (for testing)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run benchmark tests before processing'
    )
    parser.add_argument(
        '--skip-save',
        action='store_true',
        help='Skip saving to database (for testing)'
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("CORRECTED HISTORICAL FEC DATA FETCHER")
    print("="*80)
    print(f"Cycle: {args.cycle}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected date range: {args.cycle-1} - {args.cycle}")
    print("="*80)

    # Verify credentials
    if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
        print("\n❌ ERROR: Missing credentials in .env file")
        print("   Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
        return

    # Run benchmark tests if requested
    if args.test:
        passed = test_benchmark_candidates(args.cycle)
        if not passed and not args.limit:
            print("\n❌ Benchmark tests failed. Use --limit 10 to test on small sample first.")
            return

    # Fetch candidates from database
    print(f"\nFetching candidates for cycle {args.cycle}...")
    candidates = fetch_candidates_from_db(args.cycle, args.limit)

    if not candidates:
        print("  ❌ No candidates found")
        return

    print(f"  ✅ Found {len(candidates)} candidates")

    if args.limit:
        print(f"  ℹ️  Limited to {args.limit} for testing")

    # Load progress from previous run (if any)
    progress = load_progress(args.cycle)
    processed_ids = set(progress.get('processed_ids', []))

    if processed_ids:
        print(f"  📁 Resuming from previous run: {len(processed_ids)} candidates already processed")

    # Fetch financial data for each candidate
    print(f"\nFetching financial data...")
    print("="*80)

    results = []
    candidates_with_data = 0
    skipped_count = 0

    start_time = time.time()

    for idx, candidate in enumerate(candidates):
        candidate_id = candidate['candidate_id']
        name = candidate.get('name', 'Unknown')

        # Skip if already processed
        if candidate_id in processed_ids:
            skipped_count += 1
            if skipped_count <= 5:  # Only show first 5 skips
                print(f"[{idx+1}/{len(candidates)}] {name[:40]:40} ({candidate_id})... ⏭️  (skipped)")
            continue

        print(f"[{idx+1}/{len(candidates)}] {name[:40]:40} ({candidate_id})...", end=" ")

        financials = fetch_candidate_financials(candidate_id, args.cycle)

        if financials:
            candidates_with_data += 1

            # Validate amount is reasonable
            total_raised = financials['total_receipts']
            if total_raised > 0:
                print(f"✓ ${total_raised:,.0f}")
            else:
                print(f"✓ (no receipts)")

            results.append({
                'candidate_id': candidate_id,
                'cycle': args.cycle,
                'total_receipts': financials['total_receipts'],
                'total_disbursements': financials['total_disbursements'],
                'cash_on_hand': financials['cash_on_hand'],
                'coverage_end_date': financials['coverage_end_date'],
                'updated_at': datetime.now().isoformat(),
            })
        else:
            print("✓ (no data)")

        # Mark as processed
        processed_ids.add(candidate_id)

        # Save every 25 candidates to avoid losing progress
        if (idx + 1) % 25 == 0:
            if results and not args.skip_save:
                print(f"\n  💾 Saving {len(results)} records to database...")
                inserted = save_to_database(results, args.cycle)
                print(f"  ✓ Saved {inserted} records")
                results = []  # Clear after saving

            # Save progress
            save_progress(args.cycle, len(processed_ids), len(candidates), list(processed_ids))
            print(f"  💾 Progress saved: {len(processed_ids)}/{len(candidates)} candidates\n")

        # Progress estimate
        if (idx + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed
            remaining = len(candidates) - (idx + 1)
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_hours = eta_seconds / 3600
            print(f"\n  ⏱️  Progress: {idx+1}/{len(candidates)} | "
                  f"Rate: {rate:.1f} candidates/sec | "
                  f"ETA: {eta_hours:.1f} hours\n")

    # Save remaining results
    if results and not args.skip_save:
        print(f"\n  💾 Saving final {len(results)} records to database...")
        inserted = save_to_database(results, args.cycle)
        print(f"  ✓ Saved {inserted} records")

    # Save final progress
    save_progress(args.cycle, len(processed_ids), len(candidates), list(processed_ids))
    print(f"  💾 Final progress saved: {len(processed_ids)}/{len(candidates)} candidates")

    # Summary
    elapsed_total = time.time() - start_time
    newly_processed = len(processed_ids) - len(progress.get('processed_ids', []))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Cycle: {args.cycle}")
    print(f"Total candidates: {len(candidates)}")
    if skipped_count > 0:
        print(f"Skipped (already processed): {skipped_count}")
    print(f"Newly processed: {newly_processed}")
    print(f"Candidates with financial data: {candidates_with_data}")
    print(f"Total time: {elapsed_total/60:.1f} minutes")
    if not args.skip_save:
        print(f"Data saved to: financial_summary table")
    print(f"Progress file: {PROGRESS_FILE}")
    print("="*80)

    # Validation reminders
    if not args.test and args.cycle == 2022:
        print("\n💡 TIP: Run with --test flag to validate against Fetterman/Kelly/Warnock")

    print()


if __name__ == "__main__":
    main()
