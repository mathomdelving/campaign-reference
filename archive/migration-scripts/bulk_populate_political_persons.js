#!/usr/bin/env node

/**
 * Bulk Populate Political Persons System
 *
 * This script populates the political_persons system for ALL candidates
 * who appear in quarterly_financials (active candidates with financial data).
 *
 * Features:
 * - Groups candidates by normalized name + state
 * - Generates person_id slugs (e.g., "mark-kelly-az")
 * - Fetches committee designations from FEC API
 * - Progress tracking with resume capability
 * - Rate limiting for FEC API
 * - Dry-run mode for testing
 *
 * Usage:
 *   # Dry run (preview without writing)
 *   node scripts/bulk_populate_political_persons.js --dry-run
 *
 *   # Full execution
 *   SUPABASE_SERVICE_ROLE_KEY=xxx FEC_API_KEY=xxx node scripts/bulk_populate_political_persons.js
 *
 *   # Resume from checkpoint
 *   node scripts/bulk_populate_political_persons.js --resume
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const FEC_API_KEY = process.env.FEC_API_KEY || 'DEMO_KEY';

const PROGRESS_FILE = path.join(__dirname, '.bulk_populate_progress.json');
const DRY_RUN = process.argv.includes('--dry-run');
const RESUME = process.argv.includes('--resume');

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing required environment variables:');
  console.error('   NEXT_PUBLIC_SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Normalize a name to a consistent format for grouping
 * "KELLY, MARK E" -> "kelly mark"
 * "BROWN, SHERROD" -> "brown sherrod"
 */
function normalizeName(name) {
  if (!name) return '';

  // Remove special characters, extra spaces
  const cleaned = name
    .replace(/[^a-zA-Z\s,]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();

  // Convert "LAST, FIRST MIDDLE" to "last first"
  if (cleaned.includes(',')) {
    const [last, first] = cleaned.split(',').map(s => s.trim());
    // Take only first word of first name to ignore middle names/initials
    const firstName = first.split(' ')[0];
    return `${last} ${firstName}`;
  }

  return cleaned;
}

/**
 * Generate a person_id slug from name and state
 * "Mark Kelly", "AZ" -> "mark-kelly-az"
 */
function generatePersonId(name, state) {
  const normalized = normalizeName(name);
  const slug = normalized
    .split(' ')
    .filter(Boolean)
    .join('-');

  return `${slug}-${state.toLowerCase()}`;
}

/**
 * Format name from "LAST, FIRST MIDDLE" to "First Last"
 */
function formatDisplayName(name) {
  if (!name) return name;

  if (name.includes(',')) {
    const [last, first] = name.split(',').map(s => s.trim());

    const titleCase = (str) => {
      return str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
    };

    // Take full first name (may include middle name)
    return `${titleCase(first)} ${titleCase(last)}`;
  }

  return name.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * Fetch committee history from FEC API with retries
 */
async function fetchCommitteeHistory(committeeId, retries = 3) {
  const url = `https://api.open.fec.gov/v1/committee/${committeeId}/history/?api_key=${FEC_API_KEY}&per_page=100`;

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);

      if (response.status === 429) {
        console.log(`      ⏱  Rate limited, waiting 60s... (attempt ${i + 1}/${retries})`);
        await sleep(60000);
        continue;
      }

      if (!response.ok) {
        console.log(`      ⚠️  HTTP ${response.status}, waiting 5s...`);
        await sleep(5000);
        continue;
      }

      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error(`      ❌ Error: ${error.message}`);
      if (i < retries - 1) {
        await sleep(5000);
      }
    }
  }

  return [];
}

function getDesignationName(code) {
  const names = {
    'P': 'Principal campaign committee',
    'A': 'Authorized committee',
    'J': 'Joint fundraising committee',
    'U': 'Unauthorized committee',
    'B': 'Lobbyist/Registrant PAC',
    'D': 'Leadership PAC'
  };
  return names[code] || 'Unknown';
}

