# Session Status - Political Pole Development

**Last Updated:** October 22, 2025 - 5:05 PM (Wednesday)
**Current Phase:** Data Collection Running

---

## 🚨 CRITICAL: Data Collection In Progress

### Current Status
- ✅ **Process Running:** PID 36895 (started 1:48 PM Wednesday)
- ✅ **Progress:** 450/5,185 candidates (8.7%)
- ✅ **Progress file:** Saves every 50 candidates at `progress.json`
- ✅ **Caffeinate running:** Computer won't sleep
- ✅ **Expected completion:** Friday morning ~2-3 AM

### How to Monitor
```bash
# Check if still running
ps aux | grep fetch_fec_data | grep -v grep

# Watch live progress
tail -f fetch_output.log

# Check how many candidates processed
grep "last_processed_index" progress.json

# See current candidate
tail -3 fetch_output.log
```

### If Process Stopped
```bash
# Restart - it will automatically resume from progress.json
cd /Users/benjaminnelson/Desktop/fec-dashboard
nohup python3 -u fetch_fec_data.py > fetch_output.log 2>&1 &

# Keep computer awake
caffeinate &
```

---

## 📊 What's Being Collected

### Files Being Generated
1. **financials_2026.json** - Summary totals (updating)
2. **quarterly_financials_2026.json** - NEW! Quarterly timeseries data (being created)
3. **progress.json** - Auto-saved every 50 candidates

### Data Structure
- **Summary data:** Cumulative totals per candidate
- **Quarterly data:** Individual Q1, Q2, Q3 filings with:
  - Total receipts (raised this quarter)
  - Total disbursements (spent this quarter)
  - Cash beginning (start of quarter)
  - Cash ending (end of quarter)
  - Committee ID, filing ID, dates

---

## ✅ Completed Today

1. **Rate Limiting Fixed** - 4 seconds between ALL API calls
2. **Quarterly Data Collection** - Updated fetch_fec_data.py to get Q1, Q2, Q3 data
3. **Database Schema Created** - quarterly_financials table in Supabase
4. **Tested Successfully** - Validated on Vindman, Wahls, Miller-Meeks
5. **Project Organized** - Clean folder structure (docs/, sql/, tests/, etc.)
6. **Documentation Complete** - All implementation plans documented

---

## 📋 Next Steps (When Collection Finishes)

### Immediate (Friday Morning)

**1. Load Quarterly Data to Supabase (~5 minutes)**
```bash
# Update load_to_supabase.py to handle quarterly data
# Then run:
python3 load_to_supabase.py
```

**What to add to load_to_supabase.py:**
- Function to parse quarter from coverage_end_date (Jan-Mar=Q1, Apr-Jun=Q2, etc.)
- Function to load quarterly_financials_2026.json to quarterly_financials table
- Batch insert with 1000 records per batch
- Handle duplicates via unique constraint on (candidate_id, cycle, coverage_end_date, filing_id)

### Short Term (Friday - This Weekend)

**2. Update Tailwind Config with Political Pole Colors**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'pole-navy': '#121F45',
        'pole-blue': '#223971',
        'pole-red': '#CC1E4A',
        'pole-yellow': '#FFC906',
        'party-dem': '#2563EB',
        'party-rep': '#DC2626',
        'party-ind': '#7C3AED',
      }
    }
  }
}
```

**3. Install React Router**
```bash
cd frontend
npm install react-router-dom
```

**4. Build 4 Use-Case Views**
- District Race Comparison (Use-Case 1)
- Candidate Profile with Timeseries (Use-Case 2)
- Multi-Candidate Comparison (Use-Case 3)
- Leaderboard with Filters (Use-Case 4)

---

## 🎨 Political Pole Branding

### Colors
- **Navy Blue:** #121F45 - Primary backgrounds, headers
- **Blue:** #223971 - Secondary backgrounds, borders
- **Red:** #CC1E4A - Accents, CTAs, important metrics
- **Yellow:** #FFC906 - Highlights, warnings, standout data

### Party Colors (Keep Standard)
- Democrats: #2563EB
- Republicans: #DC2626
- Independents: #7C3AED

### Name
"Political Pole" - Racing/F1 inspired theme for political journalists

---

## 🏗️ UI Architecture Plan

### New Component Structure
```
frontend/src/
├── views/
│   ├── DistrictView.jsx        # Use-Case 1: District comparison
│   ├── CandidateView.jsx        # Use-Case 2: Individual profile
│   ├── ComparisonView.jsx       # Use-Case 3: Cross-district comparison
│   └── LeaderboardView.jsx      # Use-Case 4: Rankings
├── components/
│   ├── district/
│   ├── candidate/
│   ├── comparison/
│   ├── leaderboard/
│   └── shared/
│       └── QuarterlyChart.jsx   # Reusable timeseries chart
└── hooks/
    ├── useQuarterlyData.js      # NEW - fetch quarterly data
    ├── useCandidateSearch.js    # NEW - search functionality
    └── useLeaderboard.js         # NEW - leaderboard data
```

### Routing Structure
```javascript
<Routes>
  <Route path="/" element={<LeaderboardView />} />
  <Route path="/leaderboard" element={<LeaderboardView />} />
  <Route path="/district" element={<DistrictView />} />
  <Route path="/candidate/:id?" element={<CandidateView />} />
  <Route path="/compare" element={<ComparisonView />} />
