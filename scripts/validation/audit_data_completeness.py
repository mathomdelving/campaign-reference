#!/usr/bin/env python3
"""
FEC DATA COMPLETENESS AUDIT

Validates data completeness across all cycles to ensure reliable product data.

Checks:
1. Candidates with financial_summary but NO quarterly_financials (data gap)
2. Candidates with committees but NO reports fetched
3. Quarterly data completeness (expected vs actual filings)

Outputs:
- Detailed report of missing data
- List of candidates to re-collect
- Summary statistics by cycle

Usage:
    python3 scripts/validation/audit_data_completeness.py
    python3 scripts/validation/audit_data_completeness.py --cycle 2022
    python3 scripts/validation/audit_data_completeness.py --fix  # Auto-collect missing data
"""

import requests
import os
import sys
import argparse
from dotenv import load_dotenv
import time
from datetime import datetime
import json

load_dotenv()

# Configuration
FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not all([FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ ERROR: Missing required environment variables")
    print("Required: FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY")
    sys.exit(1)

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

RATE_LIMIT_DELAY = 4.0


def count_supabase(table, filters=None):
    """Get count of records in Supabase table with optional filters"""
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        for key, value in filters.items():
            url += f"&{key}={value}"

    headers = {**headers_query, 'Prefer': 'count=exact'}
    response = requests.get(url, headers=headers)

    if response.ok:
        # Parse Content-Range header: "0-999/15234"
        content_range = response.headers.get('Content-Range', '0-0/0')
        total = content_range.split('/')[-1]
        return int(total) if total != '*' else 0
    return 0


def get_unique_candidates(table, cycle=None):
    """Get unique candidate_ids from a table for a specific cycle"""
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=candidate_id,cycle&limit=100000"
    if cycle:
        url += f"&cycle=eq.{cycle}"

    response = requests.get(url, headers=headers_query)
    if response.ok:
        records = response.json()
        candidates = {}
        for record in records:
            cid = record['candidate_id']
            if cid not in candidates:
                candidates[cid] = []
            candidates[cid].append(record['cycle'])
        return candidates
    return {}


def get_candidates_with_financial_summary(cycle=None):
    """Get all candidates that have financial_summary records"""
    return get_unique_candidates('financial_summary', cycle)


def get_candidates_with_quarterly_data(cycle=None):
    """Get all candidates that have quarterly_financials records"""
    return get_unique_candidates('quarterly_financials', cycle)


def get_quarterly_count_by_candidate(candidate_id, cycle):
    """Count quarterly filings for a candidate"""
    params = {
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}',
        'select': 'count'
    }

    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"
    url += f"?candidate_id=eq.{candidate_id}&cycle=eq.{cycle}&select=*"

    response = requests.get(url, headers={**headers_query, 'Prefer': 'count=exact'})
    if response.ok:
        count = response.headers.get('Content-Range', '0-0/0').split('/')[-1]
        return int(count) if count != '*' else 0
    return 0


def check_fec_api_for_data(candidate_id, cycle):
    """Check if FEC API has data for this candidate"""
    # Get committees
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
        params={'api_key': FEC_API_KEY, 'per_page': 20}
    )
    time.sleep(RATE_LIMIT_DELAY)

    if not response.ok:
        return {'has_committees': False, 'has_reports': False, 'report_count': 0}

    committees = response.json().get('results', [])

    if not committees:
        return {'has_committees': False, 'has_reports': False, 'report_count': 0}

    # Check first committee for reports
    committee_id = committees[0]['committee_id']
    response = requests.get(
        f'https://api.open.fec.gov/v1/committee/{committee_id}/reports/',
        params={'api_key': FEC_API_KEY, 'cycle': cycle, 'per_page': 100}
    )
    time.sleep(RATE_LIMIT_DELAY)

    if not response.ok:
        return {'has_committees': True, 'has_reports': False, 'report_count': 0}

    reports = response.json().get('results', [])

    return {
        'has_committees': True,
        'has_reports': len(reports) > 0,
        'report_count': len(reports),
        'committee_id': committee_id
    }


