# Campaign Reference 🏁

**A RedBull Racing-inspired campaign finance dashboard for 2026 House and Senate races**

Real-time FEC data visualization with automated daily updates.

🔗 **Live Site:** [https://campaign-reference.com](https://campaign-reference.com)
📊 **Repository:** [https://github.com/mathomdelving/campaign-reference](https://github.com/mathomdelving/campaign-reference)

---

## 🚀 Quick Start

### Development Server
```bash
cd frontend
npm run dev
```

### Monitor Automated Data Updates
Data automatically updates daily at 6 AM ET via GitHub Actions. Check logs:
```bash
# View GitHub Actions workflow status
gh run list --workflow=update-data.yml

# View latest run logs
gh run view --log
```

---

## 📁 Project Structure

```
campaign-reference/
├── frontend/              # React + Vite application
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Helper functions
│   └── ...
│
├── docs/                  # Documentation
│   ├── ROADMAP.md                     # Project roadmap and phases
│   ├── GITHUB_DEPLOYMENT_GUIDE.md     # GitHub setup instructions
│   ├── VERCEL_DEPLOYMENT_GUIDE.md     # Vercel deployment guide
│   ├── DEBUGGING_FINDINGS.md          # Technical analysis of data issues
│   ├── IMPLEMENTATION_PLAN.md         # Quarterly timeseries implementation
│   └── RATE_LIMIT_ANALYSIS.md         # FEC API rate limiting details
│
├── .github/
│   └── workflows/
│       └── update-data.yml            # Automated data refresh workflow
│
├── sql/                   # Database schemas
│   └── create_quarterly_table.sql     # Quarterly financials table
│
├── fetch_fec_data.py      # Main data collection script
├── load_to_supabase.py    # Database loading script
├── vercel.json            # Vercel deployment configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🎨 Campaign Reference Branding

### Primary Colors (Red Bull Racing Inspired)
- **Navy Blue:** `#121F45` - Primary backgrounds
- **Blue:** `#223971` - Secondary backgrounds
- **Red:** `#CC1E4A` - Accents and CTAs
- **Yellow:** `#FFC906` - Highlights
- **White:** `#FFFFFF` - Text on dark backgrounds

### Party Colors (Standard)
- **Democrats:** `#2563EB` (Blue)
- **Republicans:** `#DC2626` (Red)
- **Independents:** `#7C3AED` (Purple)
- **Others:** `#6B7280` (Gray)

---

## 🎯 Features

1. **Leaderboard View** - Top fundraisers with sortable columns
2. **By District** - Compare all candidates within a specific House district or Senate seat
3. **By Candidate** - Search and compare candidates across different races
4. **Quarterly Trends** - Historical financial data with interactive charts
5. **Data Export** - Export tables and charts to CSV/PNG

---

## 📊 Data Pipeline

### 1. Automated Data Collection (GitHub Actions)
- **Daily Updates:** 6 AM ET (11 AM UTC)
- **Filing Period Updates:** Every 2 hours on days 13-17 of Jan, Apr, Jul, Oct
- Fetches candidate and quarterly financial data from FEC API
- Rate limited: 900 requests/hour (safely under FEC's 1,000/hour limit)
- Automated via GitHub Actions workflow

### 2. Database (Supabase)
- PostgreSQL database with three main tables:
  - `candidates` - All 2026 House and Senate candidates
  - `financial_summary` - Latest summary financial data
  - `quarterly_financials` - Historical quarterly filings
- Automatic refresh logging in `data_refresh_log`

### 3. Frontend (React + Vite)
- Deployed on Vercel
- Automatic deployments on git push
- Real-time data from Supabase
- Interactive charts with Recharts
- Export to CSV/PNG with html2canvas

---

## 🔧 Tech Stack

### Frontend
- React 19.1.1
- Vite 7.1.7
- Tailwind CSS 3.4.18
- Recharts 3.3.0
- Supabase JS Client 2.76.1
- React Router 7.1.3

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

## 📈 Current Status

**✅ Phase 1-3: Complete**
- Data collection infrastructure
- Database schema with quarterly financials
- Three-view dashboard (Leaderboard, By District, By Candidate)
- Red Bull Racing-inspired UI

**✅ Phase 4: Complete**
- GitHub Actions automation
- Daily data updates at 6 AM ET
- Intensive updates during filing periods

**✅ Phase 5: Complete**
- Vercel deployment
- Custom domain: campaign-reference.com
- Automatic deployments on push
- Live in production with SSL/HTTPS

**🎯 Current Focus:**
- Monitoring automated data updates
- Gathering user feedback
- Performance optimization

---

## 🛠️ Development

### Python Scripts (Local/Manual Use)
```bash
# Install dependencies
pip3 install -r requirements.txt

# Manually collect FEC data
python3 fetch_fec_data.py

# Manually load to database
python3 load_to_supabase.py
```

**Note:** Data updates are automated via GitHub Actions. Manual runs are only needed for testing or ad-hoc updates.

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📝 Environment Variables

### GitHub Secrets (for Actions)
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

### Vercel Environment Variables
```
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

### Local Development (.env files)

**Backend (.env in project root):**
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

**Frontend (frontend/.env):**
```
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

---

## 📚 Documentation

See `docs/` folder for detailed documentation:
- `ROADMAP.md` - Complete project history and roadmap
- `GITHUB_DEPLOYMENT_GUIDE.md` - Step-by-step GitHub setup
- `VERCEL_DEPLOYMENT_GUIDE.md` - Step-by-step Vercel deployment
- `IMPLEMENTATION_PLAN.md` - Technical implementation details
- `RATE_LIMIT_ANALYSIS.md` - FEC API rate limiting breakdown
- `DEBUGGING_FINDINGS.md` - Technical analysis and solutions

---

## 🏁 Campaign Reference

*Inspired by sports-reference.com sites (baseball-reference, football-reference) and styled after RedBull Racing.*

Built for political journalists, researchers, and enthusiasts who need fast, accurate campaign finance data.

**Version:** 1.0.0 (Deployed)
**Last Updated:** October 26, 2025
**Status:** ✅ Live in Production
