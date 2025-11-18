#!/usr/bin/env node

/**
 * Populate Political Persons System
 *
 * This script:
 * 1. Creates political_persons records
 * 2. Links candidate_ids to persons
 * 3. Fetches committee designations from FEC API
 * 4. Populates committee_designations table
 *
 * Usage:
 *   node scripts/populate_political_persons.js
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('Missing Supabase credentials');
  console.error('Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// ============================================================================
// INITIAL DATA - Manually curated political persons
// ============================================================================

const INITIAL_PERSONS = [
  {
    person_id: 'sherrod-brown-oh',
    display_name: 'Sherrod Brown',
    first_name: 'Sherrod',
    last_name: 'Brown',
    party: 'DEM',
    state: 'OH',
    district: null,
    current_office: 'S',
    is_incumbent: false, // Lost 2024 election
    candidate_ids: ['H2OH13033', 'S6OH00163', 'S6OH00379'],
    notes: 'Former House member (OH-13), Senator 2007-2025, running for Senate again in 2026'
  },
  {
    person_id: 'ruben-gallego-az',
    display_name: 'Ruben Gallego',
    first_name: 'Ruben',
    last_name: 'Gallego',
    party: 'DEM',
    state: 'AZ',
    district: null,
    current_office: 'S',
    is_incumbent: true,
    candidate_ids: ['H4AZ07098', 'S4AZ00304'], // Placeholder - need to verify
    notes: 'Former House member (AZ-07), elected to Senate in 2024'
  }
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function slugify(name, state) {
  return `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${state.toLowerCase()}`;
}

async function fetchCommitteeHistory(committeeId, retries = 3) {
  const apiKey = process.env.FEC_API_KEY || 'DEMO_KEY';
  const url = `https://api.open.fec.gov/v1/committee/${committeeId}/history/?api_key=${apiKey}&per_page=100`;

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);

      if (response.status === 429) {
        console.log(`      Rate limited, waiting 60s... (attempt ${i + 1}/${retries})`);
        await sleep(60000);
        continue;
      }

      if (!response.ok) {
        console.log(`      HTTP ${response.status}, waiting 5s...`);
        await sleep(5000);
        continue;
      }

      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error(`      Error: ${error.message}`);
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

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

async function createPoliticalPerson(personData) {
  const { candidate_ids, ...personRecord } = personData;

  console.log(`\nCreating person: ${personRecord.person_id}`);

  // 1. Insert political_persons record
  const { data: person, error: personError } = await supabase
    .from('political_persons')
    .upsert(personRecord, { onConflict: 'person_id' })
    .select()
    .single();

  if (personError) {
    console.error(`  ❌ Error creating person: ${personError.message}`);
    return false;
  }

  console.log(`  ✅ Created person: ${person.display_name}`);

  // 2. Link candidate_ids to person
  for (const candidateId of candidate_ids) {
    const { error: linkError } = await supabase
      .from('candidates')
      .update({ person_id: personRecord.person_id })
      .eq('candidate_id', candidateId);

    if (linkError) {
      console.error(`  ❌ Error linking ${candidateId}: ${linkError.message}`);
    } else {
      console.log(`  ✅ Linked ${candidateId} → ${personRecord.person_id}`);
    }
  }

  return true;
}

async function populateCommitteeDesignations(personData) {
  console.log(`\n📋 Fetching committee designations for: ${personData.display_name}`);

  // Get all committees for this person's candidates
  const { data: committees, error: committeesError } = await supabase
    .from('quarterly_financials')
    .select('committee_id, candidate_id')
    .in('candidate_id', personData.candidate_ids)
    .not('committee_id', 'is', null);

  if (committeesError) {
    console.error(`  ❌ Error fetching committees: ${committeesError.message}`);
    return;
  }

  // Get unique committees
  const uniqueCommittees = new Map();
  committees.forEach(c => {
    if (!uniqueCommittees.has(c.committee_id)) {
      uniqueCommittees.set(c.committee_id, c.candidate_id);
    }
  });

  console.log(`  Found ${uniqueCommittees.size} unique committees`);

  // Fetch history for each committee from FEC API
  for (const [committeeId, candidateId] of uniqueCommittees.entries()) {
    console.log(`\n  Committee ${committeeId}:`);

    const history = await fetchCommitteeHistory(committeeId);

    if (history.length === 0) {
      console.log(`    ⚠️  No FEC history found`);
      continue;
    }

    console.log(`    Found ${history.length} cycle(s) in FEC history`);

    // Insert designation records for each cycle
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

      if (insertError) {
        console.error(`      ❌ Error inserting ${record.cycle}: ${insertError.message}`);
      } else {
        const isPrincipal = record.designation === 'P' ? '⭐' : '  ';
        console.log(`      ${isPrincipal} ${record.cycle}: ${getDesignationName(record.designation)}`);
      }
    }

    // Rate limit: Wait between committee API calls
    await sleep(2000);
  }
}

async function verifyResults(personId) {
  console.log(`\n🔍 Verifying results for ${personId}:`);

  // Count linked candidates
  const { count: candidateCount } = await supabase
    .from('candidates')
    .select('*', { count: 'exact', head: true })
    .eq('person_id', personId);

  console.log(`  Linked candidates: ${candidateCount}`);

  // Count committee designations
  const { data: candidates } = await supabase
    .from('candidates')
    .select('candidate_id')
    .eq('person_id', personId);

  const candidateIds = candidates?.map(c => c.candidate_id) || [];

  const { count: committeeCount } = await supabase
    .from('committee_designations')
    .select('*', { count: 'exact', head: true })
    .in('candidate_id', candidateIds);

  console.log(`  Committee designation records: ${committeeCount}`);

  // Show principal committees
  const { data: principalCommittees } = await supabase
    .from('principal_committees')
    .select('*')
    .eq('person_id', personId)
    .order('cycle', { ascending: true });

  if (principalCommittees && principalCommittees.length > 0) {
    console.log(`  Principal committees:`);
    principalCommittees.forEach(pc => {
      console.log(`    ${pc.cycle}: ${pc.committee_id} (${pc.committee_name})`);
    });
  }
}

async function main() {
  console.log('='.repeat(80));
  console.log('POPULATE POLITICAL PERSONS SYSTEM');
  console.log('='.repeat(80));

  for (const personData of INITIAL_PERSONS) {
    const success = await createPoliticalPerson(personData);

    if (success) {
      await populateCommitteeDesignations(personData);
      await verifyResults(personData.person_id);
    }

    console.log('\n' + '-'.repeat(80));
  }

  console.log('\n✅ Population complete!');
  console.log('\nNext steps:');
  console.log('1. Verify data in Supabase dashboard');
  console.log('2. Update search UI to query political_persons');
  console.log('3. Update data fetching to use person_id');
}

// ============================================================================
// RUN
// ============================================================================

main().catch(console.error);
