# FEC Dashboard Implementation Plan - Quarterly Timeseries & UI Redesign

**Date:** October 22, 2025
**Status:** Ready to Implement
**Estimated Timeline:** 12-15 hours (including 6-8 hour overnight data collection)

---

## Investigation Results

### Missing Candidates ✅ RESOLVED
**Finding:** The candidates you mentioned (Wahls, Miller-Meeks) ARE in our database!
- Zach Wahls (S6IA00272): ✅ $1,303,295.44 raised
- Mariannette Miller-Meeks (H8IA02043): ✅ $3,135,424.26 raised

**Issue:** Likely a frontend filtering or display issue, NOT a data collection issue.

### Root Cause of Data Problems ✅ IDENTIFIED
1. **No timeseries data** - Currently only have cumulative totals, not quarterly breakdowns
2. **Using wrong FEC endpoint** - Need to switch from `/totals/` to `/filings/`
3. **UI doesn't support your use-cases** - Need major UI redesign for 4 distinct workflows

---

## User Requirements

### Use-Case 1: District State-of-Race View
**Goal:** Compare all candidates within a single district
**Features Needed:**
- Select state + district → see all candidates in that race
- Side-by-side comparison chart (bar chart or grouped bars)
- Table showing head-to-head metrics
- Visual indicators for party affiliation
- Quarterly trend lines for each candidate in the race

**Example:** IA-01: Miller-Meeks (R) vs. [Democrat challenger] vs. [other candidates]

### Use-Case 2: Individual Candidate Deep-Dive
**Goal:** Search for a specific candidate and see their complete history
**Features Needed:**
- Search bar with autocomplete
- Candidate profile card (name, party, state, district, photo?, incumbent status)
- Latest quarter metrics prominently displayed
- Quarterly timeseries chart showing:
  - Total raised per quarter (line or bar)
  - Total disbursed per quarter
  - Cash on hand at end of each quarter
- Table of quarterly breakdown
- Export functionality (CSV, PNG)

**Example:** Search "Vindman" → Eugene Vindman profile → Q1: $2.1M, Q2: $1.6M, Q3: $1.7M

### Use-Case 3: Cross-District Candidate Comparison
**Goal:** Compare 2+ candidates from different districts
**Features Needed:**
- Multi-select candidate picker (checkboxes or dropdown)
- Selected candidates displayed in comparison table
- Side-by-side quarterly trends chart
- Ability to add/remove candidates dynamically
- Clear visual distinction between candidates (colors, labels)

**Example:** Compare Vindman (VA-07) vs. Miller-Meeks (IA-01) vs. Wahls (IA Senate)

### Use-Case 4: Leaderboard Rankings
**Goal:** See top fundraisers across all races
**Features Needed:**
- Three leaderboard tables:
  1. Top Total Raised
  2. Top Total Disbursed
  3. Top Cash on Hand
- Filters:
  - Chamber: House / Senate / Both
  - Party: All / Democrats / Republicans
  - Time period: Latest Quarter / Cumulative
- Top 10, 25, 50, or 100 (user selectable)
- Export functionality

**Example:** Top 25 House Democrats by Cash on Hand

---

## Implementation Strategy

### Phase 1: Database Schema (30 minutes)
Create new `quarterly_financials` table alongside existing `financial_summary`.

**Why keep both tables?**
- `financial_summary` - Fast queries for cumulative totals (leaderboard, initial loads)
- `quarterly_financials` - Detailed timeseries data (charts, trends)
- Separation of concerns - don't break existing functionality

