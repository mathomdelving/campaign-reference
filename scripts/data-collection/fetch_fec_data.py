import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FEC_API_KEY = os.getenv('FEC_API_KEY')
BASE_URL = "https://api.open.fec.gov/v1"
CYCLE = 2022
PROGRESS_FILE = "progress.json"

if not FEC_API_KEY:
    print("ERROR: FEC_API_KEY not found in .env file!")
    print("Please create a .env file with your API key.")
    exit(1)

def load_progress():
    """Load progress from previous run if it exists"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_processed_index': 0, 'financials': [], 'quarterly_financials': []}

def save_progress(index, financials, quarterly_financials):
    """Save current progress"""
    progress = {
        'last_processed_index': index,
        'financials': financials,
        'quarterly_financials': quarterly_financials,
        'last_updated': datetime.now().isoformat()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def fetch_candidates(office, cycle=CYCLE):
    print(f"\n{'='*60}")
    print(f"Fetching {('House' if office == 'H' else 'Senate')} candidates for {cycle}...")
    print(f"{'='*60}")
    
    all_candidates = []
    page = 1
    
    while True:
        url = f"{BASE_URL}/candidates/"
        params = {
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'office': office,
            'per_page': 100,
            'page': page,
            'sort': 'name'
        }
        
        try:
            print(f"  Fetching page {page}...", end=" ")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print("No more results.")
                break
            
            all_candidates.extend(results)
            print(f"✓ Got {len(results)} candidates")
            
            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break
            
            page += 1
            time.sleep(0.25)
            
        except requests.exceptions.RequestException as e:
            print(f"\n  ERROR fetching page {page}: {e}")
            break
    
    print(f"\n  Total {('House' if office == 'H' else 'Senate')} candidates: {len(all_candidates)}")
    return all_candidates

def fetch_candidate_financials(candidate_id, cycle=CYCLE, retry_count=0):
    """Fetch financial totals with retry logic for rate limits"""
    url = f"{BASE_URL}/candidate/{candidate_id}/totals/"
    params = {
        'api_key': FEC_API_KEY,
        'cycle': cycle
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        # Handle rate limit specifically
        if response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT HIT! Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return fetch_candidate_financials(candidate_id, cycle, retry_count + 1)
            else:
                print(f"\n  ❌ Rate limit persists after {retry_count} retries. Skipping.")
                return None

        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            return results[0]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching financials for {candidate_id}: {e}")
        return None

def fetch_committee_quarterly_filings(candidate_id, cycle=CYCLE, retry_count=0):
    """
    Fetch quarterly filings for a candidate's committee(s)
    Returns list of quarterly reports with financial data
    NOTE: This function makes 2+ API calls (committees + filings for each committee)
    """
    try:
        # Step 1: Get committee(s) for this candidate
        committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
        committees_response = requests.get(committees_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle
        }, timeout=10)

        # Handle rate limit
        if committees_response.status_code == 429:
            if retry_count < 3:
                wait_time = 60 * (2 ** retry_count)
                print(f"\n  ⚠️  RATE LIMIT! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_committee_quarterly_filings(candidate_id, cycle, retry_count + 1)
            else:
                return []

        if not committees_response.ok:
            return []

        # Rate limit after committees call
        time.sleep(4)

        committees = committees_response.json().get('results', [])
        all_filings = []

        # Step 2: For each committee, get filings
        for committee in committees:
            committee_id = committee.get('committee_id')
            # Capture committee designation info
            designation = committee.get('designation')
            designation_full = committee.get('designation_full')
            committee_type = committee.get('committee_type')
            committee_type_full = committee.get('committee_type_full')

            filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
            filings_response = requests.get(filings_url, params={
                'api_key': FEC_API_KEY,
                'cycle': cycle,
                'form_type': 'F3',  # House/Senate candidate reports
                'sort': '-coverage_end_date',
                'per_page': 20  # Get up to 20 filings (covers multiple quarters + amendments)
            }, timeout=10)

            # Rate limit after filings call
            time.sleep(4)

            if filings_response.ok:
                filings = filings_response.json().get('results', [])

                # Filter for quarterly reports only (exclude monthly, termination, etc.)
                quarterly_types = ['Q1', 'Q2', 'Q3', 'Q4', 'APRIL QUARTERLY', 'JULY QUARTERLY',
                                   'OCTOBER QUARTERLY', 'YEAR-END']

                for filing in filings:
                    report_type = filing.get('report_type_full', '')

                    # Only keep quarterly reports
                    if any(qt in report_type.upper() for qt in quarterly_types):
                        # Skip if receipts/disbursements are both None or 0
                        receipts = filing.get('total_receipts')
                        disbursements = filing.get('total_disbursements')

                        all_filings.append({
                            'committee_id': committee_id,
                            'filing_id': filing.get('file_number'),
                            'report_type': report_type,
                            'coverage_start_date': filing.get('coverage_start_date'),
                            'coverage_end_date': filing.get('coverage_end_date'),
                            'total_receipts': receipts,
                            'total_disbursements': disbursements,
                            'cash_beginning': filing.get('cash_on_hand_beginning_period'),
                            'cash_ending': filing.get('cash_on_hand_end_period'),
                            'is_amendment': filing.get('is_amended', False),
                            'designation': designation,
                            'designation_full': designation_full,
                            'committee_type': committee_type,
                            'committee_type_full': committee_type_full
                        })

        return all_filings

    except requests.exceptions.RequestException as e:
        print(f"\n    Error fetching quarterly filings for {candidate_id}: {e}")
        return []

def main():
    print("\n" + "="*60)
    print("FEC DATA FETCHER - Starting...")
    print(f"Cycle: {CYCLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Load previous progress if it exists
    progress = load_progress()
    start_index = progress['last_processed_index']
    financials = progress['financials']
    quarterly_financials = progress.get('quarterly_financials', [])

    if start_index > 0:
        print(f"\n✓ Resuming from candidate #{start_index + 1}")
        print(f"✓ Already have {len(financials)} summary records")
        print(f"✓ Already have {len(quarterly_financials)} quarterly records")
    
    # Load or fetch candidates
    candidates_file = f"candidates_{CYCLE}.json"
    if os.path.exists(candidates_file):
        print(f"\n✓ Loading existing candidates from {candidates_file}")
        with open(candidates_file, 'r') as f:
            all_candidates = json.load(f)
    else:
        print("\nSTEP 1: Fetching candidates...")
        house_candidates = fetch_candidates('H')
        senate_candidates = fetch_candidates('S')
        all_candidates = house_candidates + senate_candidates
        
        print(f"\n{'='*60}")
        print(f"TOTAL CANDIDATES: {len(all_candidates)}")
        print(f"  House: {len(house_candidates)}")
        print(f"  Senate: {len(senate_candidates)}")
        print(f"{'='*60}")
        
        with open(candidates_file, 'w') as f:
            json.dump(all_candidates, f, indent=2)
        print(f"\n✓ Saved candidates to {candidates_file}")
    
    # Fetch financial data with progress tracking
    print(f"\nSTEP 2: Fetching financial data (summary + quarterly)...")
    print(f"{'='*60}")
    print(f"Rate limit: 7,000 requests/hour (upgraded December 2025)")
    print(f"Processing with 4 second delay between API calls (conservative)")
    print(f"Each candidate: 3 API calls (totals + committees + filings)")
    print(f"  = 12 seconds per candidate (could reduce delays if needed)")
    print(f"  = ~300 candidates/hour with current delays")
    print(f"Note: Delays kept conservative for stability")
    print(f"{'='*60}\n")

    total = len(all_candidates)
    save_frequency = 50

    for idx in range(start_index, total):
        candidate = all_candidates[idx]
        candidate_id = candidate.get('candidate_id')
        name = candidate.get('name', 'Unknown')

        print(f"  [{idx+1}/{total}] {name} ({candidate_id})...", end=" ")

        # Fetch summary data (totals) - 1 API call
        financial_data = fetch_candidate_financials(candidate_id)
        time.sleep(4)  # Rate limit: 4 seconds after totals call

        if financial_data:
            combined = {
                'candidate_id': candidate_id,
                'name': name,
                'party': candidate.get('party_full'),
                'state': candidate.get('state'),
                'district': candidate.get('district'),
                'office': candidate.get('office_full'),
                'total_receipts': financial_data.get('receipts'),
                'total_disbursements': financial_data.get('disbursements'),
                'cash_on_hand': financial_data.get('last_cash_on_hand_end_period'),  # FIXED: Use correct field name
                'coverage_start_date': financial_data.get('coverage_start_date'),
                'coverage_end_date': financial_data.get('coverage_end_date'),
                'last_report_year': financial_data.get('last_report_year'),
                'last_report_type': financial_data.get('last_report_type_full'),
                'cycle': CYCLE
            }
            financials.append(combined)

        # Fetch quarterly filings - makes 2+ API calls internally with 4s delays between each
        filings = fetch_committee_quarterly_filings(candidate_id)

        if filings:
            for filing in filings:
                quarterly_record = {
                    'candidate_id': candidate_id,
                    'name': name,
                    'party': candidate.get('party_full'),
                    'state': candidate.get('state'),
                    'district': candidate.get('district'),
                    'office': candidate.get('office_full'),
                    'committee_id': filing['committee_id'],
                    'filing_id': filing['filing_id'],
                    'report_type': filing['report_type'],
                    'coverage_start_date': filing['coverage_start_date'],
                    'coverage_end_date': filing['coverage_end_date'],
                    'total_receipts': filing['total_receipts'],
                    'total_disbursements': filing['total_disbursements'],
                    'cash_beginning': filing['cash_beginning'],
                    'cash_ending': filing['cash_ending'],
                    'is_amendment': filing['is_amendment'],
                    'designation': filing.get('designation'),
                    'designation_full': filing.get('designation_full'),
                    'committee_type': filing.get('committee_type'),
                    'committee_type_full': filing.get('committee_type_full'),
                    'cycle': CYCLE
                }
                quarterly_financials.append(quarterly_record)
            print(f"✓ ({len(filings)} quarterly filings)")
        else:
            print("✓ (no quarterly data)")

        if (idx + 1) % save_frequency == 0:
            save_progress(idx + 1, financials, quarterly_financials)
            print(f"\n  💾 Progress saved: {len(financials)} summary, {len(quarterly_financials)} quarterly (processed {idx + 1}/{total})\n")
    
    financials_file = f"financials_{CYCLE}.json"
    with open(financials_file, 'w') as f:
        json.dump(financials, f, indent=2)

    quarterly_file = f"quarterly_financials_{CYCLE}.json"
    with open(quarterly_file, 'w') as f:
        json.dump(quarterly_financials, f, indent=2)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\n{'='*60}")
    print(f"✓ Saved financial data to {financials_file}")
    print(f"  Candidates with financial summary: {len(financials)}/{total}")
    print(f"\n✓ Saved quarterly data to {quarterly_file}")
    print(f"  Total quarterly filings: {len(quarterly_financials)}")
    print(f"{'='*60}")

    print("\nSUMMARY:")
    candidates_with_money = [f for f in financials if f.get('total_receipts', 0) > 0]
    print(f"  Candidates who have raised money: {len(candidates_with_money)}")

    if candidates_with_money:
        total_raised = sum(f.get('total_receipts', 0) for f in candidates_with_money)
        print(f"  Total money raised: ${total_raised:,.2f}")

    # Quarterly summary
    candidates_with_quarterly = len(set(q['candidate_id'] for q in quarterly_financials))
    print(f"  Candidates with quarterly data: {candidates_with_quarterly}")

    print("\n✓ DATA COLLECTION COMPLETE!")
    print(f"  Check your files:")
    print(f"    - {candidates_file}")
    print(f"    - {financials_file}")
    print(f"    - {quarterly_file}")
    print()

if __name__ == "__main__":
    main()