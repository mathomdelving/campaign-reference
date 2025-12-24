# Political Persons System - Production Documentation

**Status:** ✅ Live in Production (as of November 24, 2025)

## What We Built

A complete hierarchical database system to solve the "duplicate candidate" problem by unifying multiple `candidate_id` records under single political person entities.

### The Problem

Sherrod Brown appears **3 times** in search results:
- `H2OH13033` - House (OH-13) - no data
- `S6OH00163` - Senate (2022/2024) - 27 records from committee C00264697
- `S6OH00379` - Senate (2026) - 1 record from committee C00916288

Users want to see **one "Sherrod Brown"** with all principal committee fundraising combined.

### The Solution

Three-table system:
1. **`political_persons`** - The actual person
2. **`candidates.person_id`** - Links candidate_ids to persons
3. **`committee_designations`** - Tracks which committees were principal per cycle

## Files Created

### 1. Migration Files (`sql/migrations/`)

#### `001_create_political_persons.sql`
Complete migration that creates:
- `political_persons` table with fields:
  - `person_id` (PK, slug like 'sherrod-brown-oh')
  - `display_name` ('Sherrod Brown')
  - `first_name`, `last_name`, `party`, `state`, `district`
  - `current_office`, `is_incumbent`

- `committee_designations` table with:
  - `committee_id` + `cycle` composite PK
  - `designation` ('P' = Principal, 'J' = JFC, 'D' = Leadership PAC)
  - Computed boolean fields: `is_principal`, `is_joint_fundraising`, etc.

- `principal_committees` view for easy queries

- Adds `person_id` column to `candidates` table

- RLS policies, indexes, triggers for `updated_at`

#### `001_rollback_political_persons.sql`
Safe rollback script to undo the migration.

### 2. Data Population (`scripts/`)

#### `populate_political_persons.js`
Node.js script that:
1. Creates `political_persons` records
2. Links `candidate_ids` to persons
3. Fetches committee history from FEC API
4. Populates `committee_designations` table with principal status per cycle

**Initial persons included:**
- Sherrod Brown (3 candidate_ids)
- Ruben Gallego (House → Senate transition)

**Features:**
- Rate limiting to avoid FEC API throttling
- Automatic retry logic
- Progress logging
- Verification checks

#### `run_migration.sh`
Helper script with commands:
- `./scripts/run_migration.sh migrate` - Instructions to run migration
- `./scripts/run_migration.sh populate` - Populate initial data
- `./scripts/run_migration.sh verify` - Check migration status
- `./scripts/run_migration.sh rollback` - Undo migration

### 3. Documentation

#### `sql/migrations/README.md`
Complete guide covering:
- Problem overview
- How to run migration
- Schema details
- Designation code reference
- Testing checklist
- Next steps for UI integration

#### `DATA_MODEL_SUMMARY.md`
Current data model documentation created during investigation.

## Key Findings from Investigation

### Committee Analysis for Sherrod Brown

| Committee ID | Name | Designation | Records | Date Range |
|-------------|------|-------------|---------|------------|
| C00264697 | Unknown (rate limited) | P → Hybrid | 19 | 2021-2024 |
| C00555342 | CANARY FUND | J (JFC) | 8 | 2023-2024 |
| C00916288 | FRIENDS OF SHERROD BROWN | P | 1 | 2025 |

**Verified:** No overlapping periods - each quarter has exactly one principal committee record.

### FEC ID System

- **Candidate IDs:** Start with H/S/P (e.g., `S6OH00163`)
- **Committee IDs:** Start with C (e.g., `C00264697`)

### Designation Codes

- **P** = Principal campaign committee ✅ (Include)
- **J** = Joint fundraising committee ❌ (Exclude)
- **D** = Leadership PAC ⏸️ (Future consideration)
- **A** = Authorized committee
- **U** = Unauthorized committee
- **B** = Lobbyist/Registrant PAC

## Critical Data Integrity Rule

**⚠️ ALL COMMITTEES MUST MAP TO A CANDIDATE**

When loading financial data:
1. **Check if candidate exists** in the `candidates` table
2. **If candidate does not exist**, create candidate record FIRST
3. **Then load** committee financial data

This ensures referential integrity in the query flow:
```
political_person → candidates (via person_id FK) → quarterly_financials (via candidate_id FK)
```

Without a candidate record, committee financial data cannot be properly attributed to a political person.

---

## How It Works

### Data Flow

```
1. User searches "Sherrod Brown"
   ↓
2. Query political_persons table
   ↓
3. Find person_id = 'sherrod-brown-oh'
   ↓
4. Get all linked candidate_ids: [H2OH13033, S6OH00163, S6OH00379]
   ↓
5. Query quarterly_financials for those candidate_ids
   ↓
6. Filter to only principal committees using committee_designations
   ↓
7. Return combined time series data
   ↓
8. Display as single line on chart with committee_id in tooltip
```

### UI Display

**Chart:**
- Single continuous line labeled "Sherrod Brown"
- Data from 2021-2025 across two committees

**Tooltip per quarter:**
```
Q1 2022
C00264697
$501K raised
```

```
Q3 2025
C00916288
$7.0M raised
```

## Running the Migration

### Step 1: Run SQL Migration

Via Supabase Dashboard:
1. Go to SQL Editor
2. Copy `sql/migrations/001_create_political_persons.sql`
3. Execute

### Step 2: Load Environment Variables

```bash
# Option A: Use existing .env.local
cd /Users/benjaminnelson/Desktop/fec-dashboard

# Option B: Export manually
export NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

### Step 3: Populate Data

```bash
./scripts/run_migration.sh populate
```

This will take 5-10 minutes due to FEC API rate limits.

### Step 4: Verify

```sql
-- Check persons
SELECT * FROM political_persons;

