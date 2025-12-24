# Migration Cleanup Plan: Vite → Next.js
**Date:** November 3, 2025
**Status:** Ready for execution

## Executive Summary

On October 31, 2025 (commit `e4be8c2`), Campaign Reference migrated from:
- **OLD:** Vite + React (`/frontend`)
- **NEW:** Next.js + TypeScript (`/apps/labs`)

The migration is **complete and live** at https://campaign-reference.com, but the old `/frontend` directory still exists in the main branch, causing confusion.

---

## Current State Analysis

### ✅ What's Working
- **Live Production:** `/apps/labs` is deployed and serving all traffic
- **Git History Preserved:** Old Vite UI saved in `legacy/vite-ui` branch and tagged as `v1.0.0-vite`
- **README Updated:** Already states "Next.js Labs UI (production site)" and "Legacy Vite UI (archived)"

### ⚠️ Sources of Confusion
1. **`/frontend` directory still in main branch** - 120MB of unused code
2. **Outdated docs reference `/frontend`** - 7+ documentation files mention old paths
3. **Misleading name** - `/apps/labs` sounds experimental but is actually production
4. **Duplicate dependencies** - Both package.json files exist

---

## Migration Timeline (Historical Reference)

| Date | Event | Commit |
|------|-------|--------|
| Pre-Oct 31 | Vite frontend in production | `de5897e` and earlier |
| Oct 31, 2025 | Migration to Next.js | `e4be8c2` |
| Oct 31, 2025 | Tagged old version | `v1.0.0-vite` |
| Oct 31, 2025 | Created legacy branch | `legacy/vite-ui` |
| Nov 3, 2025 | This cleanup plan | Current |

---

## Recommended Cleanup Steps

### Phase 1: Rename for Clarity (OPTIONAL but recommended)

**Problem:** `/apps/labs` sounds like an experiment, but it's production.

**Option A: Rename to `/app`**
```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard
git mv apps/labs app
# Update all references in docs
git commit -m "chore: rename labs to app (it's production, not experimental)"
```

**Option B: Keep `/apps/labs`**
- Add comment to README explaining "Labs" is production
- Update docs to clarify naming

**Recommendation:** Keep `/apps/labs` for now. Rename can happen later if needed.

---

### Phase 2: Remove Legacy `/frontend` Directory

**Safe to delete because:**
1. ✅ Code preserved in `legacy/vite-ui` branch
2. ✅ Tagged as `v1.0.0-vite` for easy recovery
3. ✅ Next.js version is live and stable
4. ✅ All features migrated to Next.js

**Steps:**
```bash
cd /Users/benjaminnelson/Desktop/fec-dashboard

# 1. Verify legacy branch exists
git branch -a | grep legacy/vite-ui

# 2. Verify tag exists
git tag | grep v1.0.0-vite

# 3. Remove frontend directory
git rm -r frontend/

# 4. Commit the removal
git commit -m "chore: remove legacy /frontend directory (preserved in legacy/vite-ui branch)"

# 5. Push to GitHub
git push origin main
```

**Rollback plan (if needed):**
```bash
# To restore from legacy branch
git checkout legacy/vite-ui -- frontend/
git commit -m "restore: bring back frontend from legacy branch"
```

---

### Phase 3: Update Documentation

Files that need updates:

#### 1. `docs/VERCEL_DEPLOYMENT_GUIDE.md`
**Current:** Instructions for deploying Vite frontend
**Update to:** Instructions for deploying Next.js from `/apps/labs`

#### 2. `docs/ROADMAP.md`
**Current:** References `frontend/` paths
**Update to:** Replace with `/apps/labs/src/` paths

#### 3. `docs/ROADMAP2.md`
**Current:** References `frontend/src/components/auth/`
**Update to:** Replace with `/apps/labs/src/components/auth/`

#### 4. `docs/IMPLEMENTATION_PLAN.md`
**Current:** References `frontend/src/views/`
**Update to:** Replace with `/apps/labs/src/app/(app)/`

#### 5. `docs/DEBUGGING_FINDINGS.md`
**Current:** References `frontend/src/hooks/useCandidateData.js`
**Update to:** Replace with `/apps/labs/src/hooks/useCandidateData.ts`

#### 6. `docs/SESSION_STATUS.md`
**Current:** Old project structure with frontend/
**Update to:** New structure with apps/labs/

#### 7. `docs/UI_IMPLEMENTATION_STATUS.md` (just created)
**Current:** Correctly identifies both implementations
**Action:** Add note that /frontend will be removed

---

### Phase 4: Update Root Configuration Files

#### Remove/Archive:
- `package.json` (root) - Only has basic deps, not needed
- `package-lock.json` (root) - Not needed

#### Keep:
- `requirements.txt` - Python backend deps
- All Python scripts - Still needed for data pipeline

---

## Detailed File Inventory

### Files to DELETE (after Phase 2)
```
frontend/                         120MB
├── .claude/
├── .env                          ← Contains secrets, ensure backed up
├── .gitignore
├── CLAUDE.md
├── README.md
├── eslint.config.js
├── index.html
├── node_modules/                 ← 99MB
├── package-lock.json
├── package.json
├── postcss.config.js
├── public/
├── src/                          ← All source code
├── tailwind.config.js
├── vercel.json
└── vite.config.js
```

### Files to KEEP (production)
```
apps/labs/                        496MB
├── All files (this is production!)
```

---

## Risk Assessment

