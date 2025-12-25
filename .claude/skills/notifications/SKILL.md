---
name: notifications
description: Detect new FEC filings and send email notifications to users. Use when the user asks to start filing detection, send notifications, check notification queue, test the notification system, run filing day operations, or troubleshoot email delivery.
allowed-tools: Bash, Read, Grep
---

# Filing Notification System Skill

## System Overview

```
Detect Filings → Queue in Database → Send Emails
     ↓                  ↓                 ↓
  FEC API        notification_queue    SendGrid
```

**Purpose:** Notify users when candidates they follow file new FEC reports.

---

## Quick Commands

### Start Filing Detection (Continuous)
```bash
python scripts/maintenance/detect_new_filings.py
```
Polls FEC API every 30 seconds, creates notification queue entries.

### Detect Once and Exit
```bash
python scripts/maintenance/detect_new_filings.py --once
```

### Send Pending Notifications
```bash
python scripts/maintenance/send_notifications.py
```

### Dry Run (Preview Without Action)
```bash
# Preview detection without creating queue entries
python scripts/maintenance/detect_new_filings.py --dry-run --once

# Preview emails without sending
python scripts/maintenance/send_notifications.py --dry-run
```

---

## Filing Day Operations

### Option A: Two Terminals

**Terminal 1 - Detect filings continuously:**
```bash
python scripts/maintenance/detect_new_filings.py
```

**Terminal 2 - Send emails every 5 minutes:**
```bash
while true; do
  python scripts/maintenance/send_notifications.py
  sleep 300
done
```

### Option B: Background with Logging

```bash
# Start detection in background
nohup python -u scripts/maintenance/detect_new_filings.py > detection.log 2>&1 &

# Monitor detection
tail -f detection.log

# Send emails periodically (separate process)
nohup bash -c 'while true; do python scripts/maintenance/send_notifications.py >> send.log 2>&1; sleep 300; done' &
```

---

## Test Mode (Early Filer Detection)

During testing period (Jan 5-11), catch ANY new filing regardless of follows:

```bash
# Notify you of ALL filings
python scripts/maintenance/detect_new_filings.py --test-all your@email.com

# Dry run first
python scripts/maintenance/detect_new_filings.py --test-all your@email.com --dry-run --once
```

---

## Environment Requirements

Required in `.env`:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# FEC API
FEC_API_KEY=your_fec_api_key

# SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=notifications@campaign-reference.com
SENDGRID_FROM_NAME=Campaign Reference
```

---

## Monitoring Queries

### Check Notification Queue Status
```sql
SELECT status, COUNT(*)
FROM notification_queue
GROUP BY status;
```

### Pending Notifications
```sql
SELECT COUNT(*) FROM notification_queue WHERE status = 'pending';
```

### Sent Today
```sql
SELECT COUNT(*) FROM notification_queue
WHERE status = 'sent' AND sent_at >= CURRENT_DATE;
```

### Failed Notifications
```sql
SELECT candidate_id, error_message, COUNT(*)
FROM notification_queue
WHERE status = 'failed'
GROUP BY candidate_id, error_message;
```

### Users with Notifications Enabled
```sql
SELECT COUNT(*) FROM user_candidate_follows WHERE notification_enabled = true;
```

---

## Troubleshooting

### No Notifications Being Created

1. **Check if anyone is following candidates:**
   ```sql
   SELECT COUNT(*) FROM user_candidate_follows WHERE notification_enabled = true;
   ```

2. **Test detection in dry-run:**
   ```bash
   python scripts/maintenance/detect_new_filings.py --once --dry-run
   ```

3. **Verify FEC API key:**
   ```bash
   curl "https://api.open.fec.gov/v1/filings/?api_key=$FEC_API_KEY&per_page=1"
   ```

### Emails Not Sending

1. **Check queue has pending items:**
   ```sql
   SELECT * FROM notification_queue WHERE status = 'pending' LIMIT 5;
   ```

2. **Test SendGrid API key:**
   ```bash
   curl -X POST https://api.sendgrid.com/v3/mail/send \
     -H "Authorization: Bearer $SENDGRID_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"personalizations":[{"to":[{"email":"test@test.com"}]}],"from":{"email":"test@test.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'
   ```

3. **Run send script in dry-run:**
   ```bash
   python scripts/maintenance/send_notifications.py --dry-run
   ```

### Rate Limit Issues

Reduce polling frequency:
```bash
# Every 2 minutes instead of 30 seconds
python scripts/maintenance/detect_new_filings.py --interval 120
```

---

## Performance

### Rate Limits
- **FEC API:** 7,000 requests/hour
- **Detection script:** ~120 requests/hour (30-second polling)
- **Headroom:** 6,880+ requests/hour for detail fetches

### Expected Latency (Filing to Email)
| Step | Time |
|------|------|
| Detection | 0-30 seconds |
| Queue creation | <1 second |
| Email sending | 1-5 seconds |
| **Total** | **~5-40 seconds** |

With 5-minute email batches: 35 seconds - 5 minutes 40 seconds total.

---

## Database Schema

### notification_queue table
```sql
CREATE TABLE notification_queue (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  candidate_id TEXT NOT NULL,
  filing_date DATE NOT NULL,
  filing_data JSONB NOT NULL,
  status TEXT DEFAULT 'pending',  -- pending, sent, failed
  queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  UNIQUE(user_id, candidate_id, filing_date)
);
```

**Deduplication:** The UNIQUE constraint prevents duplicate notifications for the same user/candidate/filing.

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/maintenance/detect_new_filings.py` | Filing detection script |
| `scripts/maintenance/send_notifications.py` | Email sending script |
| `scripts/maintenance/README_NOTIFICATIONS.md` | Full documentation |

---

## Pre-Filing Day Checklist

- [ ] Environment variables set (Supabase, FEC, SendGrid)
- [ ] Test detection: `--dry-run --once`
- [ ] Test email sending: `--dry-run`
- [ ] Verify users have follows with `notification_enabled = true`
- [ ] Test end-to-end with `--test-all your@email.com`
- [ ] Plan monitoring strategy (which terminal windows, log files)
