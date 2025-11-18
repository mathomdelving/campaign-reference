# Setting Up the Leaderboard View in Supabase

## Step 1: Access Supabase SQL Editor

1. Go to https://supabase.com
2. Sign in to your project
3. Click on **SQL Editor** in the left sidebar
4. Click **New Query**

## Step 2: Run the SQL

1. Open `sql/create_leaderboard_view.sql` in this folder
2. Copy the entire contents
3. Paste into the Supabase SQL Editor
4. Click **Run** (or press Cmd+Enter)

You should see: `Success. No rows returned`

This is normal! It means the view was created successfully.

## Step 3: Verify the View Exists

Run this test query in the SQL Editor:

```sql
SELECT * FROM leaderboard_data LIMIT 5;
```

You should see 5 rows with columns:
- candidate_id
- person_id
- display_name (cleaned names like "Ruben Gallego")
- party
- state
- district
- office
- cycle
- total_receipts
- total_disbursements
- cash_on_hand
- updated_at
- candidate_name_raw

## Step 4: Test Performance

Run this query to see how fast it is:

```sql
SELECT
  display_name,
  party,
  state,
  total_receipts,
  cash_on_hand
FROM leaderboard_data
WHERE cycle = 2026
  AND office = 'S'
ORDER BY total_receipts DESC
LIMIT 20;
```

This should return results in **<1 second** (vs the previous 10+ seconds).

## Step 5: Grant Permissions (If Needed)

If your hooks can't access the view, run:

```sql
GRANT SELECT ON leaderboard_data TO anon;
GRANT SELECT ON leaderboard_data TO authenticated;
```

## Troubleshooting

### Error: "relation does not exist"
- Make sure you ran the CREATE VIEW statement successfully
- Check that you're using the correct database (should match your .env.local)

### Error: "permission denied"
- Run the GRANT statements above
- Make sure you're using the service role key (not anon key) when creating the view

### View shows no data
- Check that your tables have data: `SELECT COUNT(*) FROM candidates;`
- Check that financial_summary has data: `SELECT COUNT(*) FROM financial_summary;`

## Next Steps

Once the view is created and tested, update the TypeScript hooks to use it:
- `apps/labs/src/hooks/useCandidateData.ts`
- `apps/labs/src/hooks/useDistrictCandidates.ts`
