"""
Detect New Filings and Queue Notifications

This script runs after incremental_update.py to detect which candidates
have new filings and queue email notifications for users following them.

Usage:
    python detect_new_filings.py              # Check last 24 hours
    python detect_new_filings.py --lookback 7 # Check last 7 days
    python detect_new_filings.py --dry-run    # Preview without queuing
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validate environment variables
if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("ERROR: Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_KEY")
    sys.exit(1)


def get_recent_filings(lookback_hours=24):
    """
    Get candidates with financial data updated in the last N hours

    This identifies candidates with new filings by looking at their
    coverage_end_date which gets updated when new filings are processed.

    Returns:
        List of candidate records with new filings
    """
    print(f"\n=== Detecting New Filings (last {lookback_hours} hours) ===")

    # Calculate the cutoff time
    cutoff_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()

    url = f"{SUPABASE_URL}/rest/v1/financial_summary"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    # Query for financial records updated recently
    # We're looking for records where coverage_end_date is recent,
    # indicating a new filing was processed
    params = {
        'select': 'candidate_id,total_receipts,total_disbursements,cash_on_hand,coverage_end_date,report_year,report_type',
        'cycle': 'eq.2026',
        'order': 'coverage_end_date.desc',
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        all_records = response.json()

        # Filter to only include records with coverage_end_date in our lookback window
        recent_filings = []
        cutoff_date = (datetime.now() - timedelta(hours=lookback_hours)).date()

        for record in all_records:
            coverage_end = record.get('coverage_end_date')
            if coverage_end:
                try:
                    coverage_date = datetime.fromisoformat(coverage_end.replace('Z', '+00:00')).date()
                    if coverage_date >= cutoff_date:
                        recent_filings.append(record)
                except:
                    continue

        print(f"Found {len(recent_filings)} candidates with new filings")
        return recent_filings

    except requests.exceptions.RequestException as e:
        print(f"Error fetching recent filings: {e}")
        return []


def get_candidate_info(candidate_id):
    """Fetch candidate name and details from database"""
    url = f"{SUPABASE_URL}/rest/v1/candidates"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'candidate_id,name,party,office,state,district',
        'candidate_id': f'eq.{candidate_id}'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        results = response.json()
        if results:
            return results[0]

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching candidate info for {candidate_id}: {e}")

    return None


def get_followers_for_candidate(candidate_id):
    """
    Get all users following this candidate with notifications enabled

    Returns:
        List of user records
    """
    url = f"{SUPABASE_URL}/rest/v1/user_candidate_follows"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'user_id,candidate_name',
        'candidate_id': f'eq.{candidate_id}',
        'notification_enabled': 'eq.true'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching followers for {candidate_id}: {e}")
        return []


def get_user_email(user_id):
    """
    Get user email from auth.users table

    Note: This uses Supabase's auth API endpoint
    """
    # For Supabase auth.users, we need to use the admin API
    # Since we can't directly query auth.users via REST API, we'll
    # need to use user_profiles or handle this via Supabase function

    # For now, we'll just store the user_id in the queue and retrieve
    # the email when sending (in send_notifications.py)
    return user_id


def queue_notification(user_id, candidate_id, filing_date, filing_data, dry_run=False):
    """
    Add a notification to the queue

    Args:
        user_id: UUID of the user to notify
        candidate_id: FEC candidate ID
        filing_date: Date of the filing
        filing_data: JSONB snapshot of filing details
        dry_run: If True, don't actually insert (for testing)

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        return True

    url = f"{SUPABASE_URL}/rest/v1/notification_queue"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=ignore-duplicates,return=minimal'
    }

    record = {
        'user_id': user_id,
        'candidate_id': candidate_id,
        'filing_date': filing_date,
        'filing_data': filing_data,
        'status': 'pending',
        'queued_at': datetime.now().isoformat(),
        'retry_count': 0
    }

    try:
        response = requests.post(url, headers=headers, json=record)
        # 201 = created, 409 = duplicate (ignored), both are success
        return response.status_code in [200, 201, 204, 409]
    except:
        return False