function getCommitteeTypeName(code) {
  const names = {
    'H': 'House',
    'S': 'Senate',
    'P': 'Presidential',
    'N': 'PAC - nonqualified',
    'Q': 'PAC - qualified',
    'I': 'Super PAC',
    'O': 'Super PAC - nonqualified'
  };
  return names[code] || 'Unknown';
}

/**
 * Save progress to disk
 */
function saveProgress(progress) {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
}

/**
 * Load progress from disk
 */
function loadProgress() {
  if (fs.existsSync(PROGRESS_FILE)) {
    return JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
  }
  return null;
}

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

/**
 * Step 1: Discover all active candidates (those with financial data)
 */
async function discoverActiveCandidates() {
  console.log('\n📊 Step 1: Discovering active candidates...\n');

  console.log('   Fetching all quarterly_financials records...');

  // Fetch ALL quarterly financial records (with pagination)
  let allFinancials = [];
  let offset = 0;
  const batchSize = 1000;

  while (true) {
    const { data: batch, error } = await supabase
      .from('quarterly_financials')
      .select('candidate_id, name, party, office, state, district')
      .not('candidate_id', 'is', null)
      .not('name', 'is', null)
      .range(offset, offset + batchSize - 1);

    if (error) {
      throw new Error(`Failed to query quarterly_financials: ${error.message}`);
    }

    if (!batch || batch.length === 0) break;

    allFinancials.push(...batch);
    offset += batchSize;

    process.stdout.write(`\r   Loaded ${allFinancials.length} records...`);

    if (batch.length < batchSize) break;
  }

  console.log(`\n   Total records loaded: ${allFinancials.length}`);

  // Group by candidate_id to get unique candidates with their metadata
  const candidateMap = new Map();

  for (const record of allFinancials) {
    if (!candidateMap.has(record.candidate_id)) {
      candidateMap.set(record.candidate_id, {
        candidate_id: record.candidate_id,
        name: record.name,
        party: record.party,
        office: record.office,
        state: record.state,
        district: record.district
      });
    }
  }

  const candidates = Array.from(candidateMap.values());
  console.log(`   Found ${candidates.length} unique candidates\n`);

  return candidates;
}

/**
 * Step 2: Group candidates into persons
 * Candidates with the same normalized name + state = same person
 */
function groupCandidatesIntoPersons(candidates) {
  console.log('\n👥 Step 2: Grouping candidates into persons...\n');

  const personMap = new Map();

  for (const candidate of candidates) {
    if (!candidate.name || !candidate.state) {
      console.log(`   ⚠️  Skipping ${candidate.candidate_id}: missing name or state`);
      continue;
    }

    const personId = generatePersonId(candidate.name, candidate.state);

    if (!personMap.has(personId)) {
      personMap.set(personId, {
        person_id: personId,
        display_name: formatDisplayName(candidate.name),
        first_name: null, // We'll extract this properly if needed
        last_name: null,
        party: candidate.party,
        state: candidate.state,
        district: null, // State-level for senators, will be set for house members
        current_office: candidate.office,
        is_incumbent: false, // We don't have this info yet
        candidate_ids: [],
        notes: null
      });
    }

    const person = personMap.get(personId);
    person.candidate_ids.push(candidate.candidate_id);

    // Update party if we don't have one yet
    if (!person.party && candidate.party) {
      person.party = candidate.party;
    }

    // Update office (prefer S > H > P)
    if (candidate.office === 'S' ||
        (candidate.office === 'H' && person.current_office !== 'S')) {
      person.current_office = candidate.office;
    }

    // Set district for House members
    if (candidate.office === 'H' && candidate.district) {
      person.district = candidate.district;
    }
  }

  const persons = Array.from(personMap.values());

  console.log(`   Created ${persons.length} unique persons`);
  console.log(`   Average ${(candidates.length / persons.length).toFixed(1)} candidate IDs per person\n`);

  // Show some examples
  const multiCandidatePersons = persons.filter(p => p.candidate_ids.length > 1).slice(0, 5);
  if (multiCandidatePersons.length > 0) {
    console.log('   Examples of persons with multiple candidate IDs:');
    multiCandidatePersons.forEach(p => {
      console.log(`   - ${p.display_name} (${p.state}): ${p.candidate_ids.length} IDs`);
    });
    console.log('');
  }

  return persons;
}

