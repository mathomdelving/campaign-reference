# Notification System - Production Readiness Checklist

**Target: Q1 2025 Filings (January) - Dry Run**
**Launch: Q2 2025 Filings (April)**

## Status: 🟡 NEARLY COMPLETE - Action Items Below

---

## ✅ COMPLETE

### Core Infrastructure
- [x] **Database Tables**
  - [x] `user_candidate_follows` table (migration exists)
  - [x] `notification_queue` table (migration exists)
  - [x] Proper indexes for performance
  - [x] Unique constraints for deduplication

- [x] **Backend Scripts**
  - [x] `detect_new_filings.py` - Polls FEC API, creates queue entries
  - [x] `send_notifications.py` - Sends emails via SendGrid
  - [x] Rate limit awareness (designed for 7k/hour, works at 1k/hour)
  - [x] Dry-run modes for testing
  - [x] Error handling and logging

- [x] **Frontend UI**
  - [x] NotificationSettingsView - Toggle notifications per candidate
  - [x] FollowButton - Follow/unfollow candidates
  - [x] Beautiful email templates (HTML + plain text)

- [x] **Documentation**
  - [x] README_NOTIFICATIONS.md - Complete usage guide
  - [x] Inline code documentation
  - [x] Troubleshooting guides

---

## 🔴 CRITICAL - MUST FIX BEFORE Q1

### 1. **Database Migrations Not Applied**

**Issue:** Migrations exist but haven't been run on your Supabase database.

**Action Required:**
```bash
# Check if tables exist in Supabase SQL Editor:
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user_candidate_follows', 'notification_queue');

# If they don't exist, run these migrations in order:
# 1. database/migrations/002_user_candidate_follows.sql
# 2. database/migrations/003_notification_queue.sql
```

**How to Apply:**
1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `002_user_candidate_follows.sql`
3. Run it
4. Copy contents of `003_notification_queue.sql`
5. Run it

---

### 2. **RLS Policy for notification_queue**

**Issue:** Supabase flagged `notification_queue` as needing RLS policies.

**Action Required:**
Create and run this SQL in Supabase:

```sql
-- Enable RLS on notification_queue
ALTER TABLE notification_queue ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (backend scripts)
CREATE POLICY "Service role full access" ON notification_queue
  FOR ALL USING (auth.role() = 'service_role');

-- Users cannot directly access the queue (no public access)
-- All access must go through backend scripts
```

**File created:** I'll create this for you now.

---

### 3. **SendGrid Configuration**

**Issue:** Need to verify SendGrid is configured and working.

**Action Required:**
1. **Verify API key in `.env`:**
   ```bash
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   SENDGRID_FROM_EMAIL=notifications@campaign-reference.com
   SENDGRID_FROM_NAME=Campaign Reference
   ```

2. **Verify sender in SendGrid:**
   - Go to SendGrid Dashboard → Settings → Sender Authentication
   - Verify `notifications@campaign-reference.com` is authenticated
   - OR use Single Sender Verification

3. **Test email sending:**
   ```bash
   # Create a test notification manually in database, then:
   python scripts/maintenance/send_notifications.py --dry-run
   python scripts/maintenance/send_notifications.py --limit 1
   ```

---

### 4. **Unsubscribe Handler**

**Issue:** Email template has unsubscribe link but no backend handler.

**Action Required:** I'll create an unsubscribe page/API endpoint.

**Current link in email:**
```
https://campaign-reference.com/unsubscribe?user={user_id}&candidate={candidate_id}
```

