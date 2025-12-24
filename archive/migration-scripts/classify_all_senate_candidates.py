#!/usr/bin/env python3
"""
Classify ALL Senate candidates based on state + election cycle.

Every Senate candidate is mapped to the class seat they're running for based on:
1. Their state (which determines which 2 classes are available)
2. Their most recent election cycle (which determines which class is up that year)

Example: Sherrod Brown (OH)
- 2024 cycle → Class I (lost)
- 2026 cycle → Class III (if running again)
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
    2010: "III",
    2012: "I",
    2014: "II",
    2016: "III",
    2018: "I",
    2020: "II",
    2022: "III",
    2024: "I",
    2026: "II",
    2028: "III",
    2030: "I",
    2032: "II",
    2034: "III",
    2036: "I",
    2038: "II",
    2040: "III",
}

# Which two classes each state has
STATE_CLASSES = {
    "AL": ["II", "III"],
    "AK": ["II", "III"],
    "AZ": ["I", "III"],
    "AR": ["II", "III"],
    "CA": ["I", "III"],
    "CO": ["II", "III"],
    "CT": ["I", "III"],
    "DE": ["I", "II"],
    "FL": ["I", "III"],
    "GA": ["II", "III"],
    "HI": ["I", "III"],
    "ID": ["II", "III"],
    "IL": ["II", "III"],
    "IN": ["I", "III"],
    "IA": ["II", "III"],
    "KS": ["II", "III"],
    "KY": ["II", "III"],
    "LA": ["II", "III"],
    "ME": ["I", "II"],
    "MD": ["I", "III"],
    "MA": ["I", "II"],
    "MI": ["I", "II"],
    "MN": ["I", "II"],
    "MS": ["I", "II"],
    "MO": ["I", "III"],
    "MT": ["I", "II"],
    "NE": ["I", "II"],
    "NV": ["I", "III"],
    "NH": ["II", "III"],
    "NJ": ["I", "II"],
    "NM": ["I", "II"],
    "NY": ["I", "III"],
    "NC": ["II", "III"],
    "ND": ["I", "III"],
    "OH": ["I", "III"],
    "OK": ["II", "III"],
    "OR": ["II", "III"],
    "PA": ["I", "III"],
    "RI": ["I", "II"],
    "SC": ["II", "III"],
    "SD": ["II", "III"],
    "TN": ["I", "II"],
    "TX": ["I", "II"],
    "UT": ["I", "III"],
    "VT": ["I", "III"],
    "VA": ["I", "II"],
    "WA": ["I", "III"],
    "WV": ["I", "II"],
    "WI": ["I", "III"],
    "WY": ["I", "II"],
}


def determine_class(state: str, cycles: list) -> str:
    """
    Determine Senate class based on state and election cycles.

    Logic:
    1. Find the most recent cycle
    2. Look up which class is up in that cycle
    3. Verify that state has that class (if not, use the other class)
    """
    if not state or state not in STATE_CLASSES:
        return None

    if not cycles:
        return None

    # Use most recent cycle
    most_recent_cycle = max(cycles)

    # What class is up in this cycle?
    class_up = CYCLE_TO_CLASS.get(most_recent_cycle)

    if not class_up:
        return None

    # Does this state have this class?
    available_classes = STATE_CLASSES[state]

    if class_up in available_classes:
        return class_up
    else:
        # This state doesn't have this class, so they must be running for the other one
        # Example: If Class III is up nationally but state only has I & II, they're running for whichever is up
        # This shouldn't normally happen in real data, but handle it gracefully
        return available_classes[0]  # Return first available class as fallback


def main():
    print("Fetching all Senate candidates with financial data...")

    response = supabase.table("candidates").select(
        "candidate_id, name, state, district, financial_summary(cycle)"
    ).eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates")

    updates = []
    no_data_count = 0

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        name = candidate['name']
        state = candidate['state']
        current_district = candidate['district']

        # Get cycles
        cycles = [fs['cycle'] for fs in candidate.get('financial_summary', []) if fs.get('cycle')]

        if not cycles:
            no_data_count += 1
            continue

        # Determine class
        senate_class = determine_class(state, cycles)

        if senate_class:
            # Only update if different from current
            if current_district != senate_class:
                updates.append({
                    'candidate_id': candidate_id,
                    'name': name,
                    'state': state,
                    'cycles': cycles,
                    'new_class': senate_class,
                    'old_class': current_district
                })

    print(f"\nFound {len(updates)} candidates to update")
    print(f"Found {no_data_count} candidates with no financial data (will remain unclassified)")

    if updates:
        print("\n" + "="*70)
        print("SAMPLE UPDATES (first 30):")
        print("="*70)
        for update in updates[:30]:
            old = update['old_class'] or 'None'
            print(f"{update['name']} ({update['state']}) - Cycles: {update['cycles']}")
            print(f"  {old} → Class {update['new_class']}")

        if len(updates) > 30:
            print(f"\n... and {len(updates) - 30} more")

        proceed = input(f"\nProceed with updating {len(updates)} candidates? (yes/no): ")
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
    else:
        print("\nNo updates needed!")

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

    print(f"Unclassified: {class_counts['Unclassified']} candidates (no financial data)")
    print(f"Total: {sum(class_counts.values())} Senate candidates")


if __name__ == "__main__":
    main()
