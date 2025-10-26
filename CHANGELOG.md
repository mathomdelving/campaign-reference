# Changelog

All notable changes to the FEC Campaign Finance Dashboard project will be documented in this file.

## [2025-01-24 PM] - UI Redesign & Search Improvements

### Added

#### "By Candidate" View (Complete Redesign)
- **New unified view** combining Candidate Profile and Compare functionality
- **Search bar** with intelligent word-based matching
  - Searches across both "LAST, FIRST" and "First Last" formats
  - Multi-word search (e.g., "Mark Kelly" finds "KELLY, MARK E")
  - Searches candidate names and states simultaneously
- **Batch data fetching** to load all 2,866 candidates (previously limited to 1,000)
- **Party filter buttons** (All, Democrats, Republicans, Third Party)
- **Ranked candidate display** with metrics
  - Shows rank number, party dot, formatted name, location, and metric value
  - Dynamic sorting by selected metric
- **Remove buttons** (X) to deselect candidates
- **Quarterly trend chart** using same component as District view
- **Formatted name display** - Shows "Mark Kelly" instead of "KELLY, MARK E"

#### District View Enhancements
- **Party filter buttons** added to District view
- **Ranked candidate list** with metric values
  - Displays as: "#1. 🔵 Candidate Name ($5.2M)"
  - Auto-sorts by selected metric (Total Raised, Total Spent, Cash on Hand)
- **Simplified chart** - Removed complex click/hover interactions
  - Added dual Y-axis labels (left and right) for better readability
  - Removed legend (data now in list above)
  - Reduced chart height to 350px (supplementary role)

### Changed

#### Navigation Restructure
- **Removed** "Candidate Profile" and "Compare" as separate views
- **Three main dashboards**: "Leaderboard", "By District", "By Candidate"
- Updated navigation labels for clarity

#### Chart Simplification (QuarterlyChart.jsx)
- Removed all click/hover tooltip complexity
- Removed legend display
- Added dual Y-axis with currency formatting on both sides
- Increased line thickness to 2.5px for better visibility
- Reduced chart height from 400px to 350px

#### Name Display
- All candidate names now display in "First Last" format throughout app
- Applied `formatCandidateName()` in CandidateView search results and selected list
- Maintains title case formatting for readability

### Fixed
- **Search now works with both name formats**: "Mark Kelly" and "Kelly, Mark" both find results
- **All 2,866 candidates** now searchable (fixed Supabase 1,000 row limit)
- Ruben Gallego, Mark Kelly, and all other candidates now appear in search
- Multi-word searches work correctly (e.g., "Donald Trump" finds "TRUMP, DONALD J")

### Technical Details

#### Files Modified
- `/frontend/src/views/CandidateView.jsx` - Complete rewrite with search and batch fetching
- `/frontend/src/views/DistrictView.jsx` - Added party filters and ranked display
- `/frontend/src/components/QuarterlyChart.jsx` - Simplified, removed interactions
- `/frontend/src/components/layout/Navigation.jsx` - Updated to 3-tab structure
- `/frontend/src/App.jsx` - Removed ComparisonView route

#### Files Removed
- `/frontend/src/views/ComparisonView.jsx` - Functionality merged into CandidateView

#### Search Algorithm
- Word-based matching using `Array.every()` and `String.includes()`
- Splits search term into words and checks if all words appear in name or state
- Case-insensitive matching
- Handles middle initials and name variations

#### Data Fetching Optimization
- Implemented pagination with `.range(from, to)` for Supabase queries
- Fetches in 1,000 record batches until all candidates loaded
- Logs total candidate count to console

### Performance
- Initial load fetches ~2,866 candidates in 3 batches (~1-2 seconds)
- Search is instant (client-side filtering)
- No additional API calls during search

---

## [2025-01-24 AM] - Senate Support & District Validation

### Added

#### Senate Support in District Race View
- Added Senate chamber support to District Race view
- Implemented Senate seat differentiation by Class (I, II, III, Special)
- Added Chamber selector dropdown (House/Senate) to DistrictView.jsx
- Senate class extraction from candidate_id encoding:
  - S0 → Class II (2020/2026 election)
  - S4 → Class I (2024/2030 election)
  - S6 → Class III (2022/2028 election)
  - S8 → Special election

#### Name Formatting
- Added `formatCandidateName()` utility function in formatters.js
- Converts names from "LAST, FIRST" format to "First Last" format
- Removes common titles (MR., DR., SEN., etc.)
- Converts to title case for better readability
- Applied to QuarterlyChart tooltip and legend labels

#### District Validation
- Added district validation to prevent invalid districts from appearing
- Implemented `VALID_DISTRICT_COUNTS` map in DistrictToggle.jsx
- Filters out 34 invalid district entries (e.g., GA-23, AZ-20)
- Based on 2022 congressional redistricting maps

### Changed

#### UI Improvements
- Reordered District Race view selectors: State → Chamber → District (left to right)
- Changed district label to always display "District" (instead of switching to "Senate Seat")
- Updated Leaderboard to show "SEN" instead of dash for Senate candidates in district column
- Removed duplicate "State" label in DistrictView selector area

#### Component Updates
- **DistrictToggle.jsx**:
  - Now supports both House districts and Senate seat classes
  - Validates districts against state maximum
  - Sorts districts numerically

- **DistrictView.jsx**:
  - Added chamber state management
  - Updated candidate fetching to handle Senate filtering by class
  - Modified display text to show appropriate labels for House/Senate

- **QuarterlyChart.jsx**:
  - Updated tooltip formatter to show readable candidate names
  - Updated legend formatter for consistency

- **RaceTable.jsx**:
  - Line 124: Changed Senate district display from "—" to "SEN"

### Fixed
- Cash on hand data now properly displays for all Senate candidates (previously missing for 103 candidates)
- Removed invalid/non-existent districts from district selector dropdowns
- Fixed duplicate labels in District Race view selector area

### Data Updates
- Ran fix_missing_cash.py to update 106 candidates with missing cash_on_hand values
- Successfully reloaded 2,832 financial records to Supabase
- All candidates now have accurate cash_on_hand data where available from FEC

### Technical Details

#### Files Modified
- `/frontend/src/components/DistrictToggle.jsx`
- `/frontend/src/components/RaceTable.jsx`
- `/frontend/src/components/QuarterlyChart.jsx`
- `/frontend/src/views/DistrictView.jsx`
- `/frontend/src/utils/formatters.js`

#### Scripts Used
- `fix_missing_cash.py` - Fixed 106 candidates with missing cash_on_hand
- `load_to_supabase.py` - Reloaded all financial data to Supabase

### Known Issues
- 34 candidates with invalid districts remain in the database but are filtered from UI
- These are legacy candidates from old redistricting maps or incorrect FEC data

### District Count Reference
Valid congressional districts by state (2022 redistricting):
- AL: 7, AK: 1, AZ: 9, AR: 4, CA: 52, CO: 8, CT: 5, DE: 1
- FL: 28, GA: 14, HI: 2, ID: 2, IL: 17, IN: 9, IA: 4, KS: 4
- KY: 6, LA: 6, ME: 2, MD: 8, MA: 9, MI: 13, MN: 8, MS: 4
- MO: 8, MT: 2, NE: 3, NV: 4, NH: 2, NJ: 12, NM: 3, NY: 26
- NC: 14, ND: 1, OH: 15, OK: 5, OR: 6, PA: 17, RI: 2, SC: 7
- SD: 1, TN: 9, TX: 38, UT: 4, VT: 1, VA: 11, WA: 10, WV: 2
- WI: 8, WY: 1, DC: 0
