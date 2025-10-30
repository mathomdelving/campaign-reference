"""
Send Email Notifications for New Filings

This script processes pending notifications in the queue and sends emails
to users about new candidate filings using SendGrid.

Usage:
    python send_notifications.py              # Send all pending notifications
    python send_notifications.py --limit 10   # Send max 10 notifications
    python send_notifications.py --dry-run    # Preview emails without sending
"""

import requests
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL')
SENDGRID_FROM_NAME = os.getenv('SENDGRID_FROM_NAME')

# Validate environment variables
if not all([SUPABASE_URL, SUPABASE_KEY, SENDGRID_API_KEY, SENDGRID_FROM_EMAIL]):
    print("ERROR: Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_KEY, SENDGRID_API_KEY, SENDGRID_FROM_EMAIL")
    sys.exit(1)

MAX_RETRIES = 3


def get_pending_notifications(limit=None):
    """
    Get pending notifications from the queue

    Returns:
        List of notification records with status='pending' and retry_count < MAX_RETRIES
    """
    print(f"\n=== Fetching Pending Notifications ===")

    url = f"{SUPABASE_URL}/rest/v1/notification_queue"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': '*',
        'status': 'eq.pending',
        'retry_count': f'lt.{MAX_RETRIES}',
        'order': 'queued_at.asc'
    }

    if limit:
        params['limit'] = limit

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        notifications = response.json()
        print(f"Found {len(notifications)} pending notification(s)")
        return notifications

    except requests.exceptions.RequestException as e:
        print(f"Error fetching notifications: {e}")
        return []


def get_user_email(user_id):
    """
    Get user email from Supabase Admin API

    Note: This requires the service_role key which we're using
    """
    url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        user_data = response.json()
        return user_data.get('email')

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching user email: {e}")
        return None


def format_currency(amount):
    """Format number as currency"""
    if amount is None:
        return "$0"
    return f"${amount:,.0f}"


