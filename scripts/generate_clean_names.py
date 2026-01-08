import re
import json
import os

# Set of honorifics/prefixes to remove (case-insensitive checking)
HONORIFICS = {
    'MR', 'MRS', 'MS', 'DR', 'HON', 'THE HON', 'REV', 'FR', 'PROF', 'GEN', 'CPT',
    'MAJ', 'LT', 'COL', 'SGT', 'AMB', 'GOV', 'SEN', 'REP', 'PRES'
}

# Set of valid suffixes to keep
SUFFIXES = {
    'JR', 'SR', 'II', 'III', 'IV', 'V', 'ESQ', 'MD', 'DDS', 'PHD'
}

# =============================================================================
# VERIFIED DISPLAY NAME OVERRIDES
# =============================================================================
# These are manually verified against Wikipedia/official sources.
# Format: candidate_id -> preferred display name
# Verified: January 2026
# =============================================================================
CANDIDATE_OVERRIDES = {
    # Senate - Leadership & Prominent Members
    "S4VT00033": "Bernie Sanders",           # SANDERS, BERNARD (I-VT)
    "S8NY00082": "Chuck Schumer",            # SCHUMER, CHARLES E. (D-NY)
    "S6IL00151": "Dick Durbin",              # DURBIN, RICHARD J. (D-IL)
    "S0IA00028": "Chuck Grassley",           # GRASSLEY, CHARLES E (R-IA)
    "S4SC00240": "Tim Scott",                # SCOTT, TIMOTHY E. (R-SC)
    "S4LA00107": "Bill Cassidy",             # CASSIDY, WILLIAM M. (R-LA)
    "S4AR00103": "Tom Cotton",               # COTTON, THOMAS (R-AR)
    "S2VA00142": "Tim Kaine",                # KAINE, TIMOTHY MICHAEL (D-VA)
    "S2CT00132": "Chris Murphy",             # MURPHY, CHRISTOPHER S (D-CT)
    "S2NC00505": "Ted Budd",                 # BUDD, THEODORE P (R-NC)
    "S6NH00091": "Maggie Hassan",            # HASSAN, MARGARET WOOD (D-NH)
    "S0DE00092": "Chris Coons",              # COONS, CHRISTOPHER A. (D-DE)
    "S8DE00079": "Tom Carper",               # CARPER, THOMAS R. (D-DE, retired)
    "S4MA00028": "Ed Markey",                # MARKEY, EDWARD (D-MA)
    "S2TX00312": "Ted Cruz",                 # CRUZ, RAFAEL EDWARD TED (R-TX)

    # House - Leadership & Prominent Members
    "H6LA04138": "Mike Johnson",             # JOHNSON, JAMES MICHAEL (R-LA) - Speaker
    "H4MN06087": "Tom Emmer",                # EMMER, THOMAS EARL JR. (R-MN) - Majority Whip
    "H6OH04082": "Jim Jordan",               # JORDAN, JAMES D. (R-OH)
    "H2SC02042": "Jim Clyburn",              # CLYBURN, JAMES E. (D-SC)
    "H4MA03022": "Jim McGovern",             # MCGOVERN, JAMES P (D-MA)
    "H8IL14067": "Bill Foster",              # FOSTER, G. WILLIAM (BILL) (D-IL)
    "H8TX02166": "Dan Crenshaw",             # CRENSHAW, DANIEL (R-TX)
    "H8VA11062": "Gerry Connolly",           # CONNOLLY, GERALD EDWARD (D-VA)
    "H6WY00159": "Liz Cheney",               # CHENEY, ELIZABETH MRS. (R-WY)
    "H6NC13129": "Ted Budd",                 # BUDD, THEODORE P. (R-NC, House version)
    "H2CT02112": "Joe Courtney",             # COURTNEY, JOSEPH (D-CT)
    "H2MI05119": "Dan Kildee",               # KILDEE, DANIEL T (D-MI)
    "H8CA04152": "Tom McClintock",           # MCCLINTOCK, THOMAS (R-CA)
    "H6NY03247": "Tom Suozzi",               # SUOZZI, THOMAS (D-NY)

    # President
    "P80000722": "Joe Biden",                # BIDEN, JOSEPH R JR (D)
}

