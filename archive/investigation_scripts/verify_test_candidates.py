#!/usr/bin/env python3
"""
Verify the test candidate IDs and find correct ones
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

def search_candidate(name):
    """Search for a candidate by name"""
    response = requests.get(
        'https://api.open.fec.gov/v1/candidates/search/',
        params={
            'api_key': FEC_API_KEY,
            'q': name,
            'per_page': 10
        },
        timeout=30
    )

    results = response.json().get('results', [])
    print(f"\n{'='*80}")
    print(f"Search: {name}")
    print('='*80)

    for cand in results[:5]:
        print(f"ID: {cand['candidate_id']}")
        print(f"Name: {cand['name']}")
        print(f"Election Years: {cand.get('election_years', [])}")
        print(f"Office: {cand.get('office')}")
        print(f"State: {cand.get('state')}")
        print()

def check_candidate_committees(candidate_id, name):
    """Check ALL committees for a candidate"""
    response = requests.get(
        f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
        params={
            'api_key': FEC_API_KEY,
            'per_page': 20
        },
        timeout=30
    )

    committees = response.json().get('results', [])

    print(f"\n{'='*80}")
    print(f"Committees for {name} ({candidate_id})")
    print('='*80)

    for comm in committees:
        print(f"ID: {comm['committee_id']}")
        print(f"Name: {comm.get('name', 'N/A')}")
        print(f"Designation: {comm.get('designation', 'N/A')}")
        print(f"Type: {comm.get('committee_type', 'N/A')}")
        print()

# Search for each test candidate
search_candidate("Kirsten Engel")
search_candidate("Christy Smith")
search_candidate("Rita Hart")
search_candidate("Abby Finkenauer")

# Check Christy Smith's committees
print("\n" + "="*80)
print("DETAILED CHECK: Christy Smith")
print("="*80)
check_candidate_committees("H0CA25154", "Christy Smith")
