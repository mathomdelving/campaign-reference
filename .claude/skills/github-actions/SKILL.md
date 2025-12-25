---
name: github-actions
description: Trigger, monitor, and troubleshoot GitHub Actions workflows for FEC data updates. Use when the user asks to run data updates, check workflow status, trigger manual refresh, view Actions logs, debug failed workflows, or asks about automated data collection.
allowed-tools: Bash, Read, Grep
---

# GitHub Actions Skill

## Available Workflows

| Workflow | File | Schedule | Purpose |
|----------|------|----------|---------|
| **Incremental Update** | `incremental-update.yml` | Daily 6 AM ET + filing periods | Regular data refresh |
| **Full Refresh** | `full-refresh.yml` | Weekly Sunday 2 AM ET | Complete data reload |

**Filing period intensive schedule:** Days 13-17 of January, April, July, October (runs every 2 hours)

---

## Quick Commands

### Check Workflow Status
```bash
# List recent runs for each workflow
gh run list --workflow=incremental-update.yml --limit=5
gh run list --workflow=full-refresh.yml --limit=5

# Check all recent runs
gh run list --limit=10
```

### Trigger Manual Run
```bash
# Incremental update (faster, daily changes only)
gh workflow run incremental-update.yml

# Full refresh (complete reload, slower)
gh workflow run full-refresh.yml
```

### View Run Logs
```bash
# Get the latest run ID
gh run list --limit=1 --json databaseId --jq '.[0].databaseId'

# View logs for a specific run
gh run view <RUN_ID> --log

# View failed steps only
gh run view <RUN_ID> --log-failed
```

### Check if Workflow is Currently Running
```bash
gh run list --status=in_progress
```

### Watch a Run in Real-Time
```bash
gh run watch
```

---

## Workflow Details

### Incremental Update (`incremental-update.yml`)
- **What it does:** Fetches recent filings and updates database
- **Duration:** ~5-30 minutes depending on new data
- **Schedule:** Daily at 11:00 UTC (6 AM ET)
- **Filing periods:** Every 2 hours on days 13-17 of Jan/Apr/Jul/Oct

### Full Refresh (`full-refresh.yml`)
- **What it does:** Complete re-collection of all cycle data
- **Duration:** Several hours (depends on cycles configured)
- **Schedule:** Weekly on Sunday at 07:00 UTC (2 AM ET)
- **Use when:** Data integrity issues, schema changes, or major updates needed

---

## Required GitHub Secrets

Navigate to: `Repository Settings → Secrets and variables → Actions`

| Secret | Description | Where to Find |
|--------|-------------|---------------|
| `FEC_API_KEY` | FEC OpenFEC API key | https://api.open.fec.gov/developers/ |
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_KEY` | Supabase **service_role** key | Supabase Dashboard → Settings → API |
| `SENDGRID_API_KEY` | (Optional) Email notifications | SendGrid Dashboard |
| `SENDGRID_FROM_EMAIL` | (Optional) Sender email | Your verified sender |

**Important:** Use the **service_role** key for GitHub Actions (not the anon key).

---

## Troubleshooting

### Workflow Not Running on Schedule
1. Verify repository has Actions enabled
2. Check workflow file syntax: `.github/workflows/*.yml`
3. Ensure at least one push has occurred recently (GitHub disables scheduled workflows on inactive repos)

### "FEC_API_KEY not found" Error
1. Go to: Repository Settings → Secrets → Actions
2. Verify `FEC_API_KEY` secret exists
3. Check for typos in secret name

### "Supabase connection failed"
1. Verify `SUPABASE_KEY` is the **service_role** key (not anon)
2. Check `SUPABASE_URL` format: `https://xxxxx.supabase.co`
3. Verify secrets don't have trailing whitespace

### Rate Limit Errors (429)
- Script handles this automatically with exponential backoff
- Check if others are using the same API key
- Next scheduled run will continue where it left off

### Workflow Keeps Failing
```bash
# View the failed run's logs
gh run view <RUN_ID> --log-failed

# Re-run failed jobs only
gh run rerun <RUN_ID> --failed
```

---

## Monitoring

### View in Browser
```
https://github.com/YOUR_USERNAME/campaign-reference/actions
```

### Email Notifications
GitHub automatically emails on workflow failures.
Configure in: GitHub Settings → Notifications → Actions

### Check Workflow Health
```bash
# See success/failure rate
gh run list --limit=20 --json status,conclusion | jq 'group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

---

## GitHub Actions Free Tier

| Resource | Limit | Typical Usage |
|----------|-------|---------------|
| Minutes/month | 2,000 | ~500-800 |
| Storage | 500 MB | Minimal |
| Concurrent jobs | 20 | 1-2 |

**Status:** Well within free tier limits.

---

## File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/incremental-update.yml` | Daily update workflow |
| `.github/workflows/full-refresh.yml` | Weekly full refresh workflow |
| `scripts/data-collection/` | Collection scripts used by workflows |
| `scripts/data-loading/` | Loading scripts used by workflows |
