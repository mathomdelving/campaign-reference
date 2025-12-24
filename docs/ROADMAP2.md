# Campaign Reference - Development Roadmap Phase 2

**Project:** Campaign Reference - Next Generation Features
**Status:** 🚧 Planning Phase
**Start Date:** October 2025
**Target Users:** Political journalists, campaign operatives, political observers

---

## Executive Summary

This roadmap outlines the next phase of Campaign Reference development, transforming it from a static data visualization tool into a **dynamic, notification-driven platform** that delivers campaign finance intelligence directly to users when it matters most.

### Strategic Vision

**Current State:** Users visit the site to check campaign finance data
**Future State:** Users receive instant alerts when candidates they follow file new reports, making Campaign Reference an essential daily tool for political professionals

### Core Improvements

1. **User Registration & Notifications** - The killer feature that creates daily engagement
2. **Enhanced Data Depth** - Historical cycles and quarterly visibility
3. **Shareable Visualizations** - Beautiful, social-media-ready charts

---

## Table of Contents

1. [Phase 1: User Registration & Notifications](#phase-1-user-registration--notifications)
2. [Phase 2: Data Enhancement](#phase-2-data-enhancement)
3. [Phase 3: Visual Excellence](#phase-3-visual-excellence)
4. [Technical Architecture](#technical-architecture)
5. [Success Metrics](#success-metrics)
6. [Risk Management](#risk-management)

---

## Phase 1: User Registration & Notifications

**Status:** ✅ COMPLETE (Completed October 30, 2025)
**Priority:** 🔴 CRITICAL - This is the primary value proposition
**Duration:** 3 weeks (Actual: 2 weeks)
**Complexity:** High
**Dependencies:** None

### Overview

Build a complete user authentication and notification system that allows users to follow specific candidates and receive email alerts when new finance reports are filed.

### Why This Matters

- **Journalists on deadline** need instant alerts when reports drop (timing is everything)
- **Campaign operatives** monitor opponent fundraising in real-time (competitive intelligence)
- **Political observers** track races without manually checking daily
- **No competing product** offers FEC filing notifications for specific candidates
- **Daily engagement** creates habit formation and user retention

---

### Part 1A: Authentication System

**Duration:** 3-4 days
**Complexity:** Medium

#### Technical Implementation

**Backend: Supabase Auth**
- Use existing Supabase instance (no new service needed)
- Enable Email Auth in Supabase dashboard
- Configure email templates (welcome, password reset, confirmation)
- Set up Row Level Security (RLS) policies

**Frontend Components to Build:**

```
src/components/auth/
├── LoginModal.jsx           // Email/password login form
├── SignUpModal.jsx          // New user registration
├── AuthButton.jsx           // Login/Logout button in nav
├── UserMenu.jsx             // Dropdown: Profile, Settings, Logout
├── ProtectedRoute.jsx       // HOC for authenticated-only pages
└── AuthContext.jsx          // React Context for auth state

src/views/
├── UserProfile.jsx          // User dashboard & settings
└── NotificationSettings.jsx // Email preferences
```

#### Database Schema

```sql
-- Supabase Auth handles users table automatically
-- We'll reference auth.users(id) in our tables

-- Optional: Extended user profile
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  organization TEXT,
  role TEXT, -- journalist, operative, researcher, enthusiast
  created_at TIMESTAMP DEFAULT NOW(),
  last_active TIMESTAMP DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id);
```

#### User Experience Flow

1. **New User Journey:**
   - User clicks "Sign Up" in nav bar
   - Modal appears: Email + Password + Confirm Password
   - User receives email verification link
   - User clicks link → Account confirmed → Auto-login
   - Redirects to profile page with "Follow candidates to get started"

2. **Returning User Journey:**
   - User clicks "Log In" in nav bar
   - Modal appears: Email + Password
   - Successful login → Modal closes, nav updates to show user menu
   - User sees "Following: 5 candidates" badge

3. **Forgot Password Flow:**
   - Link in login modal
   - Enter email → Receive reset link
   - Click link → Enter new password → Success

#### Key Questions & Decision Points

**Q1: What authentication methods should we support?**

| Method | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| Email/Password | Simple, no OAuth setup, works for all users | Requires password management | ✅ **Start here** |
| Google OAuth | Fast signup, no password to remember | Requires OAuth setup | 🟡 Add later if requested |
| Twitter/X OAuth | Relevant for journalist users | Complex setup, API costs | 🔴 Skip for now |
| Magic Links | Passwordless, secure | Requires email every login | 🟡 Consider for Phase 1.1 |

**Recommendation:** Start with email/password. Add Google OAuth in Phase 1.1 if users request it.

**Q2: Email verification - required or optional?**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| Required | Verified emails, better deliverability | Friction in signup flow | ✅ **Recommended** |
| Optional | Faster signup, less friction | Fake emails, bounces | 🔴 Not recommended |

**Recommendation:** Require email verification. Use Supabase's built-in verification system.

**Q3: User profile - minimal or detailed?**

**Option A: Minimal (Email only)**
- Fastest to implement
- No extra UI needed
- Good for MVP

**Option B: Extended Profile (Name, Organization, Role)**
- Better personalization
- Helps understand user base
- Can segment notifications later

**Recommendation:** Start minimal (Option A). Add extended profile in Part 1B after core auth works.

#### Testing Checklist

- [ ] User can sign up with email/password
- [ ] Verification email is sent and received
- [ ] User can verify email and auto-login
- [ ] User can log in with credentials
- [ ] User can log out
- [ ] User can reset forgotten password
- [ ] Session persists across page reloads
- [ ] Logged-in state shows in nav bar
- [ ] Protected routes redirect to login if not authenticated

#### Success Criteria

- ✅ 100% of signups receive verification email within 60 seconds
- ✅ Login/logout works without errors
- ✅ Session persists for 7 days (Supabase default)
- ✅ Password reset flow completes successfully
- ✅ Mobile responsive design

---

### Part 1B: Follow Candidate System

**Duration:** 2-3 days
**Complexity:** Medium

#### Technical Implementation

**Database Schema:**

```sql
CREATE TABLE user_candidate_follows (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  candidate_id TEXT NOT NULL,

  -- Cached candidate info for display (denormalized for performance)
  candidate_name TEXT NOT NULL,
  party TEXT,
  office TEXT NOT NULL,  -- 'H' or 'S'
  state TEXT NOT NULL,
  district TEXT,

  -- Notification preferences
  notification_enabled BOOLEAN DEFAULT TRUE,

  -- Metadata
  followed_at TIMESTAMP DEFAULT NOW(),
  last_notification_sent TIMESTAMP,

  -- Constraints
  UNIQUE(user_id, candidate_id)
);

-- Indexes for performance
CREATE INDEX idx_follows_user ON user_candidate_follows(user_id);
CREATE INDEX idx_follows_candidate ON user_candidate_follows(candidate_id);
CREATE INDEX idx_follows_notifications ON user_candidate_follows(user_id, notification_enabled);

-- Row Level Security
ALTER TABLE user_candidate_follows ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own follows"
  ON user_candidate_follows FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own follows"
  ON user_candidate_follows FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own follows"
  ON user_candidate_follows FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own follows"
  ON user_candidate_follows FOR UPDATE
  USING (auth.uid() = user_id);
```

**Frontend Components to Build:**

```
src/components/follow/
├── FollowButton.jsx         // Heart icon, toggle follow/unfollow
├── FollowingList.jsx        // Show all followed candidates
├── FollowingCount.jsx       // Badge: "Following: 12"
└── BulkFollowModal.jsx      // Follow multiple candidates at once
```

#### Component Specifications

**FollowButton.jsx:**
```jsx
/**
 * Props:
 * - candidateId: string (required)
 * - candidateName: string (required)
 * - party: string
 * - office: string (required)
 * - state: string (required)
 * - district: string (optional)
 * - size: 'sm' | 'md' | 'lg' (default: 'md')
 * - showLabel: boolean (default: false)
 *
 * States:
 * - Following: solid heart, "Following" label
 * - Not Following: outline heart, "Follow" label
 * - Loading: spinner
 *
 * Behavior:
 * - Requires authentication (shows login modal if not logged in)
 * - Optimistic UI update (instant feedback)
 * - Toasts on success/error
 */
```

**Where to Add Follow Buttons:**
- RaceTable.jsx - Heart icon in each row
- CandidateView.jsx - Next to each selected candidate
- DistrictView.jsx - Next to each candidate in the race
- QuarterlyChart.jsx - In legend next to candidate names

#### User Experience Flow

**Following a Candidate:**
1. User sees heart icon next to candidate name
2. User clicks heart
3. If not logged in → Login modal appears → After login, auto-follow
4. If logged in → Instant visual feedback (heart fills) + Toast: "Following Rep. Jane Smith"
5. Follow count badge updates: "Following: 6 candidates"

**Unfollowing a Candidate:**
1. User clicks filled heart
2. Confirmation dialog: "Stop following Rep. Jane Smith?"
3. User confirms → Heart outline + Toast: "No longer following"
4. Follow count updates

**Managing Follows:**
1. User clicks profile menu → "Following" (or "Profile")
2. Sees list of all followed candidates with:
   - Name, party, location
   - Last filing date
   - "View" and "Unfollow" buttons
   - Notification toggle per candidate
3. Can bulk unfollow or change notification settings

#### Key Questions & Decision Points

**Q1: Follow limit - should we impose one?**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| No limit | Maximum flexibility | Notification overload risk | 🟡 Monitor and decide |
| Soft limit (50-100) | Encourages focus | May frustrate power users | ✅ **Start with 50** |
| Hard limit (25) | Prevents spam/abuse | Too restrictive | 🔴 Too low |

**Recommendation:** Start with 50 candidate limit. Show warning at 40. Can increase based on usage patterns.

**Q2: Notification preferences - granular or binary?**

**Option A: Binary (On/Off per candidate)**
- Simple UI
- Easy to understand
- Quick to implement

**Option B: Granular (Email, Push, SMS, Frequency)**
- More control for users
- Complex UI
- Requires multiple notification channels

**Recommendation:** Start with Option A (binary on/off). Add granularity in Phase 1.1 based on feedback.

**Q3: Import follows from list - should we support it?**

**Use Case:** User has a CSV of candidates they want to follow

**Option A: Manual Follow Only**
- Simpler implementation
- More intentional follows

**Option B: Bulk Import Feature**
- Power user feature
- Useful for journalists covering specific races
- Implementation: Parse CSV → Show preview → Confirm → Bulk insert

**Recommendation:** Skip for MVP. Add in Phase 1.1 if requested by early users.

#### Testing Checklist

- [ ] Follow button shows correct state (following vs. not)
- [ ] Click to follow adds record to database
- [ ] Click to unfollow removes record (with confirmation)
- [ ] Follow requires authentication
- [ ] Following count updates correctly
- [ ] Following list shows all followed candidates
- [ ] Notification toggle works per candidate
- [ ] Can unfollow from following list
- [ ] Handles errors gracefully (network issues, etc.)
- [ ] Works on mobile (touch-friendly)

#### Success Criteria

- ✅ Follow/unfollow completes in <500ms
- ✅ Zero database errors during follow operations
- ✅ Following list loads in <1 second for 50 follows
- ✅ Mobile UX feels native (no lag on tap)

---

### Part 1C: New Filing Detection

**Duration:** 2-3 days
**Complexity:** Medium-High

#### Technical Implementation

**New Python Script: `detect_new_filings.py`**

This script runs **after** `incremental_update.py` completes in the GitHub Actions workflow.

**Core Logic:**

```python
#!/usr/bin/env python3
"""
Detect new filings and queue notifications for followed candidates
Runs after incremental_update.py in GitHub Actions workflow

Algorithm:
1. Get all candidates with updated financial data (last 24 hours)
2. For each candidate with new filing:
   a. Find all users following that candidate
   b. Check if we already notified them about this filing
   c. If not, queue a notification
3. Log results for monitoring

Runtime: ~30-60 seconds for typical filing day
"""

import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def detect_new_filings(lookback_hours=24):
    """
    Main function to detect new filings and queue notifications

    Args:
        lookback_hours: How far back to check for new filings (default: 24)
    """

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    print(f"\n{'='*60}")
    print(f"DETECT NEW FILINGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Step 1: Get candidates with recent updates
    cutoff = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()

    new_filings = supabase.table('financial_summary') \
        .select('candidate_id, updated_at, total_receipts, total_disbursements, cash_on_hand') \
        .gte('updated_at', cutoff) \
        .order('updated_at', desc=True) \
        .execute()

    print(f"Found {len(new_filings.data)} candidates with updates in last {lookback_hours}h")

    if not new_filings.data:
        print("No new filings detected. Exiting.")
        return

    total_notifications_queued = 0

    # Step 2: For each candidate with new filing, find followers
    for filing in new_filings.data:
        candidate_id = filing['candidate_id']
        filing_date = filing['updated_at'][:10]  # Extract date portion

        # Get candidate info for notification
        candidate_info = supabase.table('candidates') \
            .select('name, party, office, state, district') \
            .eq('candidate_id', candidate_id) \
            .single() \
            .execute()

        if not candidate_info.data:
            print(f"  ⚠️  Candidate {candidate_id} not found in candidates table")
            continue

        # Get all users following this candidate (with notifications enabled)
        followers = supabase.table('user_candidate_follows') \
            .select('user_id, notification_enabled') \
            .eq('candidate_id', candidate_id) \
            .eq('notification_enabled', True) \
            .execute()

        if not followers.data:
            print(f"  {candidate_info.data['name']}: No followers (skipping)")
            continue

        print(f"\n  {candidate_info.data['name']}:")
        print(f"    Followers: {len(followers.data)}")

        # Step 3: Queue notification for each follower (if not already queued)
        for follower in followers.data:
            # Check if already notified
            existing = supabase.table('notification_queue') \
                .select('id') \
                .eq('user_id', follower['user_id']) \
                .eq('candidate_id', candidate_id) \
                .eq('filing_date', filing_date) \
                .execute()

            if existing.data:
                print(f"    ⚠️  Already queued for user {follower['user_id'][:8]}")
                continue

            # Queue new notification
            notification = {
                'user_id': follower['user_id'],
                'candidate_id': candidate_id,
                'filing_date': filing_date,
                'filing_data': {
                    'name': candidate_info.data['name'],
                    'party': candidate_info.data['party'],
                    'office': candidate_info.data['office'],
                    'state': candidate_info.data['state'],
                    'district': candidate_info.data['district'],
                    'total_receipts': filing['total_receipts'],
                    'total_disbursements': filing['total_disbursements'],
                    'cash_on_hand': filing['cash_on_hand'],
                    'updated_at': filing['updated_at']
                },
                'status': 'pending'
            }

            supabase.table('notification_queue').insert(notification).execute()
            total_notifications_queued += 1
            print(f"    ✓ Queued for user {follower['user_id'][:8]}")

    print(f"\n{'='*60}")
    print(f"✅ Detection complete: {total_notifications_queued} notifications queued")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--lookback', type=int, default=24,
                       help='Hours to look back for new filings')
    args = parser.parse_args()

    detect_new_filings(lookback_hours=args.lookback)
```

**Database Schema:**

```sql
CREATE TABLE notification_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Who and what
  user_id UUID NOT NULL,
  candidate_id TEXT NOT NULL,
  filing_date DATE NOT NULL,

  -- Snapshot of filing data (denormalized for email content)
  filing_data JSONB NOT NULL,

  -- Status tracking
  status TEXT DEFAULT 'pending', -- pending, sent, failed
  queued_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  error_message TEXT,
  retry_count INT DEFAULT 0,

  -- Prevent duplicate notifications
  UNIQUE(user_id, candidate_id, filing_date)
);

-- Indexes
CREATE INDEX idx_queue_status ON notification_queue(status);
CREATE INDEX idx_queue_user ON notification_queue(user_id);
CREATE INDEX idx_queue_date ON notification_queue(queued_at);

-- Cleanup old notifications after 30 days
CREATE INDEX idx_queue_cleanup ON notification_queue(sent_at) WHERE sent_at IS NOT NULL;
```

#### Key Questions & Decision Points

**Q1: When should we detect new filings?**

| Timing | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| Immediately after incremental update | Fastest notifications | Complex error handling | ✅ **Best for users** |
| On separate schedule | Simpler error handling | Delayed notifications | 🟡 Fallback option |

**Recommendation:** Run immediately after `incremental_update.py` succeeds. If it fails, notifications wait until next successful update.

**Q2: What if a user follows a candidate AFTER their filing?**

**Scenario:**
- Rep. Smith files report on Monday at 10 AM
- User follows Rep. Smith on Tuesday
- Should user receive Monday's filing notification?

**Option A: Only notify about NEW filings after follow**
- No backfill notifications
- Cleaner logic
- User missed the filing

**Option B: Backfill recent filings (last 7 days)**
- User gets context on recent activity
- More complex logic
- Could feel spammy

**Recommendation:** Option A for MVP. Consider Option B in Phase 1.1 if users request it.

**Q3: How do we handle filing corrections/amendments?**

**Scenario:** Candidate files report, then files amendment same day

**Option A: Send notification for each filing**
- Complete information
- Risk of spam

**Option B: Dedupe by filing_date**
- One notification per day per candidate
- Might miss important amendments

**Option C: Smart deduping (only if material change)**
- Best user experience
- Complex logic

**Recommendation:** Start with Option B (dedupe by date). Add Option C in Phase 1.1 if amendments become common.

#### Testing Checklist

- [ ] Script detects new filings in last 24 hours
- [ ] Correctly identifies all followers of each candidate
- [ ] Deduplicates notifications (no duplicate queue entries)
- [ ] Handles candidates with no followers gracefully
- [ ] Handles candidates not in candidates table gracefully
- [ ] Logs clear output for monitoring
- [ ] Runs in <60 seconds for typical filing day
- [ ] Can run with custom lookback period (--lookback flag)

#### Success Criteria

- ✅ 100% of new filings detected within 30 minutes
- ✅ Zero duplicate notifications queued
- ✅ Runs without errors even if 500+ candidates file
- ✅ Clear logs for debugging

---

### Part 1D: Email Notification System

**Duration:** 3-4 days
**Complexity:** Medium-High

#### Technical Implementation

**Email Service: SendGrid**

**Why SendGrid?**
- Free tier: 100 emails/day forever
- Excellent deliverability
- Simple API
- Good analytics dashboard
- Scales to paid plans easily

**Setup Steps:**
1. Create SendGrid account at sendgrid.com
2. Verify sender email: `noreply@campaign-reference.com`
3. Set up domain authentication (SPF/DKIM records) for better deliverability
4. Get API key
5. Add to GitHub Secrets: `SENDGRID_API_KEY`

**New Python Script: `send_notifications.py`**

```python
#!/usr/bin/env python3
"""
Send queued email notifications
Runs after detect_new_filings.py in GitHub Actions

Process:
1. Get pending notifications from queue (limit to 90 for free tier)
2. For each notification:
   a. Get user email from Supabase Auth
   b. Compose email with filing data
   c. Send via SendGrid
   d. Mark as sent or failed
3. Log results

Runtime: ~1-2 minutes for 90 emails
"""

import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def format_currency(amount):
    """Format dollar amounts for display"""
    if amount is None:
        return "N/A"
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    else:
        return f"${amount:,.0f}"

def get_location_string(office, state, district):
    """Format location for display"""
    if office == 'S':
        return f"{state} Senate"
    else:
        if district:
            return f"{state}-{district}"
        return f"{state} House"

def compose_email(user_email, notification_data):
    """
    Compose email notification

    Returns: Mail object ready to send
    """

    filing = notification_data['filing_data']
    candidate_name = filing['name']
    location = get_location_string(filing['office'], filing['state'], filing.get('district'))

    # Build subject line
    subject = f"🔔 New Filing: {candidate_name} ({location})"

    # Build email body
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                 line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                    color: white; padding: 24px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">
                New Campaign Finance Report Filed
            </h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">
                Campaign Reference
            </p>
        </div>

        <!-- Main Content -->
        <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none;">

            <!-- Candidate Info -->
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h2 style="margin: 0 0 8px 0; font-size: 20px; color: #1e3a8a;">
                    {candidate_name}
                </h2>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">
                    {location} • {'Senate' if filing['office'] == 'S' else 'House'} • {filing.get('party', 'Independent')}
                </p>
            </div>

            <!-- Financial Data -->
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #374151; font-weight: 600;">
                    Financial Summary
                </h3>

                <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #6b7280; font-size: 14px;">Total Raised</span>
                        <span style="color: #059669; font-size: 18px; font-weight: 600;">
                            {format_currency(filing.get('total_receipts'))}
                        </span>
                    </div>
                </div>

                <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #6b7280; font-size: 14px;">Total Spent</span>
                        <span style="color: #dc2626; font-size: 18px; font-weight: 600;">
                            {format_currency(filing.get('total_disbursements'))}
                        </span>
                    </div>
                </div>

                <div style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #6b7280; font-size: 14px;">Cash on Hand</span>
                        <span style="color: #1e3a8a; font-size: 18px; font-weight: 600;">
                            {format_currency(filing.get('cash_on_hand'))}
                        </span>
                    </div>
                </div>
            </div>

            <!-- CTA Button -->
            <div style="text-align: center; margin: 24px 0;">
                <a href="https://campaign-reference.com/candidate?id={notification_data['candidate_id']}"
                   style="display: inline-block; background: #1e3a8a; color: white; padding: 14px 32px;
                          text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;
                          box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    View Full Details →
                </a>
            </div>

            <!-- Filing Date -->
            <p style="text-align: center; color: #6b7280; font-size: 13px; margin: 16px 0 0 0;">
                Filed: {filing.get('updated_at', notification_data['filing_date'])}
            </p>
        </div>

        <!-- Footer -->
        <div style="background: #f3f4f6; padding: 20px; border: 1px solid #e5e7eb; border-top: none;
                    border-radius: 0 0 8px 8px; text-align: center;">
            <p style="margin: 0 0 12px 0; color: #6b7280; font-size: 13px;">
                You're receiving this because you follow {candidate_name} on Campaign Reference.
            </p>
            <p style="margin: 0; font-size: 12px;">
                <a href="https://campaign-reference.com/settings"
                   style="color: #3b82f6; text-decoration: none; margin: 0 8px;">
                    Manage Settings
                </a>
                •
                <a href="https://campaign-reference.com/unsubscribe?user_id={notification_data['user_id']}&candidate_id={notification_data['candidate_id']}"
                   style="color: #6b7280; text-decoration: none; margin: 0 8px;">
                    Unfollow {candidate_name}
                </a>
            </p>
            <p style="margin: 16px 0 0 0; color: #9ca3af; font-size: 11px;">
                Campaign Reference • Data from FEC OpenFEC API<br>
                <a href="https://campaign-reference.com" style="color: #9ca3af;">campaign-reference.com</a>
            </p>
        </div>

    </body>
    </html>
    """

    # Plain text version for email clients that don't support HTML
    text_content = f"""
    New Campaign Finance Report Filed

    {candidate_name}
    {location} • {'Senate' if filing['office'] == 'S' else 'House'}

    Financial Summary:
    - Total Raised: {format_currency(filing.get('total_receipts'))}
    - Total Spent: {format_currency(filing.get('total_disbursements'))}
    - Cash on Hand: {format_currency(filing.get('cash_on_hand'))}

    View full details: https://campaign-reference.com/candidate?id={notification_data['candidate_id']}

    Filed: {filing.get('updated_at', notification_data['filing_date'])}

    ---
    You're receiving this because you follow {candidate_name} on Campaign Reference.
    Manage settings: https://campaign-reference.com/settings
    """

    message = Mail(
        from_email=('noreply@campaign-reference.com', 'Campaign Reference'),
        to_emails=user_email,
        subject=subject,
        plain_text_content=text_content,
        html_content=html_content
    )

    return message

def send_notifications(batch_size=90):
    """
    Send pending notifications

    Args:
        batch_size: Number of notifications to process (default: 90 for free tier)
    """

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    sendgrid = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

    print(f"\n{'='*60}")
    print(f"SEND NOTIFICATIONS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Get pending notifications
    pending = supabase.table('notification_queue') \
        .select('*') \
        .eq('status', 'pending') \
        .order('queued_at', desc=False) \
        .limit(batch_size) \
        .execute()

    if not pending.data:
        print("No pending notifications. Exiting.")
        return

    print(f"Processing {len(pending.data)} pending notifications\n")

    sent_count = 0
    failed_count = 0

    for notification in pending.data:
        try:
            # Get user email from Supabase Auth
            # Note: This requires admin access to auth.users
            user = supabase.auth.admin.get_user_by_id(notification['user_id'])

            if not user or not user.email:
                raise Exception(f"User {notification['user_id']} not found or has no email")

            email = user.email

            # Compose email
            message = compose_email(email, notification)

            # Send email
            response = sendgrid.send(message)

            if response.status_code in [200, 201, 202]:
                # Mark as sent
                supabase.table('notification_queue').update({
                    'status': 'sent',
                    'sent_at': datetime.now().isoformat()
                }).eq('id', notification['id']).execute()

                # Update last_notification_sent in follows table
                supabase.table('user_candidate_follows').update({
                    'last_notification_sent': datetime.now().isoformat()
                }).eq('user_id', notification['user_id']) \
                 .eq('candidate_id', notification['candidate_id']) \
                 .execute()

                sent_count += 1
                candidate_name = notification['filing_data']['name']
                print(f"✓ Sent to {email}: {candidate_name}")
            else:
                raise Exception(f"SendGrid returned status {response.status_code}")

        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            print(f"✗ Failed to send to {notification['user_id'][:8]}: {error_msg}")

            # Mark as failed (with retry logic)
            retry_count = notification.get('retry_count', 0) + 1

            if retry_count >= 3:
                # Give up after 3 retries
                status = 'failed'
            else:
                # Will retry next run
                status = 'pending'

            supabase.table('notification_queue').update({
                'status': status,
                'error_message': error_msg,
                'retry_count': retry_count
            }).eq('id', notification['id']).execute()

    print(f"\n{'='*60}")
    print(f"✅ Notification batch complete")
    print(f"   Sent: {sent_count}")
    print(f"   Failed: {failed_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=90,
                       help='Number of notifications to send')
    args = parser.parse_args()

    send_notifications(batch_size=args.batch_size)
```

#### Key Questions & Decision Points

**Q1: What if we hit SendGrid's free tier limit (100/day)?**

**Options:**
- **Option A:** Queue excess notifications for next day (deferred delivery)
- **Option B:** Upgrade to paid plan ($15/month for 40K emails)
- **Option C:** Implement smart batching (most important notifications first)

**Recommendation:** Start with Option A. If we consistently hit limit in first month, upgrade to paid plan (Option B).

**Q2: Should we support "unsubscribe" vs. "unfollow"?**

**Difference:**
- **Unfollow:** Stop following this candidate (can re-follow later)
- **Unsubscribe:** Disable all notifications (nuclear option)

**Recommendation:** Support both:
- "Unfollow [Candidate]" link in each email (removes just that follow)
- "Manage Settings" link to disable all notifications globally

**Q3: Email frequency - should we batch notifications?**

**Scenario:** User follows 20 candidates, 5 file on same day

**Option A: Send 5 separate emails**
- Immediate per-candidate
- Could feel spammy

**Option B: Daily digest email**
- One email with all 5 filings
- Delayed gratification

**Option C: Smart batching (2-hour window)**
- If multiple filings within 2 hours, batch them
- Otherwise send immediately

**Recommendation:** Start with Option A (separate emails). Add digest option in Phase 1.1 as user preference.

**Q4: What metrics should we track?**

**Email Metrics to Monitor:**
- Delivery rate (% delivered successfully)
- Open rate (% opened)
- Click rate (% clicked "View Full Details")
- Unsubscribe rate (% unfollowed or disabled notifications)
- Bounce rate (% bounced)

**SendGrid provides these automatically in dashboard.**

**Additional Custom Metrics:**
```sql
-- Track user engagement
CREATE TABLE notification_analytics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  notification_id UUID REFERENCES notification_queue(id),
  event_type TEXT, -- delivered, opened, clicked, unsubscribed
  event_timestamp TIMESTAMP DEFAULT NOW(),
  user_agent TEXT,
  ip_address TEXT
);
```

**Recommendation:** Start with SendGrid's built-in metrics. Add custom tracking in Phase 1.1 if needed.

#### Testing Checklist

- [ ] SendGrid account set up and verified
- [ ] Domain authentication (SPF/DKIM) configured
- [ ] Test email sends successfully to test account
- [ ] HTML email renders correctly in Gmail, Outlook, Apple Mail
- [ ] Plain text fallback works
- [ ] Currency formatting is correct
- [ ] Candidate links work correctly
- [ ] Unfollow link works
- [ ] Settings link works
- [ ] Script handles SendGrid errors gracefully
- [ ] Script handles user not found gracefully
- [ ] Retry logic works for failed sends
- [ ] Sent notifications are marked correctly in database
- [ ] Can process 90 emails in <2 minutes

#### Success Criteria

- ✅ 99%+ delivery rate (SendGrid dashboard)
- ✅ <5% bounce rate
- ✅ >30% open rate (industry average for notifications)
- ✅ >10% click rate
- ✅ <2% unsubscribe rate
- ✅ All emails sent within 5 minutes of queueing

---

### Part 1E: GitHub Actions Integration

**Duration:** 1 day
**Complexity:** Low

#### Implementation

Update `.github/workflows/incremental-update.yml`:

```yaml
name: Incremental Data Update

on:
  schedule:
    # Regular updates: Daily at 6 AM ET
    - cron: '0 11 * * *'

    # Filing period increases: Every 2 hours during days 13-17 of filing months
    - cron: '0 */2 13-17 1,4,7,10 *'

    # Peak filing day: Every 30 minutes on 15th, 9 AM - 6 PM ET
    - cron: '*/30 13-22 15 1,4,7,10 *'

  workflow_dispatch:
    inputs:
      lookback_days:
        description: 'Days to look back for new filings'
        required: false
        default: '1'

jobs:
  incremental-update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # STEP 1: Fetch new data from FEC API
      - name: Run incremental update
        env:
          FEC_API_KEY: ${{ secrets.FEC_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          if [ -n "${{ github.event.inputs.lookback_days }}" ]; then
            python incremental_update.py --lookback ${{ github.event.inputs.lookback_days }}
          else
            python incremental_update.py
          fi

      # STEP 2: Detect new filings and queue notifications
      - name: Detect new filings
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python detect_new_filings.py --lookback 24

      # STEP 3: Send notification emails
      - name: Send notification emails
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
        run: |
          python send_notifications.py --batch-size 90

      # STEP 4: Log completion
      - name: Log completion
        run: |
          echo "Incremental update completed at $(date)"
          echo "Check Supabase for notification queue status"
```

**Add to `requirements.txt`:**
```
sendgrid==6.11.0
```

#### Testing Checklist

- [ ] Workflow runs on schedule
- [ ] Manual trigger works with custom lookback
- [ ] All three steps execute in sequence
- [ ] Secrets are loaded correctly
- [ ] Errors in one step don't block others (if desired)
- [ ] Logs are clear and helpful
- [ ] Total runtime is <5 minutes

---

### Phase 1 Summary

**Total Duration:** 2-3 weeks
**Total Complexity:** High (but broken into manageable parts)

**Deliverables:**
- ✅ User authentication system (signup, login, password reset)
- ✅ Follow/unfollow candidate functionality
- ✅ New filing detection script
- ✅ Email notification system
- ✅ Integrated GitHub Actions workflow

**Launch Checklist:**
- [ ] All components tested individually
- [ ] End-to-end test: signup → follow → receive notification
- [ ] SendGrid domain verified and authenticated
- [ ] GitHub Secrets configured
- [ ] User testing with 5-10 beta users
- [ ] Documentation updated (README, help page)
- [ ] Analytics tracking set up (Supabase, SendGrid)
- [ ] Monitor logs for first 24 hours post-launch

**Success Metrics (30 days post-launch):**
- 🎯 100+ users signed up
- 🎯 500+ candidate follows
- 🎯 1,000+ notification emails sent
- 🎯 >95% email delivery rate
- 🎯 >30% email open rate
- 🎯 <5% unsubscribe rate

---

## Phase 1.1: Google OAuth & App Verification

**Status:** ✅ COMPLETE
**Priority:** 🔴 HIGH - Professional branding and user trust
**Duration:** 1 week (Actual: 1 day implementation + 1-2 weeks Google review)
**Complexity:** Medium
**Dependencies:** Phase 1 complete
**Completed:** October 30, 2025

### Overview

Add Google OAuth as an alternative authentication method and complete Google app verification to display professional branding during sign-in instead of the Supabase technical URL.

### Why This Matters

- **User Trust:** Professional branding ("Sign in to Campaign Reference") vs technical URL
- **Faster Signup:** One-click sign-in with Google reduces friction
- **Legal Compliance:** Privacy Policy and Terms of Service required for verification
- **Professional Image:** Verified apps appear more legitimate and trustworthy

---

### Completed Deliverables

✅ **Google OAuth Integration**
- Added "Continue with Google" buttons to LoginModal and SignUpModal
- Integrated Supabase OAuth flow with proper redirect handling
- Configured Google Cloud Console OAuth client with credentials
- Configured Supabase Google authentication provider
- Tested OAuth flow end-to-end successfully

✅ **Legal Pages**
- Created comprehensive Privacy Policy (`/privacy`)
- Created Terms of Service (`/terms`)
- Added footer links to legal pages on all views
- Set up admin@campaign-reference.com company email
- Configured MX records and verified DNS propagation

✅ **Google App Verification Submission**
- Updated OAuth consent screen with app name, logo, and URLs
- Added Privacy Policy and Terms of Service links
- Verified domain ownership in Google Search Console
- Recorded demo video showing complete OAuth flow and app features
- Submitted app for Google verification review

### Pending Items

✅ **Google Verification Approval** - Approved December 2025
- "Campaign Reference" branding now displays during Google sign-in

### Technical Implementation

**Frontend Changes:**
```
apps/labs/src/components/auth/
├── LoginModal.jsx        ← Added Google OAuth button
├── SignUpModal.jsx       ← Added Google OAuth button

apps/labs/src/views/
├── PrivacyPolicyView.jsx        ← NEW
└── TermsOfServiceView.jsx       ← NEW

apps/labs/src/App.jsx      ← Added /privacy and /terms routes
```

**Configuration:**
- Google Cloud Console: OAuth 2.0 Client configured
- Supabase: Google provider enabled with Client ID/Secret
- DNS: MX records configured for admin@campaign-reference.com
- Google Search Console: Domain verified

### Files Created
- `apps/labs/src/views/PrivacyPolicyView.jsx` - Complete privacy policy
- `apps/labs/src/views/TermsOfServiceView.jsx` - Complete terms of service
- Updated `apps/labs/src/components/auth/LoginModal.jsx` - Added Google OAuth
- Updated `apps/labs/src/components/auth/SignUpModal.jsx` - Added Google OAuth
- Updated `apps/labs/src/App.jsx` - Added legal page routes and footer links

---

## Phase 2: Data Enhancement

**Priority:** 🟡 MEDIUM - Adds depth and context
**Duration:** 2-3 weeks
**Complexity:** Medium
**Dependencies:** None (can run in parallel with Phase 1)

### Overview

Enhance the data available in Campaign Reference by adding:
1. **Historical data** from previous election cycles (2024, 2022, 2020)
2. **Quarterly data visibility** - Make quarterly trends a first-class feature

### Why This Matters

- **Context:** "Is this candidate's fundraising up or down vs. last cycle?"
- **Trends:** "Which quarter do most candidates raise the most?"
- **Comparisons:** "How does this race compare to the same race in 2024?"
- **Depth:** More data = more insights = more value for users

---

### Part 2A: Historical Data Import

**Duration:** 1-2 weeks
**Complexity:** Medium

#### Technical Implementation

**FEC Bulk Download Files:**

The FEC provides historical data as bulk downloads in pipe-delimited format:
- URL: https://www.fec.gov/files/bulk-downloads/

**Files Needed:**
```
cn24.zip          - 2024 Candidate Master File (~50 MB)
cn22.zip          - 2022 Candidate Master File
cn20.zip          - 2020 Candidate Master File
pas224.zip        - 2024 Summary File (financial totals)
pas222.zip        - 2022 Summary File
pas220.zip        - 2020 Summary File
```

**File Format:** Pipe-delimited (|) text files, NOT comma-separated CSV

**New Python Script: `bulk_import_historical.py`**

```python
#!/usr/bin/env python3
"""
Import historical FEC data from bulk download files
Run once per cycle to populate historical data

Usage:
    python bulk_import_historical.py --cycle 2024
    python bulk_import_historical.py --cycle 2022
    python bulk_import_historical.py --cycle 2020
"""

import os
import requests
import zipfile
from io import BytesIO, StringIO
import csv
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.fec.gov/files/bulk-downloads"

# Column mappings for candidate master file (cn)
CN_COLUMNS = [
    'candidate_id', 'candidate_name', 'party_code', 'party_affiliation',
    'total_receipts', 'trans_from_auth', 'candidate_contribution',
    'total_disbursements', 'trans_to_auth', 'coh_begin', 'coh_end',
    'candidate_contrib', 'debt_owed_by', 'debt_owed_to', 'cover_start_date',
    'cover_end_date', 'candidate_status', 'candidate_state', 'candidate_district',
    'spec_election', 'prim_election', 'runoff_election', 'general_election',
    'general_election_percent', 'other_pol_cmte_contrib', 'pol_party_contrib',
    'coh_cop', 'receipts_from_individuals', 'candidate_office', 'candidate_office_state',
    'candidate_office_district', 'candidate_election_year'
]

def download_and_extract(cycle, file_type):
    """
    Download and extract FEC bulk file

    Args:
        cycle: Election cycle (2024, 2022, 2020)
        file_type: 'cn' for candidate master, 'pas2' for summary

    Returns:
        List of rows (each row is a list of fields)
    """

    year_suffix = str(cycle)[-2:]  # "24" from "2024"

    if file_type == 'cn':
        filename = f"cn{year_suffix}.zip"
    elif file_type == 'pas2':
        filename = f"pas2{year_suffix}.zip"
    else:
        raise ValueError(f"Unknown file type: {file_type}")

    url = f"{BASE_URL}/{cycle}/{filename}"

    print(f"\nDownloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    print(f"Extracting {filename}...")
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        # Get the first text file in the zip
        text_file = [f for f in z.namelist() if f.endswith('.txt')][0]

        with z.open(text_file) as f:
            # Read pipe-delimited file
            content = f.read().decode('utf-8', errors='ignore')

            # Parse with csv module
            reader = csv.reader(StringIO(content), delimiter='|')
            rows = list(reader)

            print(f"Parsed {len(rows)} rows from {text_file}")
            return rows

def transform_candidate_row(row, cycle):
    """
    Transform candidate master row to our schema

    FEC format -> Our format
    """

    if len(row) < 31:
        return None  # Invalid row

    candidate_id = row[0]
    name = row[1]
    party_code = row[2]
    office = row[28]  # H, S, P (President)
    state = row[29]
    district = row[30] if len(row) > 30 else None

    # Skip presidential candidates
    if office not in ['H', 'S']:
        return None

    # Map party codes
    party_map = {
        'DEM': 'Democratic',
        'REP': 'Republican',
        'LIB': 'Libertarian',
        'GRE': 'Green',
        'IND': 'Independent',
    }
    party_full = party_map.get(party_code, party_code)

    return {
        'candidate_id': candidate_id,
        'name': name,
        'party': party_full,
        'office': office,
        'state': state,
        'district': district if district and district != '00' else None,
        'cycle': cycle
    }

def transform_financial_row(row, cycle):
    """
    Transform summary file row to our financial schema
    """

    if len(row) < 15:
        return None

    try:
        return {
            'candidate_id': row[0],
            'cycle': cycle,
            'total_receipts': float(row[4]) if row[4] else 0,
            'total_disbursements': float(row[7]) if row[7] else 0,
            'cash_on_hand': float(row[10]) if row[10] else 0,
            'coverage_start_date': row[13] if row[13] else None,
            'coverage_end_date': row[14] if row[14] else None,
            'report_year': cycle,
            'report_type': 'bulk_import',
            'data_source': 'bulk'
        }
    except (ValueError, IndexError):
        return None

def import_historical_cycle(cycle):
    """
    Main function to import one historical cycle
    """

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    print(f"\n{'='*60}")
    print(f"IMPORTING HISTORICAL DATA - CYCLE {cycle}")
    print(f"{'='*60}\n")

    # Step 1: Import candidates
    print("Step 1: Importing candidates...")
    cn_rows = download_and_extract(cycle, 'cn')

    candidates = []
    for row in cn_rows:
        transformed = transform_candidate_row(row, cycle)
        if transformed:
            candidates.append(transformed)

    print(f"Transformed {len(candidates)} candidates for import")

    # Batch insert candidates
    batch_size = 1000
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        supabase.table('candidates').upsert(batch).execute()
        print(f"  Inserted candidates {i} - {i+len(batch)}")

    # Step 2: Import financials
    print("\nStep 2: Importing financial summaries...")
    pas_rows = download_and_extract(cycle, 'pas2')

    financials = []
    for row in pas_rows:
        transformed = transform_financial_row(row, cycle)
        if transformed:
            financials.append(transformed)

    print(f"Transformed {len(financials)} financial records for import")

    # Batch insert financials
    for i in range(0, len(financials), batch_size):
        batch = financials[i:i+batch_size]
        supabase.table('financial_summary').upsert(batch).execute()
        print(f"  Inserted financials {i} - {i+len(batch)}")

    print(f"\n{'='*60}")
    print(f"✅ Import complete for cycle {cycle}")
    print(f"   Candidates: {len(candidates)}")
    print(f"   Financials: {len(financials)}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--cycle', type=int, required=True,
                       choices=[2024, 2022, 2020],
                       help='Election cycle to import')
    args = parser.parse_args()

    import_historical_cycle(args.cycle)
```

#### Key Questions & Decision Points

**Q1: Which cycles should we import?**

| Cycle | House Seats | Senate Seats | Relevance | Recommendation |
|-------|-------------|--------------|-----------|----------------|
| 2024 | All 435 | ~33 seats | Most recent, direct comparison | ✅ **Must have** |
| 2022 | All 435 | ~33 seats | Still relevant, redistricting | ✅ **Must have** |
| 2020 | All 435 | ~33 seats | Historical context | 🟡 Nice to have |
| 2018 | All 435 | ~33 seats | Older, less relevant | 🔴 Skip |

**Recommendation:** Import 2024, 2022, and 2020 to start. Can add more cycles if users request.

**Q2: Should we import quarterly data for historical cycles?**

**Option A: Import only totals (faster)**
- Quicker import (<30 min per cycle)
- Less data to store
- Good enough for most comparisons

**Option B: Import quarterly breakdowns (comprehensive)**
- Complete historical context
- Allows quarterly trend comparison across cycles
- Slower import (~2 hours per cycle)

**Recommendation:** Start with Option A (totals only). Add quarterly in Phase 2.1 if users request historical quarterly trends.

**Q3: How do we handle redistricting between 2020 and 2022?**

**Issue:** Congressional districts changed after 2020 census. Some candidates ran in "CA-12" in 2020, but CA-12 boundaries changed in 2022.

**Option A: Import as-is (keep historical district numbers)**
- Simplest approach
- Note: "CA-12 (2020)" ≠ "CA-12 (2022)" in some states

**Option B: Add redistricting mapping table**
- Complex
- Would need to research boundary changes for all states

**Recommendation:** Option A with a note in the UI explaining redistricting. Example: "District boundaries changed after 2020 census."

#### Testing Checklist

- [ ] Script downloads bulk files successfully
- [ ] Extracts and parses pipe-delimited format
- [ ] Transforms data to our schema correctly
- [ ] Handles invalid rows gracefully
- [ ] Batch inserts work without errors
- [ ] Upsert logic prevents duplicates
- [ ] Can run for 2024, 2022, 2020
- [ ] Total runtime <30 minutes per cycle
- [ ] Database constraints are satisfied

#### Success Criteria

- ✅ 2024, 2022, 2020 cycles imported successfully
- ✅ ~10,000 total historical candidates
- ✅ ~10,000 historical financial records
- ✅ No duplicate records
- ✅ Data matches FEC bulk download totals

---

### Part 2B: Quarterly Data Visibility

**Duration:** 4-5 days
**Complexity:** Low-Medium

#### Technical Implementation

**Goal:** Make quarterly data a first-class feature, not just a chart at the bottom.

**Frontend Enhancements:**

**1. Add Quarterly Columns to Tables**

Update `RaceTable.jsx`:

```jsx
// New prop: showQuarterlyData (boolean)
// New prop: selectedQuarters (array of quarter objects)

// Example columns:
<Table>
  <Column header="Name" />
  <Column header="Party" />
  <Column header="Location" />
  <Column header="Total Raised" />
  <Column header="Q1 2026" />  {/* NEW */}
  <Column header="Q2 2026" />  {/* NEW */}
  <Column header="Trend" />     {/* NEW - show ↑ or ↓ */}
</Table>
```

**2. Add Quarterly Filter to MetricToggle**

Update `MetricToggle.jsx`:

```jsx
// Add new options:
<select name="metric">
  <option value="total_receipts">Total Raised</option>
  <option value="total_disbursements">Total Spent</option>
  <option value="cash_on_hand">Cash on Hand</option>
  <option value="q1_2026">Q1 2026 Raised</option>     {/* NEW */}
  <option value="q2_2026">Q2 2026 Raised</option>     {/* NEW */}
  <option value="quarterly_avg">Quarterly Average</option> {/* NEW */}
</select>

// Add checkbox:
<label>
  <input type="checkbox" name="showQuarterlyColumns" />
  Show quarterly breakdown in table
</label>
```

**3. Add Quarterly Trend Cards**

New component: `src/components/QuarterlyTrendCards.jsx`

```jsx
/**
 * Display 3 cards showing quarterly statistics
 *
 * Card 1: Latest Quarter Summary
 * - Average raised in latest quarter
 * - Top fundraiser in latest quarter
 * - Number of candidates who filed
 *
 * Card 2: Previous Quarter Summary
 * - Same metrics for comparison
 *
 * Card 3: Quarter-over-Quarter Growth
 * - % change from previous quarter
 * - Trend indicator (up/down)
 * - Number of candidates with growth
 */
```

**4. Enhanced Quarterly Chart**

Update `QuarterlyChart.jsx`:

```jsx
// Add annotations for filing deadlines
// Example: Vertical line at end of each quarter

// Add average line
// Shows average across all candidates in the chart

// Add trend velocity
// Calculate whether momentum is increasing or decreasing

// Add "Share this chart" button
// Exports chart as PNG optimized for social media
```

#### Database Queries

**Get quarterly data for table:**

```javascript
// In useCandidateData.js
const { data, error } = await supabase
  .from('candidates')
  .select(`
    *,
    financial_summary(*),
    quarterly_financials(*)
  `)
  .eq('cycle', selectedCycle)
  .eq('office', selectedOffice);

// Transform to include quarterly columns
const transformed = data.map(candidate => {
  const quarters = candidate.quarterly_financials.reduce((acc, q) => {
    const quarterLabel = `Q${q.quarter}_${q.report_year}`;
    acc[quarterLabel] = q.total_receipts;
    return acc;
  }, {});

  return {
    ...candidate,
    ...quarters,
    quarterly_avg: calculateAverage(candidate.quarterly_financials)
  };
});
```

**Calculate quarterly trends:**

```javascript
function calculateQuarterlyTrend(quarters) {
  if (quarters.length < 2) return null;

  // Sort by date
  const sorted = quarters.sort((a, b) =>
    new Date(a.coverage_end_date) - new Date(b.coverage_end_date)
  );

  const latest = sorted[sorted.length - 1];
  const previous = sorted[sorted.length - 2];

  const change = latest.total_receipts - previous.total_receipts;
  const percentChange = (change / previous.total_receipts) * 100;

  return {
    change,
    percentChange,
    direction: change > 0 ? 'up' : 'down',
    arrow: change > 0 ? '↑' : '↓'
  };
}
```

#### Key Questions & Decision Points

**Q1: Which quarters should we show by default?**

**Option A: Last 2 quarters**
- Most relevant for current race
- Clean UI

**Option B: Last 4 quarters (full year)**
- More context
- Could be cluttered

**Option C: User selectable**
- Maximum flexibility
- More complex UI

**Recommendation:** Option A by default, with Option C as advanced filter. Show last 2 quarters in table, but allow users to toggle to show all quarters.

**Q2: How do we handle missing quarterly data?**

**Scenario:** Candidate only has 2 of 4 quarters filed

**Option A: Show "—" for missing quarters**
- Clear that data is missing
- Doesn't assume zero

**Option B: Interpolate or extrapolate**
- Smooth visualization
- Could be misleading

**Recommendation:** Option A. Never show data we don't have.

**Q3: Should quarterly view be a separate page or toggle?**

**Option A: Toggle on existing views**
- Keeps everything in one place
- Could be cluttered

**Option B: Dedicated "Quarterly Analysis" page**
- Clean, focused experience
- Extra nav item

**Recommendation:** Option A. Add quarterly options to existing views. Can add dedicated page in Phase 2.1 if users want deep quarterly analysis.

#### Testing Checklist

- [ ] Quarterly columns appear in table
- [ ] Quarterly filter works in MetricToggle
- [ ] Trend cards show correct statistics
- [ ] Enhanced chart displays correctly
- [ ] Missing data shows as "—"
- [ ] Quarterly averages calculate correctly
- [ ] Trend arrows show correct direction
- [ ] Mobile responsive
- [ ] Performance: Table renders quickly even with 10+ quarterly columns

#### Success Criteria

- ✅ Users can see quarterly data without scrolling to chart
- ✅ Trend indicators make it obvious who's gaining momentum
- ✅ UI remains clean and not cluttered
- ✅ <1 second load time with quarterly data
- ✅ Feature gets used (track with analytics)

---

### Phase 2 Summary

**Total Duration:** 2-3 weeks
**Total Complexity:** Medium

**Deliverables:**
- ✅ Historical data from 2024, 2022, 2020 cycles
- ✅ Cycle selector shows 4 options (2026, 2024, 2022, 2020)
- ✅ Quarterly columns in tables
- ✅ Quarterly metrics in filters
- ✅ Quarterly trend cards
- ✅ Enhanced quarterly chart

**Launch Checklist:**
- [ ] Historical data imported and verified
- [ ] Quarterly features tested in all views
- [ ] UI/UX reviewed for clarity
- [ ] Performance testing with full dataset
- [ ] Documentation updated
- [ ] User testing completed

**Success Metrics (30 days post-launch):**
- 🎯 >20% of users use cycle selector to view historical data
- 🎯 >30% of users toggle quarterly columns
- 🎯 Avg session time increases by 20% (more to explore)
- 🎯 Users create historical comparison tweets/posts

---

## Phase 3: Visual Excellence

**Priority:** 🟢 HIGH (for growth) - Make it beautiful and shareable
**Duration:** 2-3 weeks
**Complexity:** Medium-High
**Dependencies:** Phase 2 (more data = better charts)

### Overview

Transform Campaign Reference into a source of **screenshot-worthy visualizations** that users want to share on social media.

### Why This Matters

- **Viral growth:** Beautiful, informative charts get shared → drive traffic
- **Brand recognition:** Consistent, high-quality visuals build brand
- **User value:** Users can easily create shareable content for their own audience
- **SEO benefit:** Social shares and backlinks improve search ranking

---

### Part 3A: Shareable Chart Templates

**Duration:** 1-2 weeks
**Complexity:** Medium-High

#### Technical Implementation

**Goal:** Create 4-5 chart templates optimized for social media sharing (especially Twitter/X).

**Design Principles:**

1. **Self-contained** - All context on image (no caption needed)
2. **Optimized dimensions** - 1200x675px (16:9 for Twitter)
3. **High contrast** - Readable on mobile
4. **Branded** - Watermark with "campaign-reference.com"
5. **Data + context** - Chart + key stats + date + source

**Chart Templates to Build:**

**Template 1: Head-to-Head Comparison**
```
┌──────────────────────────────────────────────────────────────┐
│  Campaign Finance Showdown: CA-47                     [Logo] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   Rep. Jane Smith (D)          vs.     John Doe (R)         │
│                                                              │
│   $3.2M Raised                           $2.1M Raised       │
│   [████████████████] 100%    [███████████] 66%              │
│                                                              │
│   $1.8M Cash on Hand                     $400K Cash         │
│   [█████████████████] 100%   [████] 22%                     │
│                                                              │
│   Q1 2026: +38% ↗️                        Q1 2026: +12% ↗️   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Data as of March 31, 2026                                  │
│  Source: FEC via campaign-reference.com                     │
└──────────────────────────────────────────────────────────────┘
```

**Template 2: Top 10 Leaderboard**
```
┌──────────────────────────────────────────────────────────────┐
│  💰 Top 10 House Fundraisers - Q1 2026            [Logo]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 🔵 Rep. Smith (CA-47)      $3.2M  ████████████████      │
│  2. 🔴 Rep. Jones (TX-23)      $2.9M  █████████████         │
│  3. 🔵 Rep. Davis (NY-18)      $2.7M  ████████████          │
│  4. 🔴 Rep. Wilson (FL-27)     $2.5M  ███████████           │
│  5. 🔵 Rep. Garcia (AZ-03)     $2.3M  ██████████            │
│  6. 🔴 Rep. Brown (OH-09)      $2.1M  █████████             │
│  7. 🔵 Rep. Lee (CA-12)        $2.0M  ████████              │
│  8. 🔴 Rep. Taylor (PA-07)     $1.9M  ████████              │
│  9. 🔵 Rep. Martinez (CO-06)   $1.8M  ███████               │
│  10. 🔴 Rep. Anderson (VA-10)  $1.7M  ███████               │
│                                                              │
│  Total: $24.1M raised • Average: $2.4M                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Data as of March 31, 2026                                  │
│  Source: FEC via campaign-reference.com                     │
└──────────────────────────────────────────────────────────────┘
```

**Template 3: Quarterly Trend**
```
┌──────────────────────────────────────────────────────────────┐
│  📊 CA-47: The Money Race                         [Logo]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   $1.2M │                                                   │
│         │                               ●─── Smith (D)      │
│   $1.0M │                       ●───●                       │
│         │                   ●                               │
│   $800K │           ●───●                                   │
│         │                                ●─── Doe (R)       │
│   $600K │       ●               ●───●                       │
│         │   ●                                               │
│   $400K │                                                   │
│         └───┴────┴────┴────┴────┴────                       │
│           Q3   Q4   Q1   Q2   Q3   Q4                       │
│          2025 2025 2026 2026 2026 2026                      │
│                                                              │
│  Smith leads by $600K in Q4 2026 • +75% advantage           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Data as of December 31, 2026                               │
│  Source: FEC via campaign-reference.com                     │
└──────────────────────────────────────────────────────────────┘
```

**Template 4: State Map View**
```
┌──────────────────────────────────────────────────────────────┐
│  California House Fundraising - 2026 Cycle       [Logo]     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [Map of California with districts colored by total raised] │
│                                                              │
│  Top 5 Districts by Total Raised:                           │
│  1. CA-12: $8.2M (3 candidates)                             │
│  2. CA-47: $5.3M (2 candidates)                             │
│  3. CA-22: $4.8M (4 candidates)                             │
│  4. CA-49: $4.1M (2 candidates)                             │
│  5. CA-03: $3.9M (3 candidates)                             │
│                                                              │
│  Total raised across all CA House races: $128.4M            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Data as of March 31, 2026                                  │
│  Source: FEC via campaign-reference.com                     │
└──────────────────────────────────────────────────────────────┘
```

**Template 5: Party Comparison**
```
┌──────────────────────────────────────────────────────────────┐
│  House Fundraising by Party - Q1 2026            [Logo]     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Democrats                      Republicans                  │
│  ━━━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━━       │
│  $428.3M Total Raised           $392.1M Total Raised        │
│  +12% vs. Q1 2024               +8% vs. Q1 2024             │
│                                                              │
│  Avg per candidate: $1.2M       Avg per candidate: $1.1M    │
│                                                              │
│  Top Fundraiser:                Top Fundraiser:             │
│  Rep. Smith (CA-47)             Rep. Jones (TX-23)          │
│  $3.2M                          $2.9M                       │
│                                                              │
│  [Bar chart comparing totals]                               │
│  Dems ████████████████████ $428M                            │
│  GOP  ████████████████████ $392M                            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Data as of March 31, 2026                                  │
│  Source: FEC via campaign-reference.com                     │
└──────────────────────────────────────────────────────────────┘
```

#### Implementation Approach

**Option 1: HTML + html2canvas (Recommended for MVP)**

**Pros:**
- Already using html2canvas
- Leverage existing React components
- Fast iteration
- No backend needed

**Cons:**
- Limited control over output
- Browser inconsistencies
- Client-side only

**Implementation:**
```jsx
// New component structure
src/components/social/
├── ShareableChartBase.jsx       // Base component with branding
├── HeadToHeadCard.jsx           // Template 1
├── LeaderboardCard.jsx          // Template 2
├── QuarterlyTrendCard.jsx       // Template 3
├── StateMapCard.jsx             // Template 4
├── PartyComparisonCard.jsx      // Template 5
└── ShareImageGenerator.jsx      // Export logic wrapper

// Usage in views:
<ShareButton onClick={() => generateShareImage('head-to-head')}>
  Share This Comparison
</ShareButton>

// generateShareImage function:
1. Render hidden ShareableChart component with data
2. Use html2canvas to capture as PNG
3. Download or copy to clipboard
4. Show success toast
```

**Option 2: Server-side with Playwright (Phase 3.1)**

**Pros:**
- Consistent output
- Can generate OG images for link previews
- Cacheable
- Perfect rendering

**Cons:**
- Requires backend service
- More complex setup
- Costs (serverless function or dedicated server)

**Implementation:**
```python
# New serverless function
# Vercel: /api/share-image/[type].py

import playwright
from playwright.sync_api import sync_playwright

def generate_share_image(type, data):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 675})

        # Render React component server-side
        html = render_template(type, data)
        page.set_content(html)

        # Screenshot
        screenshot = page.screenshot()

        browser.close()
        return screenshot

# URL patterns:
# /api/share-image/head-to-head?candidate1=H6CA47001&candidate2=H6CA47002
# /api/share-image/leaderboard?chamber=H&limit=10
# /api/share-image/quarterly?candidate=H6CA47001
```

**Option 3: Canvas API (Most Control)**

**Pros:**
- Maximum control
- Fast rendering
- High DPI support (2x, 3x for Retina)
- No external dependencies

**Cons:**
- More code to write
- Manual layout calculations
- Harder to iterate on design

**Recommendation:** Start with Option 1 (HTML + html2canvas). Move to Option 2 in Phase 3.1 for OG images and better quality.

#### Key Questions & Decision Points

**Q1: Should we generate images client-side or server-side?**

**Recommendation:** Client-side for MVP (Option 1). Users click "Share", image generates in browser, downloads immediately. Fast, free, good enough.

**Q2: What formats should we support?**

| Format | Use Case | Recommendation |
|--------|----------|----------------|
| PNG | Screenshots, Twitter, general | ✅ **Default** |
| JPG | Smaller file size | 🟡 Phase 3.1 |
| SVG | Scalable, editable | 🔴 Skip |
| PDF | Print, reports | 🟡 Phase 3.1 |

**Recommendation:** PNG only for MVP. It's universally supported and high quality.

**Q3: Should we offer multiple design themes?**

**Option A: Single theme (current brand colors)**
- Consistent branding
- Simpler to build

**Option B: Multiple themes (Light, Dark, Red Bull Racing)**
- User preference
- More complex

**Recommendation:** Single theme for MVP (Option A). Add theme selector in Phase 3.1 if users request it.

**Q4: Should we add text overlays or annotations?**

**Use Case:** User wants to add their own commentary to the chart

**Option A: No custom text (chart only)**
- Simple, fast
- Users can add text in Twitter post caption

**Option B: Allow custom text overlay**
- More personalized
- Complex UI

**Recommendation:** Option A for MVP. Users can add context in their tweet text.

#### Frontend Components

**ShareButton.jsx:**
```jsx
/**
 * Button that triggers share image generation
 *
 * Props:
 * - chartType: 'head-to-head' | 'leaderboard' | 'quarterly' | 'state-map' | 'party-comparison'
 * - data: object with chart data
 * - label: button text (default: "Share This Chart")
 * - size: 'sm' | 'md' | 'lg'
 *
 * Behavior:
 * 1. Click button
 * 2. Modal opens showing preview
 * 3. User can customize (future: add text, change theme)
 * 4. Click "Download" → PNG downloads
 * 5. Click "Copy to Clipboard" → Image copied (for pasting in Twitter)
 */
```

**ShareModal.jsx:**
```jsx
/**
 * Modal for previewing and downloading share image
 *
 * Features:
 * - Large preview (1200x675)
 * - Download button
 * - Copy to clipboard button
 * - Share directly to Twitter button (opens tweet composer with image)
 * - Social media tips ("Add a caption for more engagement")
 */
```

#### Testing Checklist

- [ ] All 5 chart templates render correctly
- [ ] Generated images are 1200x675px
- [ ] Brand watermark is visible
- [ ] All text is legible
- [ ] Colors have sufficient contrast
- [ ] Works in Chrome, Firefox, Safari
- [ ] Works on mobile (responsive)
- [ ] Download works
- [ ] Copy to clipboard works
- [ ] Share to Twitter works
- [ ] Generated images look good on Twitter (test post)

#### Success Criteria

- ✅ Users can generate share image in <3 seconds
- ✅ Images look professional and on-brand
- ✅ >10% of users use share feature in first month
- ✅ Generated images are shared on Twitter/X
- ✅ Traffic increases from social referrals

---

### Part 3B: Open Graph Images

**Duration:** 3-4 days
**Complexity:** Medium

#### Technical Implementation

**Goal:** Generate beautiful preview images when Campaign Reference links are shared on social media or Slack.

**What are OG images?**

When you paste a link in Twitter/Slack/Discord, it shows a preview card with image. We control that image.

**Example:**
```
┌──────────────────────────────────────┐
│  [Preview Image]                     │
│  Campaign Reference                  │
│  CA-47: Rep. Jane Smith leads        │
│  fundraising with $3.2M raised       │
│  campaign-reference.com              │
└──────────────────────────────────────┘
```

**Implementation Approach:**

**Option A: Static OG Image (Easy)**
- One default image for all pages
- Fast, simple
- Not personalized

**Option B: Dynamic OG Images (Better)**
- Generate unique image per page
- Shows relevant data in preview
- More complex

**Recommendation:** Start with Option A, upgrade to Option B in Phase 3.1.

**Option A Implementation:**

1. Create static OG image (1200x630px for Facebook/LinkedIn):
   - Campaign Reference logo
   - Tagline: "Track 2026 Campaign Finance in Real-Time"
   - Sample chart or data viz

2. Add meta tags to `index.html`:
```html
<meta property="og:title" content="Campaign Reference - 2026 Campaign Finance Dashboard" />
<meta property="og:description" content="Track House and Senate campaign fundraising with real-time FEC data. Follow candidates and get instant alerts when new reports are filed." />
<meta property="og:image" content="https://campaign-reference.com/og-image.png" />
<meta property="og:url" content="https://campaign-reference.com" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="https://campaign-reference.com/og-image.png" />
```

**Option B Implementation (Phase 3.1):**

1. Create serverless function to generate OG images:
```python
# Vercel serverless function: /api/og-image.py

def handler(request):
    # Parse query params
    page = request.args.get('page')  # 'candidate', 'district', 'leaderboard'
    candidate_id = request.args.get('candidate_id')

    # Fetch data
    data = fetch_data(page, candidate_id)

    # Generate image using Playwright
    image = generate_og_image(page, data)

    # Return image with cache headers
    return Response(image, mimetype='image/png',
                   headers={'Cache-Control': 'public, max-age=3600'})
```

2. Add meta tags dynamically:
```html
<meta property="og:image" content="https://campaign-reference.com/api/og-image?page=candidate&candidate_id=H6CA47001" />
```

#### Testing Checklist

- [ ] OG image shows in Twitter preview
- [ ] OG image shows in Facebook preview
- [ ] OG image shows in LinkedIn preview
- [ ] OG image shows in Slack preview
- [ ] Image is correct size (1200x630)
- [ ] Text is legible in preview
- [ ] Cache headers work (don't regenerate every time)

#### Success Criteria

- ✅ OG images appear for all shared links
- ✅ Preview looks professional
- ✅ Click-through rate improves (track in analytics)

---

### Part 3C: Design Polish

**Duration:** 3-4 days
**Complexity:** Low-Medium

#### Technical Implementation

**Goal:** Make the entire site more visually polished and engaging.

**Areas to Enhance:**

**1. Typography**
- Use better font pairing
- Improve hierarchy (h1, h2, h3 sizing)
- Better line height and spacing

**2. Color System**
- Audit current colors for accessibility (WCAG AA contrast)
- Create consistent color palette
- Party colors (blue/red) should pop without being garish

**3. Spacing & Layout**
- Consistent padding/margin throughout
- Better use of whitespace
- Card shadows for depth

**4. Micro-interactions**
- Button hover states
- Loading skeletons (instead of spinners)
- Smooth transitions
- Toast notifications for actions

**5. Data Visualization**
- Better chart colors
- Annotations on charts
- Tooltips with more context
- Legend improvements

**6. Mobile Experience**
- Larger touch targets
- Better responsive breakpoints
- Mobile-optimized charts

#### Design System Updates

**Update Tailwind Config:**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#001F3F',      // Dark navy
          blue: '#2563EB',      // Primary blue
          red: '#DC2626',       // Republican red
          'blue-light': '#DBEAFE', // Democrat light
          'red-light': '#FEE2E2'   // Republican light
        },
        neutral: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          // ...
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'sans-serif'], // For headings
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.1)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.15)',
      }
    }
  }
}
```

**Add Loading Skeletons:**
```jsx
// src/components/LoadingSkeleton.jsx
export function TableSkeleton() {
  return (
    <div className="animate-pulse">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="h-12 bg-gray-200 rounded mb-2" />
      ))}
    </div>
  );
}
```

**Better Tooltips:**
```jsx
// Use Recharts CustomTooltip
<Tooltip content={<CustomTooltip />} />

