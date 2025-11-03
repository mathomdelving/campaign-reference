# Vercel Deployment Guide - Campaign Reference
**Updated:** November 3, 2025 (Next.js App Router)

This guide walks you through deploying Campaign Reference (Next.js) to Vercel.

---

## Part 1: Create Vercel Account

### Step 1: Sign Up for Vercel

1. **Go to:** https://vercel.com/signup
2. **Click "Continue with GitHub"** (easiest option since your code is already on GitHub)
3. **Authorize Vercel** to access your GitHub account
4. **Complete the sign-up process**

**Free Tier Includes:**
- Unlimited deployments
- Automatic HTTPS
- Global CDN
- 100GB bandwidth/month
- Custom domains supported

---

## Part 2: Import Your GitHub Repository

### Step 1: Create New Project

1. After logging in, you'll see the Vercel dashboard
2. **Click "Add New..."** → **"Project"** (top right)
3. You'll see a list of your GitHub repositories

### Step 2: Import campaign-reference

1. **Find "campaign-reference"** (or your repo name) in the list
2. **Click "Import"** next to it

---

## Part 3: Configure Build Settings

Vercel will try to auto-detect your settings. Here's what you need to configure:

### Framework Preset
- **Select:** Next.js
- Vercel should auto-detect this from `/apps/labs/package.json`

### Root Directory
- **IMPORTANT:** Set to `apps/labs`
- Click "Edit" next to "Root Directory"
- Type: `apps/labs`
- This tells Vercel your Next.js app is in the `/apps/labs` folder, not the root

### Build and Output Settings

Vercel should auto-detect these, but verify:
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`
- **Development Command:** `npm run dev`

### Node.js Version
- **Version:** 20.x or higher (Vercel uses latest LTS automatically)

---

## Part 4: Environment Variables

**CRITICAL:** You must add your Supabase credentials as environment variables.

### Step 1: Add Environment Variables

On the import/configure page, scroll down to **"Environment Variables"** section.

**Add these two variables:**

**Variable 1:**
- **Name:** `NEXT_PUBLIC_SUPABASE_URL`
- **Value:** Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
- **Environment:** Production, Preview, Development (select all three)

**Variable 2:**
- **Name:** `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Value:** (your Supabase anon key - see below)
- **Environment:** Production, Preview, Development (select all three)

**To get your Supabase credentials:**
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click "Settings" (gear icon) → "API"
4. Copy the **"Project URL"** → Use for `NEXT_PUBLIC_SUPABASE_URL`
5. Copy the **"anon public"** key (NOT the service_role key!) → Use for `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Important:**
- Use the **anon (public)** key, NOT the service_role key
- The anon key is safe to use in the browser
- It starts with `eyJhbGc...`
- Note the `NEXT_PUBLIC_` prefix (not `VITE_`)

---

## Part 5: Deploy!

### Step 1: Click Deploy

1. After setting the root directory and environment variables
2. **Click "Deploy"** button

### Step 2: Watch the Build

Vercel will:
1. Clone your repository
2. Install dependencies (`npm install`)
3. Build your Next.js app (`npm run build`)
4. Deploy to their global CDN

This takes about **2-4 minutes** (Next.js builds are slightly slower than Vite).

### Step 3: Success!

When deployment completes, you'll see:
- 🎉 Confetti animation
- Your live URL: `https://campaign-reference-xxxxx.vercel.app`
- **Click "Visit"** to see your live site!

---

## Part 6: Configure Custom Domain

Campaign Reference is live at: **https://campaign-reference.com**

### Step 1: Add Domain to Vercel

1. Go to your project in Vercel dashboard
2. Click **"Settings"** → **"Domains"**
3. **Add:** `campaign-reference.com`
4. **Also add:** `www.campaign-reference.com`

### Step 2: Configure DNS

Vercel will give you DNS records to add:

