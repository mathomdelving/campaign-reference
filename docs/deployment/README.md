# Deployment Guide - Campaign Reference

**Complete guide for deploying Campaign Reference to production**

**Last Updated:** November 19, 2025

---

## Quick Navigation

**New to deployment?** → Start here with this guide
**Need Vercel details?** → See `vercel-deployment.md`
**Need GitHub details?** → See `github-deployment.md`
**Need Actions reference?** → See `github-actions.md`

---

## Overview

Campaign Reference uses a two-part deployment architecture:

1. **Frontend (Next.js)** → Deployed to **Vercel**
2. **Data Pipeline (Python)** → Runs on **GitHub Actions**

This guide provides a quick-start overview. For detailed step-by-step instructions, see the specialized guides above.

---

## Part 1: GitHub Repository Setup

### Prerequisites
- GitHub account
- Git installed locally
- Code ready to push

### Step 1: Initialize and Push to GitHub

```bash
# Navigate to project
cd /Users/benjaminnelson/Desktop/fec-dashboard

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Campaign Reference"

# Create repository on GitHub: https://github.com/new
# Name: campaign-reference
# Visibility: Public (recommended for free Actions)

# Connect and push
git remote add origin https://github.com/YOUR_USERNAME/campaign-reference.git
git branch -M main
git push -u origin main
```

**Authentication:**
- Use a GitHub Personal Access Token (PAT) instead of password
- Create at: https://github.com/settings/tokens
- Required scope: `repo` (full repository access)

### Step 2: Add GitHub Secrets for Automation

Navigate to your repository settings:
`https://github.com/YOUR_USERNAME/campaign-reference/settings/secrets/actions`

**Add these secrets:**

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `FEC_API_KEY` | FEC OpenFEC API key | https://api.open.fec.gov/developers/ |
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_KEY` | Supabase service role key | Supabase Dashboard → Settings → API |
| `SENDGRID_API_KEY` | SendGrid API key (optional) | SendGrid Dashboard |
| `SENDGRID_FROM_EMAIL` | Sender email (optional) | Your verified sender |
| `SENDGRID_FROM_NAME` | Sender name (optional) | e.g., "Campaign Reference" |

**Important:**
- Use **service_role** key for GitHub Actions (not anon key)
- Never commit secrets to git
- See `docs/deployment/github-actions.md` for workflow details

---

## Part 2: Vercel Deployment (Frontend)

### Step 1: Create Vercel Account

1. Go to: https://vercel.com/signup
2. Click **"Continue with GitHub"**
3. Authorize Vercel to access your repositories

**Free tier includes:**
- Unlimited deployments
- Automatic HTTPS
- Global CDN
- 100GB bandwidth/month
- Custom domains

### Step 2: Import Repository

1. From Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find your `campaign-reference` repository
3. Click **"Import"**

### Step 3: Configure Build Settings

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** `apps/labs` ⚠️ **CRITICAL**
- Click "Edit" next to "Root Directory"
- Set to: `apps/labs`
- This tells Vercel your Next.js app is in `/apps/labs`, not root

**Build Settings** (auto-detected, verify):
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

**Node.js Version:** 20.x or higher (automatic)

### Step 4: Add Environment Variables

On the import page, scroll to **"Environment Variables"**:

**Add these two variables:**

| Name | Value | Environments |
|------|-------|--------------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.supabase.co` | Production, Preview, Development |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGc...` | Production, Preview, Development |

**Get your Supabase credentials:**
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Settings → API
4. Copy **"Project URL"** → `NEXT_PUBLIC_SUPABASE_URL`
5. Copy **"anon public"** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Important:**
- Use **anon (public)** key for frontend (safe for browser)
- Use `NEXT_PUBLIC_` prefix (not `VITE_`)
- DO NOT use service_role key in frontend

### Step 5: Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes for build to complete
3. Vercel will provide a URL: `https://campaign-reference-xxxxx.vercel.app`

**Your site is now live!** 🎉

### Step 6: Add Custom Domain (Optional)