function CustomTooltip({ active, payload }) {
  if (!active || !payload) return null;

  return (
    <div className="bg-white p-3 shadow-lg rounded-lg border">
      <p className="font-semibold">{payload[0].name}</p>
      <p className="text-sm text-gray-600">
        {formatCurrency(payload[0].value)}
      </p>
      <p className="text-xs text-gray-500 mt-1">
        Click to view details
      </p>
    </div>
  );
}
```

#### Key Questions & Decision Points

**Q1: Should we hire a designer or use existing design systems?**

**Option A: DIY with Tailwind UI components**
- Fast, free
- Good enough
- Less unique

**Option B: Hire designer for custom design system**
- Unique brand identity
- Professional polish
- Costs $2K-5K

**Recommendation:** Option A for MVP. Upgrade to Option B if/when revenue supports it.

**Q2: Dark mode - should we add it?**

**Pros:**
- Modern
- Some users prefer it
- Reduces eye strain

**Cons:**
- 2x the design work
- Charts need dark variants
- More testing

**Recommendation:** Skip for MVP. Add in Phase 3.1 if users request it.

#### Testing Checklist

- [ ] All colors meet WCAG AA contrast requirements
- [ ] Typography is consistent across all pages
- [ ] Spacing is consistent
- [ ] Micro-interactions feel smooth
- [ ] Mobile experience is polished
- [ ] Loading states are smooth
- [ ] No layout shift (CLS score good)
- [ ] Cross-browser tested

#### Success Criteria

- ✅ Users comment on improved design
- ✅ Lighthouse accessibility score >95
- ✅ Time on site increases (users enjoy browsing)
- ✅ Bounce rate decreases

---

### Phase 3 Summary

**Total Duration:** 2-3 weeks
**Total Complexity:** Medium-High

**Deliverables:**
- ✅ 5 shareable chart templates
- ✅ Share button on all major views
- ✅ OG images for link previews
- ✅ Design polish across entire site
- ✅ Better mobile experience

**Launch Checklist:**
- [ ] All chart templates tested
- [ ] Share feature works on all browsers
- [ ] OG images tested on all platforms
- [ ] Design system documented
- [ ] Mobile tested on real devices
- [ ] Performance tested (Lighthouse score >90)
- [ ] User feedback collected

**Success Metrics (30 days post-launch):**
- 🎯 >500 share images generated
- 🎯 >100 social media shares of generated images
- 🎯 >25% increase in social referral traffic
- 🎯 Branded images appear in political Twitter/X feeds
- 🎯 User testimonials about design quality

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │ Public     │  │ Auth       │  │ User Dashboard       │  │
│  │ Views      │  │ Components │  │ - Following List     │  │
│  │ - Leaderboard│  │ - Login   │  │ - Notification       │  │
│  │ - District │  │ - Signup   │  │   Settings           │  │
│  │ - Candidate│  │            │  │                      │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Share Components                                     │   │
│  │ - HeadToHead, Leaderboard, Quarterly, etc.          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ API Calls
┌─────────────────────────────────────────────────────────────┐
│                    Supabase (Backend)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │ Auth       │  │ Database   │  │ Storage (future)   │    │
│  │ - Users    │  │ - candidates│  │ - Cached images   │    │
│  │ - Sessions │  │ - financial │  │                   │    │
│  │            │  │ - quarterly │  │                   │    │
│  │            │  │ - follows   │  │                   │    │
│  │            │  │ - notifs    │  │                   │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↑ Updates
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions (Data Pipeline)                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Scheduled Workflows:                               │     │
│  │ 1. incremental_update.py   - Fetch new FEC data    │     │
│  │ 2. detect_new_filings.py   - Find candidates w/    │     │
│  │                              new filings            │     │
│  │ 3. send_notifications.py   - Email alerts via      │     │
│  │                              SendGrid               │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↑ Data Source
┌─────────────────────────────────────────────────────────────┐
│                    FEC OpenFEC API                           │
│  - Candidate data                                            │
│  - Financial summaries                                       │
│  - Quarterly filings                                         │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**Existing Tables:**
- `candidates` - Basic candidate info
- `financial_summary` - Current cycle financial totals
- `quarterly_financials` - Quarterly filing data
- `data_refresh_log` - Update tracking

**New Tables (Phase 1):**
- `user_profiles` (optional) - Extended user info
- `user_candidate_follows` - Following relationships
- `notification_queue` - Pending email notifications
- `notification_analytics` (optional) - Email engagement tracking

**Indexes to Add:**
```sql
-- Performance optimization for follows
CREATE INDEX idx_follows_user_enabled ON user_candidate_follows(user_id, notification_enabled);
CREATE INDEX idx_follows_candidate ON user_candidate_follows(candidate_id);

