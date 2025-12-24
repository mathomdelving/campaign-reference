# Filing Notification System

Complete system for detecting new FEC filings and notifying users via email.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. DETECT NEW FILINGS (detect_new_filings.py)            │
│     - Polls FEC API every 30 seconds                        │
│     - Finds candidates with new filings                     │
│     - Creates notification_queue entries                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  2. DATABASE (notification_queue table)                     │
│     - Stores pending notifications                          │
│     - Status: pending → sent/failed                         │
│     - Includes all filing data for email                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  3. SEND EMAILS (send_notifications.py)                     │
│     - Processes notification_queue                          │
│     - Sends HTML emails via SendGrid                        │
│     - Updates status after sending                          │
└─────────────────────────────────────────────────────────────┘
```

## Recent Updates (December 2025)

### ✅ Test-All Mode for Early Filer Detection
Added `--test-all EMAIL` mode to catch **any** new filing during the testing period (Jan 5-11) before the Jan 15 deadline:

```bash
# Notify you of ALL filings (regardless of follows)
python scripts/maintenance/detect_new_filings.py --test-all your@email.com

# Dry run first
python scripts/maintenance/detect_new_filings.py --test-all your@email.com --dry-run --once
```

### ✅ Office Display Consistency Fix
Fixed formatting to handle all office variations consistently:
- `office='H'` or `'House'` → **U.S. House - ST-##**
- `office='S'` or `'Senate'` → **U.S. Senate - ST**
- `office='P'` or `'President'` → **U.S. President**
- `district='00'` treated as no district (Senate placeholder)

### ✅ Per-Filing Financial Data
Changed from cumulative cycle totals to per-filing amounts:
- Notifications now show the amounts from that specific filing
- Uses `quarterly_financials` table instead of `financial_summary`
- Correctly displays Q3 amounts for Q3 filings, Year-End amounts for Year-End filings, etc.

### ✅ Candidate Resolution from Committee
Added `resolve_candidate_from_committee()` to handle filings without `candidate_id`:
- First checks our database
- Falls back to FEC API committee endpoint
- Enriches filings with candidate name, party, state, office, district

---

## Quick Start

### Prerequisites

1. **Environment Variables** (`.env` file):
   ```bash
   # Supabase
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_service_role_key

   # FEC API
   FEC_API_KEY=your_fec_api_key

   # SendGrid (for emails)
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDGRID_FROM_EMAIL=notifications@campaign-reference.com
   SENDGRID_FROM_NAME=Campaign Reference
   ```

2. **Database Tables**:
   - `user_candidate_follows` - Who's watching which candidates
   - `notification_queue` - Email queue (created by migration)

3. **Python Dependencies**:
   ```bash
   pip install requests python-dotenv supabase
   ```

## Usage

### Step 1: Detect New Filings

**Run continuously (filing day):**
```bash
python scripts/maintenance/detect_new_filings.py
```

**Check once and exit:**
```bash
python scripts/maintenance/detect_new_filings.py --once
```

**Dry run (preview without creating notifications):**
```bash
python scripts/maintenance/detect_new_filings.py --dry-run
```

**Custom interval:**
```bash
python scripts/maintenance/detect_new_filings.py --interval 60  # Check every 60 seconds
```

**What it does:**
- Polls FEC `/filings/` endpoint for new reports
- Checks which users follow those candidates
- Creates entries in `notification_queue`
- Uses ~120 requests/hour (30-second polling)

### Step 2: Send Email Notifications

**Send all pending notifications:**
```bash
python scripts/maintenance/send_notifications.py
```

**Limit batch size:**
```bash
python scripts/maintenance/send_notifications.py --limit 10
```

**Preview emails without sending:**
```bash
python scripts/maintenance/send_notifications.py --dry-run
```

**What it does:**
- Fetches pending notifications from queue
- Sends beautiful HTML emails via SendGrid
- Includes candidate name, party, financial data
- Marks as `sent` or `failed` with retry logic

## Filing Day Setup

### Option A: Run Both Scripts Separately

**Terminal 1 - Detect filings:**
```bash
python scripts/maintenance/detect_new_filings.py
```

**Terminal 2 - Send emails (run every 5 minutes):**
```bash
while true; do
  python scripts/maintenance/send_notifications.py
  sleep 300