### Low Risk ✅
- **Frontend removal:** Code preserved in branch + tag
- **Doc updates:** No code changes, just documentation
- **Root cleanup:** Root package.json not used by anything

### Medium Risk ⚠️
- **Renaming `/apps/labs`:** Would require updating Vercel config

### High Risk ❌
- **None identified**

---

## Execution Checklist

### Pre-Cleanup Verification
- [ ] Confirm https://campaign-reference.com is live and working
- [ ] Verify `legacy/vite-ui` branch exists in GitHub
- [ ] Verify `v1.0.0-vite` tag exists in GitHub
- [ ] Backup `.env` files from `/frontend` (if any secrets not in 1Password)

### Phase 1: Documentation Audit (COMPLETED)
- [x] Audit git history
- [x] Identify all frontend references in docs
- [x] Create cleanup plan (this document)

### Phase 2: Remove Legacy Code
- [ ] Run `git rm -r frontend/`
- [ ] Commit removal
- [ ] Push to GitHub
- [ ] Verify deployment still works

### Phase 3: Update Documentation
- [ ] Update VERCEL_DEPLOYMENT_GUIDE.md
- [ ] Update ROADMAP.md
- [ ] Update ROADMAP2.md
- [ ] Update IMPLEMENTATION_PLAN.md
- [ ] Update DEBUGGING_FINDINGS.md
- [ ] Update SESSION_STATUS.md
- [ ] Update UI_IMPLEMENTATION_STATUS.md

### Phase 4: Final Verification
- [ ] All links in docs point to valid paths
- [ ] No broken references to `/frontend`
- [ ] README.md accurately describes project structure
- [ ] GitHub README looks correct

---

## Post-Cleanup Project Structure

```
campaign-reference/
├── apps/
│   └── labs/                  # Next.js production application
│       ├── src/
│       │   ├── app/          # App Router routes
│       │   ├── components/   # React components
│       │   ├── hooks/        # Data fetching hooks
│       │   ├── lib/          # chartTheme, export utils
│       │   └── utils/        # Formatters, helpers
│       └── package.json
│
├── docs/                      # Documentation (all updated!)
│   ├── UI_IMPLEMENTATION_STATUS.md
│   ├── CR_UI_ROADMAP.md
│   ├── MIGRATION_CLEANUP_PLAN.md (this file)
│   ├── VERCEL_DEPLOYMENT_GUIDE.md (updated)
│   └── ...
│
├── .github/
│   └── workflows/
│       ├── full-refresh.yml
│       └── incremental-update.yml
│
├── Python scripts (data pipeline)
│   ├── fetch_fec_data.py
│   ├── load_to_supabase.py
│   ├── bulk_import_fec.py
│   └── ...
│
├── requirements.txt           # Python deps
└── README.md                  # Main readme (already updated)
```

---

## Benefits of Cleanup

1. **Eliminates confusion** - No more wondering which codebase is production
2. **Saves 120MB** - Remove unused frontend/ directory
3. **Clearer onboarding** - New contributors see only one UI codebase
4. **Better SEO** - Documentation accurately describes current state
5. **Reduced maintenance** - No need to keep legacy docs in sync

---

## FAQs

### Q: What if we need to reference old Vite code?
**A:** It's preserved in the `legacy/vite-ui` branch and `v1.0.0-vite` tag. You can always check out that code:
```bash
git checkout legacy/vite-ui
# or
git checkout v1.0.0-vite
```

### Q: Can we roll back to Vite if Next.js has issues?
**A:** Yes, but unlikely needed since Next.js has been live since Oct 31. To rollback:
```bash
git checkout legacy/vite-ui -- frontend/
git commit -m "rollback: restore Vite frontend"
# Update Vercel to point to frontend/ again
```

### Q: Why was it called "labs" if it's production?
**A:** Initial intent was to experiment with Next.js in a separate directory before migrating. Once migration was successful, it became production but kept the name.

### Q: Should we rename `/apps/labs` to `/app`?
**A:** Optional. Current name works fine. Can be renamed later if desired.

### Q: What about the root `package.json`?
**A:** It only has `@supabase/supabase-js` and `recharts`. Not actively used. Can be removed or kept for workspace tooling.

---

## Rollback Procedures

### If cleanup causes issues

**Step 1: Restore frontend/**
```bash
git revert HEAD  # Reverts the "remove frontend" commit
```

**Step 2: Or cherry-pick from legacy branch**
```bash
git checkout legacy/vite-ui -- frontend/
git add frontend/
git commit -m "restore: bring back frontend from legacy branch"
```

**Step 3: Update Vercel**
- Change Root Directory back to `frontend`
- Redeploy

---

## Timeline

| Task | Estimated Time | Priority |
|------|---------------|----------|
| Phase 1: Audit (DONE) | ✅ Complete | High |
| Phase 2: Remove frontend/ | 5 minutes | High |
| Phase 3: Update docs | 30 minutes | High |
| Phase 4: Final verification | 15 minutes | Medium |
| **Total** | **~50 minutes** | |

---

## Sign-Off

**Prepared by:** Claude Code (AI Assistant)
**Reviewed by:** [Benjamin Nelson - pending]
**Approved for execution:** [Pending]
**Executed on:** [TBD]

---

## Notes

- This cleanup is **safe and reversible**
- Old code is **preserved** in git history
- Production site **will not be affected**
- Documentation will be **accurate and clear**

**Ready to execute when you give the go-ahead! 🚀**
