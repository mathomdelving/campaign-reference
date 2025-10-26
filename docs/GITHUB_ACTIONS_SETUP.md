# GitHub Actions Setup Guide

This guide explains how to set up automated FEC data updates using GitHub Actions.

## What We've Created

The workflow file `.github/workflows/update-data.yml` is now in your repository. It will:

1. **Run daily at 6 AM ET** - Regular data updates
2. **Run every 2 hours during filing periods** - Days 13-17 of January, April, July, and October
3. **Can be triggered manually** - Via GitHub's web interface

## Required GitHub Secrets

Before the automation will work, you need to add three secrets to your GitHub repository:

### Step-by-Step Instructions

1. **Go to your GitHub repository** in a web browser
   - Navigate to: `https://github.com/YOUR_USERNAME/fec-dashboard`

2. **Click on "Settings"** (top navigation bar)

3. **In the left sidebar, click "Secrets and variables"** → **"Actions"**

4. **Click "New repository secret"** button

5. **Add these three secrets one at a time:**

   **Secret 1: FEC_API_KEY**
   - Name: `FEC_API_KEY`
   - Value: Your FEC API key (from your local `.env` file)
   - Click "Add secret"

   **Secret 2: SUPABASE_URL**
   - Name: `SUPABASE_URL`
   - Value: Your Supabase project URL (from your local `.env` file)
   - Click "Add secret"

   **Secret 3: SUPABASE_KEY**
   - Name: `SUPABASE_KEY`
   - Value: Your Supabase service role key (from your local `.env` file)
   - Click "Add secret"

## How to Test the Workflow

After pushing the workflow file to GitHub and adding the secrets:

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Click "Update FEC Campaign Finance Data" in the left sidebar
4. Click "Run workflow" dropdown (right side)
5. Click the green "Run workflow" button
6. Watch the workflow run in real-time

## Workflow Details

### Schedule
- **Daily**: Runs at 11:00 UTC (6 AM ET)
- **Filing periods**: Runs every 2 hours on days 13-17 of Jan/Apr/Jul/Oct

### What It Does
1. Checks out your repository code
2. Sets up Python environment
3. Installs dependencies from `requirements.txt`
4. Runs `fetch_fec_data.py` with your FEC API key
5. Runs `load_to_supabase.py` to update the database
6. Logs completion with file sizes
7. If it fails, uploads debug logs and sends error notification

### GitHub Actions Free Tier
- 2,000 minutes/month for free
- Each update takes ~5-10 minutes
- Daily updates: ~300 minutes/month (well within limit)
- Filing period updates: ~500 additional minutes during those 4 months
- **Total usage**: ~500-800 minutes/month (within free tier)

## Monitoring

### Check Workflow Status
- Go to repository → "Actions" tab
- See all workflow runs with success/failure status
- Click any run to see detailed logs

### Email Notifications
- GitHub will email you if a workflow fails
- Configure in GitHub Settings → Notifications

### View Logs
- Click on any workflow run
- Click on "update-fec-data" job
- Expand any step to see detailed output

## Troubleshooting

### Workflow Not Running
1. Check that the workflow file is in `.github/workflows/` directory
2. Verify all three secrets are added correctly
3. Ensure repository is public or you have GitHub Actions enabled

### Workflow Fails
1. Click on the failed run
2. Check the error message in the logs
3. Common issues:
   - Incorrect secret values (check for typos)
   - FEC API rate limiting (will retry next scheduled run)
   - Supabase connection issues

### Rate Limiting
- FEC API: 1,000 requests/hour
- If you hit the limit, the script will handle it gracefully
- Next scheduled run will continue where it left off

## Manual Trigger

To manually trigger an update anytime:
1. Go to repository → "Actions" tab
2. Click "Update FEC Campaign Finance Data"
3. Click "Run workflow" → "Run workflow"
4. Wait 5-10 minutes for completion

## Next Steps

After setting up GitHub Actions:
1. Push this repository to GitHub (if not already done)
2. Add the three required secrets
3. Test the manual trigger
4. Wait for the first scheduled run
5. Monitor the "Actions" tab for success
6. Move on to Phase 5 (Deployment to Vercel)
