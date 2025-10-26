#!/usr/bin/env python3
"""
Test script to validate quarterly data fetching on a small sample of candidates
"""
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

# Test candidates
TEST_CANDIDATES = [
    {'candidate_id': 'H4VA07234', 'name': 'VINDMAN, YEVGENY'},  # Eugene Vindman
    {'candidate_id': 'S6IA00272', 'name': 'WAHLS, ZACH P'},  # Zach Wahls
    {'candidate_id': 'H8IA02043', 'name': 'MILLER-MEEKS, MARIANNETTE'},  # Miller-Meeks
]

def fetch_committee_quarterly_filings(candidate_id, cycle=CYCLE, retry_count=0):
    """
    Fetch quarterly filings for a candidate's committee(s)
    Returns list of quarterly reports with financial data
    """
    try:
        # Step 1: Get committee(s) for this candidate
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle
        }, timeout=10)

        # Handle rate limit
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

        committees = committees_response.json().get('results', [])
        all_filings = []

        # Step 2: For each committee, get filings
        for committee in committees:
            committee_id = committee.get('committee_id')

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',  # House/Senate candidate reports
                'sort': '-coverage_end_date',
                'per_page': 20  # Get up to 20 filings (covers multiple quarters + amendments)
            }, timeout=10)

            if filings_response.ok:
                filings = filings_response.json().get('results', [])

                # Filter for quarterly reports only
                quarterly_types = ['Q1', 'Q2', 'Q3', 'Q4', 'APRIL QUARTERLY', 'JULY QUARTERLY',
                                   'OCTOBER QUARTERLY', 'YEAR-END']

                for filing in filings:
                    report_type = filing.get('report_type_full', '')

                    # Only keep quarterly reports
                    if any(qt in report_type.upper() for qt in quarterly_types):
                        all_filings.append({
                            'committee_id': committee_id,
                            'filing_id': filing.get('file_number'),
                            'report_type': report_type,
                            'coverage_start_date': filing.get('coverage_start_date'),
                            'coverage_end_date': filing.get('coverage_end_date'),
                            'total_receipts': filing.get('total_receipts'),
                            'total_disbursements': filing.get('total_disbursements'),
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
    print("QUARTERLY DATA FETCH TEST")
    print(f"Testing with {len(TEST_CANDIDATES)} candidates")
    print("="*60 + "\n")

    all_quarterly = []

    for i, candidate in enumerate(TEST_CANDIDATES):
        candidate_id = candidate['candidate_id']
        name = candidate['name']

        print(f"[{i+1}/{len(TEST_CANDIDATES)}] {name} ({candidate_id})...")

        filings = fetch_committee_quarterly_filings(candidate_id)

        if filings:
            print(f"  ✓ Found {len(filings)} quarterly filings:")
            for filing in filings:
                print(f"    - {filing['report_type']}")
                print(f"      Period: {filing['coverage_start_date']} to {filing['coverage_end_date']}")
                print(f"      Receipts: ${filing['total_receipts']:,.2f}" if filing['total_receipts'] else "      Receipts: None")
                print(f"      Disbursements: ${filing['total_disbursements']:,.2f}" if filing['total_disbursements'] else "      Disbursements: None")
                print(f"      Cash Ending: ${filing['cash_ending']:,.2f}" if filing['cash_ending'] else "      Cash Ending: None")

                # Add to collection
                quarterly_record = {
                    'candidate_id': candidate_id,
                    'name': name,
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
                all_quarterly.append(quarterly_record)
        else:
            print(f"  ❌ No quarterly filings found")

        print()
        time.sleep(1)  # Be nice to the API

    # Save test output
    with open('test_quarterly_output.json', 'w') as f:
        json.dump(all_quarterly, f, indent=2)

    print("="*60)
    print(f"✓ TEST COMPLETE!")
    print(f"  Total quarterly records: {len(all_quarterly)}")
    print(f"  Output saved to: test_quarterly_output.json")
    print("="*60 + "\n")

    # Validation
    if len(all_quarterly) > 0:
        print("✅ VALIDATION PASSED - Quarterly data successfully fetched!")
        print("   Ready to run full collection.")
        return True
    else:
        print("❌ VALIDATION FAILED - No quarterly data retrieved")
        print("   Please check API key and network connection")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
