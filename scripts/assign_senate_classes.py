#!/usr/bin/env python3
"""
Definitive script to assign Senate classes to all senators and candidates.

This uses a comprehensive name-to-class mapping and handles variations.
Run this whenever new senators are added to the database.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Comprehensive mapping of senators to their classes
# Format: (last_name_pattern, state, class)
# Use uppercase patterns for matching
SENATOR_MAPPINGS = [
    # Current senators as of 2025
    ("TUBERVILLE", "AL", "II"),
    ("BRITT", "AL", "III"),
    ("SULLIVAN", "AK", "II"),
    ("MURKOWSKI", "AK", "III"),
    ("GALLEGO", "AZ", "I"),
    ("KELLY", "AZ", "III"),
    ("COTTON", "AR", "II"),
    ("BOOZMAN", "AR", "III"),
    ("SCHIFF", "CA", "I"),
    ("PADILLA", "CA", "III"),
    ("HICKENLOOPER", "CO", "II"),
    ("BENNET", "CO", "III"),
    ("MURPHY", "CT", "I"),
    ("BLUMENTHAL", "CT", "III"),
    ("BLUNT ROCHESTER", "DE", "I"),
    ("ROCHESTER", "DE", "I"),  # Alternative
    ("COONS", "DE", "II"),
    ("SCOTT", "FL", "I"),
    ("MOODY", "FL", "III"),
    ("OSSOFF", "GA", "II"),
    ("WARNOCK", "GA", "III"),
    ("HIRONO", "HI", "I"),
    ("SCHATZ", "HI", "III"),
    ("RISCH", "ID", "II"),
    ("CRAPO", "ID", "III"),
    ("DURBIN", "IL", "II"),
    ("DUCKWORTH", "IL", "III"),
    ("BANKS", "IN", "I"),
    ("YOUNG", "IN", "III"),
    ("ERNST", "IA", "II"),
    ("GRASSLEY", "IA", "III"),
    ("MARSHALL", "KS", "II"),
    ("MORAN", "KS", "III"),
    ("MCCONNELL", "KY", "II"),
    ("PAUL", "KY", "III"),
    ("CASSIDY", "LA", "II"),
    ("KENNEDY", "LA", "III"),
    ("KING", "ME", "I"),
    ("COLLINS", "ME", "II"),
    ("ALSOBROOKS", "MD", "I"),
    ("VAN HOLLEN", "MD", "III"),
    ("WARREN", "MA", "I"),
    ("MARKEY", "MA", "II"),
    ("SLOTKIN", "MI", "I"),
    ("PETERS", "MI", "II"),
    ("KLOBUCHAR", "MN", "I"),
    ("SMITH", "MN", "II"),
    ("WICKER", "MS", "I"),
    ("HYDE-SMITH", "MS", "II"),
    ("HAWLEY", "MO", "I"),
    ("SCHMITT", "MO", "III"),
    ("SHEEHY", "MT", "I"),
    ("DAINES", "MT", "II"),
    ("FISCHER", "NE", "I"),
    ("RICKETTS", "NE", "II"),
    ("ROSEN", "NV", "I"),
    ("CORTEZ MASTO", "NV", "III"),
    ("SHAHEEN", "NH", "II"),
    ("HASSAN", "NH", "III"),
    ("KIM", "NJ", "I"),
    ("BOOKER", "NJ", "II"),
    ("HEINRICH", "NM", "I"),
    ("LUJAN", "NM", "II"),
    ("GILLIBRAND", "NY", "I"),
    ("SCHUMER", "NY", "III"),
    ("TILLIS", "NC", "II"),
    ("BUDD", "NC", "III"),
    ("CRAMER", "ND", "I"),
    ("HOEVEN", "ND", "III"),
    ("MORENO", "OH", "I"),
    ("HUSTED", "OH", "III"),
    ("MULLIN", "OK", "II"),
    ("LANKFORD", "OK", "III"),
    ("MERKLEY", "OR", "II"),
    ("WYDEN", "OR", "III"),
    ("MCCORMICK", "PA", "I"),
    ("FETTERMAN", "PA", "III"),
    ("WHITEHOUSE", "RI", "I"),
    ("REED", "RI", "II"),
    ("GRAHAM", "SC", "II"),
    ("SCOTT", "SC", "III"),
    ("ROUNDS", "SD", "II"),
    ("THUNE", "SD", "III"),
    ("BLACKBURN", "TN", "I"),
    ("HAGERTY", "TN", "II"),
    ("CRUZ", "TX", "I"),
    ("CORNYN", "TX", "II"),
    ("CURTIS", "UT", "I"),
    ("LEE", "UT", "III"),
    ("SANDERS", "VT", "I"),
    ("WELCH", "VT", "III"),
    ("KAINE", "VA", "I"),
    ("WARNER", "VA", "II"),
    ("CANTWELL", "WA", "I"),
    ("MURRAY", "WA", "III"),
    ("JUSTICE", "WV", "I"),
    ("CAPITO", "WV", "II"),
    ("BALDWIN", "WI", "I"),
    ("JOHNSON", "WI", "III"),
    ("BARRASSO", "WY", "I"),
    ("LUMMIS", "WY", "II"),
]

def main():
    print("Fetching all Senate candidates...")

    response = supabase.table("candidates").select("candidate_id, name, state, district").eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates")

    updates = []

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        name = (candidate['name'] or "").upper()
        state = candidate['state']
        current_district = candidate['district']

        # Skip if already has a class assigned
        if current_district in ['I', 'II', 'III']:
            continue

        # Try to match against known senators
        matched_class = None
        for name_pattern, senator_state, senate_class in SENATOR_MAPPINGS:
            if state == senator_state and name_pattern in name:
                matched_class = senate_class
                break

        if matched_class:
            updates.append({
                'candidate_id': candidate_id,
                'name': candidate['name'],
                'state': state,
                'district': matched_class
            })

    print(f"\nFound {len(updates)} candidates to update")

    if updates:
        print("\nUpdates to apply:")
        for update in updates[:20]:  # Show first 20
            print(f"  {update['name']} ({update['state']}) → Class {update['district']}")
        if len(updates) > 20:
            print(f"  ... and {len(updates) - 20} more")

        proceed = input("\nProceed with updates? (yes/no): ")
        if proceed.lower() != 'yes':
            print("Aborted.")
            return

        # Apply updates
        for i, update in enumerate(updates):
            supabase.table("candidates").update(
                {'district': update['district']}
            ).eq('candidate_id', update['candidate_id']).execute()

            if (i + 1) % 25 == 0:
                print(f"  Updated {i + 1}/{len(updates)}")

        print(f"\n✓ Updated {len(updates)} candidates")
    else:
        print("\nNo updates needed - all known senators already have classes assigned")

    # Summary
    result = supabase.table("candidates").select("district").eq("office", "S").execute()
    class_counts = {}
    for c in result.data:
        dist = c['district']
        if dist in ['I', 'II', 'III']:
            class_counts[dist] = class_counts.get(dist, 0) + 1

    print("\n" + "="*70)
    print("CURRENT STATUS")
    print("="*70)
    for cls in ['I', 'II', 'III']:
        count = class_counts.get(cls, 0)
        print(f"Class {cls}: {count} senators/candidates")

    unclassified = len([c for c in result.data if c['district'] not in ['I', 'II', 'III']])
    print(f"Unclassified: {unclassified} candidates")

if __name__ == "__main__":
    main()