**Need to create:**
- `/app/unsubscribe/page.tsx` - Unsubscribe page
- Updates `user_candidate_follows.notification_enabled = false`
- OR deletes the follow entirely (user's choice)

---

## 🟡 IMPORTANT - Should Fix Before Q2 Launch

### 5. **Deployment Strategy**

**Issue:** Where will the detection script run continuously?

**Options:**

**Option A: GitHub Actions (Free tier limits)**
- Run detect script every 5 minutes via cron
- Limitation: Can't run more frequently than every 5 minutes
- Good for: Testing, low-traffic periods

**Option B: Dedicated Server/VPS ($5-10/month)**
- Run detect script continuously
- Use systemd service for auto-restart
- Good for: Production filing day

**Option C: Vercel Cron Jobs**
- Serverless cron that triggers API endpoint
- API endpoint calls detection logic
- Good for: Scalability, zero maintenance

**My Recommendation:** Start with GitHub Actions for Q1 dry run, then move to dedicated server for Q2 launch.

---

### 6. **Monitoring & Alerting**

**Issue:** No way to know if the system breaks.

**Action Required:**

1. **Add health check script:**
   - Checks if detection script is running
   - Checks if queue is growing (sign of email sending failure)
   - Sends alert if issues detected

2. **Monitor key metrics:**
   - Notifications queued per hour
   - Notifications sent per hour
   - Failed notifications
   - Detection script uptime

3. **Set up alerts:**
   - Email yourself if detection stops
   - Email yourself if queue > 100 pending
   - Email yourself if send success rate < 90%

**I can create these monitoring scripts.**

---

### 7. **Rate Limit Buffer**

**Issue:** Detection script assumes 7k/hour, but you currently have 1k/hour.

**Action Required:**
Update the script constant:

```python
# In detect_new_filings.py, line ~35
CURRENT_RATE_LIMIT = 1000  # Change to 7000 when you upgrade
```

For Q1 testing at 1k/hour, use slower polling:
```bash
python scripts/maintenance/detect_new_filings.py --interval 60  # Every 60 seconds instead of 30
```

---

### 8. **Email Volume Testing**

**Issue:** SendGrid free tier has limits.

**Action Required:**
1. **Check SendGrid plan limits:**
   - Free: 100 emails/day
   - Essentials: 40k emails/month ($19.95)
   - Pro: 100k emails/month ($89.95)

2. **Estimate email volume:**
   - If 100 users each follow 5 candidates = 500 follows
   - On filing day (300 candidates file) × (5 followers each) = 1,500 emails
   - Need at least Essentials plan

3. **Test with your team first:**
   - Have 5-10 people follow candidates
   - Run detection script during real filing
   - Verify emails arrive within 5 minutes

---

## 🟢 NICE TO HAVE - Post Q2 Launch

### 9. **Enhanced Features**
- [ ] Daily digest option (instead of immediate emails)
- [ ] Custom notification filters (only filings > $1M)
- [ ] SMS notifications (via Twilio)
- [ ] Push notifications (web/mobile)
- [ ] Notification history in user dashboard
- [ ] A/B test different email templates

### 10. **Performance Optimizations**
- [ ] Batch email sending (SendGrid allows 1000 recipients per API call)
- [ ] Cache followed candidates (refresh every 5 minutes)
- [ ] Use FEC webhooks (if they add them)
- [ ] Database read replicas for high traffic

---

## Testing Plan for Q1 Dry Run

### Week 1 (Early January)
- [ ] Apply all database migrations
- [ ] Configure SendGrid and test sending
- [ ] Create unsubscribe handler
- [ ] Set up detection script on GitHub Actions or VPS
- [ ] Have your team follow 10-20 candidates

### Week 2 (Mid January)
- [ ] Run detection script in dry-run mode for 24 hours
- [ ] Manually trigger a test notification
- [ ] Verify email arrives with correct data
- [ ] Test unsubscribe link works
- [ ] Monitor for errors

### Week 3 (Late January - Filing Deadline Week)
- [ ] Switch to LIVE mode (remove --dry-run)
- [ ] Monitor detection script logs
- [ ] Check notification_queue table hourly
- [ ] Verify emails are sent within 5 minutes
- [ ] Document any issues

### Week 4 (Post-Filing Analysis)
- [ ] Review metrics:
  - How many filings detected?
  - How many notifications sent?
  - Average latency (filing → email)?
  - Any failures?
- [ ] Fix any issues found
- [ ] Prepare for Q2 launch

---

## Quick Start Commands

### Apply Migrations
```bash
# In Supabase SQL Editor:
# 1. Run contents of database/migrations/002_user_candidate_follows.sql
# 2. Run contents of database/migrations/003_notification_queue.sql
```

### Test Detection (Dry Run)
```bash
python scripts/maintenance/detect_new_filings.py --once --dry-run
```

### Test Email Sending (Dry Run)
```bash
python scripts/maintenance/send_notifications.py --dry-run
```

### Run Live (Filing Day)
```bash
# Terminal 1: Detect filings
python scripts/maintenance/detect_new_filings.py --interval 60

# Terminal 2: Send emails every 5 minutes
while true; do
  python scripts/maintenance/send_notifications.py
  sleep 300
done
```

---

## Critical Action Items Summary

**Before Q1 Dry Run (Do This Week):**
1. ✅ Apply database migrations (002 and 003)
2. ✅ Add RLS policy for notification_queue
3. ✅ Configure and test SendGrid
4. ✅ Create unsubscribe handler
5. ✅ Set up deployment (GitHub Actions or VPS)
6. ✅ Test end-to-end with real users

**Before Q2 Launch (Do in March):**
1. ✅ Set up monitoring and alerts
2. ✅ Upgrade FEC API to 7k/hour
3. ✅ Upgrade SendGrid plan if needed
4. ✅ Analyze Q1 metrics and fix issues

---

## Current Status: ~80% Complete

**You have:**
- ✅ All core code written
- ✅ Database schema designed
- ✅ Email templates created
- ✅ Documentation complete

**You need:**
- 🔴 Apply migrations to database
- 🔴 Configure SendGrid
- 🔴 Create unsubscribe handler
- 🔴 Deploy detection script
- 🔴 Test end-to-end

**Timeline Estimate:**
- Database setup: 30 minutes
- SendGrid setup: 1 hour
- Unsubscribe page: 2-3 hours
- Deployment setup: 2-4 hours
- Testing: 1-2 days

**Total: ~3-5 days of work to be production-ready for Q1**
