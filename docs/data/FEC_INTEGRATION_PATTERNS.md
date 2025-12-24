# FEC Integration Patterns

**Purpose:** How this application integrates FEC data - from API to database to frontend

**Last Updated:** November 19, 2025
**Application:** FEC Dashboard (Campaign Reference)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Collection Scripts](#data-collection-scripts)
3. [Frontend Data Hooks](#frontend-data-hooks)
4. [Common Integration Patterns](#common-integration-patterns)
5. [Best Practices](#best-practices)

---

## Architecture Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FEC OpenFEC API                           │
│              https://api.open.fec.gov/v1/                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Rate limited (1K/hour)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Python Collection Scripts                       │
│  scripts/data-collection/fetch_fec_data.py (full refresh)   │
│  scripts/data-loading/incremental_update.py (daily updates) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Saves to JSON (temp)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            JSON Files (Temporary Storage)                    │
│  candidates_{cycle}.json                                     │
│  financials_{cycle}.json                                     │
│  quarterly_financials_{cycle}.json                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Loaded by load_to_supabase.py
                       ↓
┌─────────────────────────────────────────────────────────────┐
│             Supabase PostgreSQL Database                     │
│  candidates | financial_summary | quarterly_financials      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Queried by Supabase client
                       ↓
┌─────────────────────────────────────────────────────────────┐
│               Frontend (Next.js/React)                       │
│  hooks/useCandidateData.ts                                   │
│  hooks/useQuarterlyData.ts                                   │
│  hooks/useDistrictCandidates.ts                              │
└─────────────────────────────────────────────────────────────┘
```

### Update Schedule

**GitHub Actions Workflow:**
- **Daily:** 6 AM ET - Full incremental update
- **Filing Period:** Every 2 hours (days 13-17 of Q1, Q2, Q3, Q4)
- **Peak Filing Day:** Every 30 minutes (15th of filing month, 9 AM - 6 PM ET)

**Workflow:**
```yaml
1. incremental_update.py → Fetch new FEC data
2. detect_new_filings.py → Find candidates with new reports
3. send_notifications.py → Email alerts to followers
```

---

## Data Collection Scripts

### 1. Full Collection: fetch_fec_data.py

**Location:** `scripts/data-collection/fetch_fec_data.py`

**Purpose:** Complete data collection for an election cycle (run once per cycle).

**Usage:**
```bash
# Collect all 2026 data
python3 scripts/data-collection/fetch_fec_data.py --cycle 2026

# Collect multiple cycles
python3 scripts/data-collection/fetch_fec_data.py --cycle 2024,2026
```

**What it does:**
1. Fetches all candidates for the cycle from `/candidates/`
2. For each candidate:
   - Gets financial totals from `/candidate/{id}/totals/`
   - Gets principal committee from candidate record
   - Fetches quarterly reports from `/committee/{committee_id}/reports/`
3. Saves to 3 JSON files:
   - `candidates_{cycle}.json`
   - `financials_{cycle}.json`
   - `quarterly_financials_{cycle}.json`

**Runtime:** 6-8 hours for full cycle (~5,000 candidates)

**Key Code Patterns:**

```python
# Rate limiting wrapper
def rate_limited_request(url, params):
    time.sleep(0.05)  # ~900 requests/hour (safe margin)
    response = requests.get(url, params=params)
    if response.status_code == 429:
        print("Rate limited, waiting 60s...")
        time.sleep(60)
        return rate_limited_request(url, params)
    return response.json()

# Fetch candidates
def fetch_candidates(cycle):
    candidates = []
    page = 1
    while True:
        data = rate_limited_request(
            f"{BASE_URL}/candidates/",
            {"api_key": API_KEY, "cycle": cycle, "office": ["H", "S"],
             "has_raised_funds": True, "per_page": 100, "page": page}
        )
        candidates.extend(data["results"])
        if len(data["results"]) < 100:
            break
        page += 1
    return candidates

# Fetch quarterly data
def fetch_quarterly_data(candidate_id, committee_id, cycle):
    data = rate_limited_request(
        f"{BASE_URL}/committee/{committee_id}/reports/",
        {"api_key": API_KEY, "cycle": cycle,
         "report_type": ["Q1", "Q2", "Q3", "Q4"],
         "most_recent": True, "per_page": 100}
    )
    return data["results"]
```

---

### 2. Incremental Updates: incremental_update.py

**Location:** `scripts/data-loading/incremental_update.py`

**Purpose:** Daily updates - only fetch candidates with recent changes.

**Usage:**
```bash
# Update data from last 1 day
python3 scripts/data-loading/incremental_update.py --lookback 1

# Update from last 7 days (after system downtime)
python3 scripts/data-loading/incremental_update.py --lookback 7
```

**What it does:**
1. Queries candidates who filed reports in last N days
2. Updates their financial_summary records
3. Adds any new quarterly_financials records
4. Much faster than full collection (5-10 minutes typical)

**Key Code Patterns:**

```python
# Find recently updated candidates
def find_recent_updates(lookback_days=1):
    cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # Query candidates with recent filings
    recent_filings = supabase.table('quarterly_financials') \
        .select('candidate_id') \
        .gte('updated_at', cutoff_date) \
        .execute()

    candidate_ids = set([r['candidate_id'] for r in recent_filings.data])
    return list(candidate_ids)

# Update only changed candidates
def incremental_update(candidate_ids):
    for candidate_id in candidate_ids:
        # Fetch latest totals
        totals = fetch_candidate_totals(candidate_id)

        # Upsert to financial_summary
        supabase.table('financial_summary').upsert({
            'candidate_id': candidate_id,
            'cycle': 2026,
            'total_receipts': totals['receipts'],
            'total_disbursements': totals['disbursements'],
            'cash_on_hand': totals['cash_on_hand_end_period'],
            'updated_at': datetime.now().isoformat()
        }).execute()

        # Fetch any new quarterly reports
        quarterly = fetch_new_quarterly_reports(candidate_id)
        if quarterly:
            supabase.table('quarterly_financials').insert(quarterly).execute()
```

---

### 3. Load to Database: load_to_supabase.py

**Location:** `scripts/data-loading/load_to_supabase.py`

**Purpose:** Load JSON files into Supabase (Step 2 of 2-step workflow).

**Usage:**
```bash
# After fetch_fec_data.py completes
python3 scripts/data-loading/load_to_supabase.py
```

**What it does:**
1. Reads JSON files from disk
2. Batch inserts to Supabase (1,000 records at a time)
3. Uses UPSERT to prevent duplicates

**Key Code Patterns:**

```python
# Load candidates
def load_candidates(filename):
    with open(filename) as f:
        candidates = json.load(f)

    # Batch insert (1,000 at a time)
    batch_size = 1000
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        supabase.table('candidates').upsert(batch).execute()
        print(f"Loaded {i+len(batch)}/{len(candidates)} candidates")

# Load quarterly financials with conflict handling
def load_quarterly_financials(filename):
    with open(filename) as f:
        records = json.load(f)

    for i in range(0, len(records), 1000):
        batch = records[i:i+1000]
        try:
            supabase.table('quarterly_financials').insert(batch).execute()
        except Exception as e:
            # Handle duplicates gracefully
            if "duplicate key" in str(e):
                print(f"Skipping {len(batch)} duplicate records")
            else:
                raise
```

---

## Frontend Data Hooks

### 1. useCandidateData Hook

**Location:** `apps/labs/src/hooks/useCandidateData.ts`

**Purpose:** Fetch candidates with their financial summaries (for leaderboard, tables).

**Usage:**
```typescript
import { useCandidateData } from '@/hooks/useCandidateData'

function LeaderboardView() {
  const { data, loading, error } = useCandidateData({
    cycle: 2026,
    office: 'H',  // or 'S'
    state: 'CA',  // optional
    district: '47', // optional
    hasData: true  // only candidates with financial data
  })

  if (loading) return <LoadingSkeleton />
  if (error) return <Error message={error} />

  return (
    <Table data={data} />
  )
}
```

**What it returns:**
```typescript
{
  candidate_id: string
  name: string
  party: string
  office: string
  state: string
  district?: string
  total_receipts: number  // From financial_summary (cumulative)
  total_disbursements: number
  cash_on_hand: number
  cycle: number
}
```

**Implementation:**
```typescript
export function useCandidateData(filters: CandidateFilters) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      let query = supabase
        .from('candidates')
        .select(`
          *,
          financial_summary!inner(*)
        `)
        .eq('cycle', filters.cycle)

      if (filters.office) query = query.eq('office', filters.office)
      if (filters.state) query = query.eq('state', filters.state)
      if (filters.district) query = query.eq('district', filters.district)
      if (filters.hasData) query = query.gt('financial_summary.total_receipts', 0)

      const { data: results, error } = await query

      if (error) throw error
      setData(results)
      setLoading(false)
    }

    fetchData()
  }, [filters])

  return { data, loading, error }
}
```

---

### 2. useQuarterlyData Hook

**Location:** `apps/labs/src/hooks/useQuarterlyData.ts`

**Purpose:** Fetch quarterly time series for charts.

**Usage:**
```typescript
import { useQuarterlyData } from '@/hooks/useQuarterlyData'

