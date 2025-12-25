#!/usr/bin/env python3
"""
Apply Senate class mapping from senate_class_mapping.json

This script uses a pre-generated mapping file to assign classes to all Senate candidates.
"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Manual overrides for senators where cycle-based logic fails
# Format: candidate_id → (class, reason)
MANUAL_OVERRIDES = {
    # Current sitting senators who need correction
    'S2PA00661': ('I', 'McCormick - elected 2024 Class I, has 2022 data from previous run'),
    'S4AZ00139': ('I', 'Gallego - elected 2024 Class I'),
    'S0AZ00350': ('III', 'Kelly - elected 2020 special, 2022 full term, Class III'),
    'S2NM00088': ('I', 'Heinrich - Class I senator'),
    'S0NM00058': ('II', 'Lujan - Class II senator'),
    'S6PA00274': ('III', 'Fetterman - elected 2022 Class III'),
    'S4AZ00220': ('I', 'Lake - 2024 challenger for Class I'),
    'S4AZ00188': ('I', 'Lamb - 2024 challenger for Class I'),
    'S8AZ00197': ('I', 'Sinema - Class I senator'),
}


def main():
    # Load the mapping file
    mapping_file = '/Users/benjaminnelson/Desktop/campaign-reference/scripts/senate_class_mapping.json'

    print("Loading mapping file...")
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)

    print(f"Loaded {len(mapping)} candidate mappings")

    # Apply manual overrides
    for candidate_id, (override_class, reason) in MANUAL_OVERRIDES.items():
        if candidate_id in mapping:
            old_class = mapping[candidate_id]['class']
            if old_class != override_class:
                print(f"Override: {mapping[candidate_id]['name']} - {old_class} → {override_class}")
                mapping[candidate_id]['class'] = override_class
        else:
            # Add to mapping if not present
            print(f"Adding override: {candidate_id} → Class {override_class} ({reason})")
            mapping[candidate_id] = {
                'class': override_class,
                'name': reason,
                'state': 'MANUAL',
                'earliest_cycle': 0
            }

    print(f"\nTotal mappings (including overrides): {len(mapping)}")

    # Apply to database
    updates = []
    for candidate_id, data in mapping.items():
        updates.append({
            'candidate_id': candidate_id,
            'class': data['class'],
            'name': data.get('name', 'Unknown')
        })

    print(f"\nApplying {len(updates)} updates to database...")

    for i, update in enumerate(updates):
        supabase.table("candidates").update(
            {'district': update['class']}
        ).eq('candidate_id', update['candidate_id']).execute()

        if (i + 1) % 50 == 0:
            print(f"  Updated {i + 1}/{len(updates)}")

    print(f"\n✓ Applied {len(updates)} class assignments")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
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


if __name__ == "__main__":
    main()
