-- ============================================================================
-- MIGRATION: Add senate_class column to candidates table
-- ============================================================================
-- This migration adds a senate_class column to identify which Senate class
-- (I, II, or III) a Senate candidate is running for. This is needed because
-- the candidate ID alone cannot determine Senate class.
-- ============================================================================

-- Step 1: Add senate_class column (nullable for now)
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS senate_class TEXT;

-- Step 2: Create index for faster filtering by senate_class
CREATE INDEX IF NOT EXISTS idx_candidates_senate_class
ON candidates(senate_class)
WHERE office = 'S';

-- Step 3: Add a check constraint to ensure valid values
ALTER TABLE candidates
ADD CONSTRAINT IF NOT EXISTS check_senate_class_valid
CHECK (senate_class IS NULL OR senate_class IN ('I', 'II', 'III'));

-- ============================================================================
-- NOTES
-- ============================================================================
-- After running this migration, use the populate_senate_class.py script
-- to populate the senate_class values for all Senate candidates.
--
-- The senate_class will be determined by:
-- 1. The candidate's state
-- 2. The candidate's election_years
-- 3. The official Senate class schedule (Class I: 2024, Class II: 2026, etc.)
-- ============================================================================