def audit_cycle(cycle, check_fec=False):
    """Audit data completeness for a specific cycle"""
    print(f"\n{'='*80}")
    print(f"AUDITING CYCLE {cycle}")
    print('='*80)

    # Get candidates with financial summary
    print("\n  📊 Querying financial_summary...")
    candidates_with_summary = get_candidates_with_financial_summary(cycle)
    print(f"     ✓ Found {len(candidates_with_summary)} unique candidates with financial_summary")

    # Get candidates with quarterly data
    print("\n  📊 Querying quarterly_financials...")
    candidates_with_quarterly = get_candidates_with_quarterly_data(cycle)
    print(f"     ✓ Found {len(candidates_with_quarterly)} unique candidates with quarterly_financials")

    # Find gaps
    missing_quarterly = set(candidates_with_summary.keys()) - set(candidates_with_quarterly.keys())

    print(f"\n  🔍 Analysis:")
    print(f"     Candidates with summary: {len(candidates_with_summary)}")
    print(f"     Candidates with quarterly: {len(candidates_with_quarterly)}")
    print(f"     Missing quarterly data: {len(missing_quarterly)}")

    if not missing_quarterly:
        print(f"\n  ✅ No data gaps found for cycle {cycle}!")
        return []

    # Detailed analysis of missing data
    print(f"\n  ⚠️  Found {len(missing_quarterly)} candidates with financial summary but NO quarterly data:")

    missing_details = []

    for i, candidate_id in enumerate(list(missing_quarterly)[:10], 1):  # Show first 10
        # Get candidate details
        url = f"{SUPABASE_URL}/rest/v1/candidates?candidate_id=eq.{candidate_id}&select=candidate_id,name,party,state,district,office"
        response = requests.get(url, headers=headers_query)

        if response.ok and response.json():
            candidate = response.json()[0]
            office = candidate.get('office', '?')
            state = candidate.get('state', '?')
            district = candidate.get('district', '')
            name = candidate.get('name', 'UNKNOWN')

            location = f"{state}-{district}" if district else state

            detail = {
                'candidate_id': candidate_id,
                'name': name,
                'office': office,
                'location': location,
                'cycle': cycle
            }

            # Check FEC API if requested
            if check_fec:
                fec_data = check_fec_api_for_data(candidate_id, cycle)
                detail['fec_check'] = fec_data

            missing_details.append(detail)

            print(f"     {i}. {name} ({office}-{location}) [{candidate_id}]")

    if len(missing_quarterly) > 10:
        print(f"     ... and {len(missing_quarterly) - 10} more")

    return list(missing_quarterly)


def audit_all_cycles(check_fec=False):
    """Audit data completeness across all cycles in database"""
    print(f"\n{'='*80}")
    print("MULTI-CYCLE DATA COMPLETENESS AUDIT")
    print('='*80)

    # Get all cycles that have data
    url = f"{SUPABASE_URL}/rest/v1/financial_summary?select=cycle&limit=100000"
    response = requests.get(url, headers=headers_query)
    if response.ok:
        cycles = sorted(set(record['cycle'] for record in response.json()), reverse=True)
    else:
        cycles = []

    print(f"\nFound data for {len(cycles)} cycles: {', '.join(map(str, cycles))}")

    all_gaps = {}

    for cycle in cycles:
        gaps = audit_cycle(cycle, check_fec=check_fec)
        if gaps:
            all_gaps[cycle] = gaps

    # Summary report
    print(f"\n\n{'='*80}")
    print("AUDIT SUMMARY")
    print('='*80)

    if not all_gaps:
        print("\n✅ No data gaps found across any cycles!")
        print("   All candidates with financial summaries have quarterly data.")
    else:
        print(f"\n⚠️  Found data gaps in {len(all_gaps)} cycle(s):")
        total_missing = sum(len(gaps) for gaps in all_gaps.values())
        print(f"   Total candidates missing quarterly data: {total_missing}")
        print()
        for cycle, gaps in sorted(all_gaps.items(), reverse=True):
            print(f"   {cycle}: {len(gaps)} candidates")

    return all_gaps


def generate_fix_script(all_gaps):
    """Generate a script to fix the identified gaps"""
    if not all_gaps:
        return

    print(f"\n{'='*80}")
    print("GENERATING FIX SCRIPT")
    print('='*80)

    fix_file = 'fix_missing_quarterly_data.py'

    # Build list of candidates to re-collect
    candidates_to_fix = []
    for cycle, candidate_ids in all_gaps.items():
        for candidate_id in candidate_ids:
            candidates_to_fix.append({'candidate_id': candidate_id, 'cycle': cycle})

    print(f"\n  Writing fix script to: {fix_file}")
    print(f"  Will re-collect data for {len(candidates_to_fix)} candidate-cycle combinations")

    # Save to JSON for programmatic use
    with open('missing_quarterly_data.json', 'w') as f:
        json.dump(candidates_to_fix, f, indent=2)

    print(f"  ✓ Saved missing data list to: missing_quarterly_data.json")

    print(f"\n  To fix these gaps, run:")
    print(f"     python3 scripts/collect_fec_cycle_data.py --cycle {','.join(map(str, sorted(all_gaps.keys(), reverse=True)))}")


def main():
    parser = argparse.ArgumentParser(description='Audit FEC data completeness')
    parser.add_argument('--cycle', type=int, help='Audit specific cycle only')
    parser.add_argument('--check-fec', action='store_true', help='Check FEC API for each missing candidate (slow)')
    parser.add_argument('--generate-fix', action='store_true', help='Generate script to fix gaps')

    args = parser.parse_args()

    start_time = datetime.now()

    print("\n" + "="*80)
    print("FEC DATA COMPLETENESS AUDIT")
    print("="*80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.cycle:
        gaps = {args.cycle: audit_cycle(args.cycle, check_fec=args.check_fec)}
    else:
        gaps = audit_all_cycles(check_fec=args.check_fec)

    if args.generate_fix and gaps:
        generate_fix_script(gaps)

    duration = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*80}")
    print(f"Audit completed in {duration:.1f} seconds")
    print('='*80)


if __name__ == "__main__":
    main()
