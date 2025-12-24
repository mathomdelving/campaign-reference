#!/usr/bin/env python3
"""
Get FEC designation data for all multi-committee candidates
to determine which committees to keep vs delete
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')

def get_committee_history(comm_id):
    """Get committee designation history from FEC API"""
    try:
        url = f"https://api.open.fec.gov/v1/committee/{comm_id}/history/"
        response = requests.get(url, params={"api_key": FEC_API_KEY, "per_page": 100}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        elif response.status_code == 429:
            print(f"  ⚠️  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return get_committee_history(comm_id)  # Retry
        else:
            print(f"  ✗ Error {response.status_code}: {response.text[:100]}")
        time.sleep(0.5)  # Rate limit protection
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
    return []

def get_committee_details(comm_id):
    """Get current committee details"""
    try:
        url = f"https://api.open.fec.gov/v1/committee/{comm_id}/"
        response = requests.get(url, params={"api_key": FEC_API_KEY}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                c = data['results'][0]
                return {
                    'name': c.get('name'),
                    'designation': c.get('designation'),
                    'designation_full': c.get('designation_full'),
                    'committee_type': c.get('committee_type'),
                    'first_file_date': c.get('first_file_date'),
                }
        elif response.status_code == 429:
            print(f"  ⚠️  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return get_committee_details(comm_id)  # Retry
        time.sleep(0.5)
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
    return None

print("=" * 100)
print("COMPREHENSIVE COMMITTEE DESIGNATION ANALYSIS")
print("=" * 100)
print(f"\nUsing FEC API Key: {FEC_API_KEY[:10]}...")
print()

# 2024 Multi-Committee Candidates
candidates_2024 = [
    ('S4AZ00220', 'LAKE, KARI', ['C00852343', 'C00829390']),
    ('H4FL23118', 'BARVE, GARY', ['C00848903', 'C00852608']),
    ('H2AK01083', 'BEGICH, NICHOLAS III', ['C00801746', 'C00856617']),
    ('H4NC01137', 'BUCKHOUT, LAURIE', ['C00848168', 'C00857839']),
]

# 2026 Multi-Committee Candidates
candidates_2026 = [
    ('H0MI02094', 'HUIZENGA, WILLIAM P', ['C00459297', 'C00580043']),
    ('H2CA03157', 'KILEY, KEVIN', ['C00801985', 'C00818328']),
    ('H2MD05155', 'HOYER, STENY', ['C00140715', 'C00513002']),
    ('H4CO03357', 'HURD, JEFFREY', ['C00848333', 'C00885319']),
    ('H4OH13153', 'COUGHLIN, KEVIN', ['C00853077', 'C00858340']),
    ('H4TX32089', 'JOHNSON, JULIE', ['C00832576', 'C00843003']),
    ('H6FL06324', 'BAKER, AARON', ['C00893289', 'C00902478']),
    ('H6VA11108', 'HEADRICK, NATHAN', ['C00905927', 'C00918490']),
    ('S4AR00103', 'COTTON, THOMAS', ['C00499988', 'C00571018']),
    ('S8MS00261', 'HYDE-SMITH, CINDY', ['C00675348', 'C00691576']),
]

# Also check 2022 case
candidates_2022 = [
    ('S2ND00123', 'CHRISTIANSEN, KATRINA', ['C00764779', 'C00802959']),
]

all_candidates = [
    (2024, candidates_2024),
    (2026, candidates_2026),
    (2022, candidates_2022),
]

# Track recommendations
sherrod_brown_pattern = []  # Both committees were principal in different cycles
simple_deletes = []  # Non-principal or terminated committees
needs_investigation = []  # Unclear cases

for cycle, candidates in all_candidates:
    print(f"\n{'=' * 100}")
    print(f"{cycle} CYCLE")
    print(f"{'=' * 100}")

    for cand_id, name, committees in candidates:
        print(f"\n{name} ({cand_id}):")
        print("-" * 100)

        committee_data = {}

        for comm_id in committees:
            print(f"\n  {comm_id}:")

            # Get current details
            details = get_committee_details(comm_id)
            if details:
                print(f"    Name: {details['name']}")
                print(f"    Current Designation: {details['designation']} ({details['designation_full']})")
                print(f"    Type: {details['committee_type']}")
                print(f"    First File: {details['first_file_date']}")

            # Get history across all cycles
            history = get_committee_history(comm_id)
            if history:
                print(f"    Designation History:")
                for record in sorted(history, key=lambda x: x.get('cycle', 0)):
                    rec_cycle = record.get('cycle')
                    designation = record.get('designation')
                    des_full = record.get('designation_full')
                    print(f"      Cycle {rec_cycle}: {designation} ({des_full})")

                # Store for analysis
                committee_data[comm_id] = {
                    'current': details,
                    'history': history
                }
            else:
                print(f"    No history available")

        # ANALYSIS: Determine pattern
        print(f"\n  ANALYSIS:")

        # Check if this is a Sherrod Brown pattern
        principal_cycles = {}
        for comm_id, data in committee_data.items():
            for record in data['history']:
                if record.get('designation') == 'P':
                    cycle_num = record.get('cycle')
                    if cycle_num not in principal_cycles:
                        principal_cycles[cycle_num] = []
                    principal_cycles[cycle_num].append(comm_id)

        if len(principal_cycles) > 1 and len(set(sum(principal_cycles.values(), []))) > 1:
            # Multiple cycles, different principal committees = Sherrod Brown pattern
            print(f"    🔍 SHERROD BROWN PATTERN: Different principal committees in different cycles")
            for cycle_num, comms in sorted(principal_cycles.items()):
                print(f"       Cycle {cycle_num}: {', '.join(comms)} was principal")
            print(f"    ✅ RECOMMENDATION: KEEP ALL COMMITTEES")
            sherrod_brown_pattern.append((cand_id, name, committees, principal_cycles))
        else:
            # Check which committees are/were principal
            principal_comms = set()
            non_principal_comms = set()

            for comm_id, data in committee_data.items():
                was_principal = False
                for record in data['history']:
                    if record.get('designation') == 'P':
                        was_principal = True
                        principal_comms.add(comm_id)
                        break
                if not was_principal:
                    non_principal_comms.add(comm_id)

            if non_principal_comms:
                print(f"    ❌ DELETE: Non-principal committee(s): {', '.join(non_principal_comms)}")
                for comm_id in non_principal_comms:
                    if comm_id in committee_data:
                        des = committee_data[comm_id]['current']['designation_full'] if committee_data[comm_id]['current'] else 'Unknown'
                        simple_deletes.append((cand_id, name, comm_id, cycle, des))

            if principal_comms and len(principal_comms) > 1:
                print(f"    ⚠️  INVESTIGATE: Multiple principal committees in same cycle")
                needs_investigation.append((cand_id, name, committees))

        print()

# FINAL SUMMARY
print("\n" + "=" * 100)
print("FINAL SUMMARY AND RECOMMENDATIONS")
print("=" * 100)

print(f"\n1. SHERROD BROWN PATTERN (KEEP ALL COMMITTEES): {len(sherrod_brown_pattern)}")
for cand_id, name, committees, cycles in sherrod_brown_pattern:
    print(f"   - {name}: {', '.join(committees)}")

print(f"\n2. NON-PRINCIPAL COMMITTEES TO DELETE: {len(simple_deletes)}")
by_cycle = {}
for cand_id, name, comm_id, cycle, des in simple_deletes:
    if cycle not in by_cycle:
        by_cycle[cycle] = []
    by_cycle[cycle].append((name, comm_id, des))

for cycle in sorted(by_cycle.keys()):
    print(f"\n   {cycle} Cycle ({len(by_cycle[cycle])} committees):")
    for name, comm_id, des in sorted(by_cycle[cycle]):
        print(f"      {comm_id}: {name:30} ({des})")

print(f"\n3. NEEDS INVESTIGATION: {len(needs_investigation)}")
for cand_id, name, committees in needs_investigation:
    print(f"   - {name}: {', '.join(committees)}")

print("\n" + "=" * 100)