/**
 * Step 3: Create political_persons records and link candidates
 */
async function createPoliticalPersons(persons, startIndex = 0) {
  console.log(`\n✍️  Step 3: Creating political_persons records...\n`);

  let created = 0;
  let skipped = 0;
  let failed = 0;

  for (let i = startIndex; i < persons.length; i++) {
    const person = persons[i];
    const progress = ((i + 1) / persons.length * 100).toFixed(1);

    console.log(`[${i + 1}/${persons.length}] ${progress}% - ${person.display_name} (${person.state})`);

    if (DRY_RUN) {
      console.log(`   [DRY RUN] Would create person: ${person.person_id}`);
      console.log(`   [DRY RUN] Would link ${person.candidate_ids.length} candidate(s)`);
      created++;
    } else {
      // Check if person already exists
      const { data: existing } = await supabase
        .from('political_persons')
        .select('person_id')
        .eq('person_id', person.person_id)
        .maybeSingle();

      if (existing) {
        console.log(`   ⏭️  Already exists, skipping...`);
        skipped++;
        continue;
      }

      // Create person record
      const { candidate_ids, ...personRecord } = person;
      const { error: personError } = await supabase
        .from('political_persons')
        .upsert(personRecord, { onConflict: 'person_id' });

      if (personError) {
        console.error(`   ❌ Failed to create person: ${personError.message}`);
        failed++;
        continue;
      }

      // Link candidate IDs
      for (const candidateId of candidate_ids) {
        const { error: linkError } = await supabase
          .from('candidates')
          .update({ person_id: person.person_id })
          .eq('candidate_id', candidateId);

        if (linkError) {
          console.error(`   ❌ Failed to link ${candidateId}: ${linkError.message}`);
        }
      }

      console.log(`   ✅ Created and linked ${candidate_ids.length} candidate(s)`);
      created++;
    }

    // Save progress every 50 persons
    if (!DRY_RUN && (i + 1) % 50 === 0) {
      saveProgress({
        step: 'create_persons',
        completed_index: i,
        total: persons.length,
        timestamp: new Date().toISOString()
      });
    }

    // Rate limit: small delay between persons
    await sleep(100);
  }

  console.log(`\n   Summary:`);
  console.log(`   ✅ Created: ${created}`);
  console.log(`   ⏭️  Skipped: ${skipped}`);
  console.log(`   ❌ Failed: ${failed}\n`);

  return { created, skipped, failed };
}

/**
 * Step 4: Populate committee designations from FEC API
 */