function QuarterlyChart({ candidateIds }: { candidateIds: string[] }) {
  const { data, loading } = useQuarterlyData({
    candidateIds: candidateIds,
    cycles: [2024, 2026],
    reportTypes: ['Q1', 'Q2', 'Q3', 'Q4']  // optional
  })

  if (loading) return <LoadingSkeleton />

  return (
    <LineChart
      data={data}
      xField="coverage_end_date"
      yField="total_receipts"
      seriesField="candidate_id"
    />
  )
}
```

**What it returns:**
```typescript
{
  candidate_id: string
  name: string
  party: string
  cycle: number
  report_type: string  // 'Q1', 'Q2', etc.
  coverage_start_date: string
  coverage_end_date: string
  total_receipts: number  // Per-quarter (NOT cumulative)
  total_disbursements: number
  cash_ending: number
}[]
```

**Implementation:**
```typescript
export function useQuarterlyData(filters: QuarterlyFilters) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      let query = supabase
        .from('quarterly_financials')
        .select('*')
        .in('candidate_id', filters.candidateIds)
        .in('cycle', filters.cycles)
        .order('coverage_end_date', { ascending: true })

      if (filters.reportTypes) {
        query = query.in('report_type', filters.reportTypes)
      }

      const { data: results, error } = await query

      if (error) throw error
      setData(results)
      setLoading(false)
    }

    fetchData()
  }, [filters])

  return { data, loading }
}
```

---

### 3. useDistrictCandidates Hook

**Location:** `apps/labs/src/hooks/useDistrictCandidates.ts`

**Purpose:** Fetch all candidates in a specific district (for district view).

**Usage:**
```typescript
import { useDistrictCandidates } from '@/hooks/useDistrictCandidates'

