#!/usr/bin/env node

/**
 * Simple Political Persons Population Script
 *
 * This script:
 * 1. Reads ALL candidates from the candidates table
 * 2. Groups them by normalized name + state
 * 3. Creates political_persons records
 * 4. Links candidate_ids to person_id
 *
 * NO FEC API calls - just uses existing data!
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing environment variables:');
  console.error('   NEXT_PUBLIC_SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Extract name parts from a candidate name
 * "KELLY, MARK E" -> { firstName: "mark", lastName: "kelly" }
 * "SANDERS, BERNARD" -> { firstName: "bernard", lastName: "sanders" }
 */
function extractNameParts(name) {
  if (!name) return { firstName: '', lastName: '' };

  const cleaned = name
    .replace(/[^a-zA-Z\s,]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();

  if (cleaned.includes(',')) {
    // Format is "LAST, FIRST MIDDLE" - take first word of each
    const [last, first] = cleaned.split(',').map(s => s.trim());
    const firstName = first.split(' ')[0]; // Just first word, ignore middle names
    return { firstName, lastName: last };
  }

  // Format is "First Last" - split into parts
  const words = cleaned.split(' ').filter(Boolean);
  if (words.length >= 2) {
    return { firstName: words[0], lastName: words[words.length - 1] };
  }

  return { firstName: '', lastName: words[0] || '' };
}

/**
 * Generate a person_id slug from first name, last name, and state
 * Uses alphabetically first state if person appears in multiple states
 * "bernard", "sanders", ["VT", "NY"] -> "bernard-sanders-ny" (alphabetically first state)
 */
function generatePersonId(firstName, lastName, states) {
  const firstState = [...states].sort()[0]; // Alphabetically first
  return `${firstName}-${lastName}-${firstState.toLowerCase()}`;
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

    return `${titleCase(first)} ${titleCase(last)}`;
  }

  return name.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

async function getAllCandidates() {
  console.log('\n📊 Step 1: Loading all candidates...\n');

  let allCandidates = [];
  let offset = 0;
  const batchSize = 1000;

  while (true) {
    const { data: batch, error } = await supabase
      .from('candidates')
      .select('candidate_id, name, party, office, state, district')
      .not('name', 'is', null)
      .not('state', 'is', null)
      .range(offset, offset + batchSize - 1);

    if (error) {
      throw new Error(`Failed to query candidates: ${error.message}`);
    }

    if (!batch || batch.length === 0) break;

    allCandidates.push(...batch);
    offset += batchSize;

    process.stdout.write(`\r   Loaded ${allCandidates.length} candidates...`);

    if (batch.length < batchSize) break;
  }

  console.log(`\n   ✅ Total candidates: ${allCandidates.length}\n`);
  return allCandidates;
}

function groupCandidatesIntoPersons(candidates) {
  console.log('\n👥 Step 2: Grouping candidates into persons...\n');

  // Step 2a: Group by last name + state (to handle multi-state candidates properly)
  // This ensures people with same last name in different states are separate
  const lastNameStateGroups = new Map();

  for (const candidate of candidates) {
    const { lastName } = extractNameParts(candidate.name);
    const groupKey = `${lastName}-${candidate.state}`;

    if (!lastNameStateGroups.has(groupKey)) {
      lastNameStateGroups.set(groupKey, []);
    }

    lastNameStateGroups.get(groupKey).push(candidate);
  }

  // Step 2b: For each last name + state group, create person
  const personMap = new Map();

  for (const candidateGroup of lastNameStateGroups.values()) {
    // Use the first candidate record to get name parts
    const firstCandidate = candidateGroup[0];
    const { firstName, lastName } = extractNameParts(firstCandidate.name);

    // Collect all unique states (in case someone appears in multiple states with same last name)
    const states = new Set(candidateGroup.map(c => c.state));

    // Generate person_id using first candidate's first name + last name + alphabetically first state
    const personId = generatePersonId(firstName, lastName, states);

    personMap.set(personId, {
      person_id: personId,
      display_name: formatDisplayName(firstCandidate.name),
      first_name: null,
      last_name: null,
      party: firstCandidate.party,
      state: [...states].sort()[0], // Alphabetically first state
      district: null,
      current_office: firstCandidate.office,
      is_incumbent: false,
      candidate_ids: [],
      notes: states.size > 1 ? `Appeared in multiple states: ${[...states].sort().join(', ')}` : null
    });

    const person = personMap.get(personId);

    // Add all candidate IDs and update metadata
    for (const candidate of candidateGroup) {
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

      // Set district for House members (use first one found)
      if (candidate.office === 'H' && candidate.district && !person.district) {
        person.district = candidate.district;
      }
    }
  }

  const persons = Array.from(personMap.values());

  console.log(`   ✅ Created ${persons.length} unique persons`);
  console.log(`   📊 Average ${(candidates.length / persons.length).toFixed(1)} candidate IDs per person\n`);

  // Show some examples
  const multiCandidatePersons = persons.filter(p => p.candidate_ids.length > 1).slice(0, 5);
  if (multiCandidatePersons.length > 0) {
    console.log('   Examples of persons with multiple candidate IDs:');
    multiCandidatePersons.forEach(p => {
      console.log(`   - ${p.display_name} (${p.person_id}): ${p.candidate_ids.length} IDs`);
      if (p.notes) console.log(`     Note: ${p.notes}`);
    });
    console.log('');
  }

  // Show multi-state persons
  const multiStatePersons = persons.filter(p => p.notes?.includes('multiple states'));
  if (multiStatePersons.length > 0) {
    console.log(`   🌍 Found ${multiStatePersons.length} persons who appeared in multiple states:`);
    multiStatePersons.slice(0, 5).forEach(p => {
      console.log(`   - ${p.display_name} (${p.person_id}): ${p.notes}`);
    });
    console.log('');
  }

  return persons;
}

async function createPoliticalPersonsAndLink(persons) {
  console.log(`\n✍️  Step 3: Creating political_persons and linking candidates...\n`);

  let created = 0;
  let skipped = 0;
  let failed = 0;

  for (let i = 0; i < persons.length; i++) {
    const person = persons[i];
    const progress = ((i + 1) / persons.length * 100).toFixed(1);

    console.log(`[${i + 1}/${persons.length}] ${progress}% - ${person.display_name} (${person.state})`);

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

    // Small delay to avoid overwhelming Supabase
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  console.log(`\n   Summary:`);
  console.log(`   ✅ Created: ${created}`);
  console.log(`   ⏭️  Skipped: ${skipped}`);
  console.log(`   ❌ Failed: ${failed}\n`);

  return { created, skipped, failed };
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  console.log('='.repeat(80));
  console.log('SIMPLE POLITICAL PERSONS POPULATION');
  console.log('(No FEC API calls - just grouping existing candidates)');
  console.log('='.repeat(80));

  try {
    // Step 1: Load all candidates
    const candidates = await getAllCandidates();

    // Step 2: Group into persons
    const persons = groupCandidatesIntoPersons(candidates);

    // Step 3: Create political_persons and link
    await createPoliticalPersonsAndLink(persons);

    console.log('='.repeat(80));
    console.log('✅ POPULATION COMPLETE!');
    console.log('='.repeat(80));

    console.log('\nNext steps:');
    console.log('1. Test search for "Bernard Sanders" - should only show once now!');
    console.log('2. Verify data in Supabase dashboard');
    console.log('3. (Optional) Run FEC API script later to populate committee designations');

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main().catch(console.error);
