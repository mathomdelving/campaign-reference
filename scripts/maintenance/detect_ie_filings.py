#!/usr/bin/env python3
"""
Detect New FEC Independent Expenditures and Queue Notifications

This script monitors the FEC API for new independent expenditure (IE) filings and:
1. Detects new IEs via polling of /schedules/schedule_e/efile/ endpoint
2. Stores IE data in our independent_expenditures table
3. Creates notification queue entries for users following targeted candidates

Independent expenditures are spending by outside groups (Super PACs, 501c4s, etc.)
FOR or AGAINST candidates. 24-hour reports are required within 24 hours of spending
$1,000+ in the final 20 days before an election.

Usage:
    python detect_ie_filings.py                # Run continuously
    python detect_ie_filings.py --once         # Check once and exit
    python detect_ie_filings.py --dry-run      # Preview without creating notifications
    python detect_ie_filings.py --interval 60  # Check every 60 seconds (default: 30)

API Call Breakdown:
    - 1 call: Poll /schedules/schedule_e/efile/ - returns up to 100 IEs
    - Well under 7,000/hour rate limit
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

# Configuration
POLL_INTERVAL_SECONDS = 30  # How often to check for new IEs
MAX_IES_PER_CHECK = 100  # Limit results per API call
LOOKBACK_HOURS = 24  # How far back to look for new IEs

# Rate limit awareness
REQUESTS_PER_HOUR_LIMIT = 7000

# Validate environment
if not all([SUPABASE_URL, SUPABASE_KEY, FEC_API_KEY]):
    print("ERROR: Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_KEY, FEC_API_KEY")
    sys.exit(1)


def get_followed_candidates_for_ie():
    """
    Get all candidates that have at least one follower with IE notifications enabled.

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
        'ie_notification_enabled': 'eq.true'
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
        print(f"  Error fetching followed candidates: {e}")
        return {}


def check_new_ies(since_date):
    """
    Check FEC API for new independent expenditures since the given date.

    Uses the /schedules/schedule_e/efile/ endpoint which provides near real-time
    data from electronically filed reports.

    Args:
        since_date: ISO format date string (YYYY-MM-DD)

    Returns:
        list: IE records from FEC API
    """
    url = "https://api.open.fec.gov/v1/schedules/schedule_e/efile/"

    params = {
        'api_key': FEC_API_KEY,
        'min_dissemination_date': since_date,
        'sort': '-dissemination_date',
        'per_page': MAX_IES_PER_CHECK,
    }

    try:
        response = requests.get(url, params=params)

        # Handle 422 (no data for date range) gracefully
        if response.status_code == 422:
            return []

        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        return results

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching IEs from FEC: {e}")
        return []


def store_ie_in_database(ie_data, dry_run=False):
    """
    Store an independent expenditure in our database.

    Args:
        ie_data: IE record from FEC API
        dry_run: If True, don't actually store

    Returns:
        bool: Success
    """
    if dry_run:
        return True

    # Extract cycle from expenditure date or receipt date
    exp_date = ie_data.get('expenditure_date') or ie_data.get('receipt_date') or ''
    if exp_date:
        year = int(exp_date[:4])
        cycle = year if year % 2 == 0 else year + 1
    else:
        cycle = 2026  # Default to current cycle

    url = f"{SUPABASE_URL}/rest/v1/independent_expenditures"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    # Add upsert conflict columns
    url += "?on_conflict=spender_committee_id,candidate_id,transaction_id,amount"

    payload = {
        'spender_committee_id': ie_data.get('committee_id'),
        'spender_committee_name': ie_data.get('committee_name') or ie_data.get('filer_name'),
        'candidate_id': ie_data.get('candidate_id'),
        'candidate_name': ie_data.get('candidate_name'),
        'support_oppose': ie_data.get('support_oppose_indicator', ''),
        'amount': ie_data.get('expenditure_amount'),
        'expenditure_date': ie_data.get('expenditure_date'),
        'dissemination_date': ie_data.get('dissemination_date'),
        'purpose': ie_data.get('expenditure_description') or ie_data.get('category_code_full'),
        'payee_name': ie_data.get('payee_name'),
        'cycle': cycle,
        'office': ie_data.get('candidate_office'),
        'state': ie_data.get('candidate_state'),
        'district': ie_data.get('candidate_district'),
        'filing_id': ie_data.get('file_number'),
        'transaction_id': ie_data.get('transaction_id'),
        'receipt_date': ie_data.get('receipt_date'),
        'is_amendment': ie_data.get('amendment_indicator') == 'A',
    }

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"      Error storing IE in database: {e}")
        return False


