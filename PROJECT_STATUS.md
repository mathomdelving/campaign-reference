# FEC Campaign Finance Dashboard - Project Status

**Last Updated**: January 24, 2025
**Status**: ✅ Production Ready

## Overview

A React-based dashboard visualizing 2026 House and Senate campaign finance data from the FEC OpenFEC API. The application provides three distinct views for analyzing campaign fundraising across all federal races.

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

## Technical Stack

### Frontend
- **Framework**: React 19 with Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Database**: Supabase (PostgreSQL)
- **Router**: React Router v6
- **Image Export**: html2canvas

### Backend/Data Pipeline
- **API Source**: FEC OpenFEC API
- **Data Scripts**: Python with Supabase client
- **Rate Limiting**: ~900 requests/hour (4 second delays)

## Data Coverage

- **Total Candidates**: 2,866 (with financial data)
- **Cycle**: 2026
- **Chambers**: House (H) and Senate (S)
- **Metrics**: Total Receipts, Total Disbursements, Cash on Hand
- **Quarterly Data**: Available for trend analysis
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

## File Structure

```
fec-dashboard/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Navigation.jsx
│   │   │   ├── DistrictToggle.jsx
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
│   └── package.json
├── fetch_fec_data.py
├── load_to_supabase.py
├── fix_missing_cash.py
├── CHANGELOG.md
└── PROJECT_STATUS.md (this file)
```

## Environment Variables

### Frontend (`.env` in `/frontend`)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Backend (`.env` in project root)
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
npm run build
npm run preview
```

## Known Limitations

1. **Data Refresh**: Requires manual re-run of Python scripts
2. **Invalid Districts**: 34 legacy candidates in database (filtered from UI)
3. **Rate Limiting**: FEC API limited to ~900 requests/hour
4. **Quarterly Data**: Not all candidates have full quarterly breakdowns

## Future Enhancements (Potential)

- [ ] Automated data refresh scheduling
- [ ] Individual donor tracking (would require significant additional data)
- [ ] Historical cycle comparison (2024, 2022, etc.)
- [ ] Geographic visualization (maps)
- [ ] Contribution timeline analysis
- [ ] Committee expenditure breakdowns

## Documentation

- **CHANGELOG.md** - Detailed change history
- **frontend/CLAUDE.md** - Technical architecture and implementation details
- **PROJECT_STATUS.md** - This file (current state overview)

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

**Status**: Ready for production deployment 🚀
