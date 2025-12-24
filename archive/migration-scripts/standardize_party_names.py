#!/usr/bin/env python3
"""
Standardize party names across all tables to use full, consistent names
(Democrat, Republican, Independent, etc.)
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Comprehensive party name mapping to standardized names
PARTY_MAPPING = {
    # Democrat variations
    'DEM': 'Democrat',
    'DEMOCRATIC PARTY': 'Democrat',
    'DEMOCRATIC': 'Democrat',
    'DFL': 'Democrat',  # Democratic-Farmer-Labor (Minnesota)

    # Republican variations
    'REP': 'Republican',
    'REPUBLICAN PARTY': 'Republican',
    'REPUBLICAN': 'Republican',

    # Independent variations
    'IND': 'Independent',
    'INDEPENDENT': 'Independent',
    'NPA': 'Independent',  # No Party Affiliation
    'NOP': 'Independent',  # No Party
    'NNE': 'Independent',  # No Party/None
    'UN': 'Independent',   # Unaffiliated
    'UND': 'Independent',  # Undeclared
    'N': 'Independent',

    # Libertarian
    'LIB': 'Libertarian',
    'LIBERTARIAN PARTY': 'Libertarian',

    # Green
    'GRE': 'Green',
    'GREEN PARTY': 'Green',

    # Constitution
    'CON': 'Constitution',
    'CONSTITUTION PARTY': 'Constitution',
    'C': 'Constitution',

    # Conservative
    'CONSERVATIVE PARTY': 'Conservative',

    # Alaska-specific
    'AIP': 'Alaskan Independence',
    'ALASKAN INDEPENDENCE PARTY': 'Alaskan Independence',

    # Working Families
    'W': 'Working Families',

    # Other/Unknown
    'OTH': 'Other',
    'UNK': 'Unknown',

    # State-specific minor parties
    'APV': 'Approval Voting',
    'PAF': 'Peace and Freedom',
    'IDP': 'Independence Party',
    'IAP': 'Independent American',
    'VET': 'Veterans',
    'UST': 'U.S. Taxpayers',
}

def update_table_parties(table_name, id_column='candidate_id'):
    """Update party names in a given table."""
    print(f"\n{'='*80}")
    print(f"UPDATING {table_name.upper()}")
    print('='*80)

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    updated_count = 0
    skipped_count = 0

    for old_party, new_party in PARTY_MAPPING.items():
        # Find records with old party name
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?party=eq.{old_party}&select={id_column},party"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"  ❌ Error fetching {old_party}: {response.status_code}")
            continue

        records = response.json()

        if len(records) == 0:
            skipped_count += 1
            continue

        print(f"  {old_party} → {new_party}: {len(records)} records")

        # Update all records with this party
        update_url = f"{SUPABASE_URL}/rest/v1/{table_name}?party=eq.{old_party}"
        update_data = {'party': new_party}

        update_response = requests.patch(update_url, headers=headers, json=update_data)

        if update_response.status_code in [200, 204]:
            updated_count += len(records)
        else:
            print(f"    ❌ Update failed: {update_response.status_code} - {update_response.text[:200]}")

    print(f"\n✓ {table_name}: {updated_count} records updated, {skipped_count} party codes not found")
    return updated_count

def main():
    print("="*80)
    print("STANDARDIZING PARTY NAMES ACROSS DATABASE")
    print("="*80)

    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return

    total_updated = 0

    # Update each table
    total_updated += update_table_parties('political_persons', id_column='person_id')
    total_updated += update_table_parties('candidates', id_column='candidate_id')
    total_updated += update_table_parties('quarterly_financials', id_column='id')

    print("\n" + "="*80)
    print(f"✅ COMPLETE - {total_updated} total records updated")
    print("="*80)

    print("\nStandardized party names:")
    print("  - Democrat (was: DEM, DEMOCRATIC PARTY, DFL)")
    print("  - Republican (was: REP, REPUBLICAN PARTY)")
    print("  - Independent (was: IND, NPA, NOP, UN, etc.)")
    print("  - Libertarian (was: LIB)")
    print("  - Green (was: GRE)")
    print("  - Constitution (was: CON, C)")
    print("  - Other minor parties standardized")

if __name__ == "__main__":
    main()
