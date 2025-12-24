#!/usr/bin/env python3
"""Test finding principal campaign committees"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.environ.get('FEC_API_KEY')

# Test with Christy Smith
candidate_id = 'H0CA25154'

print(f"Getting ALL committees for {candidate_id}")
print("="*80)

response = requests.get(
    f'https://api.open.fec.gov/v1/candidate/{candidate_id}/committees/',
    params={
        'api_key': FEC_API_KEY,
        'per_page': 20
    },
    timeout=30
)

all_committees = response.json().get('results', [])

print(f"Total committees found: {len(all_committees)}\n")

for comm in all_committees:
    print(f"ID: {comm['committee_id']}")
    print(f"Name: {comm.get('name', 'N/A')}")
    print(f"Designation: {comm.get('designation', 'N/A')} - {comm.get('designation_full', 'N/A')}")
    print(f"Type: {comm.get('committee_type', 'N/A')} - {comm.get('committee_type_full', 'N/A')}")
    print()

# Filter for principal campaign committees (designation = 'P')
principal_committees = [c for c in all_committees if c.get('designation') == 'P']

print("\n" + "="*80)
print(f"PRINCIPAL CAMPAIGN COMMITTEES (designation='P'): {len(principal_committees)}")
print("="*80)

for comm in principal_committees:
    print(f"ID: {comm['committee_id']}")
    print(f"Name: {comm.get('name', 'N/A')}")
    print()

# Also try with designation='A' (authorized by candidate)
authorized_committees = [c for c in all_committees if c.get('designation') == 'A']

print("\n" + "="*80)
print(f"AUTHORIZED COMMITTEES (designation='A'): {len(authorized_committees)}")
print("="*80)

for comm in authorized_committees:
    print(f"ID: {comm['committee_id']}")
    print(f"Name: {comm.get('name', 'N/A')}")
    print()