def create_ie_notification(user_id, candidate_id, ie_date, ie_data, dry_run=False):
    """
    Create a notification queue entry for an IE.

    Args:
        user_id: UUID of user to notify
        candidate_id: FEC candidate ID
        ie_date: Date of the IE
        ie_data: JSONB data to include in email
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

    # Add unique constraint conflict parameter (now includes notification_type)
    url += "?on_conflict=user_id,candidate_id,filing_date,notification_type"

    payload = {
        'user_id': user_id,
        'candidate_id': candidate_id,
        'filing_date': ie_date,
        'filing_data': ie_data,
        'notification_type': 'ie',
        'status': 'pending',
        'retry_count': 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201, 204, 409]

    except Exception as e:
        print(f"      Error creating notification: {e}")
        return False


def format_currency(amount):
    """Format number as currency"""
    if amount is None:
        return "$0"
    return f"${amount:,.0f}"


def process_ie(ie, followed_candidates, dry_run=False):
    """
    Process a single independent expenditure and create notifications for followers.

    Args:
        ie: IE record from FEC API
        followed_candidates: Dict of candidate_id -> list of followers
        dry_run: If True, preview without creating notifications

    Returns:
        int: Number of notifications created
    """
    candidate_id = ie.get('candidate_id')

    if not candidate_id:
        return 0

    # Skip if no one is following this candidate for IE notifications
    if candidate_id not in followed_candidates:
        return 0

    followers = followed_candidates[candidate_id]

    # Get candidate info from first follower (they all have same candidate data)
    candidate_info = followers[0]
    candidate_name = ie.get('candidate_name') or candidate_info.get('candidate_name', 'Unknown')

    # Extract IE details
    spender_name = ie.get('committee_name') or ie.get('filer_name') or 'Unknown Committee'
    amount = ie.get('expenditure_amount', 0)
    support_oppose = ie.get('support_oppose_indicator', '')
    purpose = ie.get('expenditure_description') or ie.get('category_code_full') or ''
    expenditure_date = ie.get('expenditure_date') or ie.get('receipt_date') or ''
    receipt_date = ie.get('receipt_date', '')[:10] if ie.get('receipt_date') else ''

    # Store IE in database
    store_ie_in_database(ie, dry_run=dry_run)

    # Build notification data for email
    ie_notification_data = {
        'notification_type': 'ie',
        'candidate_id': candidate_id,
        'candidate_name': candidate_name,
        'party': candidate_info.get('party'),
        'office': ie.get('candidate_office') or candidate_info.get('office'),
        'state': ie.get('candidate_state') or candidate_info.get('state'),
        'district': ie.get('candidate_district') or candidate_info.get('district'),
        'spender_committee_id': ie.get('committee_id'),
        'spender_name': spender_name,
        'amount': amount,
        'support_oppose': support_oppose,
        'purpose': purpose,
        'expenditure_date': expenditure_date[:10] if expenditure_date else '',
        'filing_date': receipt_date,
    }

    notifications_created = 0

    for follower in followers:
        user_id = follower['user_id']

        success = create_ie_notification(
            user_id=user_id,
            candidate_id=candidate_id,
            ie_date=receipt_date or datetime.now().strftime('%Y-%m-%d'),
            ie_data=ie_notification_data,
            dry_run=dry_run
        )

        if success:
            notifications_created += 1

    return notifications_created


def run_check(dry_run=False):
    """
    Run a single check for new independent expenditures.

    Args:
        dry_run: If True, preview without sending notifications

    Returns:
        Tuple of (ies_found, notifications_created)
    """
    print(f"\n{'='*80}")
    print(f"CHECKING FOR NEW INDEPENDENT EXPENDITURES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("[DRY RUN MODE - No notifications will be created]")
    print(f"{'='*80}")

    # Get candidates with IE notification followers
    print("\n1. Fetching candidates with IE notification followers...")
    followed_candidates = get_followed_candidates_for_ie()

    if not followed_candidates:
        print("   No candidates are being followed with IE notifications enabled")
        return 0, 0

    print(f"   {len(followed_candidates)} candidates have IE notification followers")

    # Calculate lookback time
    lookback_time = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
    since_date = lookback_time.strftime('%Y-%m-%d')

    print(f"\n2. Checking FEC for IEs since {since_date} (lookback: {LOOKBACK_HOURS}h)...")
    ies = check_new_ies(since_date)

    if not ies:
        print("   No new IEs found")
        return 0, 0

    print(f"   Found {len(ies)} new IE(s)")

    # Process each IE
    print(f"\n3. Processing IEs...")

    total_notifications = 0
    ies_processed = 0
    ies_with_followers = 0

    for ie in ies:
        candidate_id = ie.get('candidate_id')
        candidate_name = ie.get('candidate_name', candidate_id)
        spender_name = ie.get('committee_name') or ie.get('filer_name') or 'Unknown'
        amount = ie.get('expenditure_amount', 0)
        support_oppose = ie.get('support_oppose_indicator', '')

        # Only process IEs for followed candidates
        if candidate_id in followed_candidates:
            so_label = "FOR" if support_oppose == 'S' else "AGAINST"
            follower_count = len(followed_candidates[candidate_id])

            print(f"\n   ${amount:,.0f} {so_label} {candidate_name}")
            print(f"      Spender: {spender_name}")
            print(f"      Followers to notify: {follower_count}")

            notifications_created = process_ie(
                ie=ie,
                followed_candidates=followed_candidates,
                dry_run=dry_run
            )

            if dry_run:
                print(f"      [DRY RUN] Would create {notifications_created} notification(s)")
            else:
                print(f"      Created {notifications_created} notification(s)")

            total_notifications += notifications_created
            ies_with_followers += 1

        ies_processed += 1

    print(f"\n{'='*80}")
    print(f"CHECK COMPLETE")
    print(f"{'='*80}")
    print(f"Total IEs found: {len(ies)}")
    print(f"IEs for followed candidates: {ies_with_followers}")
    print(f"{'Notifications that would be sent' if dry_run else 'Notifications created'}: {total_notifications}")
    print(f"{'='*80}\n")

    return len(ies), total_notifications


def main():
    """Main entry point."""
    # Parse arguments
    run_once = '--once' in sys.argv
    dry_run = '--dry-run' in sys.argv

    # Get custom interval
    interval = POLL_INTERVAL_SECONDS
    for i, arg in enumerate(sys.argv):
        if arg == '--interval' and i + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[i + 1])
            except ValueError:
                print(f"  Invalid interval value, using default: {POLL_INTERVAL_SECONDS}s")

    print("\n" + "="*80)
    print("FEC INDEPENDENT EXPENDITURE DETECTION SERVICE")
    print("="*80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Run: {'ONCE' if run_once else 'CONTINUOUS'}")
    print(f"Interval: {interval} seconds")
    print(f"Lookback: {LOOKBACK_HOURS} hours")
    print("="*80)

    if run_once:
        # Run once and exit
        run_check(dry_run=dry_run)
    else:
        # Run continuously
        print(f"\n  Starting continuous monitoring (Ctrl+C to stop)...")
        print(f"   Checking every {interval} seconds\n")

        try:
            while True:
                run_check(dry_run=dry_run)

                print(f"  Waiting {interval} seconds until next check...\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n  Stopped by user")
            print("="*80)
            sys.exit(0)


if __name__ == "__main__":
    main()
