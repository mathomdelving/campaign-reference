# Complete GitHub Deployment Guide

This guide will walk you through pushing your code to GitHub, adding secrets, and testing the automation workflow.

---

## Part 1: Push Your Code to GitHub

### Step 1: Initialize Git Repository Locally

Open Terminal and navigate to your project directory:

```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
```

Initialize git:

```bash
git init
```

You should see: `Initialized empty Git repository in /Users/benjaminnelson/Desktop/fec-dashboard/.git/`

### Step 2: Add All Files to Git

```bash
git add .
```

This stages all your files (except those in .gitignore) for commit.

### Step 3: Make Your First Commit

```bash
git commit -m "Initial commit: FEC Campaign Finance Dashboard with automation"
```

You should see a summary of files added.

### Step 4: Create GitHub Repository

1. **Go to GitHub** in your web browser: https://github.com
2. **Click the "+" icon** in the top-right corner
3. **Click "New repository"**
4. **Fill in the details:**
   - Repository name: `fec-dashboard` (or whatever you prefer)
   - Description: `Interactive dashboard for 2026 House and Senate campaign finance data`
   - **Public** (recommended for free GitHub Pages/Actions)
   - **DO NOT** check "Initialize with README" (you already have code)
   - **DO NOT** add .gitignore or license (you already have these)
5. **Click "Create repository"**

### Step 5: Connect Your Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/fec-dashboard.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username.

**If prompted for credentials:**
- Username: Your GitHub username
- Password: You need a **Personal Access Token** (not your regular password)

**To create a Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `fec-dashboard-upload`
4. Select scopes: Check "repo" (this gives full repository access)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)
7. Use this token as your password when pushing

After successful push, you should see:

```
Enumerating objects: ...
Counting objects: ...
Writing objects: 100% ...
To https://github.com/YOUR_USERNAME/fec-dashboard.git
 * [new branch]      main -> main
```

### Step 6: Verify on GitHub

Go to `https://github.com/YOUR_USERNAME/fec-dashboard` in your browser. You should see all your files!

---

## Part 2: Add GitHub Secrets

Now we'll add your API keys and URLs as "secrets" so the GitHub Actions workflow can use them.

### Step 1: Get Your Secret Values

First, let's get the values from your local .env file. In Terminal:

```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
cat .env
```

You'll see something like:

```
FEC_API_KEY=abcdef123456...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

**Copy these values** - you'll need them in a moment.

### Step 2: Navigate to Repository Settings

1. **Go to your GitHub repository** in browser:
   - `https://github.com/YOUR_USERNAME/fec-dashboard`

2. **Click "Settings"** tab (top navigation bar, far right)

3. **In the left sidebar**, scroll down and click:
   - **"Secrets and variables"**
   - Then click **"Actions"**

### Step 3: Add Secret #1 - FEC_API_KEY

1. **Click "New repository secret"** (green button, top right)

2. **Fill in the form:**
   - **Name:** `FEC_API_KEY` (exactly this, all caps, no spaces)
   - **Secret:** Paste your FEC API key from your .env file
     - Example: `abcdef123456789...` (your actual key)

3. **Click "Add secret"** (green button at bottom)

4. You should see "FEC_API_KEY" appear in the list

### Step 4: Add Secret #2 - SUPABASE_URL

1. **Click "New repository secret"** again

2. **Fill in the form:**
   - **Name:** `SUPABASE_URL` (exactly this)
   - **Secret:** Paste your Supabase URL from your .env file
     - Example: `https://abcdefghijk.supabase.co`

3. **Click "Add secret"**

### Step 5: Add Secret #3 - SUPABASE_KEY

1. **Click "New repository secret"** again

