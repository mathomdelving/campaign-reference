#!/usr/bin/env python3
"""
Backfill cash_on_hand for historical cycles
CRITICAL FIX: Don't filter committees by cycle - get ALL committees for each candidate
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers_supabase = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

headers_query = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

RATE_LIMIT_DELAY = 0.5


def get_candidate_committees(candidate_id):
    """Get ALL committees for a candidate (DO NOT filter by cycle!)"""
    try:
        url = f"https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/"
        params = {
            'api_key': FEC_API_KEY,
            # CRITICAL: Do NOT add 'cycle' parameter here
            # Committees created in other cycles are still valid!
            'per_page': 20
        }

        response = requests.get(url, params=params, timeout=30)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return []

        return response.json().get('results', [])

    except Exception as e:
        return []


def get_year_end_cash(committee_id, cycle):
    """Get cash_on_hand from year-end report for a committee in a specific cycle"""
    try:
        url = f"https://api.open.fec.gov/v1/committee/{committee_id}/reports/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,  # Filter reports by cycle
            'per_page': 20,
            'sort': '-coverage_end_date'
        }

        response = requests.get(url, params=params, timeout=30)
        time.sleep(RATE_LIMIT_DELAY)

        if not response.ok:
            return None

        data = response.json()
        reports = data.get('results', [])

        if not reports:
            return None

        # Look for year-end (YE) report first
        for report in reports:
            if report.get('report_type') == 'YE':
                cash = report.get('cash_on_hand_end_period')
                if cash is not None:
                    return cash

        # If no YE report, look for Q4, 12P, or other end-of-year reports
        for report in reports:
            rtype = report.get('report_type', '')
            if rtype in ['Q4', '12P', 'M12']:
                cash = report.get('cash_on_hand_end_period')
                if cash is not None:
                    return cash

        # If still nothing, return the most recent report's cash
        if reports:
            return reports[0].get('cash_on_hand_end_period')

        return None

    except Exception as e:
        return None


def backfill_cycle(cycle):
    """Backfill cash_on_hand for all candidates in a cycle"""

    print(f"\n{'='*80}")
    print(f"BACKFILLING CASH ON HAND FOR CYCLE {cycle}")
    print('='*80)

    # Get ONLY financial records with cash_on_hand = 0 (using pagination)
    PAGE_SIZE = 1000
    from_offset = 0
    candidate_ids = []

    print("\n✓ Fetching candidates with missing cash_on_hand...")

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/financial_summary",
            params={
                'cycle': f'eq.{cycle}',
                'cash_on_hand': 'eq.0',
                'select': 'candidate_id',
                'limit': PAGE_SIZE,
                'offset': from_offset
            },
            headers=headers_query
        )

        page = response.json()
        if not page or len(page) == 0:
            break

        candidate_ids.extend([r['candidate_id'] for r in page])

        if len(page) < PAGE_SIZE:
            break

        from_offset += PAGE_SIZE

    print(f"✓ Found {len(candidate_ids)} candidates with missing cash_on_hand\n")

    updated = 0
    errors = 0
    no_data = 0

    for i, candidate_id in enumerate(candidate_ids, 1):
        try:
            # Get ALL committees for this candidate
            committees = get_candidate_committees(candidate_id)

            if not committees:
                no_data += 1
                continue

            # Try to get cash_on_hand from each committee until we find one
            cash_on_hand = None
            for committee in committees:
                committee_id = committee['committee_id']
                cash = get_year_end_cash(committee_id, cycle)

                if cash is not None:
                    cash_on_hand = cash
                    break

            if cash_on_hand is None:
                no_data += 1
                continue

            # Update the financial_summary record
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/financial_summary",
                params={
                    'candidate_id': f'eq.{candidate_id}',
                    'cycle': f'eq.{cycle}'
                },
                headers=headers_supabase,
                json={'cash_on_hand': cash_on_hand}
            )

            if response.status_code in [200, 204]:
                updated += 1
                if updated % 50 == 0:
                    print(f"  Progress: {updated} updated, {no_data} no data, {i}/{len(candidate_ids)} processed")
            else:
                errors += 1

        except Exception as e:
            errors += 1
            continue

    print(f"\n✅ Updated {updated} records")
    print(f"⚠️  {no_data} candidates had no year-end report data")
    if errors > 0:
        print(f"❌ {errors} errors")


def main():
    print("="*80)
    print("CASH ON HAND BACKFILL - ALL Historical Cycles")
    print("="*80)
    print("\nCRITICAL FIX: Getting ALL committees per candidate (not filtered by cycle)")
    print("VERIFIED: 2018 and 2020 data IS available in FEC API")

    # Process ALL cycles
    cycles = [2024, 2022, 2020, 2018]

    for cycle in cycles:
        backfill_cycle(cycle)
        time.sleep(2)

    print(f"\n{'='*80}")
    print("BACKFILL COMPLETE")
    print('='*80)


if __name__ == '__main__':
    main()
