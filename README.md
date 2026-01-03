# Campaign Reference

**Campaign finance dashboard for 2022-2026 House and Senate races**

Real-time FEC data visualization with automated updates and email notifications.

**Live Site:** [https://campaign-reference.com](https://campaign-reference.com)

---

## Quick Start

```bash
cd apps/labs
npm install
npm run dev
```

App available at http://localhost:3000

---

## Project Structure

```
campaign-reference/
├── apps/labs/             # Next.js application (production UI)
│   └── src/
│       ├── app/           # Next.js App Router pages
│       ├── components/    # React components
│       ├── contexts/      # React contexts (Auth, Follows)
│       ├── hooks/         # Custom data hooks
│       └── utils/         # Formatting helpers
│
├── scripts/               # Data collection & utilities
│   ├── data-loading/      # Database loading scripts
│   │   ├── incremental_update.py
│   │   └── update_quarterly_financials.py
│   ├── maintenance/       # Notifications & monitoring
│   │   ├── detect_new_filings.py
│   │   ├── detect_ie_filings.py
│   │   └── send_notifications.py
│   └── validation/        # Data validation scripts
│
├── database/              # Database migrations
│   └── migrations/        # SQL migration files
│
├── docs/                  # Documentation
│   ├── ROADMAP.md
│   ├── data/
│   ├── deployment/
│   └── guides/
│
├── .github/workflows/     # GitHub Actions (automated updates)
└── archive/               # Deprecated scripts
```

---

## Features

### Dashboard
1. **Leaderboard View** – Top fundraisers with sortable columns and CSV export
2. **By District** – Compare all candidates within a specific House district or Senate seat
3. **By Committee** – National committee drilldowns with quarterly trends

### User Features
4. **Watchlists** – Follow up to 50 candidates
5. **Email Notifications** – Alerts for new campaign filings
6. **Independent Expenditure Alerts** – Notifications when outside groups spend for/against followed candidates
7. **Auth** – Supabase-powered email/password and Google OAuth

---

## Data Pipeline

### 1. Automated Data Collection (GitHub Actions)

| Schedule | Frequency | Purpose |
|----------|-----------|---------|
| Normal | Hourly | Standard data refresh |
| Filing Period | Every 30 min (days 13-17 of Jan/Apr/Jul/Oct) | Capture deadline filings |
| Peak Hours | Every 10 min (deadline day 9am-6pm ET) | Real-time deadline coverage |

**Workflow Steps:**
1. Fetch new candidate filings from FEC API
2. Update quarterly financial data
3. Detect new campaign filings → queue notifications
4. Detect independent expenditures → queue IE notifications
5. Send email notifications via SendGrid

### 2. Database (Supabase PostgreSQL)

| Table | Purpose |
|-------|---------|
| `candidates` | All 2024-2026 House and Senate candidates |
| `financial_summary` | Latest summary financial data |
| `quarterly_financials` | Historical quarterly filings |
| `user_candidate_follows` | User watchlists with notification preferences |
| `notification_queue` | Pending email notifications |
| `independent_expenditures` | Outside spending data (Schedule E) |
| `data_refresh_log` | Automated update tracking |

### 3. Frontend (Next.js on Vercel)
- Automatic deployments on git push to main
- Real-time data from Supabase
- Interactive charts with Recharts

---

## Tech Stack

### Frontend
- Next.js 15 (App Router)
- React 19
- Tailwind CSS
- shadcn/ui + Radix primitives
- Recharts
- Supabase JS Client

### Backend/Data
- Python 3.9+
- Supabase (PostgreSQL)
- FEC OpenFEC API
- SendGrid (email notifications)

### Deployment & Automation
- **Hosting:** Vercel
- **Domain:** campaign-reference.com
- **CI/CD:** GitHub Actions
- **Data Updates:** Automated hourly + filing period intensive updates

---

## Status

**Live in Production**
- Dashboard with Leaderboard, District, and Committee views
- User authentication with watchlists
- Email notifications for campaign filings and independent expenditures
- Automated data updates via GitHub Actions
- Deployed at campaign-reference.com

---

## Development

### Frontend
```bash
cd apps/labs
npm install
npm run dev
```
App runs at http://localhost:3000

### Data Scripts (Manual Testing)
```bash
pip3 install -r requirements.txt

# Test filing detection (dry run)
python3 scripts/maintenance/detect_new_filings.py --once --dry-run

# Test IE detection (dry run)
python3 scripts/maintenance/detect_ie_filings.py --once --dry-run

# Test notifications (dry run)
python3 scripts/maintenance/send_notifications.py --dry-run
```
Note: Data updates run automatically via GitHub Actions. Manual runs are for testing only.

---

## Environment Variables

### GitHub Secrets (for Actions)
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=notifications@yourdomain.com
SENDGRID_FROM_NAME=Campaign Reference
```

### Vercel Environment Variables
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

### Local Development

**Backend (.env in project root):**
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=notifications@yourdomain.com
SENDGRID_FROM_NAME=Campaign Reference
```

**Frontend (apps/labs/.env.local):**
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

---

## Documentation

See `docs/` folder for detailed documentation:
- `ROADMAP.md` - Project roadmap
- `deployment/` - Deployment guides
- `guides/` - How-to guides
- `data/` - Data collection documentation

---

*Inspired by sports-reference.com sites (baseball-reference, football-reference).*

Built for political journalists, researchers, and campaign professionals who need fast, accurate campaign finance data.