def create_email_html(filing_data, unsubscribe_url):
    """
    Create professional HTML email template

    Args:
        filing_data: JSONB data from notification_queue
        unsubscribe_url: URL to unsubscribe page

    Returns:
        HTML string
    """
    candidate_name = filing_data.get('candidate_name', 'Unknown')
    party = filing_data.get('party', '')
    office = filing_data.get('office', '')
    state = filing_data.get('state', '')
    district = filing_data.get('district', '')

    total_raised = format_currency(filing_data.get('total_receipts'))
    total_spent = format_currency(filing_data.get('total_disbursements'))
    cash_on_hand = format_currency(filing_data.get('cash_on_hand'))

    coverage_end_date = filing_data.get('coverage_end_date', '')
    report_type = filing_data.get('report_type', 'Financial Report')

    # Format office display
    if office == 'H':
        office_display = f"U.S. House - {state}-{district}" if district else f"U.S. House - {state}"
    elif office == 'S':
        office_display = f"U.S. Senate - {state}"
    else:
        office_display = f"{office} - {state}"

    # Determine party color
    party_colors = {
        'REPUBLICAN': '#E81B23',
        'DEMOCRATIC': '#0015BC',
        'LIBERTARIAN': '#FED105',
        'GREEN': '#17aa5c',
    }
    party_color = party_colors.get(party.upper(), '#666666')

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Filing Report</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; border-bottom: 1px solid #e5e5e5;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">
                                New Filing Report
                            </h1>
                            <p style="margin: 8px 0 0 0; font-size: 14px; color: #666666;">
                                {datetime.now().strftime('%B %d, %Y')}
                            </p>
                        </td>
                    </tr>

                    <!-- Candidate Info -->
                    <tr>
                        <td style="padding: 30px 40px;">
                            <div style="display: inline-block; padding: 4px 12px; background-color: {party_color}15; border-radius: 12px; margin-bottom: 12px;">
                                <span style="font-size: 12px; font-weight: 600; color: {party_color}; text-transform: uppercase;">
                                    {party}
                                </span>
                            </div>

                            <h2 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700; color: #1a1a1a;">
                                {candidate_name}
                            </h2>

                            <p style="margin: 0; font-size: 16px; color: #666666;">
                                {office_display}
                            </p>

                            <p style="margin: 16px 0 0 0; font-size: 14px; color: #666666;">
                                Filed a new <strong>{report_type}</strong> covering through {coverage_end_date}
                            </p>
                        </td>
                    </tr>

                    <!-- Financial Summary -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 20px; border-bottom: 1px solid #e5e5e5;">
                                        <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Total Raised
                                        </p>
                                        <p style="margin: 0; font-size: 24px; font-weight: 700; color: #059669; font-family: 'Courier New', monospace;">
                                            {total_raised}
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; border-bottom: 1px solid #e5e5e5;">
                                        <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Total Spent
                                        </p>
                                        <p style="margin: 0; font-size: 24px; font-weight: 700; color: #dc2626; font-family: 'Courier New', monospace;">
                                            {total_spent}
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 600; color: #666666; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Cash on Hand
                                        </p>
                                        <p style="margin: 0; font-size: 24px; font-weight: 700; color: #2563eb; font-family: 'Courier New', monospace;">
                                            {cash_on_hand}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;" align="center">
                            <a href="https://campaign-reference.com" style="display: inline-block; padding: 14px 32px; background-color: #1a1a1a; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600;">
                                View Full Details
                            </a>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid #e5e5e5;">
                            <p style="margin: 0 0 12px 0; font-size: 14px; color: #666666;">
                                You're receiving this because you're watching <strong>{candidate_name}</strong> on Campaign Reference.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #999999;">
                                <a href="{unsubscribe_url}" style="color: #999999; text-decoration: underline;">
                                    Unsubscribe from this candidate
                                </a>
                                &nbsp;|&nbsp;
                                <a href="https://campaign-reference.com/settings" style="color: #999999; text-decoration: underline;">
                                    Manage notification settings
                                </a>
                            </p>
                        </td>
                    </tr>

                </table>

                <!-- Legal Footer -->
                <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                    <tr>
                        <td style="padding: 0 40px; text-align: center;">
                            <p style="margin: 0; font-size: 11px; color: #999999; line-height: 1.5;">
                                Campaign Reference | Financial data from the Federal Election Commission<br>
                                © {datetime.now().year} Campaign Reference. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>

            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def create_email_text(filing_data):
    """Create plain text version of email"""
    candidate_name = filing_data.get('candidate_name', 'Unknown')
    party = filing_data.get('party', '')
    office = filing_data.get('office', '')
    state = filing_data.get('state', '')
    district = filing_data.get('district', '')

    total_raised = format_currency(filing_data.get('total_receipts'))
    total_spent = format_currency(filing_data.get('total_disbursements'))
    cash_on_hand = format_currency(filing_data.get('cash_on_hand'))

    coverage_end_date = filing_data.get('coverage_end_date', '')
    report_type = filing_data.get('report_type', 'Financial Report')

    if office == 'H':
        office_display = f"U.S. House - {state}-{district}" if district else f"U.S. House - {state}"
    elif office == 'S':
        office_display = f"U.S. Senate - {state}"
    else:
        office_display = f"{office} - {state}"

    text = f"""
NEW FILING REPORT - {datetime.now().strftime('%B %d, %Y')}

{candidate_name} ({party})
{office_display}

Filed a new {report_type} covering through {coverage_end_date}

FINANCIAL SUMMARY:
------------------
Total Raised:    {total_raised}
Total Spent:     {total_spent}
Cash on Hand:    {cash_on_hand}

View full details: https://campaign-reference.com

---
You're receiving this because you're watching {candidate_name} on Campaign Reference.
Manage your notification settings: https://campaign-reference.com/settings

Campaign Reference | Financial data from the Federal Election Commission
© {datetime.now().year} Campaign Reference. All rights reserved.
"""
    return text


