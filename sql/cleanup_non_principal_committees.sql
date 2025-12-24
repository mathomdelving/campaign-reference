-- =====================================================================================
-- CLEANUP NON-PRINCIPAL COMMITTEE DATA
-- =====================================================================================
-- Based on FEC API designation data retrieved 2025-11-17
--
-- This script removes non-principal committee filings that distract from the core
-- message: "What do [candidate's] fundraising trends look like?"
--
-- CATEGORIES BEING REMOVED:
-- 1. Nominee Funds (Authorized committees for general election)
-- 2. Leadership PACs (Not campaign committees)
-- 3. Joint Fundraising Committees (Not campaign committees)
-- 4. Other Authorized committees (Side committees, terminated committees)
--
-- SPECIAL CASE - Aaron Baker (Sherrod Brown pattern):
--   - C00893289 was Principal in 2024 → KEEP 2024 records
--   - C00893289 became Authorized in 2026 → DELETE 2026 records
--   - C00902478 is Principal in 2026 → KEEP 2026 records
-- =====================================================================================

BEGIN;

-- Count records before deletion
SELECT
    'BEFORE' as stage,
    COUNT(*) as total_records,
    COUNT(DISTINCT committee_id) as unique_committees
FROM quarterly_financials
WHERE committee_id IN (
    -- 2024 non-principal (4 committees)
    'C00829390',  -- Kari Lake - Nominee Fund
    'C00852608',  -- Gary Barve - Authorized
    'C00856617',  -- Nick Begich - Nominee Fund
    'C00857839',  -- Laurie Buckhout - Nominee Fund

    -- 2026 non-principal (10 committees, including Aaron Baker's old committee)
    'C00580043',  -- William Huizenga - Joint Fundraising
    'C00818328',  -- Kevin Kiley - Leadership PAC
    'C00513002',  -- Steny Hoyer - Joint Fundraising
    'C00885319',  -- Jeffrey Hurd - Leadership PAC
    'C00858340',  -- Kevin Coughlin - Nominee Fund
    'C00832576',  -- Julie Johnson - Leadership PAC (despite $1.7M, it's NOT principal!)
    'C00893289',  -- Aaron Baker - WAS principal in 2024, became authorized in 2026
    'C00905927',  -- Nathan Headrick - Authorized
    'C00571018',  -- Tom Cotton - Joint Fundraising
    'C00691576',  -- Cindy Hyde-Smith - Joint Fundraising

    -- 2022 non-principal (1 committee)
    'C00764779'   -- Katrina Christiansen - Unauthorized
);

-- =====================================================================================
-- DELETION SECTION
-- =====================================================================================

-- 2024 Cycle: Delete all nominee funds and authorized committees
DELETE FROM quarterly_financials
WHERE cycle = 2024
AND committee_id IN (
    'C00829390',  -- Kari Lake - Nominee Fund (Authorized)
    'C00852608',  -- Gary Barve - Authorized
    'C00856617',  -- Nick Begich - Nominee Fund (Authorized)
    'C00857839'   -- Laurie Buckhout - Nominee Fund (Authorized)
);

-- 2026 Cycle: Delete all non-principal committees
DELETE FROM quarterly_financials
WHERE cycle = 2026
AND committee_id IN (
    'C00580043',  -- William Huizenga - Joint Fundraising Committee
    'C00818328',  -- Kevin Kiley - Leadership PAC
    'C00513002',  -- Steny Hoyer - Joint Fundraising Committee
    'C00885319',  -- Jeffrey Hurd - Leadership PAC
    'C00858340',  -- Kevin Coughlin - Authorized (Nominee Fund)
    'C00832576',  -- Julie Johnson - Leadership PAC
    'C00893289',  -- Aaron Baker - Old committee (was principal in 2024, authorized in 2026)
    'C00905927',  -- Nathan Headrick - Authorized
    'C00571018',  -- Tom Cotton - Joint Fundraising Committee
    'C00691576'   -- Cindy Hyde-Smith - Joint Fundraising Committee
);

-- 2022 Cycle: Delete unauthorized committee
DELETE FROM quarterly_financials
WHERE cycle = 2022
AND committee_id = 'C00764779';  -- Katrina Christiansen - Unauthorized

-- =====================================================================================
-- ALSO DELETE: Old committee that became non-principal
-- =====================================================================================
-- Katrina Christiansen's C00802959 was principal in 2022 but became authorized in 2024
DELETE FROM quarterly_financials
WHERE cycle = 2024
AND committee_id = 'C00802959';  -- Katrina Christiansen - became Authorized in 2024

-- =====================================================================================
-- VERIFICATION
-- =====================================================================================

-- Show what remains by candidate
WITH deleted_candidates AS (
    SELECT DISTINCT candidate_id, cycle
    FROM quarterly_financials
    WHERE committee_id IN (
        'C00829390', 'C00852608', 'C00856617', 'C00857839',  -- 2024
        'C00580043', 'C00818328', 'C00513002', 'C00885319', 'C00858340',  -- 2026
        'C00832576', 'C00893289', 'C00905927', 'C00571018', 'C00691576',  -- 2026 cont
        'C00764779', 'C00802959'  -- 2022/2024
    )
)
SELECT
    c.candidate_id,
    c.cycle,
    COUNT(DISTINCT qf.committee_id) as committees_remaining,
    STRING_AGG(DISTINCT qf.committee_id, ', ' ORDER BY qf.committee_id) as committee_ids,
    COUNT(*) as filings_remaining,
    SUM(qf.total_receipts) as total_raised
FROM deleted_candidates c
JOIN quarterly_financials qf ON c.candidate_id = qf.candidate_id AND c.cycle = qf.cycle
GROUP BY c.candidate_id, c.cycle
ORDER BY c.cycle, c.candidate_id;

-- Count after deletion
SELECT
    'AFTER' as stage,
    COUNT(*) as total_records_deleted
FROM quarterly_financials
WHERE committee_id IN (
    'C00829390', 'C00852608', 'C00856617', 'C00857839',
    'C00580043', 'C00818328', 'C00513002', 'C00885319', 'C00858340',
    'C00832576', 'C00893289', 'C00905927', 'C00571018', 'C00691576',
    'C00764779', 'C00802959'
);

-- Final verification: Show a few examples
SELECT
    'KARI LAKE 2024' as test_case,
    COUNT(DISTINCT committee_id) as committees,
    STRING_AGG(DISTINCT committee_id, ', ') as committee_ids
FROM quarterly_financials
WHERE candidate_id = 'S4AZ00220' AND cycle = 2024

UNION ALL

SELECT
    'JULIE JOHNSON 2024' as test_case,
    COUNT(DISTINCT committee_id) as committees,
    STRING_AGG(DISTINCT committee_id, ', ') as committee_ids
FROM quarterly_financials
WHERE candidate_id = 'H4TX32089' AND cycle = 2024

UNION ALL

SELECT
    'AARON BAKER 2024' as test_case,
    COUNT(DISTINCT committee_id) as committees,
    STRING_AGG(DISTINCT committee_id, ', ') as committee_ids
FROM quarterly_financials
WHERE candidate_id = 'H6FL06324' AND cycle = 2024

UNION ALL

SELECT
    'AARON BAKER 2026' as test_case,
    COUNT(DISTINCT committee_id) as committees,
    STRING_AGG(DISTINCT committee_id, ', ') as committee_ids
FROM quarterly_financials
WHERE candidate_id = 'H6FL06324' AND cycle = 2026;

-- =====================================================================================
-- IMPORTANT: Review the verification output above before committing!
--
-- Expected results:
-- - KARI LAKE 2024: 1 committee (C00852343 only, C00829390 deleted)
-- - JULIE JOHNSON 2024: 1 committee (C00843003 only, C00832576 Leadership PAC deleted)
-- - AARON BAKER 2024: 1 committee (C00893289, was principal that cycle)
-- - AARON BAKER 2026: 1 committee (C00902478 only, C00893289 deleted from 2026)
--
-- If everything looks good, COMMIT. Otherwise, ROLLBACK.
-- =====================================================================================

-- Uncomment ONE of these after reviewing:
-- COMMIT;
-- ROLLBACK;
