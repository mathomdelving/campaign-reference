# Project Conventions - Campaign Reference

**Guidelines for keeping the project organized and maintainable.**

**Last Updated:** November 5, 2025

---

## Purpose

This document establishes conventions to prevent clutter and maintain a clean, organized codebase. Following these guidelines ensures:
- Easy navigation for new contributors
- Clear separation of active vs. historical files
- Consistent file naming and organization
- Sustainable long-term maintenance

---

## Directory Structure

### Active Production Files

```
fec-dashboard/
├── README.md                    # Project overview
├── CHANGELOG.md                 # Active changelog
├── PROJECT_STATUS.md            # Current project state
├── package.json                 # Node dependencies
├── requirements.txt             # Python dependencies
│
├── scripts/                     # Active production scripts
│   ├── data-collection/        # FEC data fetching
│   ├── data-loading/           # Database loading
│   ├── maintenance/            # Updates & notifications
│   └── validation/             # Data quality checks
│
├── docs/                        # Current documentation
│   ├── README.md               # Documentation index
│   ├── deployment/             # Deployment guides
│   ├── data/                   # Database & schema docs
│   └── ui/                     # UI/design docs
│
├── apps/                        # Frontend applications
│   └── labs/                   # Next.js application (production)
│
├── .github/                     # GitHub configuration
│   └── workflows/              # GitHub Actions
│
├── database/                    # Database migrations
│   └── migrations/
│
└── sql/                         # SQL scripts
```

### Archive & Temporary Files

```
fec-dashboard/
├── archive/                     # Historical reference
│   ├── experiments/            # One-off scripts
│   │   ├── python/
│   │   └── shell/
│   ├── docs/                   # Completed plans
│   └── guides/                 # Superseded guides
│
├── deleted/                     # Quarantine (manual cleanup)
│   └── (temp files ready for deletion)
│
└── logs/                        # Runtime logs (gitignored)
    └── *.log
```

---

## File Organization Rules

### Scripts (`/scripts`)

**Rule:** All active production Python/shell scripts go in `/scripts` organized by purpose.

