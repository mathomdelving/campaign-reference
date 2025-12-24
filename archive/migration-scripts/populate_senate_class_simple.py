#!/usr/bin/env python3
"""
Simple script to populate Senate class in district column.
Uses cycle year + state to determine class.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Which class is up for election in each cycle
CYCLE_TO_CLASS = {
    2024: "I",
    2026: "II",
    2028: "III",
    2030: "I",
}

# State classes - which two classes each state has
STATE_CLASSES = {
    "NM": ["I", "II"],
    "AL": ["II", "III"], "AK": ["II", "III"], "AZ": ["I", "III"],
    "AR": ["II", "III"], "CA": ["I", "III"], "CO": ["II", "III"],
    "CT": ["I", "III"], "DE": ["I", "II"], "FL": ["I", "III"],
    "GA": ["II", "III"], "HI": ["I", "III"], "ID": ["II", "III"],
    "IL": ["II", "III"], "IN": ["I", "III"], "IA": ["II", "III"],
    "KS": ["II", "III"], "KY": ["II", "III"], "LA": ["II", "III"],
    "ME": ["I", "II"], "MD": ["I", "III"], "MA": ["I", "II"],
    "MI": ["I", "II"], "MN": ["I", "II"], "MS": ["I", "II"],
    "MO": ["I", "III"], "MT": ["I", "II"], "NE": ["I", "II"],
    "NV": ["I", "III"], "NH": ["II", "III"], "NJ": ["I", "II"],
    "NY": ["I", "III"], "NC": ["II", "III"], "ND": ["I", "III"],
    "OH": ["I", "III"], "OK": ["II", "III"], "OR": ["II", "III"],
    "PA": ["I", "III"], "RI": ["I", "II"], "SC": ["II", "III"],
    "SD": ["II", "III"], "TN": ["I", "II"], "TX": ["I", "II"],
    "UT": ["I", "III"], "VT": ["I", "III"], "VA": ["I", "II"],
    "WA": ["I", "III"], "WV": ["I", "II"], "WI": ["I", "III"],
    "WY": ["I", "II"],
}

def main():
    print("Fetching Senate candidates with financial data...")

    # Get all Senate candidates with their financial summary cycles
    response = supabase.table("candidates").select(
        "candidate_id, state, financial_summary(cycle)"
    ).eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates")

    updates = []

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        state = candidate['state']

        if not state or state not in STATE_CLASSES:
            continue

        # Get cycles they have financial data for
        cycles = [fs['cycle'] for fs in candidate.get('financial_summary', []) if fs.get('cycle')]

        if not cycles:
            continue

        # Determine class based on cycle + state
        senate_class = None
        for cycle in cycles:
            if cycle in CYCLE_TO_CLASS:
                potential_class = CYCLE_TO_CLASS[cycle]
                # Check if this state has this class
                if potential_class in STATE_CLASSES[state]:
                    senate_class = potential_class
                    break

        if senate_class:
            updates.append({
                'candidate_id': candidate_id,
                'district': senate_class
            })

    print(f"\nUpdating {len(updates)} candidates...")

    # Update in batches
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

if __name__ == "__main__":
    main()
