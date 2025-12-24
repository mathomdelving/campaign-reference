# Campaign Reference Documentation

**Complete documentation for understanding, using, and contributing to Campaign Reference**

This is your central hub for all project documentation. Start here to find what you need.

---

## 📖 Quick Navigation

### 👋 New Here?
- **[Main README](../README.md)** - Project overview & quick start
- **[Quick Start Guide](../QUICK_START.md)** - Get running in 5 minutes
- **[Project Conventions](../PROJECT_CONVENTIONS.md)** - Code standards

### 📘 User Guides
- **[Collection Guide](./guides/collection-guide.md)** - How to collect FEC data
- **[Notification System](../scripts/maintenance/README_NOTIFICATIONS.md)** - Filing detection & email alerts
- **[Deployment Guide](./deployment/README.md)** - How to deploy
- **[Data Management](./guides/data-management.md)** - Database operations

### 🔧 Technical Documentation
- **[Architecture](./technical/architecture.md)** - System design
- **[Database Schema](./data/database-schema.md)** - Data models
- **[API Reference](./technical/api-reference.md)** - Endpoints
- **[Data Pipeline](./technical/data-pipeline.md)** - Data flow

### 📜 Project History
- **[Lessons Learned](./history/lessons-learned.md)** - Problems we solved ⭐
- **[Evolution](./history/evolution.md)** - How we got here
- **[Changelog](./history/CHANGELOG.md)** - Version history
- **[Troubleshooting](./history/troubleshooting/)** - Specific fixes

### 📊 Data Documentation
- **[FEC Documentation Index](./FEC_DOCUMENTATION_INDEX.md)** - Understanding FEC data
- **[Data Quality](./data/data-quality.md)** - Quality standards
- **[Schema Mapping](./data/schema-mapping.md)** - FEC → Our DB

---

## Documentation Structure

```
docs/
├── README.md (you are here)
│
├── guides/                    # How-to guides for users
│   ├── collection-guide.md   # Data collection
│   ├── deployment-guide.md   # Deployment
│   └── data-management.md    # Database ops
│
├── technical/                 # Technical reference
│   ├── architecture.md       # System design
│   ├── database-schema.md    # Data models
│   ├── api-reference.md      # API docs
│   └── data-pipeline.md      # Data flow
│
├── history/                   # Context & learning
│   ├── lessons-learned.md    # ⭐ START HERE for context
│   ├── evolution.md          # Project iterations
│   ├── CHANGELOG.md          # Version history
│   └── troubleshooting/      # Specific issue fixes
│
├── data/                      # Data documentation
│   ├── fec-documentation/    # FEC API docs
│   ├── data-quality.md       # Quality standards
│   └── schema-mapping.md     # FEC → DB mapping
│
└── deployment/                # Deployment docs
    ├── README.md
    ├── github-actions.md
    └── vercel-setup.md
```

---

## Common Tasks

### Deploying the Application
1. Read [deployment/README.md](deployment/README.md)
2. Set up GitHub repository and secrets
3. Deploy frontend to Vercel
4. Configure GitHub Actions for data updates

### Understanding the Database
1. Read [data/database-schema.md](data/database-schema.md)
2. Learn the 3 main tables: candidates, financial_summary, quarterly_financials
3. Review FEC API endpoints and data flow

### Working on UI Features
1. Check [ui/roadmap.md](ui/roadmap.md) for design system
2. Review [ui/implementation-status.md](ui/implementation-status.md) for current status
3. Follow design tokens and component patterns

### Importing Historical Data
1. Read [data/bulk-import.md](data/bulk-import.md)
2. Download FEC bulk CSV files
3. Run `scripts/data-loading/` scripts

---

## Scripts Reference

All active production scripts are organized in `/scripts`:

```
scripts/
├── collect_cycle_data.py         # ⭐ CANONICAL DATA COLLECTION SCRIPT
│
├── data-collection/              # Additional collection tools
│   ├── fetch_fec_data.py        # Legacy (use collect_cycle_data.py instead)
│   ├── detect_new_filings.py
│   └── fix_historical_designations.py
├── data-loading/                 # Load to Supabase
│   ├── load_to_supabase.py      # Main upload script
│   ├── load_quarterly_data.py
│   └── incremental_update.py
├── maintenance/                  # Updates & notifications
│   ├── detect_new_filings.py    # ⭐ Filing detection (polls FEC API)
│   ├── send_notifications.py    # ⭐ Email notifications (SendGrid)
│   ├── README_NOTIFICATIONS.md  # Notification system docs
│   ├── update_cash_on_hand.py
│   └── retry_failed.py
└── validation/                   # Data quality
    └── comprehensive_data_audit.py
```

**⭐ For data collection, always use:** `scripts/collect_cycle_data.py`
- Robust error handling with automatic retries
- Historical committee designations (not current state)
- Collects ALL report types (quarterly + pre/post election)
- Resume capability and progress tracking

See [Project Conventions](../PROJECT_CONVENTIONS.md) for file organization guidelines.

---

## Contributing

### Adding New Documentation

**Where to put new docs:**
- **Deployment guides** → `docs/deployment/`
- **Data/schema docs** → `docs/data/`
- **UI/design docs** → `docs/ui/`
- **Temporary notes** → `docs/archive/` (when complete)

**File naming conventions:**
- Use lowercase with hyphens: `database-schema.md`
- Be descriptive: `github-actions-setup.md` not `setup.md`
- Update this README when adding major docs

### Keeping Docs Organized

1. **One source of truth** - Consolidate duplicate information
2. **Archive completed docs** - Move historical plans to `docs/archive/`
3. **Update indexes** - Keep this README and FEC_DOCUMENTATION_INDEX.md current
4. **Link liberally** - Cross-reference related docs

---

## External Resources

### FEC Data
- **FEC API Docs:** https://api.open.fec.gov/developers/
- **Bulk Data Files:** https://www.fec.gov/data/browse-data/?tab=bulk-data
- **Data Dictionaries:** https://www.fec.gov/campaign-finance-data/data-dictionaries/

### Deployment
- **Vercel Docs:** https://vercel.com/docs
- **GitHub Actions:** https://docs.github.com/en/actions
- **Next.js Deployment:** https://nextjs.org/docs/deployment

### Database
- **Supabase Docs:** https://supabase.com/docs
- **PostgreSQL Reference:** https://www.postgresql.org/docs/

---

## Questions?

- Check this README for navigation
- Review [FEC_DOCUMENTATION_INDEX.md](FEC_DOCUMENTATION_INDEX.md) for complete file list
- See [deployment/README.md](deployment/README.md) troubleshooting section
- Review [../PROJECT_CONVENTIONS.md](../PROJECT_CONVENTIONS.md) for organization guidelines

---

**Last Updated:** December 15, 2025
**Project:** Campaign Reference
**Repository:** https://github.com/YOUR_USERNAME/campaign-reference