2. **Fill in the form:**
   - **Name:** `SUPABASE_KEY` (exactly this)
   - **Secret:** Paste your Supabase service role key from your .env file
     - This is the long JWT token starting with `eyJhbGc...`
     - Make sure you get the entire key (it's very long!)

3. **Click "Add secret"**

### Step 6: Verify All Three Secrets

You should now see three secrets listed:
- ✅ FEC_API_KEY
- ✅ SUPABASE_URL
- ✅ SUPABASE_KEY

**Important:** You can't view the secret values after adding them (for security), but you can update or delete them if needed.

---

## Part 3: Test the GitHub Actions Workflow

Now let's manually trigger the workflow to make sure everything works!

### Step 1: Navigate to Actions Tab

1. **Go to your GitHub repository**:
   - `https://github.com/YOUR_USERNAME/fec-dashboard`

2. **Click the "Actions" tab** (top navigation bar)

3. You should see a message about workflows and a workflow listed:
   - **"Update FEC Campaign Finance Data"**

### Step 2: Enable GitHub Actions (if needed)

If you see a message like "Workflows aren't being run on this repository":
1. **Click "I understand my workflows, go ahead and enable them"**

### Step 3: Run the Workflow Manually

1. **Click on "Update FEC Campaign Finance Data"** (in the left sidebar)

2. You should see a message: "This workflow has a workflow_dispatch event trigger."

3. **Click the "Run workflow" dropdown** (right side, gray button)

4. A dropdown will appear:
   - Branch: `main` (should be selected)
   - **Click the green "Run workflow" button**

5. The page will refresh and you'll see:
   - A yellow dot 🟡 - Workflow is running
   - Or a green checkmark ✅ - Workflow succeeded
   - Or a red X ❌ - Workflow failed

### Step 4: Watch the Workflow Run

1. **Click on the workflow run** (the row with the yellow dot)

2. You'll see the workflow name and details

3. **Click on "update-fec-data"** (the job name)

4. You'll see each step of the workflow executing:
   - ✅ Checkout repository
   - ✅ Set up Python
   - ✅ Install Python dependencies
   - ⏳ Fetch FEC data (this takes ~5-10 minutes due to rate limiting)
   - ⏳ Load data to Supabase
   - ✅ Log completion

5. **Click on any step** to see detailed output

### Step 5: Verify Success

When the workflow completes successfully:
- All steps will have ✅ green checkmarks
- The "Log completion" step will show file sizes
- You should see something like:
  ```
  Data update completed at Sat Oct 26 15:30:00 UTC 2025
  Candidates file size: 4.3M
  Financials file size: 1.3M
  ```

### What If It Fails?

If you see a red X ❌:

1. **Click on the failed step** to see the error message

2. **Common issues:**
   - **"Invalid API key"** → Check that your FEC_API_KEY secret is correct
   - **"401 Unauthorized"** → Check your SUPABASE_KEY secret
   - **"Rate limit exceeded"** → Normal! The workflow will retry on the next scheduled run

3. **To fix:**
   - Go back to Settings → Secrets and variables → Actions
   - Click on the secret that's wrong
   - Click "Update" and paste the correct value
   - Run the workflow again

---

## Part 4: Verify Scheduled Runs

After your manual test succeeds:

### When Will It Run Automatically?

1. **Daily at 6 AM ET (11 AM UTC)**
   - Every morning

2. **Every 2 hours during filing periods**
   - Days 13-17 of January, April, July, and October

### How to Check Scheduled Runs

1. **Go to Actions tab** any time after a scheduled run should have occurred

2. You'll see the runs listed with:
   - Timestamp
   - Status (✅ or ❌)
   - Duration
   - Triggered by: "schedule" or "workflow_dispatch" (manual)

### Email Notifications

GitHub will automatically email you if a scheduled workflow fails. You can configure this in:
- GitHub Settings (your profile) → Notifications

---

## Part 5: Updating Code in the Future

When you make changes to your code locally:

```bash
# 1. See what changed
git status

# 2. Add the changes
git add .

# 3. Commit with a message
git commit -m "Description of what you changed"

# 4. Push to GitHub
git push
```

The GitHub Actions workflow file is already configured, so any push to GitHub will include your latest code. The next time the workflow runs (scheduled or manual), it will use the updated code.

---

## Quick Reference Commands

```bash
# Check what branch you're on
git branch

# See what files changed
git status

# See what specific changes you made
git diff

# View commit history
git log --oneline

# Pull latest code from GitHub
git pull

# Push your changes to GitHub
git push
```

---

## Troubleshooting

### Problem: "fatal: remote origin already exists"

**Solution:**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/fec-dashboard.git
```

### Problem: "Permission denied" when pushing

**Solution:** Use a Personal Access Token instead of your password (see Step 5 of Part 1)

### Problem: "Workflow not found"

**Solution:** Make sure the `.github/workflows/update-data.yml` file was committed:
```bash
git add .github/workflows/update-data.yml
git commit -m "Add GitHub Actions workflow"
git push
```

### Problem: Secrets not working

**Solution:**
1. Secret names must match EXACTLY (all caps, underscores)
2. No extra spaces in the secret values
3. Make sure you copied the entire value (especially SUPABASE_KEY which is very long)

---

## Summary Checklist

- [ ] Initialized git repository (`git init`)
- [ ] Made first commit (`git commit -m "..."`)
- [ ] Created GitHub repository online
- [ ] Pushed code to GitHub (`git push -u origin main`)
- [ ] Added FEC_API_KEY secret
- [ ] Added SUPABASE_URL secret
- [ ] Added SUPABASE_KEY secret
- [ ] Manually triggered workflow from Actions tab
- [ ] Verified workflow completed successfully
- [ ] Ready for Phase 5 (Vercel deployment)!

---

**Questions?** Check the error messages in the Actions tab logs - they're usually very specific about what's wrong!
