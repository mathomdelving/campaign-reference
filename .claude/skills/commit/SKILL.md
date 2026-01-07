---
name: commit
description: Safe commit workflow - creates a feature branch, commits changes, and opens a PR for review. Use when you've made code changes and want to commit them safely. NEVER commits directly to main.
allowed-tools: Bash, Read, Grep, Glob
version: 1.0.0
---

# Safe Commit Skill

**CRITICAL: This skill NEVER commits directly to main. All changes go through PRs.**

## Workflow Overview

```
1. Check for changes
2. Create feature branch
3. Review changes (safety check)
4. Stage ONLY specific files
5. Commit to branch
6. Push branch
7. Create PR
8. Return PR URL for user review
```

---

## Step-by-Step Process

### Step 1: Verify Current State

```bash
# Check we're on main and it's clean
git status
git branch --show-current

# Fetch latest from origin
git fetch origin
```

**STOP if:**
- Already on a feature branch (ask user if they want to continue there)
- Uncommitted changes exist on main that weren't made in this session

### Step 2: Identify Changed Files

```bash
# List all changed files (modified, added, deleted)
git status --porcelain
```

**SAFETY CHECK - Review the changes:**
- List each file that will be committed
- Show a summary: X files modified, Y files added, Z files deleted
- **WARNING if more than 10 files deleted** - ask user to confirm
- **STOP if more than 50 files changed** - something may be wrong

### Step 3: Create Feature Branch

Generate branch name from the change description:
- `feature/` for new features
- `fix/` for bug fixes
- `chore/` for maintenance
- `docs/` for documentation

```bash
# Create and switch to new branch
git checkout -b feature/descriptive-name

# Example:
git checkout -b feature/add-hamburger-menu
git checkout -b fix/login-redirect-bug
git checkout -b chore/update-dependencies
```

### Step 4: Stage Specific Files Only

**NEVER use `git add .` or `git add -A`**

Instead, add files explicitly:
```bash
# Add specific files
git add path/to/file1.tsx
git add path/to/file2.ts

# Or add a specific directory if all changes are intentional
git add apps/labs/src/components/
```

### Step 5: Verify Staged Changes

```bash
# Show exactly what will be committed
git diff --cached --stat

# Verify file count matches expected
git diff --cached --name-only | wc -l
```

**SAFETY CHECK:**
- Confirm staged files match the intended changes
- No unexpected deletions
- No sensitive files (.env, credentials, etc.)

### Step 6: Commit with Proper Message

```bash
git commit -m "$(cat <<'EOF'
type: short description

- Bullet point explaining change 1
- Bullet point explaining change 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `style:` - Formatting changes
- `test:` - Adding tests

### Step 7: Push Branch to Origin

```bash
git push -u origin HEAD
```

### Step 8: Create Pull Request

```bash
gh pr create --title "type: short description" --body "$(cat <<'EOF'
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Tested locally
- [ ] Verified no regressions

## Preview
Vercel will create a preview deployment automatically.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 9: Return to Main

```bash
# Switch back to main for future work
git checkout main
```

### Step 10: Provide PR URL

Output the PR URL so the user can:
1. Review the changes
2. Check the Vercel preview deployment
3. Merge when ready

---

## Safety Checks Summary

| Check | Action |
|-------|--------|
| On main branch | Create feature branch first |
| >10 files deleted | Warn user, require confirmation |
| >50 files changed | STOP - likely something wrong |
| Sensitive files | STOP - never commit .env, credentials |
| Untracked files | Only add if explicitly intended |

---

## Example Usage

**User says:** "Commit the hamburger menu changes"

**Claude does:**
```bash
# 1. Check status
git status
# Shows: modified apps/labs/src/components/home/HomePage.tsx

# 2. Create branch
git checkout -b feature/add-hamburger-menu

# 3. Stage specific file
git add apps/labs/src/components/home/HomePage.tsx

# 4. Verify
git diff --cached --stat
# Shows: 1 file changed, 46 insertions(+)

# 5. Commit
git commit -m "feat: add mobile hamburger menu..."

# 6. Push
git push -u origin HEAD

# 7. Create PR
gh pr create --title "feat: add mobile hamburger menu" --body "..."

# 8. Return to main
git checkout main

# 9. Output
"PR created: https://github.com/mathomdelving/campaign-reference/pull/XX"
"Vercel preview will be available shortly."
"Review and merge when ready."
```

---

## Handling Edge Cases

### Already on a feature branch
```bash
# Ask user: "You're already on branch 'feature/xyz'. Continue here or create new branch?"
# If continue: just commit and push
# If new: checkout main first, then create new branch
```

### Merge conflicts
```bash
# If push fails due to conflicts:
git fetch origin
git rebase origin/main
# Resolve conflicts if any
git push -u origin HEAD --force-with-lease
```

### PR already exists for branch
```bash
# Check if PR exists
gh pr list --head $(git branch --show-current)

# If exists, just push new commits
git push
```

---

## Quick Reference

```bash
# Full safe commit flow
git fetch origin
git checkout -b feature/my-feature
git add specific/files/only.tsx
git diff --cached --stat  # Verify!
git commit -m "feat: description"
git push -u origin HEAD
gh pr create --title "feat: description" --body "Summary..."
git checkout main
```

---

## What This Prevents

1. **Accidental deletions** - By staging specific files, not `git add -A`
2. **Direct pushes to main** - All changes go through PR review
3. **Unreviewed deployments** - Vercel preview lets you test first
4. **Lost work** - Feature branches preserve history even if something goes wrong

---

## Prerequisites

### GitHub CLI (gh) Installation

The `gh` CLI is required for creating PRs. Install it:

**macOS (Homebrew):**
```bash
brew install gh
gh auth login
```

**macOS (without Homebrew):**
```bash
# Download from https://cli.github.com/
# Or use the installer:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
```

### If gh is not available

If `gh` CLI isn't installed, create the PR manually:

1. Push the branch: `git push -u origin HEAD`
2. Go to: https://github.com/mathomdelving/campaign-reference/pulls
3. Click "New pull request"
4. Select your branch
5. Fill in the PR details
6. Click "Create pull request"

Or use this direct URL after pushing:
```
https://github.com/mathomdelving/campaign-reference/compare/main...BRANCH_NAME?expand=1
```

---

## Fallback: Manual PR Creation

If `gh pr create` fails, output this for the user:

```
Branch pushed successfully!

Create your PR manually:
1. Go to: https://github.com/mathomdelving/campaign-reference/compare/main...BRANCH_NAME
2. Review the changes
3. Click "Create pull request"
4. Add a title and description
5. Submit the PR

Vercel will automatically create a preview deployment.
```
