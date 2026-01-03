#!/usr/bin/env python3
"""
Backfill missing Q1-Q3 2021 data for major 2022 Senate candidates.
Uses the correct FEC API endpoints to fetch financial data.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
FEC_API_KEY = os.environ.get('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"

# Major 2022 Senate candidates to backfill
CANDIDATES_TO_BACKFILL = [
    ("Ron Johnson", "WI"),
    ("Tim Ryan", "OH"),
    ("Cheri Beasley", "NC"),
    ("Val Demings", "FL"),
]

# Target missing quarters
TARGET_QUARTERS = ['2021-03-31', '2021-06-30', '2021-09-30']

def get_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

def find_candidate(name_pattern, state):
    """Find candidate ID from database."""
    url = f"{SUPABASE_URL}/rest/v1/candidates"
    params = {
        'select': 'candidate_id,name,state,office,person_id,party,district',
        'state': f'eq.{state}',
        'office': 'eq.S',
    }
    resp = requests.get(url, headers=get_headers(), params=params)
    if resp.status_code != 200:
        print(f"Error fetching candidates: {resp.text}")
        return []

    candidates = resp.json()
    # Filter by name pattern (first word of name)
    matching = [c for c in candidates if name_pattern.lower() in c['name'].lower()]
    return matching

def get_existing_quarters(candidate_id, cycle):
    """Get quarters we already have data for."""
    url = f"{SUPABASE_URL}/rest/v1/candidate_financials"
    params = {
        'select': 'coverage_end_date',
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}'
    }
    resp = requests.get(url, headers=get_headers(), params=params)
    if resp.status_code != 200:
        return []
    
    records = resp.json()
    return [r['coverage_end_date'] for r in records]

def fetch_committees(candidate_id, cycle):
    """Get candidate's principal campaign committee(s)."""
    url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }
    
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"  Error fetching committees: {resp.status_code}")
        return []
    
    time.sleep(0.2)  # Rate limiting
    return resp.json().get('results', [])

def fetch_filings(committee_id, cycle):
    """Fetch F3 filings for a committee."""
    url = f"{BASE_URL}/committee/{committee_id}/filings/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle,
        'form_type': 'F3',
        'sort': '-coverage_end_date',
        'per_page': 50
    }
    
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"  Error fetching filings: {resp.status_code}")
        return []
    
    time.sleep(0.2)  # Rate limiting
    return resp.json().get('results', [])

def normalize_date(date_str):
    """Convert FEC date format to YYYY-MM-DD."""
    if not date_str:
        return None
    if 'T' in date_str:
        return date_str.split('T')[0]
    return date_str

def transform_filing(filing, candidate, cycle):
    """Transform FEC filing to candidate_financials format."""
    cash_ending = filing.get('cash_on_hand_end_period', 0) or 0
    return {
        'candidate_id': candidate['candidate_id'],
        'name': candidate['name'],
        'party': candidate.get('party', ''),
        'state': candidate['state'],
        'district': candidate.get('district', '00'),
        'office': 'Senate',
        'cycle': cycle,
        'committee_id': filing.get('committee_id', ''),
        'filing_id': filing.get('file_number'),
        'report_type': filing.get('report_type_full', ''),
        'coverage_start_date': normalize_date(filing.get('coverage_start_date')),
        'coverage_end_date': normalize_date(filing.get('coverage_end_date')),
        'total_receipts': filing.get('total_receipts', 0) or 0,
        'total_disbursements': filing.get('total_disbursements', 0) or 0,
        'cash_beginning': filing.get('cash_on_hand_beginning_period', 0) or 0,
        'cash_ending': cash_ending,
        'cash_on_hand': cash_ending,
        'is_amendment': filing.get('is_amended', False),
        'report_year': filing.get('report_year', cycle),
        'person_id': candidate.get('person_id')
    }

def insert_records(records):
    """Insert records into candidate_financials."""
    url = f"{SUPABASE_URL}/rest/v1/candidate_financials"
    headers = get_headers()
    headers['Prefer'] = 'return=representation'
    
    resp = requests.post(url, headers=headers, json=records)
    if resp.status_code in (200, 201):
        return len(resp.json())
    else:
        print(f"  Insert error: {resp.text}")
        return 0

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 60)
    print("Backfilling Missing 2021 Data for Major 2022 Senate Candidates")
    print("=" * 60)
    
    if dry_run:
        print("\n[DRY RUN MODE - No data will be inserted]\n")
    
    total_inserted = 0
    
    for name, state in CANDIDATES_TO_BACKFILL:
        print(f"\n--- {name} ({state}) ---")
        
        # Find candidate
        candidates = find_candidate(name.split()[0], state)
        if not candidates:
            print(f"  No candidate found matching '{name}' in {state}")
            continue
        
        candidate = candidates[0]
        candidate_id = candidate['candidate_id']
        person_id = candidate.get('person_id')
        print(f"  Found: {candidate['name']} ({candidate_id})")
        print(f"  Person ID: {person_id}")
        
        # Get existing quarters
        existing = get_existing_quarters(candidate_id, 2022)
        missing_quarters = [q for q in TARGET_QUARTERS if q not in existing]
        
        if not missing_quarters:
            print(f"  All Q1-Q3 2021 data already present")
            continue
        
        print(f"  Missing quarters: {missing_quarters}")
        
        # Get committees
        committees = fetch_committees(candidate_id, 2022)
        if not committees:
            print(f"  No committees found for 2022 cycle")
            continue
        
        print(f"  Found {len(committees)} committee(s)")
        
        # Collect filings from all committees
        all_missing_filings = []
        seen_dates = set()
        
        for committee in committees:
            committee_id = committee.get('committee_id')
            designation = committee.get('designation', '')
            
            # Only use principal campaign committees
            if designation not in ('P', 'A'):  # P=Principal, A=Authorized
                continue
            
            print(f"  Checking committee {committee_id} ({designation})")
            
            filings = fetch_filings(committee_id, 2022)
            
            for filing in filings:
                end_date = normalize_date(filing.get('coverage_end_date'))
                
                # Only target our missing quarters
                if end_date not in missing_quarters:
                    continue
                
                # Skip if already seen (dedupe)
                if end_date in seen_dates:
                    continue
                
                # Skip amendments if we have original
                if filing.get('is_amended'):
                    continue
                
                seen_dates.add(end_date)
                receipts = filing.get('total_receipts', 0) or 0
                disbursements = filing.get('total_disbursements', 0) or 0
                print(f"    Found: {end_date} - ${receipts:,.2f} raised, ${disbursements:,.2f} spent")
                all_missing_filings.append(filing)
        
        if not all_missing_filings:
            print(f"  No missing filings found in FEC API")
            continue
        
        # Transform and insert
        records = [transform_filing(f, candidate, 2022) for f in all_missing_filings]
        
        if dry_run:
            print(f"  Would insert {len(records)} records")
        else:
            inserted = insert_records(records)
            print(f"  Inserted {inserted} records")
            total_inserted += inserted
    
    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN COMPLETE - No data was modified")
    else:
        print(f"COMPLETE - Inserted {total_inserted} total records")
    print("=" * 60)

if __name__ == '__main__':
    main()