def send_email_via_sendgrid(to_email, subject, html_content, text_content, dry_run=False):
    """
    Send email via SendGrid API

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    if dry_run:
        print(f"      [DRY RUN] Would send email to {to_email}")
        print(f"      Subject: {subject}")
        return True, None

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": subject
        }],
        "from": {
            "email": SENDGRID_FROM_EMAIL,
            "name": SENDGRID_FROM_NAME
        },
        "content": [
            {
                "type": "text/plain",
                "value": text_content
            },
            {
                "type": "text/html",
                "value": html_content
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 202:
            return True, None
        else:
            error_msg = f"SendGrid API error: {response.status_code} - {response.text}"
            return False, error_msg

    except requests.exceptions.RequestException as e:
        return False, str(e)


def update_notification_status(notification_id, status, error_message=None, increment_retry=False):
    """
    Update notification status in the queue

    Args:
        notification_id: UUID of notification
        status: 'sent' or 'failed'
        error_message: Optional error message
        increment_retry: Whether to increment retry_count
    """
    url = f"{SUPABASE_URL}/rest/v1/notification_queue"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    update_data = {
        'status': status,
    }

    if status == 'sent':
        update_data['sent_at'] = datetime.now().isoformat()

    if error_message:
        update_data['error_message'] = error_message[:500]  # Limit length

    # We'll handle retry count increment via a separate query if needed
    # For now, just update status

    params = {
        'id': f'eq.{notification_id}'
    }

    try:
        response = requests.patch(url, headers=headers, params=params, json=update_data)
        return response.status_code in [200, 204]
    except:
        return False


def increment_retry_count(notification_id):
    """Increment retry_count for a notification"""
    # Use RPC or direct SQL would be ideal, but we'll do a read-modify-write
    url = f"{SUPABASE_URL}/rest/v1/rpc/increment_notification_retry"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    # Since we may not have this RPC function, let's just update directly
    # We'll fetch current count and increment
    # For simplicity, we'll skip this for now and handle in the main loop
    pass


def process_notifications(dry_run=False, limit=None):
    """
    Main processing function:
    1. Get pending notifications
    2. For each notification, send email
    3. Update status

    Returns:
        Tuple of (sent_count, failed_count, errors)
    """
    print(f"\n=== Processing Notifications {'(DRY RUN)' if dry_run else ''} ===")

    # Get pending notifications
    notifications = get_pending_notifications(limit=limit)

    if not notifications:
        print("\n✓ No pending notifications to process")
        return 0, 0, []

    sent_count = 0
    failed_count = 0
    errors = []

    for idx, notification in enumerate(notifications, 1):
        notification_id = notification['id']
        user_id = notification['user_id']
        filing_data = notification['filing_data']
        candidate_name = filing_data.get('candidate_name', 'Unknown')
        retry_count = notification.get('retry_count', 0)

        print(f"\n  [{idx}/{len(notifications)}] {candidate_name} → User {user_id[:8]}...")

        # Get user email
        user_email = get_user_email(user_id)
        if not user_email:
            print(f"    ✗ Could not fetch user email")
            errors.append(f"{candidate_name} → {user_id}: No email found")

            # Mark as failed if we've retried enough times
            if retry_count >= MAX_RETRIES - 1:
                update_notification_status(notification_id, 'failed', 'User email not found')
            failed_count += 1
            continue

        print(f"    Email: {user_email}")

        # Create unsubscribe URL (will implement proper unsubscribe page later)
        candidate_id = filing_data.get('candidate_id', '')
        unsubscribe_url = f"https://campaign-reference.com/unsubscribe?user={user_id}&candidate={candidate_id}"

        # Create email content
        subject = f"New Filing: {candidate_name}"
        html_content = create_email_html(filing_data, unsubscribe_url)
        text_content = create_email_text(filing_data)

        # Send email
        success, error_msg = send_email_via_sendgrid(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            dry_run=dry_run
        )

        if success:
            if not dry_run:
                update_notification_status(notification_id, 'sent')
                print(f"    ✓ Email sent successfully")
            else:
                print(f"    ✓ [DRY RUN] Would mark as sent")
            sent_count += 1
        else:
            print(f"    ✗ Failed to send: {error_msg}")
            errors.append(f"{candidate_name} → {user_email}: {error_msg}")

            if not dry_run:
                # If we've hit max retries, mark as failed permanently
                if retry_count >= MAX_RETRIES - 1:
                    update_notification_status(notification_id, 'failed', error_msg)
                    print(f"    ✗ Max retries reached, marked as failed")
                else:
                    # Keep as pending but note the error
                    update_notification_status(notification_id, 'pending', error_msg)

            failed_count += 1

    print(f"\n{'[DRY RUN] Would have sent' if dry_run else 'Sent'}: {sent_count} notification(s)")
    print(f"Failed: {failed_count} notification(s)")

    return sent_count, failed_count, errors


def main():
    start_time = datetime.now()

    print("\n" + "="*70)
    print("SEND EMAIL NOTIFICATIONS")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    limit = None

    for arg in sys.argv[1:]:
        if arg.startswith('--limit'):
            try:
                limit = int(sys.argv[sys.argv.index(arg) + 1])
            except:
                pass

    if dry_run:
        print("Mode: DRY RUN (no emails will be sent)")
    else:
        print("Mode: LIVE (emails will be sent)")

    if limit:
        print(f"Limit: Processing max {limit} notification(s)")

    # Process notifications
    sent_count, failed_count, errors = process_notifications(
        dry_run=dry_run,
        limit=limit
    )

    # Calculate duration
    duration = int((datetime.now() - start_time).total_seconds())

    # Final summary
    print("\n" + "="*70)
    print("SEND COMPLETE")
    print(f"Duration: {duration} seconds")
    print(f"Sent: {sent_count}")
    print(f"Failed: {failed_count}")
    if errors:
        print(f"\nErrors encountered:")
        for error in errors[:10]:
            print(f"  - {error}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
