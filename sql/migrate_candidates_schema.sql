-- ============================================================================
-- MIGRATION: Remove cycle from candidates table and add incumbent_challenge
-- ============================================================================
-- This migration:
-- 1. Creates a new candidates table with the correct schema
-- 2. Migrates unique candidate data from old table
-- 3. Drops old table and renames new table
-- 4. Adds incumbent_challenge column
-- ============================================================================

-- Step 1: Create new candidates table with correct schema
CREATE TABLE candidates_new (
    candidate_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    party TEXT,
    office TEXT,
    state TEXT,
    district TEXT,
    incumbent_challenge TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Migrate data from old table (taking only unique candidates)
-- If there are duplicates, we'll take the most recently updated record
INSERT INTO candidates_new (candidate_id, name, party, office, state, district, created_at, updated_at)
SELECT DISTINCT ON (candidate_id)
    candidate_id,
    name,
    party,
    office,
    state,
    district,
    created_at,
    updated_at
FROM candidates
ORDER BY candidate_id, updated_at DESC;

-- Step 3: Drop old table
DROP TABLE candidates;

-- Step 4: Rename new table to candidates
ALTER TABLE candidates_new RENAME TO candidates;

-- Step 5: Create index on office for faster filtering
CREATE INDEX idx_candidates_office ON candidates(office);

-- Step 6: Create index on state for faster filtering
CREATE INDEX idx_candidates_state ON candidates(state);

-- Step 7: Enable Row Level Security (if it was enabled on old table)
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

-- Step 8: Create RLS policy to allow public read access
CREATE POLICY "Allow public read access" ON candidates
    FOR SELECT
    USING (true);

-- Step 9: Create RLS policy to allow service role full access
CREATE POLICY "Allow service role full access" ON candidates
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after migration to verify success:

-- Check total candidates
-- SELECT COUNT(*) as total_candidates FROM candidates;

-- Check that there are no duplicate candidate_ids
-- SELECT candidate_id, COUNT(*) as count
-- FROM candidates
-- GROUP BY candidate_id
-- HAVING COUNT(*) > 1;

-- Check sample data
-- SELECT * FROM candidates LIMIT 5;

-- Check if Mark Kelly exists
-- SELECT * FROM candidates WHERE candidate_id = 'S0AZ00350';
