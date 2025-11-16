#!/usr/bin/env python3
"""
Detect New FEC Filings and Queue Notifications

This script continuously monitors the FEC API for new candidate filings and
creates notification queue entries for users who are following those candidates.

Designed for 7,000 requests/hour rate limit (currently testing at 1,000/hour).

Usage:
    python detect_new_filings.py                # Run continuously
    python detect_new_filings.py --once         # Check once and exit
    python detect_new_filings.py --dry-run      # Preview without creating notifications
    python detect_new_filings.py --interval 60  # Check every 60 seconds (default: 30)

Filing Day Strategy:
    - Poll bulk /filings/ endpoint every 30 seconds (designed for 7k/hour)
    - Uses only ~120 requests/hour for polling
    - Leaves 6,880 requests/hour for detail fetches if needed
    - Detection latency: ~15-45 seconds from filing to notification queued
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
POLL_INTERVAL_SECONDS = 30  # How often to check for new filings (optimized for 7k/hour)
LOOKBACK_HOURS = 1  # How far back to look for new filings on each check
MAX_FILINGS_PER_CHECK = 100  # Limit results per API call

# Rate limit awareness
REQUESTS_PER_HOUR_LIMIT = 7000  # Target rate limit (currently 1000 for testing)
CURRENT_RATE_LIMIT = 1000  # SET THIS TO YOUR CURRENT LIMIT FOR TESTING

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


def check_new_filings(since_date):
    """
    Check FEC API for new filings since the given date.

    Uses the bulk /filings/ endpoint to get all new filings in one request.

    Args:
        since_date: ISO format date string (YYYY-MM-DD)

    Returns:
        list: Filing records from FEC API
    """
    url = "https://api.open.fec.gov/v1/filings/"

    params = {
        'api_key': FEC_API_KEY,
        'min_receipt_date': since_date,
        'sort': '-receipt_date',  # Newest first
        'per_page': MAX_FILINGS_PER_CHECK,
        'form_type': ['F3', 'F3P', 'F3X'],  # Only financial reports
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        return results

    except requests.exceptions.RequestException as e:
        print(f"⚠️  Error fetching filings from FEC: {e}")
        return []


def get_candidate_financial_summary(candidate_id, cycle):
    """
    Get latest financial summary for a candidate.

    This data will be included in the notification email.

    Args:
        candidate_id: FEC candidate ID
        cycle: Election cycle (e.g., 2024, 2026)

    Returns:
        dict: Financial summary data or None
    """
    url = f"{SUPABASE_URL}/rest/v1/financial_summary"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'total_receipts,total_disbursements,cash_on_hand,coverage_end_date,report_type',
        'candidate_id': f'eq.{candidate_id}',
        'cycle': f'eq.{cycle}',
        'limit': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        results = response.json()
        return results[0] if results else None

    except Exception as e:
        print(f"    ⚠️  Could not fetch financial summary: {e}")
        return None


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

    Args:
        filing: Filing record from FEC API
        followed_candidates: Dict of candidate_id -> list of followers
        dry_run: If True, preview without creating notifications

    Returns:
        int: Number of notifications created
    """
    candidate_id = filing.get('candidate_id')

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
    coverage_end_date = filing.get('coverage_end_date', '')

    # Get latest financial summary
    cycle = filing.get('cycle', datetime.now().year)
    financial_summary = get_candidate_financial_summary(candidate_id, cycle)

    # Build filing data for email
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
        'total_receipts': financial_summary.get('total_receipts') if financial_summary else None,
        'total_disbursements': financial_summary.get('total_disbursements') if financial_summary else None,
        'cash_on_hand': financial_summary.get('cash_on_hand') if financial_summary else None,
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


def run_check(dry_run=False):
    """
    Run a single check for new filings.

    Returns:
        Tuple of (filings_found, notifications_created)
    """
    print(f"\n{'='*80}")
    print(f"CHECKING FOR NEW FILINGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("[DRY RUN MODE - No notifications will be created]")
    print(f"{'='*80}")

    # Get candidates with followers
    print("\n1. Fetching followed candidates...")
    followed_candidates = get_followed_candidates()

    if not followed_candidates:
        print("   ℹ️  No candidates are being followed with notifications enabled")
        return 0, 0

    print(f"   ✓ {len(followed_candidates)} candidates are being watched by users")

    # Calculate lookback time
    lookback_time = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
    since_date = lookback_time.strftime('%Y-%m-%d')

    print(f"\n2. Checking FEC for filings since {since_date}...")
    filings = check_new_filings(since_date)

    if not filings:
        print("   ℹ️  No new filings found")
        return 0, 0

    print(f"   ✓ Found {len(filings)} new filing(s)")

    # Process each filing
    print(f"\n3. Processing filings and creating notifications...")

    total_notifications = 0
    filings_with_followers = 0

    for filing in filings:
        candidate_id = filing.get('candidate_id')
        candidate_name = filing.get('candidate_name', candidate_id)
        receipt_date = filing.get('receipt_date', '')

        # Only process if someone is following this candidate
        if candidate_id in followed_candidates:
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
            filings_with_followers += 1

    print(f"\n{'='*80}")
    print(f"CHECK COMPLETE")
    print(f"{'='*80}")
    print(f"New filings found: {len(filings)}")
    print(f"Filings with followers: {filings_with_followers}")
    print(f"{'Notifications that would be created' if dry_run else 'Notifications created'}: {total_notifications}")
    print(f"{'='*80}\n")

    return len(filings), total_notifications


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
                print(f"⚠️  Invalid interval value, using default: {POLL_INTERVAL_SECONDS}s")

    print("\n" + "="*80)
    print("FEC FILING DETECTION SERVICE")
    print("="*80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Run: {'ONCE' if run_once else 'CONTINUOUS'}")
    print(f"Interval: {interval} seconds")
    print(f"Lookback: {LOOKBACK_HOURS} hour(s)")
    print(f"Rate limit: {CURRENT_RATE_LIMIT}/hour (designed for {REQUESTS_PER_HOUR_LIMIT}/hour)")

    if CURRENT_RATE_LIMIT < REQUESTS_PER_HOUR_LIMIT:
        print(f"\n⚠️  WARNING: Currently testing at {CURRENT_RATE_LIMIT}/hour rate limit")
        print(f"   Polling every {interval}s uses ~{3600//interval} requests/hour")
        print(f"   You have capacity for this. Upgrade to 7k/hour for production use.")

    print("="*80)

    if run_once:
        # Run once and exit
        run_check(dry_run=dry_run)
    else:
        # Run continuously
        print(f"\n▶️  Starting continuous monitoring (Ctrl+C to stop)...")
        print(f"   Checking every {interval} seconds\n")

        try:
            while True:
                run_check(dry_run=dry_run)

                print(f"⏳ Waiting {interval} seconds until next check...\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✋ Stopped by user")
            print("="*80)
            sys.exit(0)


if __name__ == "__main__":
    main()
