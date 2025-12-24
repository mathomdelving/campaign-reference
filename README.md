# Campaign Reference

**Campaign finance dashboard for 2022-2026 House and Senate races**

Real-time FEC data visualization with automated daily updates.

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
│       ├── hooks/         # Custom data hooks
│       └── utils/         # Formatting helpers
│
├── scripts/               # Data collection & utilities
│   ├── collect_cycle_data.py    # Main data collection script
│   ├── data-collection/   # Collection scripts
│   ├── data-loading/      # Database loading scripts
│   ├── maintenance/       # Maintenance & notifications
│   └── validation/        # Data validation scripts
│
├── docs/                  # Documentation
│   ├── ROADMAP.md         # Project roadmap
│   ├── data/              # Data documentation
│   ├── deployment/        # Deployment guides
│   └── guides/            # How-to guides
│
├── sql/                   # Database migrations & schemas
├── .github/workflows/     # GitHub Actions (daily data updates)
├── archive/               # Old/obsolete scripts & docs
└── fec_bulk_data/         # Raw FEC bulk data files
```

---

## Features

1. **Leaderboard View** – Top fundraisers with sortable columns and CSV export
2. **By District** – Compare all candidates within a specific House district or Senate seat
3. **By Committee** – National committee drilldowns with quarterly trends
4. **Watchlists & Notifications** – Follow up to 50 candidates and toggle email alerts
5. **Auth & Google OAuth** – Supabase-powered email/password and Google sign-in

---

## Data Pipeline

### 1. Automated Data Collection (GitHub Actions)
- **Daily Updates:** 6 AM ET (11 AM UTC)
- **Filing Period Updates:** Every 2 hours on days 13-17 of Jan, Apr, Jul, Oct
- Fetches candidate and quarterly financial data from FEC API
- Rate limited: 900 requests/hour for collection (7,000/hour limit available)
- Automated via GitHub Actions workflow

### 2. Database (Supabase)
- PostgreSQL database with three main tables:
  - `candidates` - All 2026 House and Senate candidates
  - `financial_summary` - Latest summary financial data
  - `quarterly_financials` - Historical quarterly filings
- Automatic refresh logging in `data_refresh_log`

### 3. Frontend (Next.js)
- Deployed on Vercel
- Automatic deployments on git push
- Real-time data from Supabase
- Interactive charts with Recharts

---

## Tech Stack

### Frontend
- Next.js (App Router)
- React 19
- Tailwind CSS
- shadcn/ui + Radix primitives
- Recharts
- Supabase JS Client

### Backend/Data
- Python 3.9+
- Supabase (PostgreSQL)
- FEC OpenFEC API

### Deployment & Automation
- **Hosting:** Vercel (Free tier)
- **Domain:** campaign-reference.com (via Squarespace Domains)
- **CI/CD:** GitHub Actions
- **Data Updates:** Automated daily + filing period intensive updates

---

## Status

**Live in Production**
- Dashboard with Leaderboard, District, and Committee views
- Automated daily data updates via GitHub Actions
- Deployed on Vercel at campaign-reference.com

---

## Development

### Frontend
```bash
cd apps/labs
npm install
npm run dev
```
App runs at http://localhost:3000

### Data Collection (Manual)
```bash
pip3 install -r requirements.txt
python3 scripts/collect_cycle_data.py --cycle 2024
```
Note: Data updates are automated via GitHub Actions. Manual runs are only needed for testing.

---

## Environment Variables

### GitHub Secrets (for Actions)
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

### Vercel Environment Variables
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

### Local Development (.env files)

**Backend (.env in project root):**
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
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

Built for political journalists, researchers, and enthusiasts who need fast, accurate campaign finance data.
