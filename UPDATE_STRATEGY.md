# FEC Data Update Strategy

## Overview

Campaign Reference uses an **incremental update strategy** to keep FEC campaign finance data fresh without the overhead of full data refreshes. This approach is ~500x faster than full refreshes for daily updates.

## Update Architecture

### 1. Incremental Updates (Default)
**Script:** `incremental_update.py`
**Frequency:** Daily + Filing Periods

**How it works:**
1. Queries FEC `/filings/` endpoint for new filings since last update
2. Extracts candidate IDs from recent filings
3. Updates only those candidates with new activity
4. Logs update to `data_refresh_log` table

**Performance:**
- Typical daily update: **2-3 minutes** (10-50 candidates)
- Filing period update: **5-10 minutes** (100-200 candidates)
- vs Full refresh: **17-18 hours** (5,185 candidates)

### 2. Weekly Full Refresh (Safety Net)
**Script:** `fetch_fec_data.py` + `load_to_supabase.py`
**Frequency:** Weekly (Sundays at 2 AM ET)

**Purpose:**
- Catches any missed updates or data corrections
- Ensures data integrity
- Updates candidates with no recent filings

**Performance:** 17-18 hours (runs overnight)

## Scheduled Updates

### GitHub Actions Workflows

#### `incremental-update.yml`
```yaml
Daily: 6 AM ET (11 AM UTC)
Filing Periods: Every 2 hours (days 13-17 of Jan/Apr/Jul/Oct)
Peak Hours: Every 30 minutes (9am-6pm ET on the 15th of quarter months)
```

#### `full-refresh.yml`
```yaml
Weekly: Sundays at 2 AM ET (7 AM UTC)
```

## Filing Period Schedule

FEC quarterly filing deadlines occur on the **15th** of:
- **January** (Q4 of previous year)
- **April** (Q1)
- **July** (Q2)
- **October** (Q3)

During these periods, the system checks for updates every 2 hours on days 13-17, and every 30 minutes during business hours on the deadline day itself.

## Data Freshness Indicators

### UI Display
All three views (Leaderboard, District, Candidate) show a data freshness indicator in the header:

- **Green dot + pulse**: Updated within last 2 hours
- **Green dot**: Updated within last 24 hours
- **Yellow dot**: Updated 24-48 hours ago
- **Red dot**: Updated >48 hours ago

Hover over the indicator to see the exact update timestamp.

### Database Tracking
The `data_refresh_log` table tracks every update:
- `fetch_date`: When the update occurred
- `cycle`: Election cycle (2026)
- `records_updated`: Number of records modified
- `status`: success/partial/failed
- `duration_seconds`: How long the update took

## Manual Updates

### Trigger via GitHub Actions
1. Go to https://github.com/mathomdelving/campaign-reference/actions
2. Select "Incremental Data Update" workflow
3. Click "Run workflow"
4. Optionally specify lookback days (default: since last update)

### Run Locally

**Incremental update:**
```bash
python incremental_update.py                    # Since last update
python incremental_update.py --lookback 7      # Last 7 days
```

**Full refresh:**
```bash
python fetch_fec_data.py      # Fetch all candidate data (17-18 hours)
python load_to_supabase.py    # Upload to database
```

## API Rate Limiting

The FEC API has a rate limit of **1,000 requests per hour**.

**Incremental update strategy:**
- 0.5 second delay between filing requests
- 0.5 second delay between committee lookups
- 0.5 second delay between candidate requests

If rate limits are hit, the script logs the error and continues with remaining candidates.

## Future Enhancements

### Candidate-Specific Notifications (Planned)
When implemented, users will be able to:
1. Subscribe to specific candidates
2. Receive notifications when new filings are posted
3. View filing history and amendments

This will leverage the same incremental update system, with notification triggers added to the update process.

## Monitoring

### Check Update Status
```bash
python check_db_status.py
```

This displays:
- Most recent update timestamp
- Number of candidates/financial records in database
- Recent update log entries

### GitHub Actions Dashboard
View workflow runs at: https://github.com/mathomdelving/campaign-reference/actions

- Green checkmarks = successful updates
- Red X = failed updates (check logs)
- Yellow dot = workflow in progress

## Troubleshooting

### "No updates in 3+ days"
1. Check GitHub Actions dashboard for failed workflows
2. Verify GitHub Secrets are configured (FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY)
3. Manually trigger incremental update workflow
4. Check FEC API status: https://api.open.fec.gov/developers/

### Rate limit errors (429)
- Normal during large updates
- Script continues with remaining candidates
- Updates will complete on next scheduled run

### Database connection errors
- Verify SUPABASE_URL and SUPABASE_KEY in secrets
- Check Supabase project status: https://supabase.com/dashboard

## Technical Details

### Incremental Update Process
```
1. Query last update time from data_refresh_log
2. GET /filings/?min_receipt_date={last_update}&cycle=2026&form_type=F3
3. Extract unique candidate IDs from filings
4. For each candidate:
   - GET /candidate/{id}/
   - GET /candidate/{id}/totals/?cycle=2026
   - UPSERT to candidates table
   - UPSERT to financial_summary table
5. Log update to data_refresh_log
```

### Database Schema

**candidates**
- Primary key: `candidate_id`
- Indexes: `cycle`, `state`, `office`

**financial_summary**
- Primary key: `(candidate_id, cycle, coverage_end_date)`
- Includes: `updated_at` timestamp for tracking freshness

**data_refresh_log**
- Tracks all update operations
- Used to determine "since when" for incremental updates

## Cost Analysis

### API Usage

**Incremental update (typical day):**
- 50 candidates with new filings
- 3 API calls per candidate = 150 calls
- Well under 1,000/hour limit

**Full refresh (weekly):**
- 5,185 candidates
- 3 API calls per candidate = 15,555 calls
- Over 17-18 hours = ~900 calls/hour (within limits)

### Compute Time

**GitHub Actions minutes:**
- Incremental: ~3 minutes/day × 365 = ~1,095 minutes/year
- Full refresh: 18 hours/week × 52 = ~56,000 minutes/year
- **Total: ~57,000 minutes/year** (well within free tier for public repos)

## Deployment

### Initial Setup
1. Configure GitHub Secrets (FEC_API_KEY, SUPABASE_URL, SUPABASE_KEY)
2. Manually run "Incremental Data Update" workflow once to initialize
3. Scheduled workflows will automatically run going forward

### Activating Scheduled Runs
**Important:** GitHub Actions scheduled workflows (cron jobs) do not automatically start running until the workflow has been triggered at least once by another event (push, pull request, or manual trigger).

To activate:
1. Push the workflow files to the repository
2. Manually trigger the workflow once via the Actions tab
3. Subsequent scheduled runs will execute automatically
