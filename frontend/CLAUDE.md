# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Campaign Reference**, a React-based FEC Campaign Finance Dashboard that visualizes 2026 House and Senate campaign finance data. The frontend fetches data from a Supabase backend that is populated by Python scripts that pull from the FEC OpenFEC API.

**Tech Stack:**
- React 19 with Vite
- Tailwind CSS for styling
- Recharts for data visualization
- Supabase for database/backend
- html2canvas for export functionality

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Data Pipeline Architecture

### Python Scripts (in parent directory)

1. **fetch_fec_data.py** - Fetches candidate and financial data from FEC API
   - Rate limited to ~900 requests/hour (4 second delay between requests)
   - Saves data to `candidates_2026.json` and `financials_2026.json`
   - Has resume capability via `progress.json` for long-running fetches
   - Requires `FEC_API_KEY` in `.env`

2. **load_to_supabase.py** - Loads JSON data into Supabase
   - Transforms and uploads data to `candidates` and `financial_summary` tables
   - Uses batch inserts (1000 records per batch)
   - Logs refresh operations to `data_refresh_log` table
   - Requires `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

### Database Schema (Supabase)

**candidates** table:
- candidate_id (primary key)
- name, party, state, district, office, cycle

**financial_summary** table:
- candidate_id (foreign key)
- cycle
- total_receipts, total_disbursements, cash_on_hand
- coverage_start_date, coverage_end_date
- report_year, report_type
- updated_at (timestamp)

**data_refresh_log** table:
- Tracks data refresh operations

## Frontend Architecture

### Application Structure

The app has **three main views**:

1. **LeaderboardView** (`/leaderboard`) - Rankings across all races
   - Sortable table with all candidates
   - Filter by chamber, state, district, party
   - Export to CSV/PNG

2. **DistrictView** (`/district`) - By District comparison
   - Select state, chamber, and specific district
   - Compare all candidates within that district
   - Party filter buttons for primary races
   - Ranked list with metrics
   - Quarterly trend chart

3. **CandidateView** (`/candidate`) - By Candidate search & compare
   - Search bar with intelligent word-based matching
   - Party filter buttons
   - Select multiple candidates from anywhere
   - Ranked list with metrics
   - Quarterly trend chart

### Core State Management

The app uses two main custom hooks:

**useFilters** (`src/hooks/useFilters.js`):
- Manages all filter state (cycle, chamber, state, district, candidates, metrics)
- Automatically resets district when chamber changes to Senate or Both
- Provides `updateFilter`, `updateMetric`, and `resetFilters` functions

**useCandidateData** (`src/hooks/useCandidateData.js`):
- Fetches data from Supabase based on current filters
- Joins `candidates` with `financial_summary` table
- Returns flattened data with `totalReceipts`, `totalDisbursements`, `cashOnHand`
- Tracks `lastUpdated` timestamp from most recent financial data
- Re-fetches whenever filters change

**useQuarterlyData** (`src/hooks/useQuarterlyData.js`):
- Fetches quarterly financial data for selected candidates
- Used by both DistrictView and CandidateView

### Component Structure

**App.jsx** - Main container
- React Router setup with 3 main routes
- Navigation component
- Footer with data source attribution

**Navigation.jsx** - Top navigation bar
- 3 tabs: Leaderboard, By District, By Candidate
- Responsive with icons
- Active state highlighting

**View Components**:
- **LeaderboardView.jsx** - Table/chart toggle, filters, export
- **DistrictView.jsx** - State/Chamber/District selectors, party filters, ranked list, chart
- **CandidateView.jsx** - Search bar, party filters, candidate selection, ranked list, chart

**Toggle Components**:
- ChamberToggle.jsx - House/Senate/Both selector
- CycleToggle.jsx - Election cycle selector
- StateToggle.jsx - State dropdown with all US states (searchable)
- DistrictToggle.jsx - District/Senate seat selector
  - Shows numbered districts for House races (1-52 depending on state)
  - Shows Senate seat classes (I, II, III, Special) for Senate races
  - Validates districts against VALID_DISTRICT_COUNTS map
  - Filters out invalid/legacy districts from old redistricting maps
- MetricToggle.jsx - Checkboxes for which financial metrics to display

**Data Display Components**:
- RaceTable.jsx - Sortable table view with party color indicators
  - Shows "SEN" for Senate candidates in district column
- RaceChart.jsx - Bar chart visualization using Recharts (LeaderboardView)
- QuarterlyChart.jsx - Line chart for quarterly trends (DistrictView & CandidateView)
  - Dual Y-axis labels for better readability
  - No legend (data shown in list above)
  - Simplified design as supplementary graphic

**Utility Components**:
- DataFreshnessIndicator.jsx - Shows when data was last updated
- ExportButton.jsx - Dropdown menu for CSV/PNG export options

### Key Utilities

**formatters.js**:
- `formatCurrency()` - US currency formatting ($1,234,567)
- `formatCompactCurrency()` - Compact format ($1.2M, $45.3K)
- `formatRelativeTime()` - Human-readable timestamps
- `getPartyColor()` - Returns color codes for party affiliation (Democrat: blue, Republican: red, etc.)
- `formatCandidateName()` - Converts "LAST, FIRST" to "First Last" format
  - Removes titles (MR., DR., SEN., etc.)
  - Converts to title case
  - Used in QuarterlyChart tooltips and legends

**exportUtils.js**:
- `exportToCSV()` - Exports table data to CSV file
- `exportChartToPNG()` - Uses html2canvas to export chart as PNG
- `exportTableToPNG()` - Uses html2canvas to export table as PNG

**supabaseClient.js**:
- Initializes Supabase client with env vars
- Requires `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env`

## Environment Variables

Frontend (`.env` in `/frontend`):
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Backend Python scripts (`.env` in project root):
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

## Important Implementation Notes

1. **District Filtering Logic**: District filters are automatically disabled/reset when chamber is set to Senate or Both (see useFilters.js:22-24)

2. **District Validation**: DistrictToggle.jsx validates districts against VALID_DISTRICT_COUNTS map to filter out invalid/legacy districts from old redistricting maps (34 invalid districts identified)

3. **Senate Class Encoding**: Senate candidates are differentiated by class based on candidate_id:
   - S0 → Class II (2020/2026 election)
   - S4 → Class I (2024/2030 election)
   - S6 → Class III (2022/2028 election)
   - S8 → Special election

4. **Data Flattening**: The useCandidateData hook flattens the joined candidate/financial data structure for easier consumption by components (see useCandidateData.js:66-78)

5. **Financial Data Filtering**: Candidates without financial_summary records are filtered out before display

6. **Party Colors**: The app uses consistent party colors throughout (defined in formatters.js:63-74)

7. **Export Functionality**: Chart and table exports require refs to be passed from App.jsx to the display components

8. **Supabase Queries**: All queries filter by cycle and use joins to get financial data. The relationship is one-to-many (candidates -> financial_summary)

9. **Name Formatting**: Candidate names are stored as "LAST, FIRST" in the database but displayed as "First Last" in UI components using formatCandidateName()

10. **Batch Data Fetching**: CandidateView fetches all ~2,866 candidates using pagination (`.range(from, to)`) to bypass Supabase's 1,000 row default limit. Fetches in batches of 1,000 until all records are loaded.

11. **Search Algorithm**: CandidateView uses word-based search with `Array.every()` - splits search term into words and checks if ALL words appear in either name format or state. Example: "Mark Kelly" splits to ["mark", "kelly"] and both must appear in "KELLY, MARK E" or "Mark E Kelly".

12. **Party Filtering**: Both DistrictView and CandidateView include party filter buttons (All, Democrats, Republicans, Third Party) to enable primary race analysis within districts or across the entire field.

13. **Ranked Display**: Both DistrictView and CandidateView show candidates in a ranked list sorted by the selected metric (Total Raised, Total Spent, or Cash on Hand), with rank number, party dot, name, location, and value displayed.
