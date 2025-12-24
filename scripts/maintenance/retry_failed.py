import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"
CYCLE = 2026

def fetch_candidate_financials(candidate_id, cycle=CYCLE, retry_count=0):
    """Fetch financial totals with retry logic for rate limits"""
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT HIT! Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return fetch_candidate_financials(candidate_id, cycle, retry_count + 1)
            else:
                print(f"\n  ❌ Rate limit persists after {retry_count} retries. Skipping.")
                return None

        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching financials for {candidate_id}: {e}")
        return None

def fetch_committee_quarterly_filings(candidate_id, cycle=CYCLE, retry_count=0):
    """Fetch quarterly filings for a candidate's committee(s)"""
    try:
        # Get committees
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle
        }, timeout=10)

        if committees_response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_committee_quarterly_filings(candidate_id, cycle, retry_count + 1)
            else:
                return []

        if not committees_response.ok:
            return []

        time.sleep(4)  # Rate limit

        committees = committees_response.json().get('results', [])
        all_filings = []

        for committee in committees:
            committee_id = committee.get('committee_id')

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',
                'sort': '-coverage_end_date',
                'per_page': 20
            }, timeout=10)

            time.sleep(4)  # Rate limit

            if filings_response.ok:
                filings = filings_response.json().get('results', [])
                quarterly_types = ['Q1', 'Q2', 'Q3', 'Q4', 'APRIL QUARTERLY', 'JULY QUARTERLY',
                                   'OCTOBER QUARTERLY', 'YEAR-END']

                for filing in filings:
                    report_type = filing.get('report_type_full', '')

                    if any(qt in report_type.upper() for qt in quarterly_types):
                        receipts = filing.get('total_receipts')
                        disbursements = filing.get('total_disbursements')

                        all_filings.append({
                            'committee_id': committee_id,
                            'filing_id': filing.get('file_number'),
                            'report_type': report_type,
                            'coverage_start_date': filing.get('coverage_start_date'),
                            'coverage_end_date': filing.get('coverage_end_date'),
                            'total_receipts': receipts,
                            'total_disbursements': disbursements,
                            'cash_beginning': filing.get('cash_on_hand_beginning_period'),
                            'cash_ending': filing.get('cash_on_hand_end_period'),
                            'is_amendment': filing.get('is_amended', False)
                        })

        return all_filings

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching quarterly filings for {candidate_id}: {e}")
        return []

def main():
    print("\n" + "="*60)
    print("RETRY FAILED CANDIDATES - Starting...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Load existing data
    print("\nLoading existing data...")
    candidates = json.load(open('candidates_2026.json'))
    financials = json.load(open('financials_2026.json'))
    quarterly_financials = json.load(open('quarterly_financials_2026.json'))

    # Get candidate IDs we already have
    existing_ids = {f['candidate_id'] for f in financials}

    print(f"✓ Total candidates: {len(candidates)}")
    print(f"✓ Already have: {len(existing_ids)}")

    # Find candidates that failed (after index where we last had good data)
    # Look for the last candidates that had DNS errors
    failed_candidates = []
    for i in range(len(candidates) - 1, -1, -1):
        candidate = candidates[i]
        if candidate['candidate_id'] not in existing_ids:
            failed_candidates.insert(0, candidate)
        else:
            # Stop when we find a candidate we have data for
            break

    print(f"✓ Retrying last {len(failed_candidates)} candidates that failed\n")

    if not failed_candidates:
        print("No failed candidates to retry!")
        return

    # Retry failed candidates
    new_financials = []
    new_quarterly = []

    for idx, candidate in enumerate(failed_candidates):
        candidate_id = candidate.get('candidate_id')
        name = candidate.get('name', 'Unknown')

        print(f"  [{idx+1}/{len(failed_candidates)}] {name} ({candidate_id})...", end=" ")

        # Fetch summary data
        financial_data = fetch_candidate_financials(candidate_id)
        time.sleep(4)

        if financial_data:
            combined = {
                'candidate_id': candidate_id,
                'name': name,
                'party': candidate.get('party_full'),
                'state': candidate.get('state'),
                'district': candidate.get('district'),
                'office': candidate.get('office_full'),
                'total_receipts': financial_data.get('receipts'),
                'total_disbursements': financial_data.get('disbursements'),
                'cash_on_hand': financial_data.get('last_cash_on_hand_end_period'),  # FIXED: Use correct field name
                'coverage_start_date': financial_data.get('coverage_start_date'),
                'coverage_end_date': financial_data.get('coverage_end_date'),
                'last_report_year': financial_data.get('last_report_year'),
                'last_report_type': financial_data.get('last_report_type_full'),
                'cycle': CYCLE
            }
            new_financials.append(combined)

        # Fetch quarterly filings
        filings = fetch_committee_quarterly_filings(candidate_id)

        if filings:
            for filing in filings:
                quarterly_record = {
                    'candidate_id': candidate_id,
                    'name': name,
                    'party': candidate.get('party_full'),
                    'state': candidate.get('state'),
                    'district': candidate.get('district'),
                    'office': candidate.get('office_full'),
                    'committee_id': filing['committee_id'],
                    'filing_id': filing['filing_id'],
                    'report_type': filing['report_type'],
                    'coverage_start_date': filing['coverage_start_date'],
                    'coverage_end_date': filing['coverage_end_date'],
                    'total_receipts': filing['total_receipts'],
                    'total_disbursements': filing['total_disbursements'],
                    'cash_beginning': filing['cash_beginning'],
                    'cash_ending': filing['cash_ending'],
                    'is_amendment': filing['is_amendment'],
                    'cycle': CYCLE
                }
                new_quarterly.append(quarterly_record)
            print(f"✓ ({len(filings)} quarterly filings)")
        else:
            print("✓ (no quarterly data)")

    # Merge with existing data
    print(f"\n{'='*60}")
    print("Merging data...")
    financials.extend(new_financials)
    quarterly_financials.extend(new_quarterly)

    # Save updated files
    with open('financials_2026.json', 'w') as f:
        json.dump(financials, f, indent=2)

    with open('quarterly_financials_2026.json', 'w') as f:
        json.dump(quarterly_financials, f, indent=2)

    print(f"✓ Updated financials_2026.json ({len(financials)} total)")
    print(f"✓ Updated quarterly_financials_2026.json ({len(quarterly_financials)} total)")
    print(f"✓ Added {len(new_financials)} new financial records")
    print(f"✓ Added {len(new_quarterly)} new quarterly records")
    print(f"{'='*60}")
    print("\n✓ RETRY COMPLETE!")

if __name__ == "__main__":
    main()
