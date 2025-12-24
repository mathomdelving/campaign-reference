#!/usr/bin/env python3
"""
Populate Senate class in the district column for all Senate candidates.

For Senate candidates, the district column is repurposed to store their Senate class
(I, II, or III) since Senate seats don't have numbered districts like House seats.
This script determines the Senate class based on state and election years.
"""

import os
import sys
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# State-based Senate class mapping
# Each state has two Senate seats in different classes
# Source: https://www.senate.gov/senators/ (as of 2024)
STATE_CLASS_MAP = {
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
    "NM": ["I", "II"], "NY": ["I", "III"], "NC": ["II", "III"],
    "ND": ["I", "III"], "OH": ["I", "III"], "OK": ["II", "III"],
    "OR": ["II", "III"], "PA": ["I", "III"], "RI": ["I", "II"],
    "SC": ["II", "III"], "SD": ["II", "III"], "TN": ["I", "II"],
    "TX": ["I", "II"], "UT": ["I", "III"], "VT": ["I", "III"],
    "VA": ["I", "II"], "WA": ["I", "III"], "WV": ["I", "II"],
    "WI": ["I", "III"], "WY": ["I", "II"],
}

# Election years for each Senate class
CLASS_ELECTION_YEARS = {
    "I": [2006, 2012, 2018, 2024, 2030, 2036],
    "II": [2008, 2014, 2020, 2026, 2032, 2038],
    "III": [2010, 2016, 2022, 2028, 2034, 2040],
}


def determine_senate_class(state: str, election_years: list) -> Optional[str]:
    """
    Determine the Senate class for a candidate based on their state and election years.

    Args:
        state: Two-letter state code
        election_years: List of years the candidate ran for election

    Returns:
        Senate class ('I', 'II', or 'III'), or None if cannot be determined
    """
    if not state or not election_years:
        return None

    # Get the classes available for this state
    state_classes = STATE_CLASS_MAP.get(state)
    if not state_classes:
        return None

    # Check each election year to see which class it matches
    for election_year in election_years:
        for class_name, class_years in CLASS_ELECTION_YEARS.items():
            if election_year in class_years and class_name in state_classes:
                return class_name

    # If no match found but state only has certain classes available,
    # and candidate has recent election years, try to infer
    # For example, if a state only has Class I and II, and candidate ran in 2024,
    # we know it must be Class I
    if len(state_classes) == 2 and election_years:
        most_recent_year = max(election_years)
        for class_name in state_classes:
            class_years = CLASS_ELECTION_YEARS[class_name]
            # Find the closest election year for this class
            closest_year = min(class_years, key=lambda y: abs(y - most_recent_year))
            if abs(closest_year - most_recent_year) <= 2:  # Within 2 years
                return class_name

    return None


def main():
    print("Fetching all Senate candidates from database...")

    # Fetch all Senate candidates along with their financial_summary cycles
    response = supabase.table("candidates").select(
        "candidate_id, state, office, financial_summary(cycle)"
    ).eq("office", "S").execute()

    candidates = response.data
    print(f"Found {len(candidates)} Senate candidates in database")

    # Process each candidate
    updates = []
    no_class_count = 0

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        state = candidate['state']

        # Get cycles from financial_summary
        financial_summaries = candidate.get('financial_summary', [])
        election_years = [fs['cycle'] for fs in financial_summaries if fs.get('cycle')]

        # Determine senate class
        senate_class = determine_senate_class(state, election_years)

        if senate_class:
            updates.append({
                'candidate_id': candidate_id,
                'district': senate_class  # Store class in district column
            })
        else:
            no_class_count += 1
            print(f"Could not determine class for {candidate_id} ({state}, years: {election_years})")

    print(f"\nPrepared {len(updates)} updates")
    print(f"{no_class_count} candidates without determinable class")

    if updates:
        print(f"\nUpdating {len(updates)} candidates in batches of 100...")

        # Update in batches
        batch_size = 100
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]

            # Update each candidate individually
            for update in batch:
                supabase.table("candidates").update(
                    {'district': update['district']}
                ).eq('candidate_id', update['candidate_id']).execute()

            print(f"Updated {min(i+batch_size, len(updates))}/{len(updates)}")

        print("\n✓ Successfully updated all Senate candidates!")
    else:
        print("\nNo updates to make.")

    # Print summary statistics
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for class_name in ["I", "II", "III"]:
        count = len([u for u in updates if u['district'] == class_name])
        print(f"Class {class_name}: {count} candidates")

    print(f"No class assigned: {no_class_count} candidates")
    print(f"Total: {len(candidates)} Senate candidates")


if __name__ == "__main__":
    main()