def parse_yaml_legislators(filepath):
    """
    Rudimentary YAML parser specifically for legislators-current.yaml
    Extracts mappings from FEC ID to Official Name.
    """
    fec_map = {}
    
    current_fec_ids = []
    current_name = None
    in_fec_block = False
    in_name_block = False
    
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Skipping legislators mapping.")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        stripped = line.strip()
        
        # New record starts with "- id:"
        if stripped.startswith('- id:'):
            current_fec_ids = []
            current_name = None
            in_fec_block = False
            in_name_block = False
            continue
            
        # Check for 'fec:'
        if stripped.startswith('fec:'):
            in_fec_block = True
            in_name_block = False
            val = stripped.split('fec:', 1)[1].strip()
            if val:
                val = val.replace('[', '').replace(']', '')
                ids = [x.strip() for x in val.split(',') if x.strip()]
                current_fec_ids.extend(ids)
            continue
            
        # Check for 'name:'
        if stripped.startswith('name:'):
            in_name_block = True
            in_fec_block = False
            continue
            
        # Capture FEC IDs in list
        if in_fec_block and stripped.startswith('- '):
            fec_id = stripped[2:].strip()
            current_fec_ids.append(fec_id)
            continue
            
        # Capture Official Name
        if in_name_block:
            if stripped.startswith('official_full:'):
                name = stripped.split('official_full:', 1)[1].strip()
                if name:
                    for fid in current_fec_ids:
                        fec_map[fid] = name
                    current_name = name
                
    return fec_map

def clean_word(word):
    """
    Capitalizes a word correctly, handling hyphens and Mc/Mac prefixes.
    e.g. "VALDEZ-ORTEGA" -> "Valdez-Ortega"
         "MCDONALD" -> "McDonald"
         "O'NEILL" -> "O'Neill"
    """
    if not word: 
        return ""
        
    # Handle Hyphens first: Split, process each part, rejoin
    if '-' in word:
        return '-'.join([clean_word(part) for part in word.split('-')])
    
    # Handle Parentheses: "First (Nick)"
    if '(' in word or ')' in word:
        # Just remove them for cleaner look? Or keep them formatted?
        # User example didn't specify, but standard is usually "Bill Foster" not "G. William (Bill)"
        # So maybe we should strip nicknames if they are in parentheses?
        # Let's clean the content inside.
        return word.title() # Placeholder for complex nickname logic, handled in title_case main loop
        
    # Basic Title Case
    cleaned = word.capitalize()
    
    # Handle Mc/Mac
    if cleaned.startswith('Mc') and len(cleaned) > 2:
        return 'Mc' + cleaned[2:].capitalize()
    # "Mac" is harder (Mack, Macy vs MacArthur). Skip to avoid errors.
    
    # Handle O' Apostrophe
    if cleaned.startswith("O'") and len(cleaned) > 2:
        return "O'" + cleaned[2:].capitalize()
        
    return cleaned

def title_case(text):
    """
    Heuristic name cleaner.
    Input: "VALDEZ-ORTEGA, ANIBAL MR."
    Output: "Anibal Valdez-Ortega"
    """
    if not text:
        return ""
        
    # 1. Remove explicit nickname patterns like "LAST, FIRST 'NICK'" or "LAST, FIRST (NICK)"
    # Actually, we might want to keep the nickname if it's the primary way they are known, 
    # but usually "First Last" is safest.
    # Let's strip content in quotes/parentheses if it looks like a nickname.
    
    text = text.replace('"', '').strip()
    
    # 2. Split by comma to identify Last vs First+Middle+Suffix
    parts = [p.strip() for p in text.split(',')]
    
    last_name_chunk = parts[0]
    rest_chunk = parts[1] if len(parts) > 1 else ""
    suffix_chunk = parts[2] if len(parts) > 2 else "" # Sometimes suffix is 3rd part
    
    # 3. Process Last Name
    last_name = clean_word(last_name_chunk)
    
    # 4. Process "Rest" (First, Middle, Honorifics, Suffixes mixed in)
    rest_words = rest_chunk.split()
    
    # Also grab words from suffix_chunk if it exists
    if suffix_chunk:
        rest_words.extend(suffix_chunk.split())
        
    # 5. Filter words in "Rest"
    cleaned_first_parts = []
    found_suffixes = []
    
    for word in rest_words:
        # Remove trailing periods for checking
        w_clean = word.replace('.', '').upper()
        
        # Check Honorifics (Remove)
        if w_clean in HONORIFICS:
            continue
            
        # Check Suffixes (Keep, but move to end)
        if w_clean in SUFFIXES:
            found_suffixes.append(word) # Keep original punctuation if any? Or standardize?
            continue
            
        # Check for single letters (Initials) - keep them
        # Check for parentheses (Nicknames)
        if word.startswith('(') and word.endswith(')'):
             # Extract nickname? "FOSTER, G. WILLIAM (BILL)" -> "Bill Foster"?
             # User said: "Jon Ossoff is listed as T. Jonathan Ossoff... allows users to search by common name"
             # "Bill Foster" is "FOSTER, G. WILLIAM (BILL)" in FEC.
             # If we detect a nickname, should we PREFER it?
             # That's risky for a heuristic. 
             # Let's just treat it as a middle name for now, or strip parens.
             clean_nick = clean_word(word.replace('(', '').replace(')', ''))
             cleaned_first_parts.append(f'"{clean_nick}"')
             continue
             
        # Normal Name Part
        cleaned_first_parts.append(clean_word(word))
        
    # Standardize suffixes
    clean_suffixes = [clean_word(s).replace('.', '') for s in found_suffixes] # remove periods for consistency? "Jr" vs "Jr."
    # Actually, "Jr." and "Sr." usually have dots. "III" does not.
    final_suffixes = []
    for s in clean_suffixes:
        if s in ['Jr', 'Sr']:
            final_suffixes.append(s + '.')
        else:
            final_suffixes.append(s)
            
    # 6. Assemble
    # "First Middle Last Suffix"
    
    full_first = " ".join(cleaned_first_parts)
    full_suffix = " ".join(final_suffixes)
    
    if full_suffix:
        return f"{full_first} {last_name} {full_suffix}"
    else:
        return f"{full_first} {last_name}"

