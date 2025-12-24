#!/usr/bin/env python3
"""
Detect New FEC Filings, Collect Financial Data, and Queue Notifications

This script continuously monitors the FEC API for new candidate filings and:
1. Detects new filings via "sonar blast" polling of /filings/ endpoint
2. Fetches ACTUAL financial data from FEC /committee/{id}/reports/ endpoint
3. Stores financial data in our quarterly_financials table (updates website)
4. Creates notification queue entries for email delivery

Designed for 7,000 requests/hour rate limit.

Usage:
    python detect_new_filings.py                # Run continuously
    python detect_new_filings.py --once         # Check once and exit
    python detect_new_filings.py --dry-run      # Preview without creating notifications
    python detect_new_filings.py --interval 60  # Check every 60 seconds (default: 30)

Testing Mode (for catching early filers before Jan 15 deadline):
    python detect_new_filings.py --test-all EMAIL  # Notify EMAIL of ALL new filings
    python detect_new_filings.py --test-all b.clayton.nelson@gmail.com --once

    This mode ignores the follows list and sends a direct email for every new filing.
    Use this around Jan 5-11 to catch early filers and verify the system works.

API Call Breakdown (per filing detected):
    - 1 call: Sonar blast (/filings/) - returns up to 100 filings
    - 1 call: Fetch financials (/committee/{id}/reports/) - per filing
    - 0-1 call: Committee lookup if candidate_id missing

Filing Day Estimate (500 filings):
    - ~120 sonar calls/hour
    - ~500 financial fetch calls
    - ~100 committee lookups
    = ~720 calls/hour (well under 7,000 limit)
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
FEC_API_KEY = os.getenv('FEC_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL')
SENDGRID_FROM_NAME = os.getenv('SENDGRID_FROM_NAME')

# Configuration
POLL_INTERVAL_SECONDS = 30  # How often to check for new filings (optimized for 7k/hour)
MAX_FILINGS_PER_CHECK = 100  # Limit results per API call

def get_dynamic_lookback_hours():
    """
    Dynamically adjust lookback based on FEC filing calendar.

    Filing deadlines (quarterly reports):
    - Jan 15: Q4/Year-End (covering Oct 1 - Dec 31)
    - Apr 15: Q1 (covering Jan 1 - Mar 31)
    - Jul 15: Q2 (covering Apr 1 - Jun 30)
    - Oct 15: Q3 (covering Jul 1 - Sep 30)

    Strategy:
    - Filing deadline days (13th-16th): Short lookback (2 hours)
      High volume, checking frequently, want fast response
    - Days around deadlines (10th-12th, 17th-20th): Medium lookback (6 hours)
      Moderate volume, some early/late filers
    - Primary season (Mar 1 - Sep 30): Medium lookback (12 hours)
      Primaries vary by state, steady trickle of filings
    - Quiet periods: Long lookback (48 hours)
      Low volume, resilience matters more than speed

    Returns:
        int: Number of hours to look back
    """
    from datetime import datetime

    now = datetime.now()
    month = now.month
    day = now.day

    # Quarterly filing months
    filing_months = [1, 4, 7, 10]  # Jan, Apr, Jul, Oct

    # Check if we're in a filing month
    if month in filing_months:
        # Peak filing days (13th-16th): high volume
        if 13 <= day <= 16:
            return 2  # Short lookback, checking frequently

        # Shoulder days around deadline (10th-12th, 17th-20th)
        elif 10 <= day <= 12 or 17 <= day <= 20:
            return 6  # Medium lookback

        # Rest of filing month
        else:
            return 12  # Moderate lookback

    # Primary season (March through September)
    # Various state primaries = steady trickle of pre/post-primary reports
    elif 3 <= month <= 9:
        # Check if we're near typical primary filing windows
        # Pre-primary reports due ~12 days before election
        # Post-primary reports due ~30 days after
        # Use medium lookback during this busy season
        return 12

    # Quiet periods (Nov, Dec, Feb, rest of filing months)
    else:
        return 48  # Long lookback for resilience


# Get initial lookback (will be recalculated on each check)
LOOKBACK_HOURS = get_dynamic_lookback_hours()

# Rate limit awareness
REQUESTS_PER_HOUR_LIMIT = 7000  # FEC API rate limit
CURRENT_RATE_LIMIT = 7000  # Upgraded API key (December 2025)

# Validate environment
if not all([SUPABASE_URL, SUPABASE_KEY, FEC_API_KEY]):
    print("❌ ERROR: Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_KEY, FEC_API_KEY")
    sys.exit(1)


def get_followed_candidates():
    """
    Get all candidates that have at least one follower with notifications enabled.

    Returns:
        dict: Mapping of candidate_id -> list of (user_id, candidate_info)
    """
    url = f"{SUPABASE_URL}/rest/v1/user_candidate_follows"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'user_id,candidate_id,candidate_name,state,district,office,party',
        'notification_enabled': 'eq.true'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        follows = response.json()

        # Group by candidate_id
        by_candidate = {}
        for follow in follows:
            candidate_id = follow['candidate_id']
            if candidate_id not in by_candidate:
                by_candidate[candidate_id] = []
            by_candidate[candidate_id].append(follow)

        return by_candidate

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Error fetching followed candidates: {e}")
        return {}


def resolve_candidate_from_committee(committee_id):
    """
    Look up candidate_id from committee_id.

    First checks our database, then falls back to FEC API.
    """
    # Try our database first (faster)
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    params = {
        'select': 'candidate_id,name,party,state,office,district',
        'committee_id': f'eq.{committee_id}',
        'limit': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            if results:
                return results[0]
    except:
        pass

    # Fall back to FEC API
    try:
        url = f"https://api.open.fec.gov/v1/committee/{committee_id}/"
        params = {'api_key': FEC_API_KEY}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('results', [])
            if data and data[0].get('candidate_ids'):
                candidate_id = data[0]['candidate_ids'][0]
                return {
                    'candidate_id': candidate_id,
                    'name': data[0].get('name'),
                    'party': data[0].get('party'),
                    'state': data[0].get('state'),
                    'office': None,
                    'district': None
                }
    except:
        pass

    return None


def fetch_filing_financials_from_fec(committee_id, coverage_end_date):
    """
    Fetch actual financial data from FEC API for a specific filing.

    This is the key function that gets REAL financial numbers when a new
    filing is detected, rather than relying on our database (which won't
    have the data yet for brand new filings).

    Args:
        committee_id: The committee that filed
        coverage_end_date: The coverage end date to match (YYYY-MM-DD)

    Returns:
        dict: Financial data from FEC API, or None if not found
    """
    url = f"https://api.open.fec.gov/v1/committee/{committee_id}/reports/"
    params = {
        'api_key': FEC_API_KEY,
        'per_page': 20,
        'sort': '-coverage_end_date'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        reports = response.json().get('results', [])

        # Find the report matching our coverage_end_date
        for report in reports:
            report_end_date = report.get('coverage_end_date', '')[:10]
            if report_end_date == coverage_end_date:
                return {
                    'total_receipts': report.get('total_receipts'),
                    'total_disbursements': report.get('total_disbursements'),
                    'cash_beginning': report.get('cash_on_hand_beginning_period'),
                    'cash_ending': report.get('cash_on_hand_end_period'),
                    'cash_on_hand': report.get('cash_on_hand_end_period'),  # Alias for email template
                    'coverage_start_date': report.get('coverage_start_date'),
                    'coverage_end_date': report.get('coverage_end_date'),
                    'report_type': report.get('report_type_full', report.get('report_type')),
                    'filing_id': report.get('file_number'),
                    'is_amendment': report.get('is_amended', False),
                    'debts_owed': report.get('debts_owed_by_committee'),
                }

        # If exact match not found, return the most recent report
        if reports:
            report = reports[0]
            print(f"      ⚠️  Exact date match not found, using most recent report")
            return {
                'total_receipts': report.get('total_receipts'),
                'total_disbursements': report.get('total_disbursements'),
                'cash_beginning': report.get('cash_on_hand_beginning_period'),
                'cash_ending': report.get('cash_on_hand_end_period'),
                'cash_on_hand': report.get('cash_on_hand_end_period'),
                'coverage_start_date': report.get('coverage_start_date'),
                'coverage_end_date': report.get('coverage_end_date'),
                'report_type': report.get('report_type_full', report.get('report_type')),
                'filing_id': report.get('file_number'),
                'is_amendment': report.get('is_amended', False),
                'debts_owed': report.get('debts_owed_by_committee'),
            }

        return None

    except Exception as e:
        print(f"      ⚠️  Error fetching financials from FEC: {e}")
        return None


def store_filing_in_database(candidate_id, committee_id, filing_data, candidate_info, dry_run=False):
    """
    Store the filing financial data in our quarterly_financials table.

    This ensures the website views are updated in real-time when new filings
    are detected, not just when we run batch collection scripts.

    Args:
        candidate_id: FEC candidate ID
        committee_id: FEC committee ID
        filing_data: Financial data from fetch_filing_financials_from_fec()
        candidate_info: Candidate metadata (name, party, state, office, district)
        dry_run: If True, don't actually store

    Returns:
        bool: Success
    """
    if dry_run:
        return True

    if not filing_data:
        return False

    # Determine cycle from coverage_end_date
    coverage_end = filing_data.get('coverage_end_date', '')
    if coverage_end:
        year = int(coverage_end[:4])
        cycle = year if year % 2 == 0 else year + 1
    else:
        cycle = 2026  # Default to current cycle

    # Determine quarter from coverage_end_date
    quarter = None
    if coverage_end:
        month = int(coverage_end[5:7])
        if month <= 3:
            quarter = 'Q1'
        elif month <= 6:
            quarter = 'Q2'
        elif month <= 9:
            quarter = 'Q3'
        else:
            quarter = 'Q4'

    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    # Add upsert conflict columns
    url += "?on_conflict=candidate_id,cycle,coverage_end_date,is_amendment"

    payload = {
        'candidate_id': candidate_id,
        'committee_id': committee_id,
        'cycle': cycle,
        'quarter': quarter,
        'report_type': filing_data.get('report_type'),
        'coverage_start_date': filing_data.get('coverage_start_date'),
        'coverage_end_date': filing_data.get('coverage_end_date'),
        'total_receipts': filing_data.get('total_receipts'),
        'total_disbursements': filing_data.get('total_disbursements'),
        'cash_beginning': filing_data.get('cash_beginning'),
        'cash_ending': filing_data.get('cash_ending'),
        'debts_owed': filing_data.get('debts_owed'),
        'filing_id': filing_data.get('filing_id'),
        'is_amendment': filing_data.get('is_amendment', False),
        # Candidate info for denormalized queries
        'name': candidate_info.get('name') if candidate_info else None,
        'party': candidate_info.get('party') if candidate_info else None,
        'state': candidate_info.get('state') if candidate_info else None,
        'office': candidate_info.get('office') if candidate_info else None,
        'district': candidate_info.get('district') if candidate_info else None,
    }

    # Remove None values to avoid overwriting existing data with nulls
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"      ⚠️  Error storing filing in database: {e}")
        return False


def check_new_filings(since_date):
    """
    Check FEC API for new filings since the given date.

    Uses the bulk /filings/ endpoint to get all new filings in one request.
    Enriches results with candidate_id if missing (via committee lookup).

    Args:
        since_date: ISO format date string (YYYY-MM-DD)

    Returns:
        list: Filing records from FEC API, enriched with candidate info
    """
    url = "https://api.open.fec.gov/v1/filings/"

    params = {
        'api_key': FEC_API_KEY,
        'min_receipt_date': since_date,
        'sort': '-receipt_date',  # Newest first
        'per_page': MAX_FILINGS_PER_CHECK,
        'form_type': ['F3', 'F3P'],  # Candidate committees only (not PACs/F3X)
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        # Enrich filings that don't have candidate_id
        for filing in results:
            if not filing.get('candidate_id') and filing.get('committee_id'):
                candidate_info = resolve_candidate_from_committee(filing['committee_id'])
                if candidate_info:
                    filing['candidate_id'] = candidate_info.get('candidate_id')
                    filing['candidate_name'] = candidate_info.get('name')
                    filing['party'] = candidate_info.get('party')
                    filing['state'] = candidate_info.get('state')
                    filing['office'] = candidate_info.get('office')
                    filing['district'] = candidate_info.get('district')

        return results

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Error fetching filings from FEC: {e}")
        return []


def get_filing_financials(candidate_id, coverage_end_date):
    """
    Get financial data for a specific filing.

    Fetches from quarterly_financials to get the actual amounts reported
    in this specific filing (not cumulative cycle totals).

    Args:
        candidate_id: FEC candidate ID
        coverage_end_date: Coverage end date of the filing (YYYY-MM-DD)

    Returns:
        dict: Financial data from the filing or None
    """
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'total_receipts,total_disbursements,cash_ending,coverage_end_date,report_type',
        'candidate_id': f'eq.{candidate_id}',
        'coverage_end_date': f'eq.{coverage_end_date}',
        'limit': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        results = response.json()
        if results:
            # Map cash_ending to cash_on_hand for consistency with email template
            result = results[0]
            result['cash_on_hand'] = result.pop('cash_ending', None)
            return result
        return None

    except Exception as e:
        print(f"    ⚠️  Could not fetch filing financials: {e}")
        return None


def send_test_email(to_email, filing, filing_financials, dry_run=False):
    """
    Send a direct test email for any filing (bypasses notification queue).

    Used in --test-all mode to catch early filers and verify system works.
    """
    if dry_run:
        print(f"      [DRY RUN] Would send test email to {to_email}")
        return True

    candidate_name = filing.get('candidate_name', 'Unknown')
    candidate_id = filing.get('candidate_id', '')
    party = filing.get('party', '')
    state = filing.get('state', '')
    office = filing.get('office', '')
    district = filing.get('district', '')
    report_type = filing.get('report_type_full', filing.get('report_type', 'Financial Report'))
    coverage_end_date = filing.get('coverage_end_date', '')[:10] if filing.get('coverage_end_date') else ''
    receipt_date = filing.get('receipt_date', '')[:10] if filing.get('receipt_date') else ''

    # Get financial data
    total_receipts = filing_financials.get('total_receipts') if filing_financials else None
    total_disbursements = filing_financials.get('total_disbursements') if filing_financials else None
    cash_on_hand = filing_financials.get('cash_on_hand') if filing_financials else None

    def format_currency(amount):
        if amount is None:
            return 'N/A'
        return f'${amount:,.0f}'

    # Format office display (handle variations: 'H', 'House', 'S', 'Senate', 'P', 'President')
    office_upper = (office or '').upper()
    # Clean district - treat '00', '', None as no district
    clean_district = district if district and district not in ('00', '0', '') else None

    if office_upper in ('H', 'HOUSE'):
        office_display = f"U.S. House - {state}-{clean_district}" if clean_district else f"U.S. House - {state}"
    elif office_upper in ('S', 'SENATE'):
        office_display = f"U.S. Senate - {state}"
    elif office_upper in ('P', 'PRESIDENT'):
        office_display = "U.S. President"
    else:
        office_display = f"{office} - {state}" if state else (office or "Unknown Office")

    # Party color
    party_upper = (party or '').upper()
    if 'DEM' in party_upper:
        party_color = '#0015BC'
        party_display = 'DEMOCRATIC'
    elif 'REP' in party_upper:
        party_color = '#E81B23'
        party_display = 'REPUBLICAN'
    else:
        party_color = '#666666'
        party_display = party or 'OTHER'

    html = f'''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <tr><td style="padding: 30px 40px; border-bottom: 1px solid #e5e5e5;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">🧪 TEST: New Filing Detected</h1>
                    <p style="margin: 8px 0 0 0; font-size: 14px; color: #666666;">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p style="margin: 8px 0 0 0; font-size: 12px; color: #E81B23; font-weight: 600;">This is a TEST notification from --test-all mode</p>
                </td></tr>
                <tr><td style="padding: 30px 40px;">
                    <div style="display: inline-block; padding: 4px 12px; background-color: {party_color}15; border-radius: 12px; margin-bottom: 12px;">
                        <span style="font-size: 12px; font-weight: 600; color: {party_color};">{party_display}</span>
                    </div>
                    <h2 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700; color: #1a1a1a;">{candidate_name}</h2>
                    <p style="margin: 0; font-size: 16px; color: #666666;">{office_display}</p>
                    <p style="margin: 16px 0 0 0; font-size: 14px; color: #666666;">
                        Filed a new <strong>{report_type}</strong> covering through {coverage_end_date}<br>
                        <span style="color: #999;">Filed on: {receipt_date} | Candidate ID: {candidate_id}</span>
                    </p>
                </td></tr>
                <tr><td style="padding: 0 40px 30px 40px;">
                    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px;">
                        <tr><td style="padding: 20px; border-bottom: 1px solid #e5e5e5;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666;">TOTAL RAISED</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: #059669;">{format_currency(total_receipts)}</p>
                        </td></tr>
                        <tr><td style="padding: 20px; border-bottom: 1px solid #e5e5e5;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666;">TOTAL SPENT</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: #dc2626;">{format_currency(total_disbursements)}</p>
                        </td></tr>
                        <tr><td style="padding: 20px;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666;">CASH ON HAND</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: #2563eb;">{format_currency(cash_on_hand)}</p>
                        </td></tr>
                    </table>
                </td></tr>
                <tr><td style="padding: 30px 40px; background-color: #fffbeb; border-top: 1px solid #fcd34d;">
                    <p style="margin: 0; font-size: 14px; color: #92400e;">
                        <strong>🧪 Test Mode Active</strong><br>
                        This email was sent because you're running <code>--test-all</code> mode to catch early filers.
                        Verify that this data is correct in the database before Jan 15.
                    </p>
                </td></tr>
            </table>
            <p style="margin: 20px 0 0 0; font-size: 11px; color: #999999; text-align: center;">
                Campaign Reference | Data from the Federal Election Commission
            </p>
        </td></tr>
    </table>
</body>
</html>
'''

    # Send via SendGrid
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "personalizations": [{"to": [{"email": to_email}], "subject": f"🧪 TEST: New Filing - {candidate_name}"}],
        "from": {"email": SENDGRID_FROM_EMAIL, "name": SENDGRID_FROM_NAME},
        "content": [{"type": "text/html", "value": html}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 202
    except Exception as e:
        print(f"      ⚠️  Failed to send test email: {e}")
        return False


def create_notification(user_id, candidate_id, filing_date, filing_data, dry_run=False):
    """
    Create a notification queue entry.

    Args:
        user_id: UUID of user to notify
        candidate_id: FEC candidate ID
        filing_date: Date of the filing
        filing_data: JSONB data to include in email
        dry_run: If True, don't actually create the notification

    Returns:
        bool: Success
    """
    if dry_run:
        return True

    url = f"{SUPABASE_URL}/rest/v1/notification_queue"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal,resolution=merge-duplicates'
    }

    # Add unique constraint conflict parameter
    url += "?on_conflict=user_id,candidate_id,filing_date"

    payload = {
        'user_id': user_id,
        'candidate_id': candidate_id,
        'filing_date': filing_date,
        'filing_data': filing_data,
        'status': 'pending',
        'retry_count': 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        # 201 = created, 409 = duplicate (already queued), both are fine
        return response.status_code in [200, 201, 204, 409]

    except Exception as e:
        print(f"      ⚠️  Error creating notification: {e}")
        return False


def process_filing(filing, followed_candidates, dry_run=False):
    """
    Process a single filing and create notifications for followers.

    This function:
    1. Fetches actual financial data from FEC API
    2. Stores it in our database (so website is updated)
    3. Creates notification queue entries for followers

    Args:
        filing: Filing record from FEC API
        followed_candidates: Dict of candidate_id -> list of followers
        dry_run: If True, preview without creating notifications

    Returns:
        int: Number of notifications created
    """
    candidate_id = filing.get('candidate_id')
    committee_id = filing.get('committee_id')

    # Skip if no one is following this candidate
    if candidate_id not in followed_candidates:
        return 0

    followers = followed_candidates[candidate_id]

    # Get candidate info from first follower (they all have same candidate data)
    candidate_info = followers[0]
    candidate_name = candidate_info['candidate_name']

    # Extract filing details
    receipt_date = filing.get('receipt_date', '')[:10]  # YYYY-MM-DD
    report_type = filing.get('report_type_full_name', filing.get('report_type', 'Financial Report'))
    coverage_end_date = filing.get('coverage_end_date', '')[:10] if filing.get('coverage_end_date') else ''

    # STEP 1: Fetch financial data from FEC API (not our database!)
    filing_financials = fetch_filing_financials_from_fec(committee_id, coverage_end_date)

    if filing_financials:
        # STEP 2: Store in our database (so website is updated too)
        store_filing_in_database(
            candidate_id, committee_id, filing_financials,
            {
                'name': candidate_name,
                'party': candidate_info.get('party'),
                'state': candidate_info.get('state'),
                'office': candidate_info.get('office'),
                'district': candidate_info.get('district'),
            },
            dry_run=dry_run
        )
        # Use report_type from FEC API response if available
        if filing_financials.get('report_type'):
            report_type = filing_financials.get('report_type')

    # Build filing data for email (STEP 3: notification)
    filing_data = {
        'candidate_id': candidate_id,
        'candidate_name': candidate_name,
        'party': candidate_info.get('party'),
        'office': candidate_info.get('office'),
        'state': candidate_info.get('state'),
        'district': candidate_info.get('district'),
        'report_type': report_type,
        'coverage_end_date': coverage_end_date,
        'filing_date': receipt_date,
        'total_receipts': filing_financials.get('total_receipts') if filing_financials else None,
        'total_disbursements': filing_financials.get('total_disbursements') if filing_financials else None,
        'cash_on_hand': filing_financials.get('cash_on_hand') if filing_financials else None,
    }

    notifications_created = 0

    for follower in followers:
        user_id = follower['user_id']

        success = create_notification(
            user_id=user_id,
            candidate_id=candidate_id,
            filing_date=receipt_date,
            filing_data=filing_data,
            dry_run=dry_run
        )

        if success:
            notifications_created += 1

    return notifications_created


def run_check(dry_run=False, test_all_email=None):
    """
    Run a single check for new filings.

    Args:
        dry_run: If True, preview without sending notifications
        test_all_email: If set, send test emails for ALL filings to this address

    Returns:
        Tuple of (filings_found, notifications_created)
    """
    print(f"\n{'='*80}")
    print(f"CHECKING FOR NEW FILINGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if test_all_email:
        print(f"[🧪 TEST-ALL MODE - Notifying {test_all_email} of ALL filings]")
    if dry_run:
        print("[DRY RUN MODE - No notifications will be created]")
    print(f"{'='*80}")

    # In test-all mode, we skip checking followed candidates
    if not test_all_email:
        # Get candidates with followers
        print("\n1. Fetching followed candidates...")
        followed_candidates = get_followed_candidates()

        if not followed_candidates:
            print("   ℹ️  No candidates are being followed with notifications enabled")
            return 0, 0

        print(f"   ✓ {len(followed_candidates)} candidates are being watched by users")
    else:
        print("\n1. Test-all mode: Skipping follows check (will notify on ALL filings)")
        followed_candidates = {}

    # Calculate lookback time (dynamic based on filing calendar)
    current_lookback = get_dynamic_lookback_hours()
    lookback_time = datetime.now() - timedelta(hours=current_lookback)
    since_date = lookback_time.strftime('%Y-%m-%d')

    print(f"\n2. Checking FEC for filings since {since_date} (lookback: {current_lookback}h)...")
    filings = check_new_filings(since_date)

    if not filings:
        print("   ℹ️  No new filings found")
        return 0, 0

    print(f"   ✓ Found {len(filings)} new filing(s)")

    # Process each filing
    print(f"\n3. Processing filings...")

    total_notifications = 0
    filings_processed = 0

    for filing in filings:
        candidate_id = filing.get('candidate_id')
        candidate_name = filing.get('candidate_name', candidate_id)
        receipt_date = filing.get('receipt_date', '')
        coverage_end_date = filing.get('coverage_end_date', '')[:10] if filing.get('coverage_end_date') else ''

        # In test-all mode, process ALL filings
        if test_all_email:
            committee_id = filing.get('committee_id')
            print(f"\n   📄 {candidate_name} ({candidate_id})")
            print(f"      Filed: {receipt_date} | Committee: {committee_id}")

            # STEP 1: Fetch financial data from FEC API (not our database!)
            print(f"      🔍 Fetching financials from FEC API...")
            filing_financials = fetch_filing_financials_from_fec(committee_id, coverage_end_date)

            if filing_financials:
                receipts = filing_financials.get('total_receipts') or 0
                cash = filing_financials.get('cash_on_hand') or 0
                print(f"      💰 Receipts: ${receipts:,.0f} | Cash: ${cash:,.0f}")

                # STEP 2: Store in our database (so website is updated too)
                candidate_info = {
                    'name': filing.get('candidate_name'),
                    'party': filing.get('party'),
                    'state': filing.get('state'),
                    'office': filing.get('office'),
                    'district': filing.get('district'),
                }
                stored = store_filing_in_database(
                    candidate_id, committee_id, filing_financials, candidate_info, dry_run=dry_run
                )
                if stored:
                    if dry_run:
                        print(f"      💾 [DRY RUN] Would store in database")
                    else:
                        print(f"      💾 Stored in quarterly_financials")
                else:
                    print(f"      ⚠️  Failed to store in database")
            else:
                print(f"      ⚠️  Could not fetch financials from FEC API")

            # STEP 3: Send test email with REAL data
            success = send_test_email(test_all_email, filing, filing_financials, dry_run=dry_run)

            if success:
                if dry_run:
                    print(f"      ✓ [DRY RUN] Would send test email")
                else:
                    print(f"      ✓ Test email sent to {test_all_email}")
                total_notifications += 1

            filings_processed += 1

        # In normal mode, only process followed candidates
        elif candidate_id in followed_candidates:
            follower_count = len(followed_candidates[candidate_id])
            print(f"\n   📄 {candidate_name} ({candidate_id})")
            print(f"      Filed: {receipt_date}")
            print(f"      Followers to notify: {follower_count}")

            notifications_created = process_filing(
                filing=filing,
                followed_candidates=followed_candidates,
                dry_run=dry_run
            )

            if dry_run:
                print(f"      ✓ [DRY RUN] Would create {notifications_created} notification(s)")
            else:
                print(f"      ✓ Created {notifications_created} notification(s)")

            total_notifications += notifications_created
            filings_processed += 1

    print(f"\n{'='*80}")
    print(f"CHECK COMPLETE")
    print(f"{'='*80}")
    print(f"New filings found: {len(filings)}")
    print(f"Filings processed: {filings_processed}")
    print(f"{'Notifications that would be sent' if dry_run else 'Notifications sent'}: {total_notifications}")
    print(f"{'='*80}\n")

    return len(filings), total_notifications


def main():
    """Main entry point."""
    # Parse arguments
    run_once = '--once' in sys.argv
    dry_run = '--dry-run' in sys.argv

    # Get --test-all EMAIL argument
    test_all_email = None
    for i, arg in enumerate(sys.argv):
        if arg == '--test-all' and i + 1 < len(sys.argv):
            test_all_email = sys.argv[i + 1]
            if not '@' in test_all_email:
                print(f"❌ ERROR: --test-all requires a valid email address")
                print(f"   Usage: python detect_new_filings.py --test-all your@email.com")
                sys.exit(1)

    # Get custom interval
    interval = POLL_INTERVAL_SECONDS
    for i, arg in enumerate(sys.argv):
        if arg == '--interval' and i + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[i + 1])
            except ValueError:
                print(f"⚠️  Invalid interval value, using default: {POLL_INTERVAL_SECONDS}s")

    # Get current dynamic lookback for display
    current_lookback = get_dynamic_lookback_hours()
    now = datetime.now()

    print("\n" + "="*80)
    print("FEC FILING DETECTION SERVICE")
    print("="*80)
    if test_all_email:
        print(f"🧪 TEST-ALL MODE: Sending ALL filings to {test_all_email}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Run: {'ONCE' if run_once else 'CONTINUOUS'}")
    print(f"Interval: {interval} seconds")
    print(f"Lookback: {current_lookback} hours (dynamic based on filing calendar)")
    print(f"         Today is {now.strftime('%b %d')} → ", end="")
    if now.month in [1, 4, 7, 10] and 13 <= now.day <= 16:
        print("📈 PEAK FILING DAY")
    elif now.month in [1, 4, 7, 10]:
        print("📅 Filing month")
    elif 3 <= now.month <= 9:
        print("🗳️  Primary season")
    else:
        print("😴 Quiet period")
    print(f"Rate limit: {CURRENT_RATE_LIMIT}/hour (designed for {REQUESTS_PER_HOUR_LIMIT}/hour)")

    if CURRENT_RATE_LIMIT < REQUESTS_PER_HOUR_LIMIT:
        print(f"\n⚠️  WARNING: Currently at {CURRENT_RATE_LIMIT}/hour rate limit")
        print(f"   Polling every {interval}s uses ~{3600//interval} requests/hour")
    else:
        print(f"\n✓ Full rate limit available ({CURRENT_RATE_LIMIT}/hour)")

    print("="*80)

    if run_once:
        # Run once and exit
        run_check(dry_run=dry_run, test_all_email=test_all_email)
    else:
        # Run continuously
        print(f"\n▶️  Starting continuous monitoring (Ctrl+C to stop)...")
        print(f"   Checking every {interval} seconds\n")

        try:
            while True:
                run_check(dry_run=dry_run, test_all_email=test_all_email)

                print(f"⏳ Waiting {interval} seconds until next check...\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✋ Stopped by user")
            print("="*80)
            sys.exit(0)


if __name__ == "__main__":
    main()