1. **Go to your domain registrar** (where you bought the domain)
2. **Add these DNS records:**
   - **A Record:** `@` → `76.76.21.21` (Vercel's IP)
   - **CNAME:** `www` → `cname.vercel-dns.com`

3. **Wait 24-48 hours** for DNS propagation (usually faster)

### Alternative: Use Vercel's Free Domain

Instead of buying a domain, you can customize your free Vercel URL:
1. Go to **Settings** → **General**
2. Find **"Production Branch"** and **"Project Name"**
3. Rename project to: `campaign-reference`
4. Your URL becomes: `https://campaign-reference.vercel.app`

---

## Part 7: Automatic Deployments

**Good news:** Vercel automatically deploys whenever you push to GitHub!

### How it works:
1. You make changes locally in `/apps/labs`
2. Commit: `git commit -m "Update something"`
3. Push: `git push`
4. Vercel automatically detects the push
5. Builds and deploys in ~2-4 minutes
6. Your live site updates automatically!

### Preview Deployments:
- Every push to `main` → Production deployment
- Every pull request → Preview deployment (separate URL)
- Each preview URL is unique and shareable

---

## Part 8: Monitor Your Deployment

### Check Deployment Status

1. **Vercel Dashboard:** Shows all deployments
2. **Deployment Logs:** Click any deployment to see build logs
3. **Analytics:** View traffic and performance (under "Analytics" tab)
4. **Real User Monitoring:** See actual user experience metrics

### View Real-Time Logs

1. Go to your project in Vercel
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Function Logs"** to see runtime logs
5. Useful for debugging API routes and server components

---

## Troubleshooting

### Build Fails: "Root directory not found"
**Solution:** Make sure Root Directory is set to `apps/labs`, not `frontend`

### Build Fails: "Cannot find module '@supabase/supabase-js'"
**Solution:**
1. Check that Root Directory is set to `apps/labs`
2. Verify `package.json` exists in `/apps/labs` directory
3. Try clearing build cache in Settings

### Build Fails: TypeScript Errors
**Solution:**
1. Check your local build works: `cd apps/labs && npm run build`
2. Fix any TypeScript errors locally first
3. Push fixes to GitHub

### Site Loads But Shows "Error Connecting to Database"
**Solution:**
1. Check environment variables are set correctly in Vercel
2. Make sure you used `NEXT_PUBLIC_` prefix (not `VITE_`)
3. Verify you used the **anon** key, not service_role key
4. Redeploy after updating environment variables

### Styles Not Loading Correctly
**Solution:**
1. Tailwind CSS v4 requires PostCSS config - check `/apps/labs/postcss.config.mjs` exists
2. Clear Vercel build cache: Settings → General → Clear Cache
3. Trigger new deployment

### Custom Domain Not Working
**Solution:**
1. Wait 24-48 hours for DNS propagation (can be instant, can take days)
2. Check DNS records are correct using: `dig campaign-reference.com`
3. Make sure SSL certificate is provisioned (Vercel does this automatically)
4. Try accessing with `https://` (not `http://`)

### 404 on Page Refresh
**Solution:**
- Next.js App Router handles this automatically
- If using custom server, make sure rewrites are configured
- Check `next.config.ts` for any custom routing

---

## Next.js Specific Notes

### App Router vs Pages Router
- Campaign Reference uses **App Router** (`/apps/labs/src/app`)
- All routes are file-based in the `app/` directory
- Server Components by default (faster, better SEO)

### API Routes
- API routes are in `/apps/labs/src/app/api/`
- Example: `/api/screenshot` for server-side rendering

### Environment Variables
- **Client-side:** Must start with `NEXT_PUBLIC_`
- **Server-side:** No prefix needed (not exposed to browser)
- Campaign Reference only uses client-side env vars for Supabase

### Build Output
- `.next/` directory contains the built application
- Vercel handles this automatically
- Never commit `.next/` to git (already in `.gitignore`)

---

## Quick Reference Commands

**Update your live site:**
```bash
cd apps/labs
# Make your changes
git add .
git commit -m "Your change description"
git push
```

**Test build locally before deploying:**
```bash
cd apps/labs
npm run build
npm run start  # Test production build locally
```

**Check if domain is working:**
```bash
dig campaign-reference.com
curl -I https://campaign-reference.com
```

**Force new deployment:**
- Go to Vercel dashboard
- Click project → Deployments
- Click "..." menu on latest deployment
- Click "Redeploy"

---

## Success Checklist

- [ ] Vercel account created
- [ ] Repository imported
- [ ] Root directory set to `apps/labs` (not `frontend`)
- [ ] Framework preset: Next.js
- [ ] Environment variables added (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
- [ ] First deployment succeeded
- [ ] Live site accessible
- [ ] Data loading correctly from Supabase
- [ ] Navigation working (Leaderboard, District, Committee)
- [ ] Filters working (cycle, chamber, state, district)
- [ ] Charts rendering (Recharts)
- [ ] Authentication working (login/signup modals)
- [ ] Follow system working
- [ ] (Optional) Custom domain configured

---

## Performance Optimization

### Vercel Edge Network
- Your Next.js app is automatically distributed globally
- Static assets cached at edge locations
- Server Components render close to users

### Monitoring
1. **Web Vitals:** Check Core Web Vitals in Vercel Analytics
2. **Real User Monitoring:** See actual user experience
3. **Speed Insights:** Identify slow pages
4. **Lighthouse Scores:** Monitor SEO and performance

### Caching
- Next.js automatically caches build output
- Configure caching in `next.config.ts`
- Vercel CDN handles static assets

---

## What's Next?

After deployment:
1. ✅ Test all features on the live site
2. Monitor analytics to understand usage patterns
3. Check Web Vitals for performance issues
4. Set up error tracking (Sentry, LogRocket, etc.)
5. Enable Vercel Analytics for deeper insights
6. Configure preview deployments for testing
7. Push updates (they deploy automatically!)

**Your Campaign Reference dashboard is now live at https://campaign-reference.com! 🚀**

---

## Additional Resources

- **Next.js Documentation:** https://nextjs.org/docs
- **Vercel Documentation:** https://vercel.com/docs
- **Supabase Documentation:** https://supabase.com/docs
- **Tailwind CSS v4:** https://tailwindcss.com/docs

**Questions?** Check the Vercel support docs or Campaign Reference GitHub issues.
