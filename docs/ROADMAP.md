# FEC Campaign Finance Dashboard - Development Roadmap

**Project:** Interactive dashboard for 2026 House and Senate campaign finance data
**Data Source:** FEC OpenFEC API
**Status:** Phase 4 Complete - Ready for Phase 5
**Last Updated:** October 26, 2025

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Phase 1: Data Collection](#phase-1-data-collection-complete)
3. [Phase 2: Database Setup](#phase-2-database-setup-complete)
4. [Phase 3: Frontend Dashboard](#phase-3-frontend-dashboard-complete)
5. [Phase 4: Automation](#phase-4-automation)
6. [Phase 5: Deployment](#phase-5-deployment)
7. [Technical Specifications](#technical-specifications)
8. [Next Steps](#next-steps)

---

## Project Overview

### Goal
Build a campaign finance dashboard displaying House and Senate race data with interactive filters for cycle, chamber, state, district, candidates, and financial metrics.

### Target Users
Political journalists (Jake Sherman, Lakshya Jain types) who need fast, screenshot-worthy visualizations when filings drop.

### Core Features
- 5 toggles: Cycle, Chamber, State, District, Metrics
- Real-time financial data: Total Raised, Total Disbursed, Cash on Hand
- Table and chart views
- Data freshness indicator
- Export capabilities (CSV/PNG)
- Mobile responsive

---

## Phase 1: Data Collection [✅ COMPLETE]

### Status: Complete
**Completed:** October 21, 2025  
**Duration:** ~6 hours total

### Results
- ✅ All 5,185 candidates collected
- ✅ 1,925 candidates with financial data (37%)
- ✅ Total raised: $1,127,847,452.02
- ✅ Data files created successfully

### Files Created
```
candidates_2026.json      4.3 MB    Complete - All candidates
financials_2026.json      1.3 MB    Complete - Current totals only
```

### Notes
- Current implementation fetches latest totals only (not quarterly breakdowns)
- Quarterly trend data deferred to post-MVP
- Resume capability worked successfully after rate limit issues

### Data Schema

**Candidates:**
```json
{
  "candidate_id": "H6CA12345",
  "name": "SMITH, JOHN",
  "party_full": "Republican",
  "state": "CA",
  "district": "12",
  "office_full": "House",
  "cycle": 2026
}
```

**Financials:**
```json
{
  "candidate_id": "H6CA12345",
  "name": "SMITH, JOHN",
  "party": "Republican",
  "state": "CA",
  "district": "12",
  "office": "House",
  "total_receipts": 1234567.89,
  "total_disbursements": 987654.32,
  "cash_on_hand": 246913.57,
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-06-30",
  "cycle": 2026
}
```

---

## Phase 2: Database Setup [✅ COMPLETE]

### Status: Complete
**Completed:** October 21, 2025  
**Duration:** ~2 hours total

### Platform: Supabase (PostgreSQL)
**Why:** Free tier (500MB), managed PostgreSQL, good API support

### Database Schema

#### Table: `candidates`
```sql
CREATE TABLE candidates (
  candidate_id VARCHAR(9) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  party VARCHAR(50),
  state VARCHAR(2),
  district VARCHAR(3),
  office VARCHAR(1) NOT NULL,
  cycle INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_candidates_cycle_office ON candidates(cycle, office);
CREATE INDEX idx_candidates_state_district ON candidates(state, district);
```

#### Table: `financial_summary`
```sql
CREATE TABLE financial_summary (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  cycle INTEGER NOT NULL,
  total_receipts DECIMAL(15,2),
  total_disbursements DECIMAL(15,2),
  cash_on_hand DECIMAL(15,2),
  coverage_start_date DATE,
  coverage_end_date DATE,
  report_year INTEGER,
  report_type VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_financial_candidate ON financial_summary(candidate_id);
CREATE INDEX idx_financial_cycle ON financial_summary(cycle);
CREATE UNIQUE INDEX idx_financial_unique 
  ON financial_summary(candidate_id, cycle, coverage_end_date);
```

#### Table: `data_refresh_log`
```sql
CREATE TABLE data_refresh_log (
  id SERIAL PRIMARY KEY,
  fetch_date TIMESTAMP DEFAULT NOW(),
  cycle INTEGER,
  records_updated INTEGER,
  errors TEXT,
  status VARCHAR(20),
  duration_seconds INTEGER
);
```

### Load Results
- ✅ 5,185 candidates loaded
- ✅ 2,841 financial records loaded
- ✅ Total records: 8,026
- ✅ Duration: 3 seconds
- ✅ Zero errors
- ✅ Data refresh logged successfully

### Files Created
```
load_to_supabase.py       Script to load JSON data to database
```

### Notes
- Script uses batch inserts (1,000 records per batch) for efficiency
- `merge-duplicates` preference allows re-running without creating duplicates
- Financial records properly linked to candidates via foreign key
- All indexes created for optimal query performance
- RLS (Row Level Security) disabled for public read access

### Historical Cycles
- Same schema supports multiple cycles
- Filter by `cycle` field
- Add historical data by re-running fetch script with different CYCLE value

---

## Phase 3: Frontend Dashboard [✅ COMPLETE]

### Status: Complete
**Started:** October 21, 2025  
**Completed:** October 21, 2025  
**Duration:** ~4 hours total

### Tech Stack
- **Framework:** React 19.1.1 + Vite 7.1.7 ✅
- **Styling:** Tailwind CSS v3.4.18 ✅
- **Charts:** Recharts 3.3.0 ✅
- **State:** Custom React hooks ✅
- **Database:** @supabase/supabase-js 2.76.1 ✅
- **Export:** html2canvas 1.4.1 ✅
- **Hosting:** Vercel (Phase 5)

### Completed Features
- ✅ React + Vite initialized
- ✅ Tailwind CSS v3 configured and working
- ✅ Supabase client connected
- ✅ Environment variables configured
- ✅ All toggle components built and functional
- ✅ Table view with sortable columns
- ✅ Chart visualization (top 20 candidates)
- ✅ Export functionality (CSV, Chart PNG, Table PNG)
- ✅ Data freshness indicator
- ✅ Responsive design
- ✅ Loading and error states
- ✅ Real-time data filtering

### Final File Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ChamberToggle.jsx        ✅ Button group (House/Senate/Both)
│   │   ├── CycleToggle.jsx           ✅ Dropdown for cycle selection
│   │   ├── DataFreshnessIndicator.jsx ✅ Last updated timestamp
│   │   ├── DistrictToggle.jsx        ✅ Conditional dropdown
│   │   ├── ExportButton.jsx          ✅ CSV/PNG export menu
│   │   ├── MetricToggle.jsx          ✅ Checkboxes for metrics
│   │   ├── RaceChart.jsx             ✅ Chart visualization
│   │   ├── RaceTable.jsx             ✅ Main data table
│   │   ├── StateToggle.jsx           ✅ Searchable dropdown
│   │   └── ToggleBar.jsx             ✅ Container for all toggles
│   ├── hooks/
│   │   ├── useCandidateData.js       ✅ Data fetching logic
│   │   └── useFilters.js             ✅ Filter state management
│   ├── utils/
│   │   ├── exportUtils.js            ✅ CSV/PNG export functions
│   │   ├── formatters.js             ✅ Currency/number/date formatting
│   │   └── supabaseClient.js         ✅ Supabase connection
│   ├── App.jsx                        ✅ Main application component
│   ├── App.css
│   ├── index.css                      ✅ Tailwind directives
│   └── main.jsx
├── .env                                ✅ Environment variables
├── package.json                        ✅ Dependencies
├── vite.config.js                      ✅ Vite configuration
├── tailwind.config.js                  ✅ Tailwind configuration
└── postcss.config.js                   ✅ PostCSS configuration
```

### Component Architecture

**State Management:**
- `useFilters` hook manages all filter state (cycle, chamber, state, district, metrics)
- `useCandidateData` hook fetches data from Supabase based on current filters
- Automatic refetch when filters change
- React's built-in state management (no external library needed)

**Toggle Components:**
1. **CycleToggle** - Dropdown for election cycle (2026, 2024, 2022, 2020)
2. **ChamberToggle** - Button group for House/Senate/Both
3. **StateToggle** - Searchable dropdown with all 50 states + DC
4. **DistrictToggle** - Conditional dropdown (only shows when House selected, dynamically fetches districts)
5. **MetricToggle** - Checkboxes for Total Raised, Total Disbursed, Cash on Hand

**Display Components:**
1. **RaceTable** - Sortable table with party color coding, monospace numbers, conditional columns
2. **RaceChart** - Bar chart showing top 20 candidates with custom tooltips and rotated labels
3. **DataFreshnessIndicator** - Shows last update time with green dot indicator
4. **ExportButton** - Dropdown menu with CSV/Chart PNG/Table PNG options

**Utility Functions:**
- Currency formatting ($1,234,567 and $1.2M compact format)
- Relative time formatting ("5 hours ago")
- Party color mapping (blue for Democrats, red for Republicans, etc.)
- CSV generation with proper escaping
- PNG export using html2canvas

### Data Flow
```
User adjusts filters
  ↓
useFilters hook updates state
  ↓
useCandidateData hook detects change
  ↓
Supabase query built with filters
  ↓
Data fetched and processed
  ↓
RaceTable or RaceChart renders
```

### Results Dashboard
- ✅ Successfully displays 541 candidates with default filters
- ✅ All filter combinations work correctly
- ✅ Table sorting functional on all numeric columns
- ✅ Chart displays top 20 fundraisers
- ✅ Export to CSV downloads properly formatted file
- ✅ PNG export captures visuals for screenshots
- ✅ Data freshness indicator shows last update time
- ✅ Mobile responsive (grid adapts to screen size)

### Challenges Encountered & Solutions

#### Challenge 1: Empty Component Files
**Problem:** Created component files but they were empty (0 bytes), causing import errors  
**Solution:** Verified file sizes using `ls -la src/components/` and re-pasted code into each file  
**Learning:** Always verify file sizes after creating files to ensure content was saved

#### Challenge 2: Supabase API Key Errors (401 Unauthorized)
**Problem:** Frontend couldn't connect to Supabase despite having credentials  
**Root Cause:** Environment variable file (`frontend/.env`) didn't exist  
**Solution:** Created `frontend/.env` with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY  
**Learning:** Vite requires VITE_ prefix for environment variables to be exposed to browser

#### Challenge 3: Invalid API Key After .env Creation
**Problem:** Still getting 401 errors even after creating .env file  
**Root Cause:** Anon key in .env was incorrect (single character typo in middle of key)  
**Solution:** Re-copied anon key from Supabase dashboard API settings  
**Learning:** Always double-check long API keys character-by-character; one typo breaks everything

#### Challenge 4: Environment Variables Not Loading
**Problem:** Added .env file but app still showed "Invalid API key"  
**Solution:** Must restart Vite dev server after any .env changes (Ctrl+C, then `npm run dev`)  
**Learning:** Vite only reads environment variables on startup, not hot-reload

### Testing Results
- ✅ Filter by cycle: Works
- ✅ Filter by chamber (House/Senate/Both): Works
- ✅ Filter by state: Works with searchable dropdown
- ✅ Filter by district: Conditionally appears, loads districts dynamically
- ✅ Toggle metrics on/off: Table columns update correctly
- ✅ Sort table by any financial column: Works with ascending/descending
- ✅ Switch between table and chart view: Smooth transitions
- ✅ Export to CSV: Downloads with proper formatting
- ✅ Export chart to PNG: High-quality screenshot
- ✅ Export table to PNG: Captures visible table
- ✅ Data freshness indicator: Shows "5 hours ago" correctly
- ✅ Party color coding: Blue (D), Red (R), Purple (I), etc.
- ✅ Empty state handling: Shows "No data available" message
- ✅ Loading states: Shows spinner during fetch
- ✅ Error states: Displays error message in red

### Performance Notes
- Initial load: ~1-2 seconds for 541 candidates with default filters
- Filter changes: Sub-second response
- Sorting: Instant (client-side)
- Chart rendering: ~500ms for 20 candidates
- Export operations: 1-3 seconds depending on data size

### Browser Compatibility
- Tested on Chrome (primary development browser)
- Uses modern JavaScript features (ES6+)
- Tailwind CSS ensures consistent styling
- Recharts uses SVG (universal browser support)

---

## Phase 4: Automation [✅ COMPLETE]

### Status: Complete
**Completed:** October 26, 2025
**Duration:** ~1 hour

### GitHub Actions Workflow

**File:** `.github/workflows/update-data.yml` ✅

**Schedule:**
- ✅ Daily at 6 AM ET (11 AM UTC): Regular updates
- ✅ Every 2 hours on days 13-17 of filing months (Jan, Apr, Jul, Oct)
- ✅ Manual trigger available via GitHub web interface

**Jobs:**
1. ✅ Checkout repository code
2. ✅ Set up Python environment
3. ✅ Install dependencies from requirements.txt
4. ✅ Fetch FEC data (`fetch_fec_data.py`)
5. ✅ Load to Supabase (`load_to_supabase.py`)
6. ✅ Log completion with file sizes
7. ✅ Upload debug logs on failure
8. ✅ Notify on failure

**Required GitHub Secrets:**
- `FEC_API_KEY` - Your FEC API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key

**Documentation Created:**
- ✅ `docs/GITHUB_ACTIONS_SETUP.md` - Complete setup guide with step-by-step instructions

**Free Tier Usage:**
- GitHub Actions: 2,000 free minutes/month
- Daily updates: ~300 minutes/month
- Filing period updates: ~500 additional minutes (4 months/year)
- **Total: ~500-800 minutes/month** (well within free tier)

### Next Steps for User

To activate automation:
1. Push repository to GitHub (if not already done)
2. Add three secrets in GitHub Settings → Secrets and variables → Actions:
   - `FEC_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
3. Test workflow manually via GitHub Actions tab
4. Monitor first scheduled run

See `docs/GITHUB_ACTIONS_SETUP.md` for detailed instructions.

---

## Phase 5: Deployment

### Frontend (Vercel)

**Steps:**
1. Push to GitHub
2. Import repository on vercel.com
3. Configure build settings:
   - Framework: Vite
   - Build: `cd frontend && npm run build`
   - Output: `frontend/dist`
4. Set environment variables
5. Deploy (automatic on push)

**Domain:**
- Free: `fec-dashboard.vercel.app`
- Custom domain supported

### Backend/Data
- Database: Supabase (hosted)
- Updates: GitHub Actions
- No separate backend server needed

### Performance
- Database indexes on key fields
- Query caching (5-minute TTL)
- CDN via Vercel
- Lazy loading for large datasets

---

## Technical Specifications

### Versions
- **Node.js:** v22.21.0
- **npm:** (bundled with Node)
- **Python:** 3.x
- **React:** 19.1.1
- **Vite:** 7.1.7
- **Tailwind CSS:** 3.4.18
- **Recharts:** 3.3.0
- **@supabase/supabase-js:** 2.76.1
- **html2canvas:** 1.4.1

### API Details
**FEC OpenFEC API:**
- Base URL: `https://api.open.fec.gov/v1`
- Rate Limit: 1,000 requests/hour (personal key)
- Authentication: API key via query parameter
- Data Updates: Nightly (official), 15-min (electronic filings)

### Installed Dependencies

**Python:**
```
requests==2.31.0
python-dotenv==1.0.0
```

**JavaScript:**
```json
{
  "dependencies": {
    "react": "^19.1.1",
    "react-dom": "^19.1.1",
    "@supabase/supabase-js": "^2.76.1",
    "recharts": "^3.3.0",
    "html2canvas": "^1.4.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.0.4",
    "tailwindcss": "^3.4.18",
    "postcss": "^8.5.6",
    "autoprefixer": "^10.4.21",
    "vite": "^7.1.7"
  }
}
```

### Environment Variables
```
# Backend (root .env)
FEC_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_service_role_key_here

# Frontend (frontend/.env)
VITE_SUPABASE_URL=your_url_here
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

**IMPORTANT:** Vite requires `VITE_` prefix for environment variables to be exposed to the browser. Must restart dev server after any .env changes.

---

## Design Decisions

### Why No Separate Backend?
- Supabase provides direct frontend access
- Row-level security handles permissions (disabled for public read access)
- Reduces complexity for non-technical user
- Fewer moving parts to maintain

### Why JSON Intermediate Files?
- Easy to inspect and debug
- Resume capability
- Version control friendly
- Can rerun parts without refetching

### Why 2026 Only Initially?
- 2025 current year, 2026 next cycle
- Presidential 2028 won't heat up until 2027
- Historical cycles can be added later

### Why Recharts?
- Simpler than D3
- Better defaults for this use case
- Easier maintenance
- Sufficient for bar/line charts
- Good TypeScript support

### Why Tailwind v3 Instead of v4?
- More stable and well-documented
- Better PostCSS integration with Vite
- Fewer configuration issues
- Standard syntax widely used
- v4 had compatibility issues with Vite during setup

### Why Custom Hooks Instead of State Management Library?
- Simple enough for built-in React state
- No need for Redux/Zustand complexity
- Two hooks handle all state needs
- Easier to understand and maintain
- Less bundle size

---

## Known Challenges

### Challenge: Rate Limiting
**Solution:** 4-second delays, exponential backoff, progress saving

### Challenge: Long Data Collection
**Solution:** Resume capability, overnight runs, automation

### Challenge: Data Freshness
**Solution:** Automated updates around filing deadlines

### Challenge: Non-Technical User
**Solution:** Managed services, minimal tools, clear docs

### Challenge: Large Datasets
**Solution:** Database indexes, filtered queries, lazy loading

### Challenge: Tailwind Configuration
**Solution:** Used v3 with PostCSS instead of v4 Vite plugin for stability

### Challenge: Environment Variables
**Solution:** Must use VITE_ prefix and restart dev server after changes

### Challenge: API Key Typos
**Solution:** Double-check long keys character-by-character; use copy-paste from Supabase dashboard

---

## Next Steps

### Immediate (Phase 4)
1. Set up GitHub Actions workflow
2. Configure automated data updates
3. Test automation with manual triggers
4. Set up error notifications

### Short Term (Phase 5)
5. Create Vercel account
6. Deploy to Vercel
7. Configure production environment variables
8. Test live deployment
9. Set up custom domain (optional)

### Medium Term
10. Add historical cycles (2024, 2022)
11. Performance optimization
12. Test with real users (target journalists)
13. Gather feedback and iterate
14. Monitor query performance
15. Add database query caching

### Long Term
16. Add quarterly trend data
17. Advanced filtering options (date ranges, contribution sources)
18. Mobile app consideration
19. Additional data visualizations (pie charts, trend lines)
20. Real-time updates during filing periods

---

## Success Metrics

### Technical
- ✅ All 5,185 candidates loaded
- ✅ All 2,841 financial records loaded
- ✅ Frontend successfully connected to database
- ✅ Tailwind CSS working correctly
- ✅ All toggle components functional
- ✅ Table and chart views working
- ✅ Export functionality operational
- ✅ Data freshness indicator accurate
- ⬜ Sub-second query times (currently 1-2 seconds)
- ⬜ Zero downtime during traffic spikes
- ⬜ Automated daily updates working

### User Experience
- ✅ Clean, readable visualizations
- ✅ Easy filtering (≤3 clicks to any view)
- ✅ Export functionality working
- ✅ Mobile responsive design
- ⬜ Used by target journalists
- ⬜ Tested with real users

---

## Accounts & Dependencies

### Already Have
- ✅ GitHub account + repository
- ✅ FEC API key
- ✅ VS Code installed
- ✅ Python environment working
- ✅ Mac Terminal setup
- ✅ Supabase account + project
- ✅ Node.js v22.21.0 installed
- ✅ All npm packages installed

### Still Need
- ⬜ Vercel account (free tier)
- ⬜ GitHub Actions configured

---

## Current File Structure
```
fec-dashboard/
├── .env                        # Backend API keys (not in git)
├── .gitignore                  # Excludes sensitive files
├── fetch_fec_data.py           # Data collection script
├── load_to_supabase.py         # Database loading script
├── requirements.txt            # Python dependencies
├── candidates_2026.json        # 5,185 candidates (4.3 MB)
├── financials_2026.json        # 2,841 financial records (1.3 MB)
├── progress.json               # Resume tracking
├── ROADMAP.md                  # This file
├── README.md                   # GitHub readme
└── frontend/                   # React application
    ├── src/
    │   ├── components/         # All UI components (10 files)
    │   ├── hooks/              # Custom React hooks (2 files)
    │   ├── utils/              # Utility functions (3 files)
    │   ├── App.jsx             # Main application
    │   ├── App.css
    │   ├── index.css           # Tailwind directives
    │   └── main.jsx
    ├── .env                     # Frontend env vars (not in git)
    ├── package.json             # Dependencies
    ├── vite.config.js          # Vite configuration
    ├── tailwind.config.js      # Tailwind configuration
    └── postcss.config.js       # PostCSS configuration
```

---

## Development Notes

### User Context
- Mac user, Terminal + VS Code
- Non-technical but willing to learn
- Prefers thorough explanations
- Values rigorous dialogue

### Communication Guidelines
- Be direct, avoid flattery
- Use separate code blocks per file
- State assumptions clearly
- Explain complexity without condescension
- Use analogies for new concepts
- Treat as thought partner

---

## Session History

### Session 1: Data Collection (October 21, 2025)
- Set up Python environment
- Created FEC API data collection script
- Fetched all 5,185 2026 candidates
- Fetched financial data for 2,841 candidates
- Implemented progress saving for resume capability

### Session 2: Database Setup (October 21, 2025)
- Created Supabase account and project
- Designed database schema
- Created tables with proper indexes
- Loaded all candidate and financial data
- Verified data integrity

### Session 3: Frontend Foundation (October 21, 2025)
- Initialized React + Vite project
- Configured Tailwind CSS v3 (after v4 compatibility issues)
- Set up Supabase JavaScript client
- Configured environment variables
- Created connection test component
- Verified successful database connection

### Session 4: Component Development (October 21, 2025)
- Built custom hooks for state and data management
- Created utility functions for formatting and export
- Built all 10 UI components
- Integrated components in main App.jsx
- Troubleshot empty file issue
- Fixed Supabase API key connection problems
- Successfully loaded and displayed real data
- Tested all features (filters, table, chart, export)
- Achieved fully functional dashboard

---

## Resources

- FEC API Docs: https://api.open.fec.gov/developers/
- Supabase Docs: https://supabase.com/docs
- Vercel Docs: https://vercel.com/docs
- Recharts Docs: https://recharts.org/
- Tailwind CSS v3: https://tailwindcss.com/docs
- React Docs: https://react.dev/
- Vite Docs: https://vite.dev/
- html2canvas: https://html2canvas.hertzen.com/

---

**Last Updated:** October 21, 2025  
**Version:** 3.0  
**Status:** Phase 3 Complete - Ready for Phase 4 (Automation)  
**Completion:** 60% overall (Phases 1-3 complete, Phases 4-5 remaining)