done
```

### Option B: Scheduled Jobs (Production)

**Cron jobs:**
```cron
# Detect new filings every 30 seconds (use systemd service instead for < 1 min intervals)
* * * * * cd /path/to/fec-dashboard && python scripts/maintenance/detect_new_filings.py --once
* * * * * sleep 30 && cd /path/to/fec-dashboard && python scripts/maintenance/detect_new_filings.py --once

# Send notifications every 5 minutes
*/5 * * * * cd /path/to/fec-dashboard && python scripts/maintenance/send_notifications.py
```

**Or use systemd service (better for frequent runs):**
```ini
[Unit]
Description=FEC Filing Detection Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/fec-dashboard
ExecStart=/usr/bin/python3 scripts/maintenance/detect_new_filings.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Performance & Rate Limits

### Current Rate Limit: 7,000 requests/hour ✅

**Detection script:**
- Polls every 30 seconds = 120 requests/hour
- Remaining: 6,880 requests/hour for detail fetches
- Can handle 3,000+ new filings per hour easily
- Well within capacity for Jan 15 filing deadline

### Expected Latency

**From filing to user notification:**
1. **Detection:** 0-30 seconds (polling interval)
2. **Queue creation:** <1 second
3. **Email sending:** 1-5 seconds (SendGrid)
4. **Total:** ~5-40 seconds

On filing day with emails sent every 5 minutes:
- **Total latency:** 35 seconds - 5 minutes 40 seconds

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

**Deduplication:**
- The UNIQUE constraint prevents duplicate notifications
- Same user won't get multiple emails for the same filing

## Troubleshooting

### No notifications being created

1. **Check if anyone is following candidates:**
   ```sql
   SELECT COUNT(*) FROM user_candidate_follows WHERE notification_enabled = true;
   ```

2. **Check for new filings:**
   ```bash
   python scripts/maintenance/detect_new_filings.py --once --dry-run
   ```

3. **Check FEC API key:**
   ```bash
   curl "https://api.open.fec.gov/v1/filings/?api_key=YOUR_KEY&per_page=1"
   ```

### Emails not sending

1. **Check SendGrid API key:**
   ```bash
   curl -X POST https://api.sendgrid.com/v3/mail/send \
     -H "Authorization: Bearer YOUR_SENDGRID_KEY" \
     -H "Content-Type: application/json"
   ```

2. **Check notification queue:**
   ```sql
   SELECT status, COUNT(*) FROM notification_queue GROUP BY status;
   ```

3. **Run in dry-run mode:**
   ```bash
   python scripts/maintenance/send_notifications.py --dry-run
   ```

### Rate limit issues

If you hit rate limits (unlikely with 7,000/hour limit):

**Reduce polling frequency:**
```bash
python scripts/maintenance/detect_new_filings.py --interval 120  # Every 2 minutes = 30 requests/hour
```

**Or check less frequently:**
```bash
python scripts/maintenance/detect_new_filings.py --once  # Manual runs only
```

## Monitoring

### Check system health

**How many notifications are pending?**
```sql
SELECT COUNT(*) FROM notification_queue WHERE status = 'pending';
```

**How many were sent today?**
```sql
SELECT COUNT(*) FROM notification_queue
WHERE status = 'sent' AND sent_at >= CURRENT_DATE;
```

**Any failures?**
```sql
SELECT candidate_id, error_message, COUNT(*)
FROM notification_queue
WHERE status = 'failed'
GROUP BY candidate_id, error_message;
```

## Email Preview

Users receive emails that look like this:

```
┌─────────────────────────────────────────┐
│ New Filing Report                       │
│ November 15, 2025                       │
├─────────────────────────────────────────┤
│                                         │
│ REPUBLICAN                              │
│ Mike Johnson                            │
│ U.S. House - LA-04                      │
│                                         │
│ Filed a new Q3 Report covering through  │
│ September 30, 2025                      │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Total Raised:     $2,450,000        │ │
│ │ Total Spent:      $1,820,000        │ │
│ │ Cash on Hand:     $630,000          │ │
│ └─────────────────────────────────────┘ │
│                                         │
│        [View Full Details]              │
│                                         │
│ You're receiving this because you're    │
│ watching Mike Johnson on Campaign Ref.  │
│ Unsubscribe | Manage settings           │
└─────────────────────────────────────────┘
```

## Future Enhancements

- [ ] Add webhook support from FEC (if available)
- [ ] Push notifications (web push, mobile)
- [ ] SMS notifications (Twilio)
- [ ] Notification preferences (immediate vs daily digest)
- [ ] Custom notification filters (e.g., only for filings > $1M)
