#!/usr/bin/env python3
"""Test sitting senator matching"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Just the problem senators
SITTING_SENATORS_CLASS_II = [("SULLIVAN", "AK")]
SITTING_SENATORS_CLASS_III = [("GRASSLEY", "IA"), ("SCHUMER", "NY")]
SITTING_SENATORS_CLASS_I = [("GILLIBRAND", "NY")]

def is_sitting_senator(name: str, state: str) -> tuple:
    """Check if candidate is a sitting senator. Returns (is_sitting, class)"""
    name_upper = (name or "").upper()

    # Check Class I
    for senator_name, senator_state in SITTING_SENATORS_CLASS_I:
        if state == senator_state and senator_name in name_upper:
            return (True, "I")

    # Check Class II
    for senator_name, senator_state in SITTING_SENATORS_CLASS_II:
        if state == senator_state and senator_name in name_upper:
            return (True, "II")

    # Check Class III
    for senator_name, senator_state in SITTING_SENATORS_CLASS_III:
        if state == senator_state and senator_name in name_upper:
            return (True, "III")

    return (False, None)


# Get these specific senators
test_ids = ['S4AK00214', 'S0IA00028', 'S0NY00410', 'S8NY00082']

print('Testing sitting senator matching:')
print('='*70)

for candidate_id in test_ids:
    result = supabase.table('candidates').select('candidate_id, name, state, district').eq('candidate_id', candidate_id).execute()

    if result.data:
        candidate = result.data[0]
        name = candidate['name']
        state = candidate['state']
        current_district = candidate['district']

        is_sitting, official_class = is_sitting_senator(name, state)

        print(f'{name} ({state})')
        print(f'  Current district: {current_district}')
        print(f'  Is sitting senator: {is_sitting}')
        print(f'  Official class: {official_class}')
        print(f'  Needs update: {current_district != official_class}')
        print()
