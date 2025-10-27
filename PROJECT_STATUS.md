# Campaign Reference - Project Status

**Last Updated**: October 26, 2025
**Status**: ✅ Live in Production

🔗 **Live Site**: [https://campaign-reference.com](https://campaign-reference.com)
📊 **Repository**: [https://github.com/mathomdelving/campaign-reference](https://github.com/mathomdelving/campaign-reference)

## Overview

Campaign Reference is a React-based dashboard visualizing 2026 House and Senate campaign finance data from the FEC OpenFEC API. The application provides three distinct views for analyzing campaign fundraising across all federal races, with automated daily data updates and a Red Bull Racing-inspired design.

## Current Features

### Three Main Views

#### 1. Leaderboard (`/leaderboard`)
- **Purpose**: Rankings across all races
- **Features**:
  - Sortable table with 2,866 candidates
  - Filter by chamber, state, district, party
  - Toggle between table and bar chart view
  - Export to CSV/PNG
  - Data freshness indicator
  - Red Bull Racing theme with yellow highlights

#### 2. By District (`/district`)
- **Purpose**: Deep dive into specific district races
- **Features**:
  - State, Chamber, and District selectors
  - Compare all candidates within a single district
  - Party filter buttons (All, Democrats, Republicans, Third Party)
  - Ranked candidate list with metrics
  - Quarterly trend chart with dual Y-axis
  - Senate support with class differentiation (I, II, III, Special)

#### 3. By Candidate (`/candidate`)
- **Purpose**: Search and compare any candidates across all races
- **Features**:
  - Intelligent search bar (searches both name formats and states)
  - Multi-word search support ("Mark Kelly", "Kelly Mark", etc.)
  - Party filter buttons
  - Select multiple candidates from anywhere
  - Ranked candidate list with metrics
  - Quarterly trend chart
  - Loads all 2,866 candidates via batch fetching

## Deployment & Automation

### ✅ GitHub Actions (Phase 4 Complete)
- **Daily Updates**: 6 AM ET (11 AM UTC)
- **Filing Period Updates**: Every 2 hours on days 13-17 of Jan, Apr, Jul, Oct
- Automated FEC data fetching and Supabase loading
- Error logging and failure notifications
- Workflow: `.github/workflows/update-data.yml`

### ✅ Vercel Deployment (Phase 5 Complete)
- **Hosting**: Vercel Free Tier
- **Domain**: campaign-reference.com (via Squarespace Domains)
- **URL**: [https://campaign-reference.com](https://campaign-reference.com)
- **Auto-Deploy**: On every push to `main` branch
- **Build Time**: ~1-2 minutes
- **SSL/HTTPS**: Automatic via Vercel
- **Configuration**: `vercel.json` with Root Directory set to `frontend`

## Technical Stack

### Frontend
- **Framework**: React 19.1.1 with Vite 7.1.7
- **Styling**: Tailwind CSS 3.4.18 (Red Bull Racing theme)
- **Charts**: Recharts 3.3.0
- **Database**: Supabase JS Client 2.76.1
- **Router**: React Router 7.1.3
- **Image Export**: html2canvas 1.4.1

### Backend/Data Pipeline
- **API Source**: FEC OpenFEC API
- **Database**: Supabase (PostgreSQL)
- **Automation**: GitHub Actions
- **Data Scripts**: Python with Supabase client
- **Rate Limiting**: ~900 requests/hour (4 second delays)

### Deployment & CI/CD
- **Hosting**: Vercel
- **Automation**: GitHub Actions
- **Repository**: GitHub Public

## Data Coverage

- **Total Candidates**: 2,866 (with financial data)
- **Cycle**: 2026
- **Chambers**: House (H) and Senate (S)
- **Metrics**: Total Receipts, Total Disbursements, Cash on Hand
- **Quarterly Data**: Available for trend analysis
- **Update Schedule**: Daily at 6 AM ET + intensive during filing periods
- **Last Data Refresh**: See DataFreshnessIndicator in app

## Key Technical Achievements

### Search Functionality
- Word-based matching algorithm
- Searches both "LAST, FIRST" and "First Last" formats
- Handles middle initials and name variations
- Case-insensitive
- Instant client-side filtering

### Data Fetching Optimization
- Batch loading to bypass Supabase 1,000 row limit
- Pagination with `.range(from, to)`
- Loads ~2,866 candidates in 3 batches (~1-2 seconds)
- Console logging for transparency

### District Validation
- VALID_DISTRICT_COUNTS map with 2022 redistricting data
- Filters out 34 invalid/legacy districts
- Senate class extraction from candidate_id encoding

### Name Formatting
- `formatCandidateName()` utility function
- Converts "LAST, FIRST" → "First Last"
- Removes titles (MR., DR., SEN., etc.)
- Title case formatting
- Applied throughout UI

### Chart Design
- Simplified quarterly trend chart
- Dual Y-axis labels for better readability
- No legend clutter (data in list above)
- Thicker lines (2.5px) for visibility
- Supplementary role to ranked list

### Automated Data Pipeline
- GitHub Actions workflow for scheduled updates
- Fetches candidate and quarterly financial data
- Loads to Supabase automatically
- Logs refresh operations
- Email notifications on failure

### Continuous Deployment
- Automatic Vercel deployments on git push
- Build success/failure notifications
- Preview deployments for branches
- Production deployment to campaign-reference-five.vercel.app

## File Structure

```
campaign-reference/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navigation.jsx  # "Campaign Reference" branding
│   │   │   │   └── Footer.jsx
│   │   │   ├── toggles/
│   │   │   │   └── DistrictToggle.jsx
│   │   │   ├── QuarterlyChart.jsx
│   │   │   ├── RaceTable.jsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   ├── useCandidateData.js
│   │   │   ├── useQuarterlyData.js
│   │   │   └── useFilters.js
│   │   ├── views/
│   │   │   ├── LeaderboardView.jsx
│   │   │   ├── DistrictView.jsx
│   │   │   └── CandidateView.jsx
│   │   ├── utils/
│   │   │   ├── formatters.js
│   │   │   ├── exportUtils.js
│   │   │   └── supabaseClient.js
│   │   └── App.jsx
│   ├── CLAUDE.md
│   ├── README.md
│   └── package.json
├── .github/
│   └── workflows/
│       └── update-data.yml         # Automated data refresh
├── docs/
│   ├── GITHUB_DEPLOYMENT_GUIDE.md
│   ├── VERCEL_DEPLOYMENT_GUIDE.md
│   └── ...
├── fetch_fec_data.py
├── load_to_supabase.py
├── vercel.json                     # Vercel deployment config
├── CHANGELOG.md
├── PROJECT_STATUS.md (this file)
└── README.md
```

## Environment Variables

### GitHub Secrets
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
```

### Vercel Environment Variables
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

### Local Development

**Frontend (`.env` in `/frontend`):**
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Backend (`.env` in project root):**
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

## Development

### Start Dev Server
```bash
cd frontend
npm run dev
```
Runs on http://localhost:5173 (or 5174 if 5173 is in use)

### Build for Production
```bash
cd frontend
npm run build
npm run preview
```

### Monitor Automated Updates
```bash
# View GitHub Actions workflow status
gh run list --workflow=update-data.yml

# View latest run logs
gh run view --log
```

## Known Limitations

1. **Rate Limiting**: FEC API limited to ~900 requests/hour (mitigated with delays)
2. **Invalid Districts**: 34 legacy candidates in database (filtered from UI)
3. **Quarterly Data**: Not all candidates have full quarterly breakdowns
4. **Vercel URL**: Using default Vercel subdomain (campaign-reference-five.vercel.app)

## Future Enhancements (Potential)

- [ ] Custom domain (campaign-reference.com)
- [ ] Individual donor tracking (would require significant additional data)
- [ ] Historical cycle comparison (2024, 2022, etc.)
- [ ] Geographic visualization (maps)
- [ ] Contribution timeline analysis
- [ ] Committee expenditure breakdowns
- [ ] Mobile app version

## Documentation

- **README.md** - Project overview and quick start
- **frontend/README.md** - Frontend-specific documentation
- **frontend/CLAUDE.md** - Technical architecture for Claude Code
- **CHANGELOG.md** - Detailed change history
- **PROJECT_STATUS.md** - This file (current state overview)
- **docs/GITHUB_DEPLOYMENT_GUIDE.md** - GitHub Actions setup guide
- **docs/VERCEL_DEPLOYMENT_GUIDE.md** - Vercel deployment guide

## Project Phases

### ✅ Phase 1-3: Core Development (Complete)
- Data collection infrastructure
- Database schema with quarterly financials
- Three-view dashboard (Leaderboard, By District, By Candidate)
- Red Bull Racing-inspired UI
- Search, filter, and export functionality

### ✅ Phase 4: Automation (Complete)
- GitHub Actions workflow
- Daily data updates at 6 AM ET
- Intensive updates during filing periods (every 2 hours on days 13-17)
- Error logging and notifications

### ✅ Phase 5: Deployment (Complete)
- Vercel hosting
- Automatic deployments on push
- Live at campaign-reference-five.vercel.app
- Production-ready with monitoring

### 🎯 Current Focus
- Monitoring automated data updates
- Gathering user feedback
- Performance optimization
- Potential custom domain acquisition

## Deployment Readiness

✅ All features complete and tested
✅ Search working with all name variations
✅ All 2,866 candidates accessible
✅ Party filters functional in both District and Candidate views
✅ Charts optimized and simplified
✅ Responsive design with Tailwind CSS
✅ Export functionality working
✅ Senate support complete
✅ District validation implemented
✅ GitHub Actions automation live
✅ Vercel deployment successful
✅ Automated daily data updates

**Status**: ✅ Live in Production at [campaign-reference.com](https://campaign-reference.com) 🚀

**Branding**: Campaign Reference (formerly Political Pole)
**Version**: 1.0.0
**Last Updated**: October 26, 2025
