# FEC Troubleshooting Guide

**Purpose:** Solutions to common problems when working with FEC data

**Last Updated:** November 19, 2025

---

## Table of Contents

1. [API Issues](#api-issues)
2. [Data Collection Problems](#data-collection-problems)
3. [Database Issues](#database-issues)
4. [Data Quality Problems](#data-quality-problems)
5. [Frontend Integration Issues](#frontend-integration-issues)
6. [Quick Fixes](#quick-fixes)

---

## API Issues

### Problem: 429 Rate Limit Error

**Symptoms:**
```
Error: 429 Too Many Requests
X-RateLimit-Remaining: 0
```

**Cause:** Exceeded 1,000 requests/hour or 120 requests/minute limit.

**Solutions:**

**Solution 1: Add Rate Limiting (Permanent Fix)**
```python
import time

def rate_limited_request(url, params):
    time.sleep(0.05)  # ~900 requests/hour (safe margin)
    response = requests.get(url, params=params)
    return response
```

**Solution 2: Implement Retry Logic**
```python
def safe_request(url, params, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 429:
            wait_time = 60  # Wait 1 minute
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue

        return response.json()

    raise Exception("Max retries exceeded")
```

**Solution 3: Run During Off-Peak Hours**
- Night (11 PM - 5 AM ET) = Less competition for rate limit
- Avoid 9 AM - 5 PM ET (peak FEC usage)

---

### Problem: API Key Not Working

**Symptoms:**
```
Error: 403 Forbidden
Message: "Invalid API key"
```

**Solutions:**

**Solution 1: Check Environment Variable**
```bash
# Verify API key is set
echo $FEC_API_KEY

# If empty, add to .env
echo "FEC_API_KEY=your_key_here" >> .env
```

**Solution 2: Get New API Key**
1. Visit https://api.open.fec.gov/developers/
2. Sign up for free API key (instant)
3. Update `.env` file

**Solution 3: Check Key Format**
```python
# Should be 40 characters, alphanumeric
print(len(os.getenv('FEC_API_KEY')))  # Should print 40
```

---

### Problem: Empty Response from API

**Symptoms:**
```json
{"results": [], "pagination": {"count": 0}}
```

**Causes & Solutions:**

**Cause 1: Wrong Cycle**
```python
# Bad: Cycle doesn't exist yet
response = requests.get(f"{BASE_URL}/candidates/?cycle=2028")

# Good: Use current/past cycles
response = requests.get(f"{BASE_URL}/candidates/?cycle=2026")
```

**Cause 2: Too Many Filters**
```python
# Bad: No candidates match all filters
response = requests.get(f"{BASE_URL}/candidates/?state=CA&district=99")  # CA has no district 99

# Good: Check filters are valid
response = requests.get(f"{BASE_URL}/candidates/?state=CA&office=H")
```

**Cause 3: Candidate Has No Financial Data**
```python
# Add has_raised_funds filter
response = requests.get(
    f"{BASE_URL}/candidates/?cycle=2026&has_raised_funds=true"
)
```

---

## Data Collection Problems

### Problem: Script Runs for Hours, Then Crashes

**Symptoms:**
- Script runs for 4-6 hours
- Crashes with network error or rate limit
- Have to start over from beginning

**Solutions:**

**Solution 1: Use Progress Tracking (Permanent Fix)**
```python
# Save progress every 25 candidates
def save_progress(candidate_id, total_processed):
    with open('progress.json', 'w') as f:
        json.dump({
            'last_candidate': candidate_id,
            'total_processed': total_processed,
            'timestamp': datetime.now().isoformat()
        }, f)

# Resume from progress
def load_progress():
    if os.path.exists('progress.json'):
        with open('progress.json') as f:
            return json.load(f)
    return None
```

**Solution 2: Run in Background with Logs**
```bash
# Use nohup to keep running if terminal closes
nohup python3 -u scripts/data-collection/fetch_fec_data.py > collection.log 2>&1 &

# Monitor progress
tail -f collection.log
```

**Solution 3: Batch Processing**
```python
# Process in smaller batches
def process_candidates_batch(candidates, batch_size=100):
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        process_batch(batch)
        save_to_json(batch, f"batch_{i}.json")  # Save after each batch
```

---

### Problem: Missing Quarterly Data

**Symptoms:**
- Candidate has financial_summary totals
- But no quarterly_financials records
- Charts show empty

**Causes & Solutions:**

**Cause 1: Candidate Has No Principal Committee**
```python
# Check if candidate has principal committee
candidate = requests.get(f"{BASE_URL}/candidate/{candidate_id}/").json()
if not candidate['principal_committees']:
    print(f"No principal committee for {candidate_id}")
    # Skip quarterly collection for this candidate
```

**Cause 2: Wrong Report Type Filter**
```python
# Bad: Filters out quarterly reports
reports = get_reports(committee_id, report_type="YE")  # Only year-end

# Good: Get all quarterly reports
reports = get_reports(committee_id, report_type=["Q1", "Q2", "Q3", "Q4"])
```

**Cause 3: Committee Changed During Cycle**
```python
# Solution: Check committee_designations table
def get_all_principal_committees(candidate_id, cycle):
    committees = supabase.table('committee_designations') \
        .select('committee_id') \
        .eq('candidate_id', candidate_id) \
        .eq('cycle', cycle) \
        .eq('is_principal', True) \
        .execute()

    return [c['committee_id'] for c in committees.data]

# Fetch reports from ALL principal committees
for committee_id in get_all_principal_committees(candidate_id, 2026):
    reports = fetch_quarterly_reports(committee_id, 2026)
```

---

### Problem: Duplicate Records in Database

**Symptoms:**
```sql
SELECT candidate_id, COUNT(*)
FROM candidates
GROUP BY candidate_id
HAVING COUNT(*) > 1;
-- Returns duplicates
```

**Solutions:**

**Solution 1: Use UPSERT (Permanent Fix)**
```python
# Replace INSERT with UPSERT
supabase.table('candidates').upsert(candidates).execute()

# For quarterly financials, use unique constraint
supabase.table('quarterly_financials').insert(records).execute()
# Will fail if duplicate - that's good!
```

**Solution 2: Deduplicate Existing Data**
```sql
-- Find duplicates
WITH duplicates AS (
  SELECT candidate_id, MIN(created_at) as keep_id
  FROM candidates
  GROUP BY candidate_id
  HAVING COUNT(*) > 1
)
-- Delete all but oldest
DELETE FROM candidates c
WHERE EXISTS (
  SELECT 1 FROM duplicates d
  WHERE c.candidate_id = d.candidate_id
  AND c.created_at > d.keep_id
);
```

**Solution 3: Add Unique Constraint**
```sql
-- Prevent future duplicates
ALTER TABLE candidates
ADD CONSTRAINT candidates_pkey PRIMARY KEY (candidate_id);
```

---

## Database Issues

### Problem: Database Query Too Slow

**Symptoms:**
- Query takes >5 seconds
- Frontend loading spinner forever
- Supabase dashboard shows slow queries

**Solutions:**

**Solution 1: Add Indexes**
```sql
-- Check if indexes exist
SELECT * FROM pg_indexes WHERE tablename = 'candidates';

-- Add missing indexes
CREATE INDEX idx_candidates_cycle ON candidates(cycle);
CREATE INDEX idx_candidates_state ON candidates(state);
CREATE INDEX idx_financial_receipts ON financial_summary(total_receipts DESC);
```

**Solution 2: Use EXPLAIN to Debug**
```sql
EXPLAIN ANALYZE
SELECT * FROM candidates
WHERE cycle = 2026 AND state = 'CA';

-- Look for "Seq Scan" = BAD (full table scan)
-- Look for "Index Scan" = GOOD (using index)
```

**Solution 3: Limit Results**
```sql
-- Bad: Fetch all 5,000 candidates
SELECT * FROM candidates WHERE cycle = 2026;

-- Good: Paginate
SELECT * FROM candidates
WHERE cycle = 2026
ORDER BY name
LIMIT 100 OFFSET 0;
```

**Solution 4: Optimize JOIN**
```sql
-- Bad: Join without indexes
SELECT c.*, fs.*
FROM candidates c
JOIN financial_summary fs ON c.candidate_id = fs.candidate_id;

-- Good: Add .eq() filters to reduce JOIN size
SELECT c.*, fs.*
FROM candidates c
JOIN financial_summary fs
  ON c.candidate_id = fs.candidate_id
WHERE c.cycle = 2026
  AND fs.cycle = 2026;  -- Much faster
```

---

### Problem: Database Connection Timeouts

**Symptoms:**
```
Error: Connection timeout
Error: Too many connections
```

**Solutions:**

**Solution 1: Use Connection Pooling**
```python
# Create single Supabase client, reuse it
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Don't create new client for each request
def fetch_data():
    # Bad: Creates new connection
    client = create_client(url, key)  # NO!

    # Good: Reuse existing
    return supabase.table('candidates').select('*').execute()
```

**Solution 2: Close Connections**
```python
# If using raw psycopg2
conn = psycopg2.connect(...)
try:
    # Do work
    pass
finally:
    conn.close()  # Always close
```

**Solution 3: Increase Timeout**
```python
# Increase timeout for long queries
response = requests.get(url, params=params, timeout=60)  # 60 seconds
```

---

## Data Quality Problems

### Problem: Totals Don't Match Quarterly Sum

**Symptoms:**
```sql
-- financial_summary says $3.2M
-- Sum of quarterly says $2.8M
-- Difference of $400K
```

**Causes & Solutions:**

**Cause 1: Missing Quarterly Reports**
```sql
-- Check how many quarterly reports exist
SELECT
  candidate_id,
  COUNT(*) as num_reports
FROM quarterly_financials
WHERE candidate_id = 'H6CA47001'
  AND cycle = 2026
GROUP BY candidate_id;

-- Should have 4 reports (Q1-Q4) per year
```

**Cause 2: Non-Quarterly Reports Included**
```sql
-- Exclude non-quarterly report types
SELECT SUM(total_receipts)
FROM quarterly_financials
WHERE candidate_id = 'H6CA47001'
  AND cycle = 2026
  AND report_type IN ('Q1', 'Q2', 'Q3', 'Q4');  -- Only quarterly
```

**Cause 3: Amendments Not Handled**
```sql
-- Only count most recent version
SELECT SUM(total_receipts)
FROM quarterly_financials
WHERE candidate_id = 'H6CA47001'
  AND cycle = 2026
  AND report_type IN ('Q1', 'Q2', 'Q3', 'Q4')
  AND is_amendment = FALSE;  -- Exclude amendments
```

---

### Problem: Negative Cash on Hand

**Symptoms:**
```sql
SELECT candidate_id, cash_on_hand
FROM financial_summary
WHERE cash_on_hand < 0;
-- Returns candidates with negative cash
```

**Cause:** Debts exceed cash (legitimate but unusual).

**Solution:** This is actually valid FEC data - campaigns can have negative cash if they have outstanding debts. Display as-is.

```typescript
// Frontend display
const displayCash = (cash: number) => {
  if (cash < 0) {
    return <span className="text-red-600">-${Math.abs(cash).toLocaleString()}</span>
  }
  return <span>${cash.toLocaleString()}</span>
}
```

---

### Problem: Candidate Name in ALL CAPS

**Symptoms:**
```
"SMITH, JANE" instead of "Jane Smith"
```

**Solution:** Format names in frontend.

```typescript
function formatCandidateName(name: string): string {
  if (!name) return ''

  // Split "LAST, FIRST" into parts
  const parts = name.split(',').map(p => p.trim())

  if (parts.length === 2) {
    const [last, first] = parts
    // Title case
    return `${toTitleCase(first)} ${toTitleCase(last)}`
  }

  return toTitleCase(name)
}

function toTitleCase(str: string): string {
  return str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())
}

// Usage
formatCandidateName("SMITH, JANE")  // Returns: "Jane Smith"
```

---

## Frontend Integration Issues

### Problem: Supabase Query Returns Empty

**Symptoms:**
```typescript
const { data } = await supabase.from('candidates').select('*')
// data is []
```

**Solutions:**

**Solution 1: Check RLS Policies**
```sql
-- View current policies
SELECT * FROM pg_policies WHERE tablename = 'candidates';

-- Ensure SELECT policy exists
CREATE POLICY "Public read access"
ON candidates FOR SELECT
TO anon
USING (true);
```

**Solution 2: Use Correct Supabase Key**
```typescript
// Frontend uses ANON key
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!  // NOT service role key
)
```

**Solution 3: Check Filter Logic**
```typescript
// Bad: Filters cancel each other out
  .eq('office', 'H')
  .eq('office', 'S')  // Can't be both!

// Good: Use .in() for multiple values
  .in('office', ['H', 'S'])
```

---

### Problem: Chart Shows Incorrect Data

**Symptoms:**
- Chart displays cumulative totals instead of per-quarter
- Or vice versa

**Solution:** Check data source.

```typescript
// For time series charts: Use quarterly_financials (per-period)
const { data } = await supabase
  .from('quarterly_financials')  // Correct table
  .select('*')
  .eq('candidate_id', id)

// For leaderboard: Use financial_summary (cumulative)
const { data } = await supabase
  .from('financial_summary')  // Correct table
  .select('*')
```

---

### Problem: TypeScript Type Errors

**Symptoms:**
```
Property 'total_receipts' does not exist on type 'never'
```

**Solution:** Define proper types.

```typescript
// Define types matching database schema
interface Candidate {
  candidate_id: string
  name: string
  party: string
  office: string
  state: string
  district?: string
  cycle: number
}

interface FinancialSummary {
  candidate_id: string
  cycle: number
  total_receipts: number
  total_disbursements: number
  cash_on_hand: number
}

// Use types in queries
const { data } = await supabase
  .from('candidates')
  .select<'*', Candidate>('*')
```

---

## Quick Fixes

### Quick Fix: Reset Collection Script

```bash
# Delete progress and start fresh
rm progress.json
rm *.json
python3 scripts/data-collection/fetch_fec_data.py --cycle 2026
```

---

### Quick Fix: Check API Status

```bash
# Test API is working
curl "https://api.open.fec.gov/v1/candidates/?api_key=YOUR_KEY&per_page=1"

# Should return JSON with 1 candidate
```

---

### Quick Fix: Verify Database Connection

```bash
# Test Supabase connection
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

result = client.table('candidates').select('count').execute()
print(f'Total candidates: {len(result.data)}')
"
```

---

### Quick Fix: Clear Frontend Cache

```bash
# Next.js cache
rm -rf .next
npm run dev

# Browser cache
# Chrome: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

---

### Quick Fix: Check GitHub Actions Logs

```bash
# View latest workflow run
gh run list --limit 5

# View logs for specific run
gh run view <run-id> --log
```

---

## Getting Help

### 1. Check Documentation First
- `FEC_API_GUIDE.md` - API usage
- `FEC_SCHEMA_REFERENCE.md` - Database schema
- `FEC_INTEGRATION_PATTERNS.md` - Code examples

### 2. Check FEC Official Docs
- https://api.open.fec.gov/developers/
- https://www.fec.gov/help-candidates-and-committees/

### 3. Email FEC Support
- APIinfo@fec.gov (for API issues)
- Response time: 1-2 business days

### 4. Check Project History
- `docs/history/lessons-learned.md` - Past issues and solutions
- GitHub Issues - Search closed issues

---

## Common Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Add delay, retry after 60s |
| `403 Forbidden` | Invalid API key | Check FEC_API_KEY env variable |
| `404 Not Found` | Endpoint/ID doesn't exist | Verify candidate_id format |
| `500 Internal Server Error` | FEC API issue | Retry, check api.data.gov status |
| `Connection timeout` | Network/database issue | Increase timeout, check connection |
| `duplicate key value` | Trying to insert duplicate | Use UPSERT instead of INSERT |
| `relation does not exist` | Table not created | Run database migrations |
| `column does not exist` | Schema mismatch | Check field names in schema |

---

**Last Updated:** November 19, 2025
**Need More Help?** Check `docs/history/lessons-learned.md` for detailed problem-solving examples