-- Performance optimization for notifications
CREATE INDEX idx_queue_pending ON notification_queue(status) WHERE status = 'pending';
CREATE INDEX idx_queue_candidate ON notification_queue(candidate_id);

-- Performance optimization for historical data
CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_financials_cycle ON financial_summary(cycle);
```

### API Endpoints

**Supabase (automatically generated from tables):**
- `GET /rest/v1/candidates` - Get candidates with filters
- `GET /rest/v1/financial_summary` - Get financial data
- `GET /rest/v1/quarterly_financials` - Get quarterly data
- `POST /rest/v1/user_candidate_follows` - Follow candidate
- `DELETE /rest/v1/user_candidate_follows` - Unfollow candidate
- `GET /rest/v1/notification_queue` - Get notifications (admin only)

**Supabase Auth:**
- `POST /auth/v1/signup` - Create account
- `POST /auth/v1/token?grant_type=password` - Login
- `POST /auth/v1/recover` - Password reset
- `POST /auth/v1/logout` - Logout

**Future API Endpoints (Phase 3.1):**
- `GET /api/og-image?page=...&id=...` - Generate OG image
- `GET /api/share-image?type=...&data=...` - Generate share image

### Environment Variables

**Frontend (.env):**
```
VITE_SUPABASE_URL=https://xyz.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
```

**Backend (GitHub Secrets):**
```
FEC_API_KEY=3FchpJwxR0Wf7PpqyyBJJhCX9ytqwGzsVVqE8yh3
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=eyJhbGc... (service role key)
SENDGRID_API_KEY=SG.xyz...
```

### Third-Party Services

| Service | Purpose | Cost | Status |
|---------|---------|------|--------|
| Supabase | Database + Auth | Free tier (500 MB) | ✅ Active |
| SendGrid | Email notifications | Free (100/day) → $15/mo (40K) | 🟡 Phase 1 |
| Vercel | Hosting + deployment | Free | ✅ Active |
| FEC API | Campaign data | Free (1K req/hr) | ✅ Active |

### Performance Considerations

**Frontend:**
- Code splitting by route
- Lazy load charts (only render when visible)
- Debounce search inputs
- Cache candidate data in React Query or SWR
- Optimize images (WebP format)
- Minimize bundle size

**Backend:**
- Index all foreign keys
- Use Supabase RLS for security (not application logic)
- Batch database operations
- Cache frequently accessed data
- Limit query results (pagination)

**Notification System:**
- Batch email sends (90 at a time for free tier)
- Deduplicate notifications
- Retry failed sends (max 3 attempts)
- Queue cleanup (delete sent notifications after 30 days)

### Security Considerations

**Authentication:**
- Use Supabase Auth (battle-tested)
- Require email verification
- Rate limit signup attempts (Supabase built-in)
- Session timeout after 7 days

**Authorization:**
- Row Level Security (RLS) on all tables
- Users can only see/modify their own follows
- Admin-only access to notification queue
- Validate all user inputs

**API Keys:**
- Never expose service role key to frontend
- Use anon key in frontend (public, read-only)
- Store secrets in GitHub Secrets
- Rotate keys if compromised

**Email Security:**
- Verify SendGrid sender domain (SPF/DKIM)
- Include unsubscribe link in all emails
- Rate limit email sends
- Handle bounces gracefully

---

## Success Metrics

### Phase 1: Notifications

**User Acquisition:**
- 🎯 100 users in first week
- 🎯 500 users in first month
- 🎯 2,000 users in 3 months

**Engagement:**
- 🎯 Avg 5 follows per user
- 🎯 >30% email open rate
- 🎯 >10% email click rate
- 🎯 <5% unsubscribe rate

**Retention:**
- 🎯 >50% of users return within 7 days
- 🎯 >70% of users keep notifications enabled

### Phase 2: Data Enhancement

**Usage:**
- 🎯 >20% of users view historical data
- 🎯 >30% of users use quarterly filters
- 🎯 Avg session time increases 20%

**Engagement:**
- 🎯 >40% of users compare across cycles
- 🎯 Quarterly trend cards get viewed on >50% of sessions

### Phase 3: Visual Excellence

**Sharing:**
- 🎯 >500 share images generated per month
- 🎯 >100 shares on Twitter/X per month
- 🎯 >25% increase in social referral traffic

**Growth:**
- 🎯 >1,000 new users from social referrals
- 🎯 Campaign Reference images appear in political journalism

**Quality:**
- 🎯 Lighthouse score >90
- 🎯 Core Web Vitals all green
- 🎯 >95% accessibility score

### Overall Platform Metrics (6 months)

**Users:**
- 🎯 10,000+ registered users
- 🎯 50,000+ monthly visitors

**Engagement:**
- 🎯 Avg 3 sessions per user per week
- 🎯 Avg 5 minutes per session
- 🎯 50,000+ candidate follows

**Reach:**
- 🎯 Top 3 on Google for "campaign finance dashboard"
- 🎯 Mentioned by political journalists on Twitter
- 🎯 Featured in at least 1 major publication (Politico, Roll Call, etc.)

---

## Risk Management

### Technical Risks

**Risk 1: Email Deliverability Issues**
- **Likelihood:** Medium
- **Impact:** High (core feature broken)
- **Mitigation:**
  - Use SendGrid (high deliverability)
  - Verify sender domain (SPF/DKIM)
  - Monitor bounce rate
  - Implement retry logic
  - Provide support email for issues

**Risk 2: Database Performance Degradation**
- **Likelihood:** Medium (as data grows)
- **Impact:** Medium (slow page loads)
- **Mitigation:**
  - Add indexes proactively
  - Monitor query performance
  - Implement pagination
  - Cache frequently accessed data
  - Upgrade Supabase plan if needed ($25/mo)

**Risk 3: FEC API Rate Limits**
- **Likelihood:** Low (careful rate limiting)
- **Impact:** High (can't update data)
- **Mitigation:**
  - Stay under 900 req/hr (10% buffer)
  - Implement exponential backoff
  - Monitor API usage
  - Cache API responses

**Risk 4: SendGrid Free Tier Exceeded**
- **Likelihood:** Medium (if popular)
- **Impact:** Low (can upgrade easily)
- **Mitigation:**
  - Monitor daily usage
  - Implement batching (90 max per run)
  - Upgrade to paid plan if needed ($15/mo)
  - Allow users to opt for digest emails (reduces volume)

### Product Risks

**Risk 5: Low User Adoption**
- **Likelihood:** Medium
- **Impact:** High (product doesn't serve purpose)
- **Mitigation:**
  - User testing before launch
  - Beta program with target users (journalists)
  - Gather feedback early
  - Iterate based on usage data
  - Marketing to target audience (Twitter, political Slack groups)

**Risk 6: High Unsubscribe Rate**
- **Likelihood:** Medium
- **Impact:** Medium (notifications lose value)
- **Mitigation:**
  - Make unfollow easy (not unsubscribe from all)
  - Offer digest email option
  - Only notify for material changes
  - Allow per-candidate notification settings
  - Survey users who unsubscribe

**Risk 7: Users Don't Share Charts**
- **Likelihood:** Medium
- **Impact:** Medium (less viral growth)
- **Mitigation:**
  - Make charts truly beautiful and informative
  - Make sharing frictionless (one click)
  - Provide multiple format options
  - Add social proof ("1,234 charts shared this month")
  - Incentivize sharing (feature top sharers?)

### Business Risks

**Risk 8: Can't Scale Costs**
- **Likelihood:** Low (starts free)
- **Impact:** Medium (need funding)
- **Mitigation:**
  - Stay on free tiers as long as possible
  - Paid plans are reasonable ($40-50/mo total at scale)
  - Consider donations/sponsorships
  - Consider Pro tier for power users

**Risk 9: Competition Launches Similar Product**
- **Likelihood:** Medium
- **Impact:** Medium (market gets crowded)
- **Mitigation:**
  - Launch quickly (first-mover advantage)
  - Build loyal user base
  - Differentiate on UX and design
  - Add unique features (shareable charts, historical data)

**Risk 10: FEC Data Quality Issues**
- **Likelihood:** Low
- **Impact:** Medium (inaccurate data damages trust)
- **Mitigation:**
  - Show "Last Updated" timestamps
  - Link to original FEC reports
  - Disclaimer: "Data sourced from FEC"
  - Handle missing/null data gracefully
  - Monitor data anomalies

---

## Next Steps

### Immediate Actions (This Week)

1. **Review this roadmap** with stakeholders
2. **Prioritize phases** - Confirm Phase 1 (Notifications) is priority
3. **Set up accounts:**
   - SendGrid free account
   - Test email domain verification
4. **Create project board** - GitHub Projects or Trello with tasks
5. **Start Phase 1A** - Authentication system

### Weekly Milestones

**Week 1:** Phase 1A complete (Auth working)
**Week 2:** Phase 1B complete (Follow system working)
**Week 3:** Phase 1C + 1D complete (Notifications working end-to-end)
**Week 4:** Phase 1 testing & bug fixes
**Week 5:** Phase 1 launch + monitor
**Week 6-7:** Phase 2 (Historical + Quarterly)
**Week 8-10:** Phase 3 (Visual Excellence)

### Questions to Answer Before Starting

1. **Who is the primary developer?** (Solo or team?)
2. **What's the realistic timeline?** (Part-time or full-time work?)
3. **What's the budget?** (SendGrid paid tier, designer, etc.)
4. **Who are the beta testers?** (Need 5-10 target users)
5. **What's the launch plan?** (Marketing, PR, social media?)
6. **How will we measure success?** (Analytics setup, goals)

---

## Appendix

### Development Resources

**Supabase Documentation:**
- Auth: https://supabase.com/docs/guides/auth
- Database: https://supabase.com/docs/guides/database
- RLS: https://supabase.com/docs/guides/auth/row-level-security

**SendGrid Documentation:**
- Getting Started: https://docs.sendgrid.com/for-developers/sending-email
- API Reference: https://docs.sendgrid.com/api-reference

**React Documentation:**
- Hooks: https://react.dev/reference/react
- Context: https://react.dev/reference/react/useContext

**Tailwind CSS:**
- Documentation: https://tailwindcss.com/docs
- Tailwind UI: https://tailwindui.com/ (paid components)

### Code Snippets

**Supabase Auth Context:**
```jsx
// src/contexts/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../utils/supabaseClient';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const value = {
    user,
    loading,
    signUp: (data) => supabase.auth.signUp(data),
    signIn: (data) => supabase.auth.signInWithPassword(data),
    signOut: () => supabase.auth.signOut(),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
