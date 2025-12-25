# Database Migrations - Political Persons System

## Overview

This migration creates a system to merge multiple candidate_ids into single political person entities, solving the "duplicate candidate" problem where the same person appears multiple times in search results.

## Problem Being Solved

**Before:** Searching for "Sherrod Brown" returns 3 separate results:
- H2OH13033 (House seat from 90s - no data)
- S6OH00163 (2022/2024 Senate runs)
- S6OH00379 (2026 Senate run)

**After:** Searching for "Sherrod Brown" returns 1 result with combined financial data from all principal campaign committees.

## Migration Files

### 1. `001_create_political_persons.sql`
Creates the new schema:
- `political_persons` table - Represents actual people
- Adds `person_id` column to `candidates` table
- `committee_designations` table - Tracks committee type per cycle
- `principal_committees` view - Helper view for principal committees only

### 2. `001_rollback_political_persons.sql`
Rollback script to safely undo the migration if needed.

### 3. `../scripts/populate_political_persons.js`
Node.js script to populate initial data using FEC API.

## Running the Migration

### Step 1: Run the SQL migration

**Option A: Via Supabase Dashboard**
1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `001_create_political_persons.sql`
3. Execute the SQL

**Option B: Via psql**
```bash
psql -h <your-db-host> -U postgres -d postgres -f sql/migrations/001_create_political_persons.sql
```

### Step 2: Populate data

Set environment variables:
```bash
export NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

Run the population script:
```bash
cd /Users/benjaminnelson/Desktop/campaign-reference
node scripts/populate_political_persons.js
```

This will:
1. Create `political_persons` records for Sherrod Brown and Ruben Gallego
2. Link their candidate_ids to the person records
3. Fetch committee designation history from FEC API
4. Populate the `committee_designations` table

**Note:** The script includes rate limiting to avoid hitting FEC API limits.

### Step 3: Verify the migration

```sql
-- Check persons created
SELECT * FROM political_persons;

-- Check candidate linkages
SELECT candidate_id, name, person_id
FROM candidates
WHERE person_id IS NOT NULL;

-- Check committee designations
SELECT * FROM committee_designations
WHERE is_principal = TRUE
ORDER BY cycle;

-- Use the helper view
SELECT * FROM principal_committees
WHERE person_id = 'sherrod-brown-oh'
ORDER BY cycle;
```

## Rollback

If you need to undo the migration:

```bash
psql -h <your-db-host> -U postgres -d postgres -f sql/migrations/001_rollback_political_persons.sql
```

**⚠️ WARNING:** This will delete all political_persons and committee_designations data.

## Schema Details

### political_persons table

| Column | Type | Description |
|--------|------|-------------|
| person_id | TEXT (PK) | Unique slug (e.g., 'sherrod-brown-oh') |
| display_name | TEXT | Name for UI display (e.g., 'Sherrod Brown') |
| first_name | TEXT | First name |
| last_name | TEXT | Last name |
| party | TEXT | Party affiliation |
| state | TEXT | State |
| district | TEXT | District (for House) |
| current_office | TEXT | 'H', 'S', 'P', or NULL |
| is_incumbent | BOOLEAN | Currently in office |
| notes | TEXT | Additional notes |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### committee_designations table

| Column | Type | Description |
|--------|------|-------------|
| committee_id | TEXT (PK) | FEC committee ID |
| cycle | INTEGER (PK) | Election cycle |
| designation | TEXT | 'P', 'A', 'J', 'D', 'U', 'B' |
| designation_name | TEXT | Full name of designation |
| committee_type | TEXT | 'H', 'S', 'P', 'N', 'Q', etc. |
| committee_type_name | TEXT | Full name of type |
| committee_name | TEXT | Committee name |
| is_principal | BOOLEAN | Computed: TRUE if designation='P' |
| is_authorized | BOOLEAN | Computed: TRUE if designation='A' |
| is_joint_fundraising | BOOLEAN | Computed: TRUE if designation='J' |
| is_leadership_pac | BOOLEAN | Computed: TRUE if designation='D' |
| candidate_id | TEXT | Linked candidate |
| source | TEXT | Data source (default: 'fec_api') |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Designation Codes

- **P** = Principal campaign committee (what we want to display)
- **A** = Authorized committee
- **J** = Joint fundraising committee (exclude from display)
- **D** = Leadership PAC (may include later)
- **U** = Unauthorized committee
- **B** = Lobbyist/Registrant PAC

## Next Steps After Migration

1. **Update Search UI** (`apps/labs/src/components/committee/CommitteeView.tsx`)
   - Query `political_persons` table instead of `candidates`
   - Display `display_name` instead of formatted candidate name

2. **Update Data Fetching Hooks**
   - Modify `useQuarterlyData` to accept `person_id` and fetch all linked candidate_ids
   - Filter results to only include principal committee data

3. **Add Committee Info to Tooltips**
   - Include `committee_id` in tooltip display
   - Format: "Q3 2022: C00264697 • $500K raised"

4. **Create Admin Tools**
   - UI to create new political_persons
   - UI to link candidates to persons
   - Bulk import tool for common cases

## Testing Checklist

- [ ] Migration runs without errors
- [ ] Population script completes successfully
- [ ] Sherrod Brown shows 3 linked candidates
- [ ] Committee designations populated for all cycles
- [ ] Principal committees view shows correct data
- [ ] Search returns political_persons instead of candidates
- [ ] Chart shows combined data from all candidate_ids
- [ ] Tooltips display committee_id correctly
- [ ] No data overlap in quarterly records

## Support

For questions or issues, check the project documentation or review the investigation scripts in the project root.
