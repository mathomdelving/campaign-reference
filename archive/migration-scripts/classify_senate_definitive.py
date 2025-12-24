#!/usr/bin/env python3
"""
Definitive Senate classification using official senate.gov data.

Approach:
1. All 100 current sitting senators are assigned their official class from senate.gov
2. All other candidates use earliest election cycle logic:
   - Cycles 2023-2024 → Class I (next election 2030)
   - Cycles 2025-2026 → Class II (next election 2032)
   - Cycles 2027-2028 → Class III (next election 2034)
   - Pattern continues backwards for historical data
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# DEFINITIVE LIST: All 100 current sitting senators from senate.gov
# Format: (last_name, state, class)
# Source: https://www.senate.gov/senators/Class_I.htm, Class_II.htm, Class_III.htm
# Retrieved: January 2025

SITTING_SENATORS_CLASS_I = [
    # Democrats
    ("ALSOBROOKS", "MD"), ("BALDWIN", "WI"), ("BLUNT ROCHESTER", "DE"),
    ("CANTWELL", "WA"), ("GALLEGO", "AZ"), ("GILLIBRAND", "NY"),
    ("HEINRICH", "NM"), ("HIRONO", "HI"), ("KAINE", "VA"), ("KIM", "NJ"),
    ("KLOBUCHAR", "MN"), ("MURPHY", "CT"), ("ROSEN", "NV"), ("SCHIFF", "CA"),
    ("SLOTKIN", "MI"), ("WARREN", "MA"), ("WHITEHOUSE", "RI"),
    # Republicans
    ("BANKS", "IN"), ("BARRASSO", "WY"), ("BLACKBURN", "TN"), ("CRAMER", "ND"),
    ("CRUZ", "TX"), ("CURTIS", "UT"), ("FISCHER", "NE"), ("HAWLEY", "MO"),
    ("JUSTICE", "WV"), ("MCCORMICK", "PA"), ("MORENO", "OH"), ("SCOTT", "FL"),
    ("SHEEHY", "MT"), ("WICKER", "MS"),
    # Independents
    ("KING", "ME"), ("SANDERS", "VT"),
]

SITTING_SENATORS_CLASS_II = [
    # Democrats
    ("BOOKER", "NJ"), ("COONS", "DE"), ("DURBIN", "IL"), ("HICKENLOOPER", "CO"),
    ("LUJÁN", "NM"), ("LUJAN", "NM"), ("MARKEY", "MA"), ("MERKLEY", "OR"),
    ("OSSOFF", "GA"), ("PETERS", "MI"), ("REED", "RI"), ("SHAHEEN", "NH"),
    ("SMITH", "MN"), ("WARNER", "VA"),
    # Republicans
    ("CAPITO", "WV"), ("CASSIDY", "LA"), ("COLLINS", "ME"), ("CORNYN", "TX"),
    ("COTTON", "AR"), ("DAINES", "MT"), ("ERNST", "IA"), ("GRAHAM", "SC"),
    ("HAGERTY", "TN"), ("HYDE-SMITH", "MS"), ("LUMMIS", "WY"), ("MARSHALL", "KS"),
    ("MCCONNELL", "KY"), ("MULLIN", "OK"), ("RICKETTS", "NE"), ("RISCH", "ID"),
    ("ROUNDS", "SD"), ("SULLIVAN", "AK"), ("TILLIS", "NC"), ("TUBERVILLE", "AL"),
]

SITTING_SENATORS_CLASS_III = [
    # Democrats
    ("BENNET", "CO"), ("BLUMENTHAL", "CT"), ("CORTEZ MASTO", "NV"),
    ("DUCKWORTH", "IL"), ("FETTERMAN", "PA"), ("HASSAN", "NH"), ("KELLY", "AZ"),
    ("MURRAY", "WA"), ("PADILLA", "CA"), ("SCHATZ", "HI"), ("SCHUMER", "NY"),
    ("VAN HOLLEN", "MD"), ("WARNOCK", "GA"), ("WELCH", "VT"), ("WYDEN", "OR"),
    # Republicans
    ("BOOZMAN", "AR"), ("BRITT", "AL"), ("BUDD", "NC"), ("CRAPO", "ID"),
    ("GRASSLEY", "IA"), ("HOEVEN", "ND"), ("HUSTED", "OH"), ("JOHNSON", "WI"),
    ("KENNEDY", "LA"), ("LANKFORD", "OK"), ("LEE", "UT"), ("MOODY", "FL"),
    ("MORAN", "KS"), ("MURKOWSKI", "AK"), ("PAUL", "KY"), ("SCHMITT", "MO"),
    ("SCOTT", "SC"), ("THUNE", "SD"), ("YOUNG", "IN"),
]


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


def determine_class_from_cycle(earliest_cycle: int) -> str:
    """
    Determine class based on earliest election cycle.

    User specified pattern:
    - 2023-2024 (or 2023-2024 filings) → Class I
    - 2025-2026 (or 2025-2026 filings) → Class II
    - 2027-2028 (or 2027-2028 filings) → Class III

    Election pattern (repeating every 6 years):
    - 2024, 2030, 2036... → Class I
    - 2026, 2032, 2038... → Class II
    - 2028, 2034, 2040... → Class III
    - 2022, 2028, 2034... → Class III (2022 was Class III)
    - 2020, 2026, 2032... → Class II (2020 was Class II)
    - 2018, 2024, 2030... → Class I (2018 was Class I)
    """
    # Normalize: if odd year, it's for the next even year's election
    # (candidates often file in odd years for next year's election)
    election_year = earliest_cycle if earliest_cycle % 2 == 0 else earliest_cycle + 1

    # Determine class based on election year modulo 6
    # Starting point: 2024 is Class I
    # 2024 % 6 = 0 → Class I
    # 2026 % 6 = 2 → Class II
    # 2028 % 6 = 4 → Class III
    # 2022 % 6 = 4 → Class III
    # 2020 % 6 = 2 → Class II
    # 2018 % 6 = 0 → Class I

    remainder = election_year % 6

    if remainder == 2:  # 2018, 2024, 2030, 2036... → Class I
        return "I"
    elif remainder == 4:  # 2020, 2026, 2032, 2038... → Class II
        return "II"
    elif remainder == 0:  # 2022, 2028, 2034, 2040... → Class III
        return "III"
    else:
        # Shouldn't happen, but fallback
        return None


def main():
    print("Fetching all Senate candidates...")

    # Supabase has a hard limit of 1000 rows per request. We need to paginate.
    all_candidates = []
    page_size = 1000
    offset = 0

    while True:
        response = supabase.table("candidates").select(
            "candidate_id, name, state, district, financial_summary(cycle)"
        ).eq("office", "S").range(offset, offset + page_size - 1).execute()

        if not response.data:
            break

        all_candidates.extend(response.data)
        print(f"  Fetched {len(all_candidates)} candidates so far...")

        if len(response.data) < page_size:
            # Last page
            break

        offset += page_size

    candidates = all_candidates
    print(f"\nFound {len(candidates)} total Senate candidates\n")

    updates = []
    sitting_count = 0
    challenger_count = 0
    no_data_count = 0

    sitting_fixes = []

    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        name = candidate['name']
        state = candidate['state']
        current_district = candidate['district']

        # Check if sitting senator
        is_sitting, official_class = is_sitting_senator(name, state)

        if is_sitting:
            sitting_count += 1
            # Ensure sitting senators have correct class
            if current_district != official_class:
                sitting_fixes.append({
                    'candidate_id': candidate_id,
                    'name': name,
                    'state': state,
                    'type': 'SITTING_SENATOR',
                    'new_class': official_class,
                    'old_class': current_district
                })
                updates.append(sitting_fixes[-1])
            continue

        # For non-sitting senators, use earliest cycle
        cycles = [fs['cycle'] for fs in candidate.get('financial_summary', []) if fs.get('cycle')]

        if not cycles:
            no_data_count += 1
            continue

        challenger_count += 1
        earliest_cycle = min(cycles)
        determined_class = determine_class_from_cycle(earliest_cycle)

        if determined_class and current_district != determined_class:
            updates.append({
                'candidate_id': candidate_id,
                'name': name,
                'state': state,
                'type': 'CHALLENGER',
                'earliest_cycle': earliest_cycle,
                'new_class': determined_class,
                'old_class': current_district
            })

    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Sitting senators identified: {sitting_count}")
    print(f"Challengers/former senators: {challenger_count}")
    print(f"Candidates with no financial data: {no_data_count}")
    print(f"\nTotal candidates to update: {len(updates)}")

    if sitting_fixes:
        print(f"\n{'='*70}")
        print(f"SITTING SENATORS TO FIX ({len(sitting_fixes)}):")
        print('='*70)
        for u in sitting_fixes:
            old = u['old_class'] or 'None'
            print(f"{u['name']} ({u['state']}): {old} → Class {u['new_class']}")

    if updates:
        challenger_updates = [u for u in updates if u['type'] == 'CHALLENGER']

        if challenger_updates:
            print(f"\n{'='*70}")
            print(f"CHALLENGERS TO CLASSIFY (showing first 30 of {len(challenger_updates)}):")
            print('='*70)
            for u in challenger_updates[:30]:
                old = u['old_class'] or 'None'
                print(f"{u['name']} ({u['state']}) - Earliest cycle: {u['earliest_cycle']}")
                print(f"  {old} → Class {u['new_class']}")

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
    print("FINAL DATABASE STATUS")
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
