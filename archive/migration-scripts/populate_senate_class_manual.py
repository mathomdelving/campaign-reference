#!/usr/bin/env python3
"""
Populate Senate class using manual mapping of current senators.
Based on official Senate data from senate.gov (as of 2024).
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Manual mapping of state → classes
# Each state has exactly 2 Senate classes
STATE_TO_CLASSES = {
    "AL": {"II": "Tuberville", "III": "Britt"},
    "AK": {"II": "Sullivan", "III": "Murkowski"},
    "AZ": {"I": "Gallego", "III": "Kelly"},
    "AR": {"II": "Cotton", "III": "Boozman"},
    "CA": {"I": "Schiff", "III": "Padilla"},
    "CO": {"II": "Hickenlooper", "III": "Bennet"},
    "CT": {"I": "Murphy", "III": "Blumenthal"},
    "DE": {"I": "Blunt Rochester", "II": "Coons"},
    "FL": {"I": "Scott", "III": "Moody"},
    "GA": {"II": "Ossoff", "III": "Warnock"},
    "HI": {"I": "Hirono", "III": "Schatz"},
    "ID": {"II": "Risch", "III": "Crapo"},
    "IL": {"II": "Durbin", "III": "Duckworth"},
    "IN": {"I": "Banks", "III": "Young"},
    "IA": {"II": "Ernst", "III": "Grassley"},
    "KS": {"II": "Marshall", "III": "Moran"},
    "KY": {"II": "McConnell", "III": "Paul"},
    "LA": {"II": "Cassidy", "III": "Kennedy"},
    "ME": {"I": "King", "II": "Collins"},
    "MD": {"I": "Alsobrooks", "III": "Van Hollen"},
    "MA": {"I": "Warren", "II": "Markey"},
    "MI": {"I": "Slotkin", "II": "Peters"},
    "MN": {"I": "Klobuchar", "II": "Smith"},
    "MS": {"I": "Wicker", "II": "Hyde-Smith"},
    "MO": {"I": "Hawley", "III": "Schmitt"},
    "MT": {"I": "Sheehy", "II": "Daines"},
    "NE": {"I": "Fischer", "II": "Ricketts"},
    "NV": {"I": "Rosen", "III": "Cortez Masto"},
    "NH": {"II": "Shaheen", "III": "Hassan"},
    "NJ": {"I": "Kim", "II": "Booker"},
    "NM": {"I": "Heinrich", "II": "Lujan"},
    "NY": {"I": "Gillibrand", "III": "Schumer"},
    "NC": {"II": "Tillis", "III": "Budd"},
    "ND": {"I": "Cramer", "III": "Hoeven"},
    "OH": {"I": "Moreno", "III": "Husted"},
    "OK": {"II": "Mullin", "III": "Lankford"},
    "OR": {"II": "Merkley", "III": "Wyden"},
    "PA": {"I": "McCormick", "III": "Fetterman"},
    "RI": {"I": "Whitehouse", "II": "Reed"},
    "SC": {"II": "Graham", "III": "Scott"},
    "SD": {"II": "Rounds", "III": "Thune"},
    "TN": {"I": "Blackburn", "II": "Hagerty"},
    "TX": {"I": "Cruz", "II": "Cornyn"},
    "UT": {"I": "Curtis", "III": "Lee"},
    "VT": {"I": "Sanders", "III": "Welch"},
    "VA": {"I": "Kaine", "II": "Warner"},
    "WA": {"I": "Cantwell", "III": "Murray"},
    "WV": {"I": "Justice", "II": "Capito"},
    "WI": {"I": "Baldwin", "III": "Johnson"},
    "WY": {"I": "Barrasso", "II": "Lummis"},
}

# Map of likely cycles for each class (for non-incumbents)
CLASS_TO_CYCLES = {
    "I": [2024, 2018, 2012, 2030, 2036],
    "II": [2026, 2020, 2014, 2032, 2038],
    "III": [2028, 2022, 2016, 2034, 2040],
}

def normalize_name(name):
    """Normalize name for matching (last name only, uppercase)"""
    if not name:
        return ""
    # Take last name (after last comma or last space)
    if ',' in name:
        return name.split(',')[0].strip().upper()
    else:
        return name.split()[-1].strip().upper()

def main():
    print("Fetching all Senate candidates...")

    # Get all Senate candidates
    response = supabase.table("candidates").select(
        "candidate_id, name, state, office, financial_summary(cycle)"
    ).eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates")

    updates = []

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        name = candidate['name']
        state = candidate['state']

        if not state or state not in STATE_TO_CLASSES:
            continue

        # Get cycles they have data for
        cycles = [fs['cycle'] for fs in candidate.get('financial_summary', []) if fs.get('cycle')]

        # Try to match by name to known senators
        normalized_name = normalize_name(name)
        senate_class = None

        # Check if this matches a known senator
        for cls, senator_last_name in STATE_TO_CLASSES[state].items():
            if normalized_name and senator_last_name.upper() in normalized_name:
                senate_class = cls
                break

        # If not a known senator, try to infer by cycles
        if not senate_class and cycles:
            for cycle in cycles:
                for cls, cls_cycles in CLASS_TO_CYCLES.items():
                    if cycle in cls_cycles:
                        # Check if this state has this class
                        if cls in STATE_TO_CLASSES[state]:
                            senate_class = cls
                            break
                if senate_class:
                    break

        if senate_class:
            updates.append({
                'candidate_id': candidate_id,
                'name': name,
                'district': senate_class
            })

    print(f"\nUpdating {len(updates)} candidates...")

    # Update database
    for i, update in enumerate(updates):
        supabase.table("candidates").update(
            {'district': update['district']}
        ).eq('candidate_id', update['candidate_id']).execute()

        if (i + 1) % 50 == 0:
            print(f"  Updated {i + 1}/{len(updates)}")

    print(f"\n✓ Done! Updated {len(updates)} Senate candidates")

    # Print summary
    class_counts = {}
    for u in updates:
        cls = u['district']
        class_counts[cls] = class_counts.get(cls, 0) + 1

    print("\nSummary:")
    for cls in ["I", "II", "III"]:
        print(f"  Class {cls}: {class_counts.get(cls, 0)} candidates")

    # Show some examples
    print("\nExample updates:")
    for update in updates[:10]:
        print(f"  {update['name']} → Class {update['district']}")

if __name__ == "__main__":
    main()