</Routes>
```

---

## 📁 Current Project Structure

```
fec-dashboard/
├── docs/                         # Documentation
│   ├── ROADMAP.md                # Full project history
│   ├── IMPLEMENTATION_PLAN.md    # Quarterly timeseries plan
│   ├── RATE_LIMIT_ANALYSIS.md    # API rate limiting details
│   ├── DEBUGGING_FINDINGS.md     # Technical analysis
│   ├── READY_TO_RUN.md           # Data collection instructions
│   └── SESSION_STATUS.md         # THIS FILE
├── sql/
│   └── create_quarterly_table.sql
├── tests/
│   ├── test_quarterly_fetch.py
│   └── test_quarterly_output.json
├── frontend/                     # React app
├── fetch_fec_data.py             # Data collection (RUNNING)
├── load_to_supabase.py           # Database loader (NEEDS UPDATE)
├── progress.json                 # Auto-generated progress
├── fetch_output.log              # Collection log
└── README.md
```

---

## 🔑 Key Files to Reference

### Implementation Details
- `docs/IMPLEMENTATION_PLAN.md` - Complete quarterly timeseries implementation guide
- `docs/RATE_LIMIT_ANALYSIS.md` - FEC API rate limiting (4s between calls)

### Code to Update
- `load_to_supabase.py` - Add quarterly data loading function
- `frontend/src/hooks/useCandidateData.js` - Add quarterly data fetching
- `frontend/tailwind.config.js` - Add Political Pole colors

### Database
- Supabase already has `quarterly_financials` table created
- Just need to load data when collection finishes

---

## 🐛 Known Issues & Solutions

### Issue: Computer Goes to Sleep
**Solution:** Run `caffeinate` to keep awake
```bash
caffeinate &
```

### Issue: Process Stops
**Solution:** Restart - automatic resume from progress.json
```bash
nohup python3 -u fetch_fec_data.py > fetch_output.log 2>&1 &
```

### Issue: Want to Check Progress
**Solution:**
```bash
tail -f fetch_output.log  # Live view
grep "last_processed_index" progress.json  # Last saved progress
```

---

## 💾 Data Collection Statistics

### Rate Limiting (CRITICAL - Don't Change!)
- **4 seconds between EACH API call**
- 3 API calls per candidate (totals + committees + filings)
- ~12 seconds minimum per candidate
- 900 requests/hour (safely under FEC's 1,000/hour limit)

### Expected Results
- **Summary records:** ~3,000 candidates with financial data
- **Quarterly records:** ~6,000-10,000 filings (multiple quarters per candidate)
- **File sizes:**
  - financials_2026.json: ~1.3 MB (existing, updating)
  - quarterly_financials_2026.json: ~3-5 MB (new, being created)

---

## 🎯 Use Cases (Requirements from User)

### 1. District State-of-Race View
Compare all candidates within a single district
- Select state + district → see all candidates
- Side-by-side comparison chart
- Quarterly trend lines for each candidate

### 2. Individual Candidate Deep-Dive
Search for specific candidate, see complete history
- Search bar with autocomplete
- Candidate profile card
- Latest quarter metrics prominent
- Quarterly timeseries chart (raised, spent, cash on hand)

### 3. Cross-District Comparison
Compare 2+ candidates from different districts
- Multi-select candidate picker
- Side-by-side quarterly trends
- Comparison table

### 4. Leaderboard Rankings
Top fundraisers across all races
- Three leaderboards: Total Raised, Total Spent, Cash on Hand
- Filters: House/Senate, Party (All/Dem/Rep)
- Time period: Latest Quarter / Cumulative
- Top 10/25/50/100

---

## 🚀 When You Return

### First Priority: Check Data Collection
```bash
ps aux | grep fetch_fec_data | grep -v grep
tail fetch_output.log
grep "last_processed_index" progress.json
```

### If Collection Complete (quarterly_financials_2026.json exists):
1. Read `docs/IMPLEMENTATION_PLAN.md` section "Phase 3: Update load_to_supabase.py"
2. Update load_to_supabase.py with quarterly loading function
3. Run `python3 load_to_supabase.py`
4. Start building Political Pole UI

### If Collection Still Running:
- Let it continue
- Can start building UI components with mock data
- Can update tailwind.config.js with Political Pole colors
- Can set up react-router-dom routing

---

## 📞 Quick Reference Commands

```bash
# Navigate to project
cd /Users/benjaminnelson/Desktop/fec-dashboard

# Check collection status
ps aux | grep fetch_fec_data | grep -v grep
tail -f fetch_output.log

# Start/restart collection
nohup python3 -u fetch_fec_data.py > fetch_output.log 2>&1 &

# Keep computer awake
caffeinate &

# When ready to load data
python3 load_to_supabase.py

# Start frontend dev server
cd frontend && npm run dev
```

---

## ✅ What's Working Perfectly

1. ✅ Rate limiting properly configured (4s between all calls)
2. ✅ Auto-resume from progress.json working
3. ✅ Quarterly data collection tested and validated
4. ✅ Database schema created in Supabase
5. ✅ Project well-organized and documented
6. ✅ Progress saves every 50 candidates
7. ✅ Both summary AND quarterly data being collected

---

## 🎨 Design Philosophy

**Political Pole = RedBull Racing for Political Journalism**
- Fast, slick, tech-forward
- Screenshot-worthy visualizations
- Racing/F1 aesthetic (pole position = #1 fundraiser)
- Built for speed and clarity
- Target users: Political journalists like Jake Sherman, Lakshya Jain

---

**Last Status Check:** 5:05 PM Wednesday, Oct 22, 2025
**Process:** Running smoothly with caffeinate
**Next Check:** When collection completes or Friday morning

Good luck! Everything is set up for success. 🏁
