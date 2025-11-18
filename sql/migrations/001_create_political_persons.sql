-- ============================================================================
-- MIGRATION 001: Create Political Persons System
-- ============================================================================
-- Purpose: Enable merging multiple candidate_ids into a single person entity
--
-- This migration creates:
-- 1. political_persons table - Represents actual people/politicians
-- 2. Adds person_id to candidates table - Links candidates to persons
-- 3. committee_designations table - Tracks committee type per cycle
--
-- Example use case: Sherrod Brown has 3 candidate_ids (House + 2 Senate)
-- but should appear as one searchable person with combined financial data
-- ============================================================================

-- ============================================================================
-- 1. CREATE POLITICAL_PERSONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS political_persons (
    -- Primary key: human-readable slug
    person_id TEXT PRIMARY KEY,

    -- Display information
    display_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,

    -- Political affiliation
    party TEXT,

    -- Geographic info
    state TEXT,
    district TEXT,

    -- Current status
    current_office TEXT, -- 'H', 'S', 'P', or NULL
    is_incumbent BOOLEAN DEFAULT FALSE,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for common queries
CREATE INDEX idx_political_persons_state ON political_persons(state);
CREATE INDEX idx_political_persons_party ON political_persons(party);
CREATE INDEX idx_political_persons_office ON political_persons(current_office);
CREATE INDEX idx_political_persons_name ON political_persons(display_name);

-- Add comment
COMMENT ON TABLE political_persons IS 'Represents actual politicians/persons, enabling multiple candidate_ids to be merged into one entity';

-- ============================================================================
-- 2. ADD PERSON_ID TO CANDIDATES TABLE
-- ============================================================================

ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS person_id TEXT REFERENCES political_persons(person_id);

-- Add index for joins
CREATE INDEX IF NOT EXISTS idx_candidates_person_id ON candidates(person_id);

-- Add comment
COMMENT ON COLUMN candidates.person_id IS 'Links this candidate record to a political_persons entity for merging multiple candidacies';

-- ============================================================================
-- 3. CREATE COMMITTEE_DESIGNATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS committee_designations (
    -- Composite primary key: committee + cycle
    committee_id TEXT NOT NULL,
    cycle INTEGER NOT NULL,

    -- FEC metadata
    designation TEXT, -- 'P', 'A', 'J', 'D', 'U', 'B'
    designation_name TEXT,
    committee_type TEXT, -- 'H', 'S', 'P', 'N', 'Q', etc.
    committee_type_name TEXT,
    committee_name TEXT,

    -- Computed flags for easy filtering
    is_principal BOOLEAN GENERATED ALWAYS AS (designation = 'P') STORED,
    is_authorized BOOLEAN GENERATED ALWAYS AS (designation = 'A') STORED,
    is_joint_fundraising BOOLEAN GENERATED ALWAYS AS (designation = 'J') STORED,
    is_leadership_pac BOOLEAN GENERATED ALWAYS AS (designation = 'D') STORED,

    -- Linked candidate
    candidate_id TEXT REFERENCES candidates(candidate_id),

    -- Metadata
    source TEXT DEFAULT 'fec_api',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (committee_id, cycle)
);

-- Add indexes for common queries
CREATE INDEX idx_committee_designations_candidate ON committee_designations(candidate_id);
CREATE INDEX idx_committee_designations_principal ON committee_designations(is_principal) WHERE is_principal = TRUE;
CREATE INDEX idx_committee_designations_cycle ON committee_designations(cycle);

-- Add comment
COMMENT ON TABLE committee_designations IS 'Tracks committee designation and type per election cycle from FEC data';

-- ============================================================================
-- 4. CREATE HELPER VIEW FOR PRINCIPAL COMMITTEES
-- ============================================================================

CREATE OR REPLACE VIEW principal_committees AS
SELECT
    cd.committee_id,
    cd.cycle,
    cd.committee_name,
    cd.candidate_id,
    c.name as candidate_name,
    c.person_id,
    pp.display_name as person_name
FROM committee_designations cd
LEFT JOIN candidates c ON cd.candidate_id = c.candidate_id
LEFT JOIN political_persons pp ON c.person_id = pp.person_id
WHERE cd.is_principal = TRUE;

COMMENT ON VIEW principal_committees IS 'Convenience view showing only principal campaign committees with person linkage';

-- ============================================================================
-- 5. ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE political_persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE committee_designations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for public read access
CREATE POLICY "Allow public read access" ON political_persons
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access" ON committee_designations
    FOR SELECT
    USING (true);

-- Create RLS policies for service role full access
CREATE POLICY "Allow service role full access" ON political_persons
    FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON committee_designations
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- 6. CREATE UPDATED_AT TRIGGER FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to political_persons
CREATE TRIGGER update_political_persons_updated_at
    BEFORE UPDATE ON political_persons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to committee_designations
CREATE TRIGGER update_committee_designations_updated_at
    BEFORE UPDATE ON committee_designations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verification queries (comment out when running migration):
-- SELECT COUNT(*) FROM political_persons;
-- SELECT COUNT(*) FROM candidates WHERE person_id IS NOT NULL;
-- SELECT COUNT(*) FROM committee_designations;