function DistrictView({ state, district }: { state: string, district: string }) {
  const { candidates, loading } = useDistrictCandidates({
    state: state,
    district: district,
    cycle: 2026
  })

  return (
    <div>
      <h1>{state}-{district}</h1>
      {candidates.map(c => (
        <CandidateCard key={c.candidate_id} candidate={c} />
      ))}
    </div>
  )
}
```

---

## Common Integration Patterns

### Pattern 1: Search Candidates (Autocomplete)

**Use Case:** User types candidate name, see matching results.

**Frontend:**
```typescript
async function searchCandidates(query: string) {
  const { data } = await supabase
    .from('candidates')
    .select('candidate_id, name, party, office, state, district')
    .ilike('name', `%${query}%`)
    .eq('cycle', 2026)
    .limit(20)

  return data
}

// Usage in component
const [results, setResults] = useState([])
const handleSearch = debounce(async (query: string) => {
  if (query.length < 3) return
  const results = await searchCandidates(query)
  setResults(results)
}, 300)
```

---

### Pattern 2: Build Leaderboard (Top Fundraisers)

**Use Case:** Show top 20 House candidates by money raised.

**SQL Query:**
```sql
SELECT
  c.candidate_id,
  c.name,
  c.party,
  c.state,
  c.district,
  fs.total_receipts,
  fs.cash_on_hand
FROM candidates c
JOIN financial_summary fs
  ON c.candidate_id = fs.candidate_id
WHERE c.office = 'H'
  AND c.cycle = 2026
  AND fs.cycle = 2026
ORDER BY fs.total_receipts DESC
LIMIT 20;
```

**TypeScript:**
```typescript
const { data } = await supabase
  .from('candidates')
  .select(`
    *,
    financial_summary!inner(total_receipts, cash_on_hand)
  `)
  .eq('office', 'H')
  .eq('cycle', 2026)
  .order('financial_summary.total_receipts', { ascending: false })
  .limit(20)
```

---

### Pattern 3: Time Series Chart (Quarterly Trends)

**Use Case:** Show quarterly fundraising trends for multiple candidates.

**SQL Query:**
```sql
SELECT
  candidate_id,
  name,
  party,
  coverage_end_date,
  total_receipts,
  cash_ending
FROM quarterly_financials
WHERE candidate_id IN ('H6CA47001', 'H6CA47002')
  AND cycle = 2026
  AND report_type IN ('Q1', 'Q2', 'Q3', 'Q4')