**Categories:**
- **data-collection/** - Fetches data from external APIs
- **data-loading/** - Loads data into database
- **maintenance/** - Recurring updates, notifications, retries
- **validation/** - Data quality checks, audits

**When to use:**
```bash
# ✅ CORRECT: Production script
scripts/data-collection/fetch_new_candidates.py

# ❌ WRONG: Root level
fetch_new_candidates.py
```

**Lifecycle:**
1. **Experiment** → Create in root or `experiments/` folder
2. **Stabilize** → Move to appropriate `/scripts` category
3. **Deprecate** → Move to `archive/experiments/`

---

### Documentation (`/docs`)

**Rule:** Active documentation only. Archive completed plans.

**Categories:**
- **deployment/** - Deployment and automation guides
- **data/** - Database schemas, data import guides
- **ui/** - Design system, UI roadmaps
- **archive/** - Completed plans, superseded docs

**When to use:**
```bash
# ✅ CORRECT: Active guide
docs/data/database-schema.md

# ❌ WRONG: Duplicate guides
docs/database-schema-v1.md
docs/database-schema-v2.md
docs/db-schema.md

# ✅ CORRECT: Single consolidated guide
docs/data/database-schema.md

# Archive old versions
archive/docs/database-schema-v1.md
```

**Naming conventions:**
- Lowercase with hyphens: `database-schema.md`
- Descriptive: `github-actions-setup.md` not `setup.md`
- No version numbers in filename (use git for versions)

**Update requirements:**
When adding docs, also update:
- `docs/README.md` (navigation index)
- `docs/FEC_DOCUMENTATION_INDEX.md` (complete list)

---

### Root Directory

**Rule:** Keep root directory minimal. Only essential project files.

**Allowed in root:**
- `README.md` - Project overview
- `CHANGELOG.md` - Active changelog
- `PROJECT_STATUS.md` - Current status
- `PROJECT_CONVENTIONS.md` - This file
- Configuration files (`.gitignore`, `package.json`, etc.)
- License, contributing guides

**NOT allowed in root:**
- Scripts (use `/scripts`)
- Logs (use `/logs`, gitignored)
- Temporary files
- Experiment scripts
- One-off documentation

---

### Logs and Temporary Files

**Rule:** Never commit logs. Use `/logs` directory (gitignored).

**Setup `.gitignore`:**
```gitignore
# Logs
logs/
*.log

# Temporary files
deleted/
*.tmp
progress.json

# Data files (too large for git)
*.json
!package.json
!package-lock.json

# Environment
.env
.env.local
```

**Cleanup:**
```bash
# Move logs out of root
mv *.log logs/

# Quarantine temp files
mv temp_*.py deleted/

# Review and permanently delete
rm -rf deleted/
```

---

## File Lifecycle

### 1. Experimentation Phase

**Where:** Root directory or `experiments/` folder
**Duration:** Until proven useful or abandoned
**Naming:** Prefix with `test_` or `experiment_`

```bash
# Temporary experiment
test_new_api_endpoint.py
experiment_bulk_import.py
```

### 2. Active Use Phase

**Where:** Organized in appropriate directory
**Duration:** While actively used
**Naming:** Descriptive, permanent names

```bash
# Production script
scripts/data-collection/fetch_candidates.py

# Active documentation
docs/data/api-reference.md
```

### 3. Archive Phase

**Where:** `archive/` directory
**Duration:** Indefinite (historical reference)
**When:** No longer actively used but may be referenced

```bash
# Archived experiment
archive/experiments/python/bulk_import_v1.py

# Archived documentation
archive/docs/OLD_IMPLEMENTATION_PLAN.md
```

### 4. Deletion Phase

**Where:** `deleted/` directory (temporary quarantine)
**Duration:** 24-48 hours for review
**When:** No future value

```bash
# Quarantined for deletion
deleted/debug_output.log
deleted/temp_test.py
```

---

## Naming Conventions

### Python Scripts

```python
# ✅ CORRECT: Verb-noun format, descriptive
fetch_fec_data.py
update_cash_on_hand.py
send_notifications.py

# ❌ WRONG: Vague or numbered
script.py
update_v2.py
fetch.py
```

### Markdown Documentation

```markdown
# ✅ CORRECT: Lowercase with hyphens
database-schema.md
deployment-guide.md
api-reference.md

# ❌ WRONG: Mixed case or underscores
Database_Schema.md
deploymentGuide.md
APIReference.md
```

### Shell Scripts

```bash
# ✅ CORRECT: Descriptive action
backup_database.sh
deploy_to_production.sh

# ❌ WRONG: Generic
run.sh
script.sh
```

---

## Documentation Standards

### Single Source of Truth

**Rule:** Consolidate duplicate information into one canonical document.

**Example:**
```bash
# ❌ WRONG: Three separate guides
docs/DEPLOYMENT_GUIDE_GITHUB.md
docs/DEPLOYMENT_GUIDE_VERCEL.md
docs/HOW_TO_DEPLOY.md

# ✅ CORRECT: One consolidated guide
docs/deployment/README.md
  ├─ Part 1: GitHub Setup
  ├─ Part 2: Vercel Setup
  └─ Part 3: Continuous Deployment
```

### Cross-Referencing

**Rule:** Link to other docs instead of duplicating information.

```markdown
# ✅ CORRECT: Reference existing docs
See [Database Schema](data/database-schema.md) for table definitions.

# ❌ WRONG: Duplicate schema in multiple docs
```

### Keep Current

**Rule:** Update or archive outdated docs. Don't leave stale information.

**Checklist when docs become outdated:**
- [ ] Can it be updated quickly? → Update it
- [ ] Is it historical reference? → Move to `archive/`
- [ ] Is it superseded? → Delete it, update links
- [ ] Is it still accurate? → Add "Last Updated" date

---

## Git Commit Conventions

### Commit Message Format

```bash
<type>: <description>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation changes
refactor: Code reorganization (no functionality change)
chore: Maintenance tasks
archive: Moving files to archive
cleanup: Removing deprecated files
```

### Examples

```bash
# ✅ GOOD: Clear and specific
git commit -m "feat: add quarterly data import script"
git commit -m "docs: consolidate deployment guides"
git commit -m "refactor: organize scripts into categories"
git commit -m "cleanup: archive completed experiment scripts"

# ❌ BAD: Vague
git commit -m "updates"
git commit -m "fixed stuff"
git commit -m "changes"
```

---

## Cleanup Checklist

### Weekly Maintenance

- [ ] Move any `.log` files to `/logs` directory
- [ ] Review root directory for misplaced files
- [ ] Check for duplicate documentation
- [ ] Archive completed experiment scripts

### Monthly Maintenance

- [ ] Review `archive/` for files that can be permanently deleted
- [ ] Update `docs/README.md` with new documentation
- [ ] Verify all links in documentation are working
- [ ] Clean up `deleted/` directory

### Before Major Releases

- [ ] Full audit of file organization
- [ ] Consolidate any duplicate guides
- [ ] Update PROJECT_STATUS.md
- [ ] Update CHANGELOG.md
- [ ] Archive old roadmaps/plans

---

## Quick Reference

### Where does this file go?

| File Type | Location | Example |
|-----------|----------|---------|
| Active Python script | `/scripts/{category}/` | `scripts/data-collection/fetch_fec_data.py` |
| Active documentation | `/docs/{category}/` | `docs/deployment/README.md` |
| Experiment script | Root (temp) → `/scripts/` or `archive/` | `experiment_test.py` → `archive/experiments/` |
| Completed plan | `archive/docs/` | `archive/docs/IMPLEMENTATION_PLAN_2024.md` |
| Log file | `/logs/` (gitignored) | `logs/fetch_2024.log` |
| Temporary file | `/deleted/` (quarantine) | `deleted/temp_test.py` |
| SQL migration | `/database/migrations/` | `database/migrations/001_create_users.sql` |
| Frontend code | `/apps/labs/` | `apps/labs/src/components/Chart.tsx` |

---

## Enforcement

### Code Reviews

All pull requests should verify:
- [ ] Files are in correct directories
- [ ] No duplicate documentation
- [ ] Logs and temp files are gitignored
- [ ] README files are updated if needed

### Automated Checks (Future)

Consider adding GitHub Actions to check:
- No `.log` files in commits
- No duplicate guide filenames
- All docs linked from `docs/README.md`

---

## Questions?

- **"Where should I put this script?"** → See "Quick Reference" table above
- **"Should I archive or delete this?"** → Archive if it might be referenced, delete if no future value
- **"Can I create a new doc?"** → Yes, in appropriate `/docs` category, and update `docs/README.md`
- **"How do I clean up the project?"** → Follow "Cleanup Checklist" above

---

**Remember:** A well-organized codebase is easier to maintain, onboard new contributors, and scale over time. When in doubt, err on the side of consolidation and organization.

---

**Last Updated:** November 5, 2025
**Maintained By:** Campaign Reference Team
