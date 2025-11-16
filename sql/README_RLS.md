# Apply Row Level Security Policies

## What This Does

Protects your database from unauthorized modifications while keeping campaign finance data publicly readable.

**Current Problem:**
- Anyone can modify your database using the browser console
- Someone could artificially inflate/decrease financial data
- Data integrity is at risk

**After Applying:**
- ✅ Public can READ all campaign finance data (frontend works normally)
- ❌ Public CANNOT insert, update, or delete data
- ✅ Only your backend scripts (with service key) can modify data

## How to Apply

### Method 1: Supabase SQL Editor (Recommended)

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy the entire contents of `enable_rls_policies.sql` (this file)
6. Paste into the SQL Editor
7. Click **Run** (or press Cmd/Ctrl + Enter)

You should see: "Success. No rows returned"

### Method 2: Command Line (If you have psql installed)

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres" -f sql/enable_rls_policies.sql
```

## Verify It Worked

1. Go to **Database** → **Tables** in Supabase
2. Click on any table (e.g., `candidates`)
3. Go to **Policies** tab
4. You should see:
   - RLS enabled: ✅
   - Two policies:
     - "Allow public read access" (SELECT for everyone)
     - "Allow service role full access" (ALL for service_role)

## Testing

After applying, your frontend should still work normally (reads are allowed).

To verify writes are blocked, open browser console on your site and try:

```javascript
// This should FAIL with permission error
const { createClient } = window.supabase;
const client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
await client.from('candidates').insert({ candidate_id: 'TEST123', name: 'HACKER' });
// Expected: Error 42501 - new row violates row-level security policy
```

Your backend scripts will continue to work because they use `SUPABASE_KEY` (service role).

## Tables Protected

- ✅ candidates
- ✅ financial_summary
- ✅ quarterly_financials
- ✅ committees
- ✅ committee_financials
- ✅ data_refresh_log (admin only, no public read)
- ✅ notification_queue (admin only, no public read)

## Troubleshooting

**Frontend can't read data after applying:**
- Check that you're using `SUPABASE_ANON_KEY` in frontend, not `SUPABASE_KEY`
- The "Allow public read access" policy should allow SELECT for everyone

**Backend scripts can't write data:**
- Verify you're using `SUPABASE_KEY` (service_role key) in your scripts, not the anon key
- Check that the key is in your `.env` file

**Still seeing Supabase warnings:**
- Give it a few minutes to update
- Refresh the Supabase dashboard
- Verify RLS is enabled on the table (Database → Tables → [table name] → Settings)
