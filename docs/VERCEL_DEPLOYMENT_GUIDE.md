# Vercel Deployment Guide - Campaign Reference

This guide walks you through deploying your FEC Campaign Finance Dashboard to Vercel.

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

### Step 2: Import fec-dashboard

1. **Find "fec-dashboard"** in the list
2. **Click "Import"** next to it

---

## Part 3: Configure Build Settings

Vercel will try to auto-detect your settings. Here's what you need to configure:

### Framework Preset
- **Select:** Vite
- Vercel should auto-detect this

### Root Directory
- **IMPORTANT:** Set to `frontend`
- Click "Edit" next to "Root Directory"
- Type: `frontend`
- This tells Vercel your app is in the `/frontend` folder, not the root

### Build and Output Settings

Vercel should auto-detect these, but verify:
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### Node.js Version
- **Version:** 18.x or higher (Vercel usually uses latest LTS automatically)

---

## Part 4: Environment Variables

**CRITICAL:** You must add your Supabase credentials as environment variables.

### Step 1: Add Environment Variables

On the import/configure page, scroll down to **"Environment Variables"** section.

**Add these two variables:**

**Variable 1:**
- **Name:** `VITE_SUPABASE_URL`
- **Value:** `https://idgxiaxniwpduifvinqq.supabase.co`
- **Environment:** Production, Preview, Development (select all three)

**Variable 2:**
- **Name:** `VITE_SUPABASE_ANON_KEY`
- **Value:** (your Supabase anon key - see below)

**To get your Supabase anon key:**
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click "Settings" (gear icon) → "API"
4. Copy the **"anon public"** key (NOT the service_role key!)
5. Paste it into Vercel

**Important:**
- Use the **anon (public)** key, NOT the service_role key
- The anon key is safe to use in the browser
- It starts with `eyJhbGc...`

---

## Part 5: Deploy!

### Step 1: Click Deploy

1. After setting the root directory and environment variables
2. **Click "Deploy"** button

### Step 2: Watch the Build

Vercel will:
1. Clone your repository
2. Install dependencies (`npm install`)
3. Build your app (`npm run build`)
4. Deploy to their global CDN

This takes about **2-3 minutes**.

### Step 3: Success!

When deployment completes, you'll see:
- 🎉 Confetti animation
- Your live URL: `https://fec-dashboard-xxxxx.vercel.app`
- **Click "Visit"** to see your live site!

---

## Part 6: Configure Custom Domain (Optional)

If you purchase `campaign-reference.com`:

### Step 1: Add Domain to Vercel

1. Go to your project in Vercel dashboard
2. Click **"Settings"** → **"Domains"**
3. **Add:** `campaign-reference.com`
4. **Also add:** `www.campaign-reference.com`

### Step 2: Configure DNS

Vercel will give you DNS records to add. You'll need to:

1. **Go to your domain registrar** (where you bought the domain)
2. **Add these DNS records:**
   - **A Record:** `@` → `76.76.21.21` (Vercel's IP)
   - **CNAME:** `www` → `cname.vercel-dns.com`

3. **Wait 24-48 hours** for DNS propagation

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
1. You make changes locally
2. Commit: `git commit -m "Update something"`
3. Push: `git push`
4. Vercel automatically detects the push
5. Builds and deploys in ~2 minutes
6. Your live site updates automatically!

### Preview Deployments:
- Every push to `main` → Production deployment
- Every pull request → Preview deployment (separate URL)

---

## Part 8: Monitor Your Deployment

### Check Deployment Status

1. **Vercel Dashboard:** Shows all deployments
2. **Deployment Logs:** Click any deployment to see build logs
3. **Analytics:** View traffic and performance (under "Analytics" tab)

### View Real-Time Logs

1. Go to your project in Vercel
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Function Logs"** to see runtime logs

---

## Troubleshooting

### Build Fails: "Command not found: npm"
**Solution:** Node.js version issue. Set Node.js version in project settings to 18.x or higher.

### Build Fails: "Cannot find module"
**Solution:**
1. Check that Root Directory is set to `frontend`
2. Verify `package.json` exists in `/frontend` directory

### Site Loads But Shows "Error Connecting to Database"
**Solution:**
1. Check environment variables are set correctly
2. Make sure you used the **anon** key, not service_role key
3. Verify `VITE_` prefix on both variables

### CSS Not Loading / Styles Missing
**Solution:**
1. Clear Vercel build cache: Settings → General → Clear Cache
2. Trigger new deployment

### Custom Domain Not Working
**Solution:**
1. Wait 24-48 hours for DNS propagation
2. Check DNS records are correct
3. Try using `https://` instead of `http://`

---

## Quick Reference Commands

**Update your live site:**
```bash
git add .
git commit -m "Your change description"
git push
```

**Check if domain is working:**
```bash
dig campaign-reference.com
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
- [ ] Root directory set to `frontend`
- [ ] Environment variables added (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
- [ ] First deployment succeeded
- [ ] Live site accessible
- [ ] Data loading correctly from Supabase
- [ ] Navigation working
- [ ] Filters working
- [ ] Charts rendering
- [ ] Export functionality working
- [ ] (Optional) Custom domain configured

---

## What's Next?

After deployment:
1. Test all features on the live site
2. Share the URL with friends/colleagues for feedback
3. Monitor analytics to see usage
4. Make improvements based on feedback
5. Push updates (they deploy automatically!)

**Your FEC Campaign Finance Dashboard is now live! 🚀**