def parse_cn_file(filepath, fec_map):
    candidates = []
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
        
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) < 10:
                continue
                
            cand_id = parts[0]
            raw_name = parts[1]
            party = parts[2]
            state = parts[4]
            office = parts[5]
            district = parts[6]
            
            # Priority 1: Use manual override (Highest Confidence - verified)
            if cand_id in CANDIDATE_OVERRIDES:
                clean_name = CANDIDATE_OVERRIDES[cand_id]
                source = "manual_override"
            # Priority 2: Use Legislators YAML (High Confidence)
            elif cand_id in fec_map:
                clean_name = fec_map[cand_id]
                source = "legislators_yaml"
            else:
                # Priority 3: Use Heuristic (Medium Confidence)
                clean_name = title_case(raw_name)
                source = "heuristic"
                
            candidates.append({
                "candidate_id": cand_id,
                "original_name": raw_name,
                "display_name": clean_name,
                "party": party,
                "state": state,
                "office": office,
                "district": district,
                "source": source
            })
            
    return candidates

def main():
    # Determine script location to find files relative to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    # 1. Download legislators.yaml if missing
    legislators_path = os.path.join(repo_root, 'legislators.yaml')
    if not os.path.exists(legislators_path):
        print("Downloading legislators.yaml...")
        os.system(f"curl -L -o {legislators_path} https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml")

    print("Parsing legislators.yaml...")
    fec_map = parse_yaml_legislators(legislators_path)
    print(f"Loaded {len(fec_map)} FEC ID mappings from legislators YAML.")
    print(f"Loaded {len(CANDIDATE_OVERRIDES)} manual display name overrides.")

    # 2. Process all FEC bulk data cycles
    cycles = ['2018', '2020', '2024', '2026']
    all_candidates = []
    seen_ids = set()  # Track unique candidate IDs

    for cycle in cycles:
        filepath = os.path.join(repo_root, 'fec_bulk_data', f'cn_{cycle}.txt')
        if os.path.exists(filepath):
            print(f"\nProcessing {filepath}...")
            candidates = parse_cn_file(filepath, fec_map)

            # Deduplicate - keep first occurrence (which has correct cycle info)
            new_candidates = []
            for c in candidates:
                if c['candidate_id'] not in seen_ids:
                    seen_ids.add(c['candidate_id'])
                    new_candidates.append(c)

            all_candidates.extend(new_candidates)
            print(f"  Added {len(new_candidates)} unique candidates from {cycle}.")
        else:
            print(f"Warning: {filepath} not found, skipping.")

    print(f"\nTotal unique candidates: {len(all_candidates)}")

    # 3. Report source breakdown
    sources = {}
    for c in all_candidates:
        src = c['source']
        sources[src] = sources.get(src, 0) + 1

    print("\nSource breakdown:")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count}")

    # 4. Validation / Suspicious Check
    print("\nValidating names...")
    suspicious = []
    for c in all_candidates:
        name = c['display_name']
        # Check for leftover honorifics
        for word in name.replace('.', '').split():
            if word.upper() in HONORIFICS:
                suspicious.append(f"{c['candidate_id']}: {name} (Contains {word})")

    if suspicious:
        print(f"Found {len(suspicious)} names with leftover honorifics:")
        for s in suspicious[:10]:
            print(f"  - {s}")
        if len(suspicious) > 10:
            print(f"  ... and {len(suspicious) - 10} more")
    else:
        print("No obvious leftover honorifics found.")

    # 5. Save output
    output_file = os.path.join(script_dir, 'candidates_clean_names.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_candidates, f, indent=2)

    print(f"\nSaved {len(all_candidates)} candidates to {output_file}")

if __name__ == "__main__":
    main()