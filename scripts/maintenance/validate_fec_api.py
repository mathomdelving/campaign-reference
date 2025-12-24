#!/usr/bin/env python3
"""
FEC API Health Check and Validation

Run this before major data collections to ensure FEC API hasn't changed
in ways that would break our collection scripts.

Usage:
  python3 scripts/maintenance/validate_fec_api.py
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

# Known working candidate for testing
TEST_CANDIDATE_ID = "H0CA52177"  # Pelosi - always has data

def validate_api():
    """Validate FEC API structure matches our expectations"""
    print("\n" + "="*60)
    print("FEC API HEALTH CHECK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    issues = []

    # Test 1: Candidates endpoint
    print("\n1. Testing /candidates/ endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/candidates/",
            params={'api_key': FEC_API_KEY, 'cycle': 2022, 'per_page': 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if 'results' not in data:
            issues.append("❌ /candidates/ response missing 'results' field")
        elif len(data['results']) == 0:
            issues.append("⚠️  /candidates/ returned no results")
        else:
            candidate = data['results'][0]
            expected_fields = ['candidate_id', 'name', 'party_full', 'state',
                             'district', 'office_full']
            missing = [f for f in expected_fields if f not in candidate]
            if missing:
                issues.append(f"❌ Candidate record missing fields: {missing}")
            else:
                print("   ✅ Structure valid")
    except Exception as e:
        issues.append(f"❌ /candidates/ endpoint failed: {e}")

    # Test 2: Financial totals endpoint
    print("\n2. Testing /candidate/{id}/totals/ endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/candidate/{TEST_CANDIDATE_ID}/totals/",
            params={'api_key': FEC_API_KEY, 'cycle': 2022},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if 'results' not in data:
            issues.append("❌ /totals/ response missing 'results' field")
        elif len(data['results']) == 0:
            print("   ⚠️  No financial data (might be normal for test candidate)")
        else:
            totals = data['results'][0]
            expected_fields = ['receipts', 'disbursements', 'last_cash_on_hand_end_period',
                             'coverage_start_date', 'coverage_end_date', 'last_report_year',
                             'last_report_type_full']
            missing = [f for f in expected_fields if f not in totals]
            if missing:
                issues.append(f"❌ Financial totals missing fields: {missing}")
            else:
                print("   ✅ Structure valid")
                print(f"      Sample: ${totals.get('receipts', 0):,.0f} raised")
    except Exception as e:
        issues.append(f"❌ /totals/ endpoint failed: {e}")

    # Test 3: Committees endpoint
    print("\n3. Testing /candidate/{id}/committees/ endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/candidate/{TEST_CANDIDATE_ID}/committees/",
            params={'api_key': FEC_API_KEY, 'cycle': 2022},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if 'results' not in data:
            issues.append("❌ /committees/ response missing 'results' field")
        elif len(data['results']) == 0:
            print("   ⚠️  No committees (might be normal)")
        else:
            committee = data['results'][0]
            expected_fields = ['committee_id', 'designation', 'designation_full',
                             'committee_type', 'committee_type_full']
            missing = [f for f in expected_fields if f not in committee]
            if missing:
                issues.append(f"❌ Committee record missing fields: {missing}")
            else:
                print("   ✅ Structure valid")
                print(f"      Sample: {committee.get('designation_full', 'N/A')}")
    except Exception as e:
        issues.append(f"❌ /committees/ endpoint failed: {e}")

    # Test 4: Filings endpoint
    print("\n4. Testing /committee/{id}/filings/ endpoint...")
    try:
        # First get a committee ID
        committees_response = requests.get(
            f"{BASE_URL}/candidate/{TEST_CANDIDATE_ID}/committees/",
            params={'api_key': FEC_API_KEY, 'cycle': 2022},
            timeout=10
        )
        committees_response.raise_for_status()
        committees = committees_response.json().get('results', [])

        if committees:
            committee_id = committees[0]['committee_id']

            response = requests.get(
                f"{BASE_URL}/committee/{committee_id}/filings/",
                params={'api_key': FEC_API_KEY, 'cycle': 2022, 'per_page': 1},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'results' not in data:
                issues.append("❌ /filings/ response missing 'results' field")
            elif len(data['results']) == 0:
                print("   ⚠️  No filings (might be normal)")
            else:
                filing = data['results'][0]
                expected_fields = ['file_number', 'report_type_full', 'coverage_start_date',
                                 'coverage_end_date', 'total_receipts', 'total_disbursements',
                                 'cash_on_hand_beginning_period', 'cash_on_hand_end_period',
                                 'is_amended']
                missing = [f for f in expected_fields if f not in filing]
                if missing:
                    issues.append(f"❌ Filing record missing fields: {missing}")
                else:
                    print("   ✅ Structure valid")
                    print(f"      Sample: {filing.get('report_type_full', 'N/A')}")
        else:
            print("   ⚠️  No committees found for test candidate")
    except Exception as e:
        issues.append(f"❌ /filings/ endpoint failed: {e}")

    # Test 5: Rate limit headers
    print("\n5. Testing rate limit headers...")
    try:
        response = requests.get(
            f"{BASE_URL}/candidates/",
            params={'api_key': FEC_API_KEY, 'per_page': 1},
            timeout=10
        )

        rate_limit = response.headers.get('X-RateLimit-Limit')
        rate_remaining = response.headers.get('X-RateLimit-Remaining')

        if rate_limit:
            print(f"   ✅ Rate limit: {rate_limit} requests/hour")
            print(f"      Remaining: {rate_remaining}")

            if int(rate_limit) != 1000:
                issues.append(f"⚠️  Rate limit changed from 1000 to {rate_limit}")
        else:
            print("   ⚠️  No rate limit headers (API might have changed)")
    except Exception as e:
        issues.append(f"⚠️  Could not check rate limits: {e}")

    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    if not issues:
        print("✅ ALL CHECKS PASSED - API structure is stable")
        print("\nYour collection scripts should work correctly.")
        return True
    else:
        print(f"⚠️  FOUND {len(issues)} ISSUE(S):\n")
        for issue in issues:
            print(f"  {issue}")

        print("\n❌ WARNING: FEC API may have changed!")
        print("Review issues above before running large collections.")
        print("You may need to update the collection scripts.\n")
        return False

if __name__ == "__main__":
    if not FEC_API_KEY:
        print("ERROR: FEC_API_KEY not found in .env file!")
        exit(1)

    success = validate_api()
    exit(0 if success else 1)