async function populateCommitteeDesignations(persons, startIndex = 0) {
  console.log(`\n🏛️  Step 4: Fetching committee designations from FEC...\n`);

  let totalCommittees = 0;
  let totalDesignations = 0;

  for (let i = startIndex; i < persons.length; i++) {
    const person = persons[i];
    const progress = ((i + 1) / persons.length * 100).toFixed(1);

    console.log(`[${i + 1}/${persons.length}] ${progress}% - ${person.display_name}`);

    // Get committees for this person's candidates
    const { data: committees, error: committeesError } = await supabase
      .from('quarterly_financials')
      .select('committee_id, candidate_id')
      .in('candidate_id', person.candidate_ids)
      .not('committee_id', 'is', null);

    if (committeesError) {
      console.error(`   ❌ Failed to fetch committees: ${committeesError.message}`);
      continue;
    }

    // Get unique committees
    const uniqueCommittees = new Map();
    committees.forEach(c => {
      if (!uniqueCommittees.has(c.committee_id)) {
        uniqueCommittees.set(c.committee_id, c.candidate_id);
      }
    });

    if (uniqueCommittees.size === 0) {
      console.log(`   ℹ️  No committees found`);
      continue;
    }

    console.log(`   Found ${uniqueCommittees.size} committee(s)`);
    totalCommittees += uniqueCommittees.size;

    // Fetch designations for each committee
    for (const [committeeId, candidateId] of uniqueCommittees.entries()) {
      if (DRY_RUN) {
        console.log(`   [DRY RUN] Would fetch designations for ${committeeId}`);
        continue;
      }

      const history = await fetchCommitteeHistory(committeeId);

      if (history.length === 0) {
        console.log(`      ⚠️  No FEC history for ${committeeId}`);
        continue;
      }

      // Insert designation records
      for (const record of history) {
        const designation = {
          committee_id: committeeId,
          cycle: record.cycle,
          designation: record.designation,
          designation_name: getDesignationName(record.designation),
          committee_type: record.committee_type,
          committee_type_name: getCommitteeTypeName(record.committee_type),
          committee_name: record.name,
          candidate_id: candidateId,
          source: 'fec_api'
        };

        const { error: insertError } = await supabase
          .from('committee_designations')
          .upsert(designation, { onConflict: 'committee_id,cycle' });

        if (!insertError) {
          totalDesignations++;
        }
      }

      console.log(`      ✅ ${committeeId}: ${history.length} cycles`);

      // Rate limit: 2 second delay between FEC API calls
      await sleep(2000);
    }

    // Save progress every 10 persons
    if (!DRY_RUN && (i + 1) % 10 === 0) {
      saveProgress({
        step: 'populate_designations',
        completed_index: i,
        total: persons.length,
        total_committees: totalCommittees,
        total_designations: totalDesignations,
        timestamp: new Date().toISOString()
      });
    }
  }

  console.log(`\n   Summary:`);
  console.log(`   📋 Committees processed: ${totalCommittees}`);
  console.log(`   📝 Designations created: ${totalDesignations}\n`);

  return { totalCommittees, totalDesignations };
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  console.log('='.repeat(80));
  console.log('BULK POPULATE POLITICAL PERSONS SYSTEM');
  if (DRY_RUN) console.log('[DRY RUN MODE - NO CHANGES WILL BE MADE]');
  if (RESUME) console.log('[RESUME MODE - CONTINUING FROM CHECKPOINT]');
  console.log('='.repeat(80));

  try {
    let startIndex = 0;
    let step = 'discover';

    // Load progress if resuming
    if (RESUME) {
      const progress = loadProgress();
      if (progress) {
        console.log(`\n📥 Resuming from checkpoint:`);
        console.log(`   Step: ${progress.step}`);
        console.log(`   Index: ${progress.completed_index + 1}/${progress.total}`);
        console.log(`   Timestamp: ${progress.timestamp}\n`);

        step = progress.step;
        startIndex = progress.completed_index + 1;
      } else {
        console.log(`\n⚠️  No checkpoint found, starting from beginning\n`);
      }
    }

    // Step 1: Discover candidates
    const candidates = await discoverActiveCandidates();

    // Step 2: Group into persons
    const persons = groupCandidatesIntoPersons(candidates);

    // Step 3: Create political_persons
    if (step === 'discover' || step === 'create_persons') {
      await createPoliticalPersons(persons, step === 'create_persons' ? startIndex : 0);
    }

    // Step 4: Populate committee designations
    if (!DRY_RUN) {
      if (step === 'discover' || step === 'create_persons' || step === 'populate_designations') {
        await populateCommitteeDesignations(persons, step === 'populate_designations' ? startIndex : 0);
      }
    }

    // Clean up progress file on successful completion
    if (!DRY_RUN && fs.existsSync(PROGRESS_FILE)) {
      fs.unlinkSync(PROGRESS_FILE);
      console.log('✅ Progress file cleaned up\n');
    }

    console.log('='.repeat(80));
    console.log('✅ BULK POPULATION COMPLETE!');
    console.log('='.repeat(80));

    if (DRY_RUN) {
      console.log('\nTo execute for real, run without --dry-run flag:');
      console.log('  SUPABASE_SERVICE_ROLE_KEY=xxx FEC_API_KEY=xxx node scripts/bulk_populate_political_persons.js');
    } else {
      console.log('\nNext steps:');
      console.log('1. Verify data in Supabase dashboard');
      console.log('2. Test search functionality with various candidates');
      console.log('3. Monitor for any missing persons or data issues');
    }

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main().catch(console.error);