**Schema:**
```sql
CREATE TABLE quarterly_financials (
  id SERIAL PRIMARY KEY,
  candidate_id VARCHAR(9) REFERENCES candidates(candidate_id),
  committee_id VARCHAR(9),
  cycle INTEGER NOT NULL,

  -- Quarter identification
  quarter VARCHAR(10),                     -- 'Q1', 'Q2', 'Q3', 'Q4'
  report_year INTEGER,
  report_type VARCHAR(100),                -- 'APRIL QUARTERLY', 'JULY QUARTERLY', etc.

  -- Period coverage
  coverage_start_date DATE,
  coverage_end_date DATE,

  -- Financial data for THIS QUARTER ONLY (not cumulative)
  total_receipts DECIMAL(15,2),           -- Raised this quarter
  total_disbursements DECIMAL(15,2),      -- Spent this quarter
  cash_beginning DECIMAL(15,2),           -- Cash at start of quarter
  cash_ending DECIMAL(15,2),              -- Cash at end of quarter

  -- FEC metadata
  filing_id BIGINT,                       -- FEC file_number
  is_amendment BOOLEAN DEFAULT false,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(candidate_id, cycle, coverage_end_date, filing_id)
);

-- Indexes for performance
CREATE INDEX idx_qf_candidate ON quarterly_financials(candidate_id);
CREATE INDEX idx_qf_cycle ON quarterly_financials(cycle);
CREATE INDEX idx_qf_quarter ON quarterly_financials(quarter, report_year);
CREATE INDEX idx_qf_committee ON quarterly_financials(committee_id);
CREATE INDEX idx_qf_timeseries ON quarterly_financials(candidate_id, cycle, coverage_end_date);
```

### Phase 2: Update Data Collection Scripts (2-3 hours coding + 6-8 hours overnight run)

#### A. Modify `fetch_fec_data.py`

**New function to add:**
```python
def fetch_committee_quarterly_filings(candidate_id, cycle=CYCLE):
    """
    Fetch quarterly filings for a candidate's committee(s)
    Returns list of quarterly reports with financial data
    """
    # Step 1: Get committee(s) for this candidate
    committees_url = f"{BASE_URL}/candidate/{candidate_id}/committees/"
    committees_response = requests.get(committees_url, params={
        'api_key': FEC_API_KEY,
        'cycle': cycle
    })

    if not committees_response.ok:
        return []

    committees = committees_response.json().get('results', [])

    all_filings = []

    # Step 2: For each committee, get filings
    for committee in committees:
        committee_id = committee.get('committee_id')

        filings_url = f"{BASE_URL}/committee/{committee_id}/filings/"
        filings_response = requests.get(filings_url, params={
            'api_key': FEC_API_KEY,
            'cycle': cycle,
            'form_type': 'F3',  # House/Senate candidate reports
            'sort': '-coverage_end_date',
            'per_page': 20  # Get up to 20 filings (covers multiple quarters + amendments)
        })

        if filings_response.ok:
            filings = filings_response.json().get('results', [])

            # Filter for quarterly reports only (exclude monthly, termination, etc.)
            quarterly_types = ['Q1', 'Q2', 'Q3', 'Q4', 'APRIL QUARTERLY', 'JULY QUARTERLY',
                               'OCTOBER QUARTERLY', 'YEAR-END']

            for filing in filings:
                report_type = filing.get('report_type_full', '')

                # Only keep quarterly reports
                if any(qt in report_type.upper() for qt in quarterly_types):
                    all_filings.append({
                        'committee_id': committee_id,
                        'filing_id': filing.get('file_number'),
                        'report_type': report_type,
                        'coverage_start_date': filing.get('coverage_start_date'),
                        'coverage_end_date': filing.get('coverage_end_date'),
                        'total_receipts': filing.get('total_receipts'),
                        'total_disbursements': filing.get('total_disbursements'),
                        'cash_beginning': filing.get('cash_on_hand_beginning_period'),
                        'cash_ending': filing.get('cash_on_hand_end_period'),
                        'is_amendment': filing.get('is_amended', False)
                    })

    return all_filings
```

**Update main() function:**
```python
# After fetching candidates, fetch quarterly data
quarterly_financials = []

for idx, candidate in enumerate(all_candidates):
    candidate_id = candidate.get('candidate_id')
    name = candidate.get('name')

    print(f"[{idx+1}/{total}] {name} ({candidate_id})...", end=" ")

    filings = fetch_committee_quarterly_filings(candidate_id)

    if filings:
        for filing in filings:
            combined = {
                'candidate_id': candidate_id,
                'name': name,
                'party': candidate.get('party_full'),
                'state': candidate.get('state'),
                'district': candidate.get('district'),
                'office': candidate.get('office_full'),
                'committee_id': filing['committee_id'],
                'filing_id': filing['filing_id'],
                'report_type': filing['report_type'],
                'coverage_start_date': filing['coverage_start_date'],
                'coverage_end_date': filing['coverage_end_date'],
                'total_receipts': filing['total_receipts'],
                'total_disbursements': filing['total_disbursements'],
                'cash_beginning': filing['cash_beginning'],
                'cash_ending': filing['cash_ending'],
                'is_amendment': filing['is_amendment'],
                'cycle': CYCLE
            }
            quarterly_financials.append(combined)
        print(f"✓ {len(filings)} filings")
    else:
        print("(no quarterly data)")

    # Save progress every 50 candidates
    if (idx + 1) % 50 == 0:
        save_progress(idx + 1, quarterly_financials)

    time.sleep(4)  # Rate limiting

# Save quarterly financials
with open(f'quarterly_financials_{CYCLE}.json', 'w') as f:
    json.dump(quarterly_financials, f, indent=2)
```