```

**Follow Button Component:**
```jsx
// src/components/follow/FollowButton.jsx
import { useState } from 'react';
import { supabase } from '../../utils/supabaseClient';
import { useAuth } from '../../contexts/AuthContext';

export function FollowButton({
  candidateId,
  candidateName,
  party,
  office,
  state,
  district,
  size = 'md'
}) {
  const { user } = useAuth();
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (!user) {
      // Show login modal
      return;
    }

    setLoading(true);

    try {
      if (isFollowing) {
        // Unfollow
        await supabase
          .from('user_candidate_follows')
          .delete()
          .eq('user_id', user.id)
          .eq('candidate_id', candidateId);

        setIsFollowing(false);
        toast.success(`No longer following ${candidateName}`);
      } else {
        // Follow
        await supabase
          .from('user_candidate_follows')
          .insert({
            user_id: user.id,
            candidate_id: candidateId,
            candidate_name: candidateName,
            party,
            office,
            state,
            district,
            notification_enabled: true
          });

        setIsFollowing(true);
        toast.success(`Following ${candidateName}`);
      }
    } catch (error) {
      toast.error('Something went wrong');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`
        flex items-center gap-2 rounded-lg transition-colors
        ${size === 'sm' ? 'px-2 py-1 text-xs' : 'px-4 py-2 text-sm'}
        ${isFollowing
          ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }
        ${loading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      {loading ? (
        <Spinner size={size} />
      ) : (
        <HeartIcon filled={isFollowing} />
      )}
      {isFollowing ? 'Following' : 'Follow'}
    </button>
  );
}
```

### Design Assets

**Color Palette:**
```css
/* Brand Colors */
--navy: #001F3F;
--blue: #2563EB;
--blue-light: #DBEAFE;
--red: #DC2626;
--red-light: #FEE2E2;

/* Neutral Grays */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-600: #4B5563;
--gray-900: #111827;

/* Party Colors */
--democrat: #2563EB;
--republican: #DC2626;
--independent: #9CA3AF;
--libertarian: #F59E0B;
--green: #10B981;
```

**Typography:**
```css
/* Font Stack */
font-family: 'Inter', system-ui, -apple-system, sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
--text-3xl: 1.875rem; /* 30px */
```

---

## Future Features (Backlog)

Features identified for future development, not currently scheduled.

### Candidate Registration Detection (Form 2 Monitoring)

**Problem:** "Hotshot" candidates announce their campaigns well before their first financial filing. Users may want to watch these candidates, but they won't appear in our database until we run collection scripts.

**Proposed Solution:**
- Add Form 2 (Statement of Candidacy) detection to our monitoring system
- When FEC receives a new candidate registration, automatically add them to our `candidates` table
- This allows users to "Watch" candidates before their first financial filing

**Implementation Options:**
1. **Form 2 Detection:** Add `'F2'` to the form_type filter in `detect_new_filings.py`
2. **Periodic Candidate Sync:** Daily/weekly pull of `/candidates/` endpoint to catch new registrations
3. **Both:** Real-time Form 2 detection + periodic sync as backup

**Timeline:** Post-Jan 15, 2026 (after notification system is battle-tested)

**Estimated Effort:** Small - extends existing detection infrastructure

**Related:** This is separate from the financial filing notification system (which is production-ready for Jan 15, 2026).

---

**Document Version:** 1.1
**Last Updated:** December 15, 2025
**Next Review:** After Phase 1 completion

---

**End of Roadmap Phase 2**
