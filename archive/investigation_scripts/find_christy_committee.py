#!/usr/bin/env python3
"""Find Christy Smith's actual campaign committee"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

# Try different approaches to find her committee

# 1. Check if her candidate record has a principal_committees field
print("="*80)
print("Checking Christy Smith candidate record")
print("="*80)
response = requests.get(
    'https://api.open.fec.gov/v1/candidates/',
    params={
        'api_key': FEC_API_KEY,
        'candidate_id': 'H0CA25154',
        'per_page': 10
    },
    timeout=30
)

for cand in response.json().get('results', []):
    print(f"Candidate ID: {cand['candidate_id']}")
    print(f"Name: {cand['name']}")
    print(f"Election Years: {cand.get('election_years', [])}")
    print(f"Principal Committees: {cand.get('principal_committees', [])}")
    print()

# 2. Search committees directly for "Christy Smith"
print("\n" + "="*80)
print("Searching committees for 'Christy Smith'")
print("="*80)
response = requests.get(
    'https://api.open.fec.gov/v1/committees/',
    params={
        'api_key': FEC_API_KEY,
        'q': 'Christy Smith',
        'per_page': 20
    },
    timeout=30
)

for comm in response.json().get('results', []):
    print(f"Committee ID: {comm['committee_id']}")
    print(f"Name: {comm.get('name', 'N/A')}")
    print(f"Designation: {comm.get('designation', 'N/A')}")
    print(f"Type: {comm.get('committee_type', 'N/A')}")
    print(f"Candidate IDs: {comm.get('candidate_ids', [])}")
    print()

# 3. Try the totals endpoint
print("\n" + "="*80)
print("Checking totals endpoint for H0CA25154")
print("="*80)
response = requests.get(
    'https://api.open.fec.gov/v1/candidate/H0CA25154/totals/',
    params={
        'api_key': FEC_API_KEY,
        'cycle': 2022,
        'per_page': 10
    },
    timeout=30
)

data = response.json()
print(f"Results: {data.get('results', [])}")
