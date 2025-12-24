# Product Roadmap - Campaign Reference

## Current Status (Phase 1: Foundation) ✅

### Political Persons System
- **Status**: Complete
- **Description**: Unified person entities that link multiple candidate_ids for the same individual
- **Implementation**: 5,407 political persons with committee designation tracking
- **Use Cases**:
  - CommitteeView search ("Ruben Gallego" shows all principal committee data)
  - Name normalization across the platform

### Database Views (In Progress)
- **Status**: In Development
- **Goal**: Create "prep station" views for fast data loading
- **Implementation**: `leaderboard_data` view combining candidates + political_persons + financial_summary

---

## Phase 2: Leadership PACs (Future - Q2/Q3 2025)

### Goal
Show the complete financial picture of a candidate by including their Leadership PAC fundraising alongside their Principal Committee.

### Why This Matters
Leadership PACs (LPACs) are separate committees that candidates use to raise money outside of their principal campaign committee. Examples:
- **John Fetterman**: "Fetterman for PA" (Principal) + "Every Vote PAC" (LPAC)
- **Candidate fundraises for both**, but they're tracked separately in FEC data

### Current Infrastructure (Already Built)
✅ `committee_designations` table tracks Principal (P), Leadership PAC (D), and Joint Fundraising (J)
✅ `political_persons` table links all committees to one person
✅ `quarterly_financials` stores filings for all committee types

### What We Need to Add
1. **Database View**: `person_financials`
   - Aggregates Principal + LPAC money by person
   - Shows breakdown by committee type

2. **UI Toggle**: "Show Principal Only" vs "Show Principal + LPAC"
   - Leaderboard can display either view
   - Allows users to see full fundraising picture

3. **Data Collection Verification**
   - Ensure scripts capture designation = 'D' for all LPACs
   - Verify historical LPAC data is complete

### Example Query Concept
```sql
-- Total fundraising for John Fetterman (Principal + LPAC)
SELECT
  p.display_name,
  SUM(CASE WHEN cd.designation = 'P' THEN qf.total_receipts ELSE 0 END) as principal_raised,
  SUM(CASE WHEN cd.designation = 'D' THEN qf.total_receipts ELSE 0 END) as lpac_raised,
  SUM(qf.total_receipts) as total_raised
FROM political_persons p
JOIN candidates c ON p.person_id = c.person_id
JOIN committee_designations cd ON c.candidate_id = cd.candidate_id
JOIN quarterly_financials qf ON cd.committee_id = qf.committee_id
WHERE p.person_id = 'john-fetterman-pa'
GROUP BY p.display_name
```

---

## Phase 3: Independent Expenditure Notifications (Future - Q3/Q4 2025)

### Goal
Notify users when a Super PAC or outside group files a 24-hour or 48-hour Independent Expenditure (IE) report spending for or against a candidate.

### Why This Matters
IEs are high-impact spending that happens close to elections. A $500k TV ad buy filed against a candidate can change a race. Users want to know immediately when this happens.

### The Challenge
- FEC IE reports list spending **by candidate name** (e.g., "FETTERMAN, JOHN")
- Names can be spelled inconsistently
- Need to match messy name data → clean `person_id`

### How Political Persons Solves This
The `political_persons` table acts as the **matching hub** to link IE reports to the correct person.

### Infrastructure Needed

#### 1. New Table: `independent_expenditures`
```sql
CREATE TABLE independent_expenditures (
  id SERIAL PRIMARY KEY,
  person_id TEXT REFERENCES political_persons(person_id),
  filer_committee_id TEXT,
  filer_committee_name TEXT,
  expenditure_amount NUMERIC,
  expenditure_date DATE,
  support_oppose_indicator TEXT, -- 'S' for support, 'O' for oppose
  candidate_name_raw TEXT, -- Original name from FEC
  report_type TEXT, -- '24H', '48H', etc.
  filed_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. FEC API Integration
- Poll FEC IE endpoint: `/schedules/schedule_e/`
- Filter for `report_type` = '24' or '48'
- Match `candidate_name` to `person_id` via political_persons lookup

#### 3. Matching Logic
```
IE Report: "FETTERMAN, JOHN"
  ↓
Search political_persons.display_name OR candidates.name
  ↓
Match: person_id = 'john-fetterman-pa'
  ↓
Store IE with person_id
```

#### 4. Notification System
```sql
-- Find all IEs against John Fetterman in last 24 hours
SELECT
  ie.filer_committee_name,
  ie.expenditure_amount,
  ie.support_oppose_indicator,
  ie.filed_date
FROM independent_expenditures ie
WHERE ie.person_id = 'john-fetterman-pa'
  AND ie.filed_date > NOW() - INTERVAL '24 hours'
  AND ie.support_oppose_indicator = 'O'
ORDER BY ie.filed_date DESC;
```

#### 5. User-Facing Features
- Email/SMS notifications for tracked candidates
- Dashboard showing recent IEs for/against candidates
- Aggregated IE spending totals by race

---

## Database Architecture Vision

### Core Tables (Current)
```
political_persons (hub)
  ↓
candidates (many-to-one)
  ↓
committee_designations (tracks P/D/J status)
  ↓
quarterly_financials (principal committee filings)
```

### Future Expansion
```
political_persons (hub)
  ↓
├─ candidates → committee_designations → quarterly_financials (Principal + LPAC)
├─ independent_expenditures (IE spending for/against)
└─ (future: endorsements, polling, news mentions, etc.)
```

---

## Technical Principles

### 1. Political Persons as Central Hub
All person-related data flows through `political_persons.person_id`:
- Fundraising (principal + LPAC)
- Independent Expenditures
- Future: Polling, endorsements, news

### 2. Database Views for Performance
Pre-joined views act as "prep stations":
- `leaderboard_data` - Fast candidate leaderboard loading
- `person_financials` - Principal + LPAC aggregation
- `person_summary` - Complete person overview

### 3. Flexible Querying
Views support all current use cases:
- Leaderboard view
- By-district view
- By-committee view
- Future: By-person view with full financial picture

### 4. Notification-Ready
Architecture supports real-time alerts:
- IE filings
- Quarterly report filings
- Cash-on-hand changes
- LPAC activity

---

## Implementation Priorities

### Now (Phase 1)
1. ✅ Political persons system
2. 🚧 Database views for performance
3. 🚧 Hook updates to use views

### Next 3-6 Months (Phase 2)
1. LPAC data verification
2. `person_financials` view
3. UI toggle for Principal vs Principal+LPAC

### 6-12 Months (Phase 3)
1. `independent_expenditures` table
2. FEC IE API integration
3. Name matching logic
4. Notification system

---

## Notes

- All future features are designed to plug into existing `political_persons` architecture
- No breaking changes to current data collection or views
- Incremental additions only
- Performance-first approach using database views