#### B. Modify `load_to_supabase.py`

**Add function to parse quarter:**
```python
def parse_quarter(coverage_end_date):
    """Determine quarter (Q1, Q2, Q3, Q4) from coverage end date"""
    if not coverage_end_date:
        return None

    date = datetime.fromisoformat(coverage_end_date.replace('T00:00:00', ''))
    month = date.month

    if month <= 3:
        return 'Q1'
    elif month <= 6:
        return 'Q2'
    elif month <= 9:
        return 'Q3'
    else:
        return 'Q4'

def load_quarterly_financials(file_path):
    """Load quarterly financials to Supabase"""
    print(f"\nLoading quarterly financials from {file_path}...")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Transform data
    records = []
    for item in data:
        quarter = parse_quarter(item.get('coverage_end_date'))
        year = datetime.fromisoformat(
            item.get('coverage_end_date', '').replace('T00:00:00', '')
        ).year if item.get('coverage_end_date') else None

        record = {
            'candidate_id': item.get('candidate_id'),
            'committee_id': item.get('committee_id'),
            'cycle': item.get('cycle'),
            'quarter': quarter,
            'report_year': year,
            'report_type': item.get('report_type'),
            'coverage_start_date': item.get('coverage_start_date'),
            'coverage_end_date': item.get('coverage_end_date'),
            'total_receipts': item.get('total_receipts'),
            'total_disbursements': item.get('total_disbursements'),
            'cash_beginning': item.get('cash_beginning'),
            'cash_ending': item.get('cash_ending'),
            'filing_id': item.get('filing_id'),
            'is_amendment': item.get('is_amendment', False)
        }
        records.append(record)

    # Batch insert
    batch_size = 1000
    total_inserted = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            result = supabase.table('quarterly_financials').upsert(
                batch,
                on_conflict='candidate_id,cycle,coverage_end_date,filing_id'
            ).execute()
            total_inserted += len(batch)
            print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} records")
        except Exception as e:
            print(f"  Error inserting batch: {e}")

    print(f"✓ Loaded {total_inserted} quarterly financial records")
    return total_inserted
```

### Phase 3: Frontend Architecture Redesign (4-5 hours)

#### New Component Structure

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Navigation.jsx              # Top nav with view switcher
│   │   └── SearchBar.jsx               # Global candidate search
│   ├── district/
│   │   ├── DistrictRaceView.jsx        # Use-Case 1
│   │   ├── DistrictSelector.jsx
│   │   └── DistrictComparisonChart.jsx
│   ├── candidate/
│   │   ├── CandidateProfile.jsx        # Use-Case 2
│   │   ├── CandidateSearch.jsx
│   │   ├── CandidateTimeseriesChart.jsx
│   │   └── CandidateQuarterlyTable.jsx
│   ├── comparison/
│   │   ├── MultiCandidateComparison.jsx # Use-Case 3
│   │   ├── CandidatePicker.jsx
│   │   └── ComparisonChart.jsx
│   ├── leaderboard/
│   │   ├── LeaderboardView.jsx         # Use-Case 4
│   │   ├── LeaderboardTable.jsx
│   │   └── LeaderboardFilters.jsx
│   └── shared/
│       ├── QuarterlyChart.jsx          # Reusable timeseries chart
│       ├── CandidateCard.jsx
│       └── MetricDisplay.jsx
├── hooks/
│   ├── useCandidateData.js             # Updated for quarterly data
│   ├── useCandidateSearch.js           # New
│   ├── useQuarterlyData.js             # New
│   └── useLeaderboard.js               # New
└── views/
    ├── DistrictView.jsx                # Route: /district
    ├── CandidateView.jsx               # Route: /candidate/:id
    ├── ComparisonView.jsx              # Route: /compare
    └── LeaderboardView.jsx             # Route: /leaderboard
