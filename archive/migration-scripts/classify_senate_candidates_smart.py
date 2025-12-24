#!/usr/bin/env python3
"""
Smart Senate candidate classification.

Approach:
1. NEVER change sitting senators (protected list) - they keep their class forever
2. For challengers/former senators, assign class based on election cycle + state
3. Use the EARLIEST cycle with data (not most recent) to determine their class
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cycle to class mapping
CYCLE_TO_CLASS = {
    2010: "III", 2012: "I", 2014: "II", 2016: "III", 2018: "I", 2020: "II",
    2022: "III", 2024: "I", 2026: "II", 2028: "III", 2030: "I", 2032: "II",
    2034: "III", 2036: "I", 2038: "II", 2040: "III",
}

# State classes
STATE_CLASSES = {
    "AL": ["II", "III"], "AK": ["II", "III"], "AZ": ["I", "III"], "AR": ["II", "III"],
    "CA": ["I", "III"], "CO": ["II", "III"], "CT": ["I", "III"], "DE": ["I", "II"],
    "FL": ["I", "III"], "GA": ["II", "III"], "HI": ["I", "III"], "ID": ["II", "III"],
    "IL": ["II", "III"], "IN": ["I", "III"], "IA": ["II", "III"], "KS": ["II", "III"],
    "KY": ["II", "III"], "LA": ["II", "III"], "ME": ["I", "II"], "MD": ["I", "III"],
    "MA": ["I", "II"], "MI": ["I", "II"], "MN": ["I", "II"], "MS": ["I", "II"],
    "MO": ["I", "III"], "MT": ["I", "II"], "NE": ["I", "II"], "NV": ["I", "III"],
    "NH": ["II", "III"], "NJ": ["I", "II"], "NM": ["I", "II"], "NY": ["I", "III"],
    "NC": ["II", "III"], "ND": ["I", "III"], "OH": ["I", "III"], "OK": ["II", "III"],
    "OR": ["II", "III"], "PA": ["I", "III"], "RI": ["I", "II"], "SC": ["II", "III"],
    "SD": ["II", "III"], "TN": ["I", "II"], "TX": ["I", "II"], "UT": ["I", "III"],
    "VT": ["I", "III"], "VA": ["I", "II"], "WA": ["I", "III"], "WV": ["I", "II"],
    "WI": ["I", "III"], "WY": ["I", "II"],
}

# PROTECTED: Current sitting senators - NEVER change their class
# Format: (last_name_uppercase, state, class, reason)
PROTECTED_SENATORS = [
    ("TUBERVILLE", "AL", "II", "Sitting"),
    ("BRITT", "AL", "III", "Sitting"),
    ("SULLIVAN", "AK", "II", "Sitting"),
    ("MURKOWSKI", "AK", "III", "Sitting"),
    ("GALLEGO", "AZ", "I", "Sitting"),
    ("KELLY", "AZ", "III", "Sitting"),
    ("COTTON", "AR", "II", "Sitting"),
    ("BOOZMAN", "AR", "III", "Sitting"),
    ("SCHIFF", "CA", "I", "Sitting"),
    ("PADILLA", "CA", "III", "Sitting"),
    ("HICKENLOOPER", "CO", "II", "Sitting"),
    ("BENNET", "CO", "III", "Sitting"),
    ("MURPHY", "CT", "I", "Sitting"),
    ("BLUMENTHAL", "CT", "III", "Sitting"),
    ("ROCHESTER", "DE", "I", "Sitting"),  # Blunt Rochester
    ("COONS", "DE", "II", "Sitting"),
    ("SCOTT", "FL", "I", "Sitting"),
    ("MOODY", "FL", "III", "Sitting"),
    ("OSSOFF", "GA", "II", "Sitting"),
    ("WARNOCK", "GA", "III", "Sitting"),
    ("HIRONO", "HI", "I", "Sitting"),
    ("SCHATZ", "HI", "III", "Sitting"),
    ("RISCH", "ID", "II", "Sitting"),
    ("CRAPO", "ID", "III", "Sitting"),
    ("DURBIN", "IL", "II", "Sitting"),
    ("DUCKWORTH", "IL", "III", "Sitting"),
    ("BANKS", "IN", "I", "Sitting"),
    ("YOUNG", "IN", "III", "Sitting"),
    ("ERNST", "IA", "II", "Sitting"),
    ("GRASSLEY", "IA", "III", "Sitting"),
    ("MARSHALL", "KS", "II", "Sitting"),
    ("MORAN", "KS", "III", "Sitting"),
    ("MCCONNELL", "KY", "II", "Sitting"),
    ("PAUL", "KY", "III", "Sitting"),
    ("CASSIDY", "LA", "II", "Sitting"),
    ("KENNEDY", "LA", "III", "Sitting"),
    ("KING", "ME", "I", "Sitting"),
    ("COLLINS", "ME", "II", "Sitting"),
    ("ALSOBROOKS", "MD", "I", "Sitting"),
    ("VAN HOLLEN", "MD", "III", "Sitting"),
    ("WARREN", "MA", "I", "Sitting"),
    ("MARKEY", "MA", "II", "Sitting"),
    ("SLOTKIN", "MI", "I", "Sitting"),
    ("PETERS", "MI", "II", "Sitting"),
    ("KLOBUCHAR", "MN", "I", "Sitting"),
    ("SMITH", "MN", "II", "Sitting"),
    ("WICKER", "MS", "I", "Sitting"),
    ("HYDE-SMITH", "MS", "II", "Sitting"),
    ("HAWLEY", "MO", "I", "Sitting"),
    ("SCHMITT", "MO", "III", "Sitting"),
    ("SHEEHY", "MT", "I", "Sitting"),
    ("DAINES", "MT", "II", "Sitting"),
    ("FISCHER", "NE", "I", "Sitting"),
    ("RICKETTS", "NE", "II", "Sitting"),
    ("ROSEN", "NV", "I", "Sitting"),
    ("CORTEZ MASTO", "NV", "III", "Sitting"),
    ("SHAHEEN", "NH", "II", "Sitting"),
    ("HASSAN", "NH", "III", "Sitting"),
    ("KIM", "NJ", "I", "Sitting"),
    ("BOOKER", "NJ", "II", "Sitting"),
    ("HEINRICH", "NM", "I", "Sitting"),
    ("LUJAN", "NM", "II", "Sitting"),
    ("GILLIBRAND", "NY", "I", "Sitting"),
    ("SCHUMER", "NY", "III", "Sitting"),
    ("TILLIS", "NC", "II", "Sitting"),
    ("BUDD", "NC", "III", "Sitting"),
    ("CRAMER", "ND", "I", "Sitting"),
    ("HOEVEN", "ND", "III", "Sitting"),
    ("MORENO", "OH", "I", "Sitting"),
    ("HUSTED", "OH", "III", "Sitting"),
    ("MULLIN", "OK", "II", "Sitting"),
    ("LANKFORD", "OK", "III", "Sitting"),
    ("MERKLEY", "OR", "II", "Sitting"),
    ("WYDEN", "OR", "III", "Sitting"),
    ("MCCORMICK", "PA", "I", "Sitting"),
    ("FETTERMAN", "PA", "III", "Sitting"),
    ("WHITEHOUSE", "RI", "I", "Sitting"),
    ("REED", "RI", "II", "Sitting"),
    ("GRAHAM", "SC", "II", "Sitting"),
    ("SCOTT", "SC", "III", "Sitting"),
    ("ROUNDS", "SD", "II", "Sitting"),
    ("THUNE", "SD", "III", "Sitting"),
    ("BLACKBURN", "TN", "I", "Sitting"),
    ("HAGERTY", "TN", "II", "Sitting"),
    ("CRUZ", "TX", "I", "Sitting"),
    ("CORNYN", "TX", "II", "Sitting"),
    ("CURTIS", "UT", "I", "Sitting"),
    ("LEE", "UT", "III", "Sitting"),
    ("SANDERS", "VT", "I", "Sitting"),
    ("WELCH", "VT", "III", "Sitting"),
    ("KAINE", "VA", "I", "Sitting"),
    ("WARNER", "VA", "II", "Sitting"),
    ("CANTWELL", "WA", "I", "Sitting"),
    ("MURRAY", "WA", "III", "Sitting"),
    ("JUSTICE", "WV", "I", "Sitting"),
    ("CAPITO", "WV", "II", "Sitting"),
    ("BALDWIN", "WI", "I", "Sitting"),
    ("JOHNSON", "WI", "III", "Sitting"),
    ("BARRASSO", "WY", "I", "Sitting"),
    ("LUMMIS", "WY", "II", "Sitting"),
]


def is_protected(name: str, state: str) -> tuple:
    """Check if candidate is a protected senator. Returns (is_protected, class)"""
    name_upper = (name or "").upper()
    for pattern, senator_state, senator_class, reason in PROTECTED_SENATORS:
        if state == senator_state and pattern in name_upper:
            return (True, senator_class)
    return (False, None)


def determine_class_for_challenger(state: str, cycles: list) -> str:
    """Determine class for challengers/candidates based on earliest election cycle"""
    if not state or state not in STATE_CLASSES:
        return None

    if not cycles:
        return None

    # Use EARLIEST cycle (their first election attempt)
    earliest_cycle = min(cycles)

    # What class was up in that cycle?
    class_up = CYCLE_TO_CLASS.get(earliest_cycle)

    if not class_up:
        return None

    # Does this state have that class?
    if class_up in STATE_CLASSES[state]:
        return class_up
    else:
        # Fallback to first available class
        return STATE_CLASSES[state][0]


def main():
    print("Fetching all Senate candidates...")

    response = supabase.table("candidates").select(
        "candidate_id, name, state, district, financial_summary(cycle)"
    ).eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates")

    updates = []
    protected_count = 0
    no_data_count = 0

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        name = candidate['name']
        state = candidate['state']
        current_district = candidate['district']

        # Check if protected
        is_prot, protected_class = is_protected(name, state)
        if is_prot:
            protected_count += 1
            # Ensure protected senators have correct class
            if current_district != protected_class:
                updates.append({
                    'candidate_id': candidate_id,
                    'name': name,
                    'type': 'PROTECTED',
                    'new_class': protected_class,
                    'old_class': current_district
                })
            continue

        # For non-protected, get cycles
        cycles = [fs['cycle'] for fs in candidate.get('financial_summary', []) if fs.get('cycle')]

        if not cycles:
            no_data_count += 1
            continue

        # Determine class for challenger
        senate_class = determine_class_for_challenger(state, cycles)

        if senate_class and current_district != senate_class:
            updates.append({
                'candidate_id': candidate_id,
                'name': name,
                'type': 'CHALLENGER',
                'cycles': cycles,
                'new_class': senate_class,
                'old_class': current_district
            })

    print(f"\nProtected senators: {protected_count}")
    print(f"Candidates to update: {len(updates)}")
    print(f"No financial data: {no_data_count}")

    if updates:
        protected_updates = [u for u in updates if u['type'] == 'PROTECTED']
        challenger_updates = [u for u in updates if u['type'] == 'CHALLENGER']

        if protected_updates:
            print(f"\n{'='*70}")
            print("PROTECTED SENATORS TO FIX:")
            print('='*70)
            for u in protected_updates:
                print(f"{u['name']}: {u['old_class']} → Class {u['new_class']}")

        if challenger_updates:
            print(f"\n{'='*70}")
            print(f"CHALLENGERS TO CLASSIFY (first 20 of {len(challenger_updates)}):")
            print('='*70)
            for u in challenger_updates[:20]:
                print(f"{u['name']} - Cycles: {u['cycles']}")
                print(f"  {u['old_class']} → Class {u['new_class']}")

        proceed = input(f"\nProceed with {len(updates)} updates? (yes/no): ")
        if proceed.lower() != 'yes':
            print("Aborted.")
            return

        # Apply updates
        print("\nApplying updates...")
        for i, update in enumerate(updates):
            supabase.table("candidates").update(
                {'district': update['new_class']}
            ).eq('candidate_id', update['candidate_id']).execute()

            if (i + 1) % 50 == 0:
                print(f"  Updated {i + 1}/{len(updates)}")

        print(f"\n✓ Updated {len(updates)} candidates")

    # Final summary
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)

    result = supabase.table("candidates").select("district").eq("office", "S").execute()

    class_counts = {"I": 0, "II": 0, "III": 0, "Unclassified": 0}
    for c in result.data:
        dist = c['district']
        if dist in ['I', 'II', 'III']:
            class_counts[dist] += 1
        else:
            class_counts['Unclassified'] += 1

    for cls in ['I', 'II', 'III']:
        print(f"Class {cls}: {class_counts[cls]} candidates")

    print(f"Unclassified: {class_counts['Unclassified']} candidates")


if __name__ == "__main__":
    main()
