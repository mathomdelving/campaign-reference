# Political Pole 🏁

**A RedBull Racing-inspired campaign finance dashboard for 2026 House and Senate races**

Real-time FEC data visualization with quarterly timeseries analysis.

---

## 🚀 Quick Start

### Monitor Data Collection
```bash
# Watch live progress
tail -f fetch_output.log

# Check current status
grep "last_processed_index" progress.json

# Verify process is running
ps aux | grep fetch_fec_data | grep -v grep
```

### Development Server
```bash
cd frontend
npm run dev
```

---

## 📁 Project Structure

```
fec-dashboard/
├── frontend/              # React + Vite application
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Helper functions
│   └── ...
│
├── docs/                 # Documentation
│   ├── ROADMAP.md                    # Project roadmap and phases
│   ├── DEBUGGING_FINDINGS.md         # Technical analysis of data issues
│   ├── IMPLEMENTATION_PLAN.md        # Quarterly timeseries implementation
│   ├── RATE_LIMIT_ANALYSIS.md        # FEC API rate limiting details
│   └── READY_TO_RUN.md               # Data collection instructions
│
├── sql/                  # Database schemas
│   └── create_quarterly_table.sql    # Quarterly financials table
│
├── tests/                # Test scripts and outputs
│   ├── test_quarterly_fetch.py       # Sample data fetch test
│   └── test_quarterly_output.json    # Test results
│
├── data/                 # (Empty - future data organization)
│
├── scripts/              # (Empty - future utility scripts)
│
├── fetch_fec_data.py     # Main data collection script
├── load_to_supabase.py   # Database loading script
├── candidates_2026.json  # All 5,185 2026 candidates
├── financials_2026.json  # Summary financial data
├── progress.json         # Data collection progress (auto-generated)
├── fetch_output.log      # Collection log (auto-generated)
├── requirements.txt      # Python dependencies
├── package.json          # Node.js frontend dependencies
└── README.md             # This file
```

---

## 🎨 Political Pole Branding

### Colors
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

## 🎯 Use Cases

1. **District Race View** - Compare all candidates within a single district
2. **Candidate Profile** - Deep-dive into individual candidate financials with quarterly timeseries
3. **Cross-District Comparison** - Compare 2+ candidates from different districts
4. **Leaderboard** - Top fundraisers with House/Senate and party filters

---

## 📊 Data Pipeline

### 1. Data Collection (fetch_fec_data.py)
- Fetches candidate data from FEC API
- Collects quarterly financial filings
- Rate limited: 900 requests/hour (safely under FEC's 1,000/hour limit)
- Saves progress every 50 candidates
- **Current collection:** 17-18 hours for 5,185 candidates

### 2. Database Loading (load_to_supabase.py)
- Loads data to Supabase PostgreSQL
- Tables: `candidates`, `financial_summary`, `quarterly_financials`
- Batch inserts for efficiency
- Logs refresh operations

### 3. Frontend Display
- React + Vite + Tailwind CSS
- Real-time data from Supabase
- Interactive charts with Recharts
- Export to CSV/PNG

---

## 🔧 Tech Stack

### Frontend
- React 19.1.1
- Vite 7.1.7
- Tailwind CSS 3.4.18
- Recharts 3.3.0
- Supabase JS Client 2.76.1

### Backend/Data
- Python 3.9+
- Supabase (PostgreSQL)
- FEC OpenFEC API

---

## 📈 Current Status

**Phase 3 Complete ✅**
- ✅ Data collection infrastructure
- ✅ Database schema
- ✅ Basic frontend dashboard

**Phase 4 In Progress 🏗️**
- 🔄 Quarterly timeseries data collection (running now)
- ⏳ Political Pole UI redesign
- ⏳ 4 use-case views implementation

**Phase 5 Pending 📅**
- ⏳ Automation (GitHub Actions)
- ⏳ Deployment (Vercel)

---

## 🛠️ Development

### Python Scripts
```bash
# Install dependencies
pip3 install -r requirements.txt

# Collect FEC data
python3 fetch_fec_data.py

# Load to database
python3 load_to_supabase.py
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

---

## 📝 Environment Variables

### Backend (.env in project root)
```
FEC_API_KEY=your_fec_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_key
```

### Frontend (frontend/.env)
```
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 📚 Documentation

See `docs/` folder for detailed documentation:
- `ROADMAP.md` - Complete project roadmap and history
- `IMPLEMENTATION_PLAN.md` - Quarterly timeseries implementation details
- `RATE_LIMIT_ANALYSIS.md` - FEC API rate limiting breakdown
- `DEBUGGING_FINDINGS.md` - Technical analysis and solutions

---

## 🏁 Political Pole

*Inspired by RedBull Racing - Built for political journalists who need fast, screenshot-worthy campaign finance data.*

**Version:** 0.4.0 (Quarterly Timeseries)
**Last Updated:** October 22, 2025
**Status:** Data Collection in Progress
