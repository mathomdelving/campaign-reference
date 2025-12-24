# Non-Principal Committee Cleanup

**Date:** 2025-11-17
**Issue:** Kari Lake's chart showed confusing "TER $0" tooltip from nominee fund termination

## Problem Statement

The purpose of candidate fundraising charts is to answer: **"What do [candidate's] fundraising trends look like?"**

Showing nominee funds, leadership PACs, and joint fundraising committees on these charts distracts from this core message and creates confusion.

## Investigation Summary

Used FEC API to retrieve official committee designation data for all candidates with multiple committees across 2022, 2024, and 2026 cycles.

### Key Findings

**Total Committees to Remove:** 15 committees across 16 candidates

#### By Committee Type:
- **Nominee Funds (4):** Authorized committees for general election expenses only
- **Leadership PACs (3):** Political action committees, NOT campaign committees
- **Joint Fundraising Committees (4):** Not campaign committees
- **Other Authorized (4):** Side committees, terminated committees

#### By Cycle:
- **2022:** 1 committee (Christiansen unauthorized committee)
- **2024:** 5 committees (4 nominee funds + 1 becoming non-principal)
- **2026:** 10 committees (JFCs, Leadership PACs, authorized committees)

## Special Cases

### 1. Aaron Baker (H6FL06324) - Committee Transition
**Pattern:** Similar to Sherrod Brown, but handled differently

- **C00893289** - Was Principal in 2024 → KEEP 2024 records
- **C00893289** - Became Authorized in 2026 → DELETE 2026 records
- **C00902478** - Is Principal in 2026 → KEEP 2026 records

**Why not show both?** Unlike Sherrod Brown (incumbent senator with historical story), Aaron Baker is a new 2026 House candidate. Users only care about his current principal committee.

### 2. Julie Johnson (H4TX32089) - Leadership PAC Surprise
**Initial assumption:** Both committees had substantial activity, might be Sherrod Brown pattern
**Reality:** C00832576 "PATRIOT PAC" was NEVER principal - it's a Leadership PAC

- **C00832576** - Leadership PAC, despite $1.7M raised → DELETE all records
- **C00843003** - Principal campaign committee → KEEP

**Lesson:** High dollar amount ≠ Principal campaign committee

### 3. Kari Lake (S4AZ00220) - The Original Issue
- **C00852343** - "KARI LAKE FOR SENATE" (Principal, $26M) → KEEP
- **C00829390** - Nominee Fund (Authorized, $92K with TER) → DELETE

Removing the nominee fund eliminates the confusing "TER $0" tooltip.

## Committees Being Removed

### 2024 Cycle (4 committees)
| Committee | Candidate | Type | Reason |
|-----------|-----------|------|--------|
| C00829390 | LAKE, KARI | Nominee Fund | Authorized, not principal |
| C00852608 | BARVE, GARY | Authorized | Side committee |
| C00856617 | BEGICH, NICHOLAS III | Nominee Fund | Authorized, not principal |
| C00857839 | BUCKHOUT, LAURIE | Nominee Fund | Authorized, not principal |

### 2026 Cycle (10 committees)
| Committee | Candidate | Type | Reason |
|-----------|-----------|------|--------|
| C00580043 | HUIZENGA, WILLIAM P | JFC | Joint fundraising, not principal |
| C00818328 | KILEY, KEVIN | Leadership PAC | Not campaign committee |
| C00513002 | HOYER, STENY | JFC | Joint fundraising, not principal |
| C00885319 | HURD, JEFFREY | Leadership PAC | Not campaign committee |
| C00858340 | COUGHLIN, KEVIN | Nominee Fund | Authorized, not principal |
| C00832576 | JOHNSON, JULIE | Leadership PAC | Not campaign committee |
| C00893289 | BAKER, AARON | Old Committee | Was principal in 2024, authorized in 2026 |
| C00905927 | HEADRICK, NATHAN | Authorized | Side committee |
| C00571018 | COTTON, THOMAS | JFC | Joint fundraising, not principal |
| C00691576 | HYDE-SMITH, CINDY | JFC | Joint fundraising, not principal |

### 2022 Cycle (1 committee)
| Committee | Candidate | Type | Reason |
|-----------|-----------|------|--------|
| C00764779 | CHRISTIANSEN, KATRINA | Unauthorized | Not a campaign committee |

### Also Removing: Committees That Changed Status
| Committee | Candidate | Cycles | Reason |
|-----------|-----------|--------|--------|
| C00802959 | CHRISTIANSEN, KATRINA | 2024 | Was principal in 2022, became authorized in 2024 |

## Data Quality Note

Julie Johnson's Leadership PAC (C00832576) has massive duplicates - each filing appears 6 times in the database. This is a separate data quality issue to address.

## Impact Analysis

**Candidates Affected:** 16 candidates out of ~1,000 total (1.6%)
**Cycles Affected:** 2022 (1), 2024 (5), 2026 (10)

### Before Cleanup Examples:
- **Kari Lake 2024:** 2 committees (C00852343 + C00829390 nominee fund)
- **Julie Johnson 2024:** 2 committees (C00843003 + C00832576 Leadership PAC)
- **Aaron Baker 2026:** 2 committees (C00902478 + C00893289 old committee)

### After Cleanup:
- **Kari Lake 2024:** 1 committee (C00852343 only) ✓
- **Julie Johnson 2024:** 1 committee (C00843003 only) ✓
- **Aaron Baker 2026:** 1 committee (C00902478 only) ✓
- **Aaron Baker 2024:** 1 committee (C00893289, was principal) ✓

## Execution Plan

1. **Review SQL script:** `sql/cleanup_non_principal_committees.sql`
2. **Verify output:** Check that verification queries show expected results
3. **Execute deletion:** Run script with COMMIT (currently set to require manual uncommenting)
4. **Test frontend:** Verify Kari Lake chart no longer shows TER tooltip
5. **Monitor:** Check other affected candidates' charts for correctness

## FEC API Data Source

All committee designations retrieved from:
- **Endpoint:** `https://api.open.fec.gov/v1/committee/{id}/history/`
- **API Key:** Personal key (1000/hour limit)
- **Date Retrieved:** 2025-11-17
- **Script:** `get_all_committee_designations.py`

## No Sherrod Brown Patterns Found

Despite checking all multi-committee candidates, **only Aaron Baker** showed a pattern similar to Sherrod Brown (principal committee changing between cycles). However, unlike Sherrod Brown (where both committees tell the historical story of an incumbent), Aaron Baker is a new 2026 candidate, so we only show his current principal committee on the 2026 chart.

## Related Files

- **Investigation Scripts:**
  - `get_all_committee_designations.py` - Main FEC API designation retrieval
  - `investigate_kari_lake.py` - Initial investigation
  - `check_committee_transitions.py` - Sherrod Brown pattern detection
  - `verify_julie_johnson.py` - Leadership PAC verification

- **SQL:**
  - `sql/cleanup_non_principal_committees.sql` - Deletion script

- **This Document:**
  - `NON_PRINCIPAL_COMMITTEE_CLEANUP.md`