ORDER BY coverage_end_date ASC;
```

**TypeScript:**
```typescript
const { data } = await supabase
  .from('quarterly_financials')
  .select('*')
  .in('candidate_id', ['H6CA47001', 'H6CA47002'])
  .eq('cycle', 2026)
  .in('report_type', ['Q1', 'Q2', 'Q3', 'Q4'])
  .order('coverage_end_date', { ascending: true })
```

**Chart Transformation:**
```typescript
// Transform for Recharts
const chartData = data.reduce((acc, row) => {
  const existing = acc.find(d => d.date === row.coverage_end_date)
  if (existing) {
    existing[row.candidate_id] = row.total_receipts
  } else {
    acc.push({
      date: row.coverage_end_date,
      [row.candidate_id]: row.total_receipts
    })
  }
  return acc
}, [])
```

---

### Pattern 4: District Race Overview

**Use Case:** Show all candidates in a specific district with head-to-head comparison.

**SQL Query:**
```sql
SELECT
  c.candidate_id,
  c.name,
  c.party,
  c.incumbent_challenge,
  fs.total_receipts,
  fs.cash_on_hand,
  COUNT(qf.id) as num_filings
FROM candidates c
JOIN financial_summary fs
  ON c.candidate_id = fs.candidate_id
LEFT JOIN quarterly_financials qf
  ON c.candidate_id = qf.candidate_id
  AND qf.cycle = 2026
WHERE c.state = 'CA'
  AND c.district = '47'
  AND c.cycle = 2026
GROUP BY c.candidate_id, c.name, c.party, c.incumbent_challenge,
         fs.total_receipts, fs.cash_on_hand
ORDER BY fs.total_receipts DESC;
```

---

## Best Practices

### 1. Always Use the 2-Step Workflow

**✅ CORRECT:**
```bash
# Step 1: Fetch to JSON
python3 scripts/data-collection/fetch_fec_data.py --cycle 2026

# Step 2: Review JSON, then load
ls -lh *.json
head -20 candidates_2026.json
python3 scripts/data-loading/load_to_supabase.py
```

**❌ WRONG:**
```bash
# Don't write directly to Supabase from fetch script
python3 old_script_that_writes_directly.py  # NO!
```

**Why:** Review JSON files before uploading to catch errors.

---

### 2. Rate Limiting

**Always include delay between requests:**
```python
time.sleep(0.05)  # ~900 requests/hour (safe margin)
```

**Handle 429 errors:**
```python
if response.status_code == 429:
    time.sleep(60)  # Wait 1 minute
    return retry_request(url, params)
```

---

### 3. Frontend Query Optimization

**Use indexes effectively:**
```typescript
// Good: Uses indexed columns
  .eq('cycle', 2026)
  .eq('office', 'H')
  .eq('state', 'CA')

// Bad: Full table scan
  .ilike('name', '%smith%')  // Slow on large tables
```

**Limit result sets:**
```typescript
// Always use .limit() for safety
  .select('*')
  .limit(1000)  // Prevent fetching 50K records
```

**Use specific selects:**
```typescript
// Good: Only fetch needed columns
  .select('candidate_id, name, total_receipts')

// Bad: Fetch everything
  .select('*')  // Wastes bandwidth
```

---

### 4. Error Handling

**Always handle database errors:**
```typescript
try {
  const { data, error } = await supabase.from('candidates').select('*')
  if (error) throw error
  return data
} catch (err) {
  console.error('Database error:', err)
  // Show user-friendly message
  toast.error('Failed to load candidates')
}
```

---

### 5. Caching Strategy

**Frontend:**
```typescript
// Use SWR or React Query for caching
import useSWR from 'swr'

function useCandidates(filters) {
  const { data, error } = useSWR(
    ['candidates', filters],
    () => fetchCandidates(filters),
    { revalidateOnFocus: false, refreshInterval: 60000 }  // Cache for 1 min
  )

  return { data, loading: !data && !error, error }
}
```

**Backend:**
```python
# Save progress to avoid re-fetching
with open('progress.json', 'w') as f:
    json.dump({"last_processed": candidate_id}, f)
```

---

## Related Documentation

- `FEC_API_GUIDE.md` - API usage reference
- `FEC_SCHEMA_REFERENCE.md` - Database schema mappings
- `FEC_TROUBLESHOOTING_GUIDE.md` - Common issues
- `../guides/collection-guide.md` - Quick reference for data collection
- `../guides/collection-workflow.md` - 2-step workflow (CRITICAL!)

---

**Last Updated:** November 19, 2025
**Application:** FEC Dashboard (Campaign Reference)
**Framework:** Next.js 16 + Supabase + Python