```

#### Updated App.jsx with Routing

```javascript
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import DistrictView from './views/DistrictView';
import CandidateView from './views/CandidateView';
import ComparisonView from './views/ComparisonView';
import LeaderboardView from './views/LeaderboardView';
import Navigation from './components/layout/Navigation';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<LeaderboardView />} />
            <Route path="/leaderboard" element={<LeaderboardView />} />
            <Route path="/district" element={<DistrictView />} />
            <Route path="/candidate/:id?" element={<CandidateView />} />
            <Route path="/compare" element={<ComparisonView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

#### New Hook: useQuarterlyData.js

```javascript
import { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';

export function useQuarterlyData(candidateId, cycle = 2026) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchQuarterlyData() {
      try {
        setLoading(true);
        setError(null);

        const { data: results, error: queryError } = await supabase
          .from('quarterly_financials')
          .select('*')
          .eq('candidate_id', candidateId)
          .eq('cycle', cycle)
          .order('coverage_end_date', { ascending: true });

        if (queryError) throw queryError;

        // Process and format data
        const processedData = results.map(q => ({
          quarter: q.quarter,
          year: q.report_year,
          period: `${q.coverage_start_date} to ${q.coverage_end_date}`,
          receipts: q.total_receipts || 0,
          disbursements: q.total_disbursements || 0,
          cashBeginning: q.cash_beginning || 0,
          cashEnding: q.cash_ending || 0,
          reportType: q.report_type
        }));

        setData(processedData);
      } catch (err) {
        console.error('Error fetching quarterly data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (candidateId) {
      fetchQuarterlyData();
    }
  }, [candidateId, cycle]);

  return { data, loading, error };
}
```

#### New Component: QuarterlyChart.jsx

```javascript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCurrency } from '../utils/formatters';

export function QuarterlyChart({ data, metrics = ['receipts', 'disbursements', 'cashEnding'] }) {
  // Transform data for Recharts
  const chartData = data.map(q => ({
    name: `${q.quarter} ${q.year}`,
    receipts: q.receipts,
    disbursements: q.disbursements,
    cashOnHand: q.cashEnding
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis tickFormatter={(value) => formatCurrency(value, true)} />
        <Tooltip formatter={(value) => formatCurrency(value)} />
        <Legend />

        {metrics.includes('receipts') && (
          <Line type="monotone" dataKey="receipts" stroke="#10b981" name="Total Raised" strokeWidth={2} />
        )}
        {metrics.includes('disbursements') && (
          <Line type="monotone" dataKey="disbursements" stroke="#ef4444" name="Total Spent" strokeWidth={2} />
        )}
        {metrics.includes('cashOnHand') && (
          <Line type="monotone" dataKey="cashOnHand" stroke="#3b82f6" name="Cash on Hand" strokeWidth={2} />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Phase 4: Implement Each Use-Case (3-4 hours total)

#### Use-Case 1: District Race View
```javascript
// frontend/src/views/DistrictView.jsx
export default function DistrictView() {
  const [state, setState] = useState('');
  const [district, setDistrict] = useState('');
  const { data: candidates, loading } = useCandidateData({
    cycle: 2026,
    chamber: 'H',
    state,
    district
  });

  return (
    <div>
      <h1>District Race Comparison</h1>
      <DistrictSelector
        state={state}
        district={district}
        onStateChange={setState}
        onDistrictChange={setDistrict}
      />
      {candidates.length > 0 && (
        <>
          <DistrictComparisonChart candidates={candidates} />
          <CandidatesTable candidates={candidates} />
        </>
      )}
    </div>
  );
}
```

#### Use-Case 2: Candidate Profile
```javascript
// frontend/src/views/CandidateView.jsx
import { useParams } from 'react-router-dom';

export default function CandidateView() {
  const { id } = useParams();
  const [candidateId, setCandidateId] = useState(id);
  const { data: candidate } = useCandidateData({ candidates: [candidateId] });
  const { data: quarterly } = useQuarterlyData(candidateId);

  return (
    <div>
      {!candidateId ? (
        <CandidateSearch onSelect={setCandidateId} />
      ) : (
        <>
          <CandidateProfile candidate={candidate[0]} />
          <QuarterlyChart data={quarterly} />
          <CandidateQuarterlyTable data={quarterly} />
        </>
      )}
    </div>
  );
}
```

#### Use-Case 3: Multi-Candidate Comparison
```javascript
// frontend/src/views/ComparisonView.jsx
export default function ComparisonView() {
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const { data: candidates } = useCandidateData({ candidates: selectedCandidates });

  // Fetch quarterly data for each candidate
  const quarterlyData = selectedCandidates.map(id =>
    useQuarterlyData(id)
  );

  return (
    <div>
      <h1>Compare Candidates</h1>
      <CandidatePicker
        selected={selectedCandidates}
        onChange={setSelectedCandidates}
      />
      {candidates.length > 1 && (
        <>
          <ComparisonChart candidates={candidates} quarterlyData={quarterlyData} />
          <ComparisonTable candidates={candidates} />
        </>
      )}
    </div>
  );
}
```

#### Use-Case 4: Leaderboard
```javascript
// frontend/src/views/LeaderboardView.jsx
export default function LeaderboardView() {
  const [chamber, setChamber] = useState('both');
  const [party, setParty] = useState('all');
  const [metric, setMetric] = useState('totalRaised');
  const [limit, setLimit] = useState(25);

  const { data: leaders, loading } = useLeaderboard({
    chamber,
    party,
    metric,
    limit
  });

  return (
    <div>
      <h1>Campaign Finance Leaderboard</h1>
      <LeaderboardFilters
        chamber={chamber}
        party={party}
        metric={metric}
        limit={limit}
        onChamberChange={setChamber}
        onPartyChange={setParty}
        onMetricChange={setMetric}
        onLimitChange={setLimit}
      />
      <LeaderboardTable data={leaders} metric={metric} />
    </div>
  );
}
```

---

## Execution Order & Timeline

### Tonight (Before Sleep)
**Option A: Start data collection now** (~30 min setup, 6-8 hours overnight)
1. Update `fetch_fec_data.py` with quarterly fetching logic
2. Test on 10 candidates to validate
3. Start full collection overnight (all 5,185 candidates)

**Option B: Do database and UI work first** (2-3 hours)
1. Create `quarterly_financials` table in Supabase
2. Start building new UI components and routing
3. Start data collection later tonight before bed

**My Recommendation: Option A**
- Get the long-running task started ASAP
- We can work on UI tomorrow while data is still collecting (if needed)
- Test script on small sample first to catch errors early

### Tomorrow (After Data Collection)
1. Load quarterly data to Supabase (30 minutes)
2. Update `useCandidateData` and create new hooks (1 hour)
3. Build UI components for 4 use-cases (3-4 hours)
4. Test complete pipeline (1 hour)

---

## Answer to Your Question #4

**Should we collect data overnight or is there not much else to do?**

**My answer:** We should START the data collection tonight (Option A above) because:

1. **The 6-8 hour collection time is a blocker** - We can't test the quarterly features without the data
2. **We CAN work in parallel** - While data collects, we can:
   - Create the database schema (10 minutes)
   - Build UI components using mock data
   - Set up routing and navigation
   - Create the new hooks
3. **If we wait, we lose a day** - If we do UI first and start collection tomorrow night, we can't fully test until the day after
4. **Low risk** - We'll test the fetch script on 10 candidates first, so we know it works before letting it run all night

**Suggested tonight's workflow:**
1. (~30 min) Update `fetch_fec_data.py` with quarterly fetching
2. (~5 min) Test on 5-10 candidates, verify JSON output looks correct
3. (~2 min) Start full collection with progress saving
4. (~30 min) Create `quarterly_financials` table in Supabase
5. (Optional, ~1 hour) Start building UI components with mock data
6. → Go to sleep, let it run overnight
7. Tomorrow morning: Load data to Supabase, continue UI work

---

## Next Steps - Your Approval Needed

1. ✅ **Approve overall approach** - Quarterly table + 4 use-case UI redesign?
2. ✅ **Confirm execution order** - Start data collection tonight (Option A)?
3. ✅ **Any UI preferences** - Do you have design preferences, existing UI libraries you like, color schemes?
4. 🤔 **Additional requirements** - Any other features for the 4 use-cases I didn't capture?

Once you approve, I'll:
1. Update `fetch_fec_data.py` immediately
2. Test on small sample
3. Start overnight collection
4. Create database schema
5. Begin UI work (if time permits tonight)

Let me know when you're ready to proceed!
