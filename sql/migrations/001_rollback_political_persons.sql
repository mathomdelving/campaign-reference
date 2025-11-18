-- ============================================================================
-- ROLLBACK 001: Remove Political Persons System
-- ============================================================================
-- Purpose: Safely rollback the political persons migration
-- WARNING: This will delete all political_persons and committee_designations data
-- ============================================================================

-- Drop triggers
DROP TRIGGER IF EXISTS update_political_persons_updated_at ON political_persons;
DROP TRIGGER IF EXISTS update_committee_designations_updated_at ON committee_designations;

-- Drop trigger function (only if no other tables use it)
-- DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop view
DROP VIEW IF EXISTS principal_committees;

-- Drop committee_designations table
DROP TABLE IF EXISTS committee_designations;

-- Remove person_id column from candidates
ALTER TABLE candidates DROP COLUMN IF EXISTS person_id;

-- Drop political_persons table
DROP TABLE IF EXISTS political_persons;

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================