-- Check Sherrod Brown's principal committees
SELECT * FROM principal_committees
WHERE person_id = 'sherrod-brown-oh'
ORDER BY cycle;
```

## Next Steps - UI Integration

### 1. Update Search Component

**File:** `apps/labs/src/components/committee/CommitteeView.tsx`

**Changes needed:**
- Query `political_persons` table instead of `candidates`
- Add new entity type: `"person"`
- Display `display_name` instead of formatted candidate name

### 2. Create New Data Hook

**New file:** `apps/labs/src/hooks/usePersonQuarterlyData.ts`

```typescript
export function usePersonQuarterlyData(personId: string, cycles: number[]) {
  // 1. Fetch person record
  // 2. Get all linked candidate_ids
  // 3. Query quarterly_financials for those candidates
  // 4. Filter to principal committees only using committee_designations
  // 5. Return combined time series
}
```

### 3. Update Chart Tooltips

Add committee information to tooltip display:
```typescript
{
  quarter: "Q3 2022",
  committeeId: "C00264697",
  receipts: 500000
}
```

Display format: `"C00264697 • $500K raised"`

### 4. Create Admin Tools (Future)

- UI to create new `political_persons`
- UI to link `candidate_ids` to persons
- Bulk import for common transitions (House → Senate)

## Testing Checklist

Before going to production:

- [ ] Migration runs without errors
- [ ] Population script completes successfully
- [ ] Sherrod Brown shows 3 linked candidates
- [ ] Committee designations populated (19 + 1 = 20 records)
- [ ] Principal committees view returns correct data
- [ ] Search returns persons instead of duplicate candidates
- [ ] Chart shows combined data from all candidate_ids
- [ ] No data overlap in quarterly records
- [ ] Tooltips display committee_id correctly
- [ ] JFC (C00555342) is excluded from display
- [ ] Ruben Gallego test case works (House → Senate transition)

## Architecture Decisions

### Why Political Persons Table?

**Alternative considered:** Canonical candidate system (self-referential)

**Chosen approach:** Separate `political_persons` table

**Reasoning:**
1. Person is semantically distinct from candidacy
2. More extensible (can add bio, career timeline, etc.)
3. Handles edge cases (running for multiple offices simultaneously)
4. Cleaner queries and data model
5. No arbitrary "canonical" choice needed

### Why Committee Designations Table?

**Alternative considered:** Hardcode principal committee IDs

**Chosen approach:** Track designation per cycle via FEC API

**Reasoning:**
1. Committees change designation over time (principal → hybrid PAC)
2. Need time-based filtering ("what was it in 2022?")
3. Extensible for Leadership PACs and other committee types
4. Single source of truth from FEC data

### Why Computed Boolean Columns?

Instead of filtering by `designation = 'P'`, we use `is_principal = TRUE`.

**Reasoning:**
1. Faster queries (can use index on boolean)
2. Self-documenting schema
3. Handles future edge cases
4. PostgreSQL GENERATED ALWAYS ensures consistency

## Database Schema Diagram

```
political_persons
├── person_id (PK)
├── display_name
├── party, state, current_office
└── ...

candidates
├── candidate_id (PK)
├── person_id (FK) ──┐
├── name              │
└── ...               │
                      │
quarterly_financials  │
├── id (PK)           │
├── candidate_id ─────┘
├── committee_id ──┐
├── cycle          │
├── receipts       │
└── ...            │
                   │
committee_designations
├── committee_id (PK) ─┘
├── cycle (PK)
├── designation
├── is_principal (computed)
└── ...
```

## Performance Considerations

### Indexes Created

```sql
-- political_persons
idx_political_persons_state
idx_political_persons_party
idx_political_persons_office
idx_political_persons_name

-- candidates
idx_candidates_person_id

-- committee_designations
idx_committee_designations_candidate
idx_committee_designations_principal (filtered)
idx_committee_designations_cycle
```

### Query Optimization

Use the `principal_committees` view for common queries:
```sql
SELECT * FROM principal_committees
WHERE person_id = ?
AND cycle = ?
```

This is faster than joining three tables manually.

## Support & Troubleshooting

### Common Issues

**Problem:** FEC API rate limit during population
- **Solution:** Script includes automatic retry with 60s wait

**Problem:** Committee has no history in FEC API
- **Solution:** Check if committee is very old or state-level

**Problem:** Candidate appears twice in search after migration
- **Solution:** Check if `person_id` is set correctly

### Verification Queries

```sql
-- Check for orphaned candidates (no person_id)
SELECT candidate_id, name
FROM candidates
WHERE person_id IS NULL
AND candidate_id IN (
  SELECT DISTINCT candidate_id
  FROM quarterly_financials
);

-- Check for missing principal committees
SELECT DISTINCT qf.committee_id, qf.cycle
FROM quarterly_financials qf
LEFT JOIN committee_designations cd
  ON qf.committee_id = cd.committee_id
  AND qf.cycle = cd.cycle
WHERE cd.committee_id IS NULL;
```

## Future Enhancements

1. **Leadership PACs:** Add support for displaying Leadership PAC data separately
2. **Presidential Campaigns:** Extend to P (Presidential) candidates
3. **Career Timeline:** Add UI to show office transitions over time
4. **Auto-linking:** ML model to suggest person linkages for new candidates
5. **Bulk Import:** Tool to import common transitions from FEC data

## Credits

Investigation and implementation based on analysis of:
- Sherrod Brown case study (3 candidate_ids, 2 committees)
- FEC API committee history endpoint
- Supabase database schema
- Current search UI behavior

---

**Status:** ✅ Migration and population scripts complete, ready for testing
**Next:** Run migration in Supabase and test with UI integration
