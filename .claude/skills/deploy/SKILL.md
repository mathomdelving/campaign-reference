---
name: deploy
description: Deploy to Vercel, check deployment status, troubleshoot build failures, and manage environment variables. Use when the user asks to deploy, check if deployment succeeded, fix build errors, update Vercel settings, or troubleshoot the live site.
allowed-tools: Bash, Read, Grep
---

# Vercel Deployment Skill

## Architecture

- **Frontend (Next.js):** Deployed to Vercel from `apps/labs/`
- **Live URL:** https://campaign-reference.com
- **Auto-deploy:** Every push to `main` triggers deployment
- **Build time:** ~2-3 minutes

---

## Quick Commands

### Check Recent Deployments
```bash
# Check git log (Vercel deploys on every push to main)
git log --oneline -5

# Check current branch status
git status
```

### Deploy Changes
```bash
# Standard deployment (auto-triggered on push)
git add .
git commit -m "Your change description"
git push origin main
```

### Force Redeploy (No Code Changes)
```bash
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Test Build Locally Before Deploy
```bash
cd apps/labs
npm run build      # Build production version
npm run start      # Test production build locally at http://localhost:3000
```

### Check if Site is Up
```bash
curl -I https://campaign-reference.com
```

---

## Environment Variables (Vercel)

Set in: Vercel Dashboard → Project → Settings → Environment Variables

| Variable | Value | Environments |
|----------|-------|--------------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.supabase.co` | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGc...` | All |

**Important:**
- Use `NEXT_PUBLIC_` prefix (required for client-side access)
- Use the **anon (public)** key for frontend (NOT service_role)
- Redeploy after changing environment variables

### Get Supabase Credentials
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Settings → API
4. Copy **"Project URL"** → `NEXT_PUBLIC_SUPABASE_URL`
5. Copy **"anon public"** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

## Vercel Project Settings

### Critical Settings
- **Framework Preset:** Next.js
- **Root Directory:** `apps/labs` (NOT the repository root)
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Node.js Version:** 20.x

### How to Access Settings
1. Go to: https://vercel.com/dashboard
2. Select your project
3. Click "Settings" tab

---

## Troubleshooting

### Build Fails: "Cannot find module"
**Cause:** Root directory not set correctly
**Solution:**
1. Go to Vercel → Project Settings → General
2. Set Root Directory to `apps/labs`
3. Trigger redeploy

### Build Fails: TypeScript Errors
**Solution:** Test locally first
```bash
cd apps/labs
npm run build
```
Fix any errors, then push.

### Site Loads But Shows No Data
**Causes:**
- Environment variables not set
- Wrong prefix used (should be `NEXT_PUBLIC_`)
- Using wrong Supabase key

**Solution:**
1. Check Vercel → Settings → Environment Variables
2. Verify `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` exist
3. Redeploy after fixing

### 500 Errors on Live Site
**Solution:**
1. Check Vercel → Project → Logs (Runtime Logs)
2. Look for error messages in server components
3. Check API routes in `apps/labs/src/app/api/`

### Styles Not Loading / Broken Layout
**Solution:**
1. Clear Vercel build cache: Settings → General → "Clear Cache and Redeploy"
2. Verify Tailwind CSS config exists
3. Check `postcss.config.mjs` in `apps/labs/`

### Custom Domain Not Working
```bash
# Check DNS propagation
dig campaign-reference.com

# Check if site responds
curl -I https://campaign-reference.com
```
**Note:** DNS changes can take up to 48 hours to propagate.

### 404 on Direct Page Access
- Next.js App Router handles this automatically
- If occurring, check `next.config.ts` for custom routing issues

---

## Deployment Checklist

Before deploying:
- [ ] Local build works: `cd apps/labs && npm run build`
- [ ] Tests pass (if applicable)
- [ ] Environment variables set in Vercel
- [ ] Root directory set to `apps/labs`

After deploying:
- [ ] Site loads at https://campaign-reference.com
- [ ] Data displays correctly
- [ ] Navigation works
- [ ] Filters and search work
- [ ] Charts render

---

## Custom Domain Configuration

**Live at:** https://campaign-reference.com

### DNS Records (at your domain registrar)
| Type | Name | Value |
|------|------|-------|
| A | @ | 76.76.21.21 |
| CNAME | www | cname.vercel-dns.com |

### Verify Domain
```bash
dig campaign-reference.com
dig www.campaign-reference.com
```

---

## Rollback to Previous Deployment

If a deployment breaks the site:

1. Go to Vercel Dashboard → Project → Deployments
2. Find the last working deployment
3. Click "..." menu → "Promote to Production"

Or via git:
```bash
git revert HEAD
git push
```

---

## Monitoring

### Vercel Analytics
- Go to: Project → Analytics tab
- View traffic, performance, Web Vitals

### Real-Time Logs
- Go to: Project → Logs tab
- Filter by function, time, or error type

### Build Logs
- Go to: Project → Deployments
- Click any deployment to see build output

---

## Free Tier Limits

| Resource | Limit | Current Usage |
|----------|-------|---------------|
| Bandwidth | 100 GB/month | ~5-10 GB |
| Build minutes | 6,000/month | ~50-100 |
| Serverless functions | 100 GB-hours | Minimal |

**Status:** Well within free tier limits.

---

## File Locations

| Path | Purpose |
|------|---------|
| `apps/labs/` | Next.js application root |
| `apps/labs/src/app/` | App Router pages and layouts |
| `apps/labs/src/app/api/` | API routes |
| `apps/labs/next.config.ts` | Next.js configuration |
| `apps/labs/package.json` | Dependencies and scripts |