1. In Vercel project settings, go to **"Domains"**
2. Click **"Add"**
3. Enter your domain: `campaign-reference.com`
4. Follow DNS configuration instructions
5. Vercel will automatically provision SSL certificate

**DNS Configuration:**
- Type: `CNAME`
- Name: `@` (or `www`)
- Value: `cname.vercel-dns.com`

---

## Part 3: Verify Deployment

### Frontend Checks

✅ Visit your Vercel URL
✅ Check that data loads from Supabase
✅ Test filtering and search functionality
✅ Verify charts render correctly
✅ Check mobile responsiveness

### Automation Checks

✅ Go to: `https://github.com/YOUR_USERNAME/campaign-reference/actions`
✅ Manually trigger "Full Data Refresh" workflow
✅ Monitor workflow execution (takes ~30 min for incremental)
✅ Check Supabase to verify data updated

**Workflow schedules:**
- **Incremental Update:** Daily at 6 AM ET + intensive during filing periods
- **Full Refresh:** Weekly on Sunday at 2 AM ET

See `docs/deployment/github-actions.md` for details.

---

## Part 4: Continuous Deployment

Once set up, deployments are **fully automatic:**

### Frontend (Vercel)
- **Trigger:** Any push to `main` branch
- **Build:** Automatic (~2 min)
- **Deploy:** Automatic to production URL
- **Rollback:** Available in Vercel dashboard

### Backend (GitHub Actions)
- **Trigger:** Scheduled (cron) or manual dispatch
- **Execution:** Runs on GitHub's servers
- **Logs:** Available in Actions tab
- **Notifications:** Sent on failure

**To deploy changes:**
```bash
git add .
git commit -m "Your changes"
git push origin main
```

Vercel will automatically build and deploy within 2-3 minutes.

---

## Troubleshooting

### Build Failures on Vercel

**Issue:** Build fails with "Cannot find module"
**Solution:** Verify `Root Directory` is set to `apps/labs`

**Issue:** Environment variables not working
**Solution:** Check spelling of `NEXT_PUBLIC_SUPABASE_URL` and redeploy

**Issue:** 500 errors on deployed site
**Solution:** Check Vercel Functions logs in dashboard

### GitHub Actions Failures

**Issue:** "Error: FEC_API_KEY not found"
**Solution:** Verify secrets are added in repository settings

**Issue:** "Supabase connection failed"
**Solution:** Check `SUPABASE_KEY` is the service_role key (not anon)

**Issue:** Workflow doesn't run on schedule
**Solution:** Ensure repository is not private (Actions require public repo or paid plan)

### Data Not Updating

**Issue:** Frontend shows old data
**Solution:** Check GitHub Actions logs to verify workflows ran successfully

**Issue:** Empty charts/tables
**Solution:** Run manual "Full Data Refresh" workflow to populate database

---

## Monitoring

### Vercel Analytics
- Go to: Vercel project → "Analytics"
- View traffic, performance, and errors

### GitHub Actions Status
- Go to: Repository → "Actions" tab
- View workflow runs, logs, and history

### Supabase Logs
- Go to: Supabase project → "Logs"
- View database queries and errors

---

## Cost Estimates

**Free Tier Usage (as of Nov 2025):**

| Service | Free Tier | Current Usage | Status |
|---------|-----------|---------------|--------|
| Vercel | 100 GB bandwidth | ~5-10 GB/month | ✅ Well within limit |
| GitHub Actions | 2,000 min/month | ~500-800 min/month | ✅ Well within limit |
| Supabase | 500 MB database | ~50 MB | ✅ Well within limit |

**All services remain free indefinitely with current traffic.**

---

## Next Steps

- ✅ Set up custom domain
- ✅ Configure SendGrid for email notifications
- ✅ Monitor automation workflows
- ✅ Test data updates during filing periods

---

## Additional Resources

- **GitHub Actions Workflows:** `docs/deployment/github-actions.md`
- **Vercel Documentation:** https://vercel.com/docs
- **Supabase Documentation:** https://supabase.com/docs
- **Next.js Deployment:** https://nextjs.org/docs/deployment

---

**Questions?** Check the troubleshooting section or review workflow logs.