def process_new_filings(dry_run=False, lookback_hours=24):
    """
    Main processing function:
    1. Get candidates with new filings
    2. For each candidate, find followers
    3. Queue notifications for each follower

    Returns:
        Tuple of (notifications_queued, errors)
    """
    print(f"\n=== Processing New Filings {'(DRY RUN)' if dry_run else ''} ===")

    # Step 1: Get recent filings
    recent_filings = get_recent_filings(lookback_hours)

    if not recent_filings:
        print("\n✓ No new filings to process")
        return 0, []

    notifications_queued = 0
    errors = []

    # Step 2: Process each filing
    for filing in recent_filings:
        candidate_id = filing['candidate_id']
        coverage_end_date = filing.get('coverage_end_date', datetime.now().date().isoformat())

        print(f"\n  Processing: {candidate_id}")

        # Get candidate info
        candidate_info = get_candidate_info(candidate_id)
        if not candidate_info:
            print(f"    ✗ Could not fetch candidate info")
            errors.append(f"{candidate_id}: No candidate info found")
            continue

        candidate_name = candidate_info.get('name', 'Unknown')
        print(f"    Candidate: {candidate_name}")

        # Get followers
        followers = get_followers_for_candidate(candidate_id)

        if not followers:
            print(f"    No followers watching this candidate")
            continue

        print(f"    Found {len(followers)} follower(s) with notifications enabled")

        # Create filing data snapshot for email
        filing_data = {
            'candidate_id': candidate_id,
            'candidate_name': candidate_name,
            'party': candidate_info.get('party'),
            'office': candidate_info.get('office'),
            'state': candidate_info.get('state'),
            'district': candidate_info.get('district'),
            'total_receipts': filing.get('total_receipts'),
            'total_disbursements': filing.get('total_disbursements'),
            'cash_on_hand': filing.get('cash_on_hand'),
            'coverage_end_date': coverage_end_date,
            'report_type': filing.get('report_type')
        }

        # Queue notification for each follower
        for follower in followers:
            user_id = follower['user_id']

            if queue_notification(
                user_id=user_id,
                candidate_id=candidate_id,
                filing_date=coverage_end_date,
                filing_data=filing_data,
                dry_run=dry_run
            ):
                notifications_queued += 1
                if not dry_run:
                    print(f"      ✓ Queued notification for user {user_id[:8]}...")
                else:
                    print(f"      [DRY RUN] Would queue notification for user {user_id[:8]}...")
            else:
                error_msg = f"{candidate_id} -> {user_id}: Failed to queue"
                errors.append(error_msg)
                print(f"      ✗ Failed to queue notification")

    print(f"\n{'[DRY RUN] Would have queued' if dry_run else 'Queued'} {notifications_queued} notifications")
    if errors:
        print(f"Encountered {len(errors)} errors")

    return notifications_queued, errors


def main():
    start_time = datetime.now()

    print("\n" + "="*70)
    print("DETECT NEW FILINGS & QUEUE NOTIFICATIONS")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    lookback_hours = 24

    for arg in sys.argv[1:]:
        if arg.startswith('--lookback'):
            try:
                lookback_days = int(sys.argv[sys.argv.index(arg) + 1])
                lookback_hours = lookback_days * 24
            except:
                pass

    if dry_run:
        print("Mode: DRY RUN (no notifications will be queued)")
    else:
        print("Mode: LIVE (notifications will be queued)")

    # Process new filings
    notifications_queued, errors = process_new_filings(
        dry_run=dry_run,
        lookback_hours=lookback_hours
    )

    # Calculate duration
    duration = int((datetime.now() - start_time).total_seconds())

    # Final summary
    print("\n" + "="*70)
    print("DETECTION COMPLETE")
    print(f"Duration: {duration} seconds")
    print(f"Notifications queued: {notifications_queued}")
    print(f"Errors: {len(errors)}")
    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
