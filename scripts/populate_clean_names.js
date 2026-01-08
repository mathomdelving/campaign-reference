const { createClient } = require('../apps/labs/node_modules/@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// --- Configuration ---
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY;
const JSON_FILE_PATH = path.join(__dirname, 'candidates_clean_names.json');

// --- Validation ---
if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing required environment variables:');
  console.error('   NEXT_PUBLIC_SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

if (!fs.existsSync(JSON_FILE_PATH)) {
  console.error(`❌ Data file not found: ${JSON_FILE_PATH}`);
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// --- Helpers ---

/**
 * Generates a consistent slug from name and state.
 * e.g., "Anibal Valdez-Ortega", "CA" -> "anibal-valdez-ortega-ca"
 */
function generatePersonId(name, state) {
  if (!name) return null;
  
  const cleanName = name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // remove special chars except hyphens
    .replace(/\s+/g, '-')         // spaces to hyphens
    .replace(/-+/g, '-')          // collapse multiple hyphens
    .trim();

  return `${cleanName}-${state.toLowerCase()}`;
}

// --- Main ---

async function main() {
  console.log('🚀 Starting Political Persons population...');
  
  // 1. Load Data
  const rawData = fs.readFileSync(JSON_FILE_PATH, 'utf-8');
  const candidates = JSON.parse(rawData);
  console.log(`📄 Loaded ${candidates.length} candidates from JSON.`);

  // 2. Group by Person (Name + State) to handle duplicates
  //    (e.g., a candidate might have multiple IDs or filings)
  const personsMap = new Map();

  for (const c of candidates) {
    if (!c.display_name || !c.state) continue;

    const personId = generatePersonId(c.display_name, c.state);
    
    // If we haven't seen this person yet, initialize
    if (!personsMap.has(personId)) {
      personsMap.set(personId, {
        person_id: personId,
        display_name: c.display_name,
        // We can infer partial data, but let's keep it minimal for now
        // The table might have first_name/last_name columns, but display_name is key
        party: c.party,
        state: c.state,
        current_office: c.office, // We'll simple-overwrite with latest found
        candidate_ids: []
      });
    }

    // Add this candidate ID to the person's list (for linking later if needed)
    const person = personsMap.get(personId);
    person.candidate_ids.push(c.candidate_id);
    
    // Update office logic: Prefer 'S' (Senate) > 'H' (House) > 'P' 
    // If we find a Senate filing, upgrade them to Senate designation
    if (c.office === 'S' && person.current_office !== 'S') {
      person.current_office = 'S';
    }
  }

  const uniquePersons = Array.from(personsMap.values());
  console.log(`👥 Consolidated into ${uniquePersons.length} unique persons.`);

  // 3. Batch Upsert to Supabase
  //    We'll do this in chunks to avoid request size limits
  const BATCH_SIZE = 100;
  let successCount = 0;
  let errorCount = 0;

  for (let i = 0; i < uniquePersons.length; i += BATCH_SIZE) {
    const batch = uniquePersons.slice(i, i + BATCH_SIZE);
    
    // Prepare payload for `political_persons` table
    const upsertPayload = batch.map(p => ({
      person_id: p.person_id,
      display_name: p.display_name,
      party: p.party,
      state: p.state,
      current_office: p.current_office,
      updated_at: new Date().toISOString()
    }));

    // Perform Upsert
    const { error } = await supabase
      .from('political_persons')
      .upsert(upsertPayload, { onConflict: 'person_id' });

    if (error) {
      console.error(`❌ Error upserting batch ${i} - ${i + BATCH_SIZE}:`, error.message);
      errorCount += batch.length;
    } else {
      successCount += batch.length;
      
      // OPTIONAL: Link candidates to this person
      // This requires a second update to the 'candidates' table
      // Let's do it to ensure full integrity
      for (const p of batch) {
        if (p.candidate_ids.length > 0) {
           const { error: linkError } = await supabase
             .from('candidates')
             .update({ person_id: p.person_id })
             .in('candidate_id', p.candidate_ids);
             
           if (linkError) {
             console.error(`   ⚠️ Failed to link candidates for ${p.display_name}: ${linkError.message}`);
           }
        }
      }
    }

    // Simple progress log
    process.stdout.write(`\r✅ Processed ${Math.min(i + BATCH_SIZE, uniquePersons.length)} / ${uniquePersons.length} persons...`);
  }

  console.log('\n\n🏁 Finished!');
  console.log(`   Success: ${successCount}`);
  console.log(`   Errors:  ${errorCount}`);
}

main().catch(console.error);
