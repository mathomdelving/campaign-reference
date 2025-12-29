#!/usr/bin/env python3
"""
Apply Name Overlay to Political Persons

This script updates the display_name field in the political_persons table
using a JSON overlay file. This allows correcting auto-generated names
(from FEC data like "T. Jonathan Ossoff") to their common names ("Jon Ossoff").

The overlay file is additive - it only updates names that are specified.
Run this script anytime to apply or update name corrections.

Usage:
    # Dry run (preview changes)
    python scripts/data-loading/apply_name_overlay.py --dry-run

    # Apply changes
    python scripts/data-loading/apply_name_overlay.py

Environment variables:
    SUPABASE_URL - Supabase project URL
    SUPABASE_KEY - Supabase service role key (for write access)
"""

import json
import os
import sys
from pathlib import Path

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Path to overlay file (relative to this script)
SCRIPT_DIR = Path(__file__).parent
OVERLAY_FILE = SCRIPT_DIR / "name_overlay.json"

def load_overlay():
    """Load the name overlay JSON file."""
    if not OVERLAY_FILE.exists():
        print(f"❌ Overlay file not found: {OVERLAY_FILE}")
        sys.exit(1)

    with open(OVERLAY_FILE, "r") as f:
        return json.load(f)

def apply_overlay(dry_run=False):
    """Apply name overlay to political_persons table."""
    try:
        from supabase import create_client
    except ImportError:
        print("❌ supabase-py not installed. Run: pip install supabase")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing environment variables:")
        print("   SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)")
        print("   SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY)")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    overlay = load_overlay()

    print("=" * 60)
    print("APPLY NAME OVERLAY TO POLITICAL PERSONS")
    if dry_run:
        print("[DRY RUN - NO CHANGES WILL BE MADE]")
    print("=" * 60)
    # Filter out metadata keys
    name_entries = {k: v for k, v in overlay.items() if not k.startswith("_")}

    print(f"\nOverlay file: {OVERLAY_FILE}")
    print(f"Total entries: {len(name_entries)}\n")

    updated = 0
    skipped = 0
    not_found = 0

    for person_id, display_name in overlay.items():
        # Skip metadata keys (those starting with underscore)
        if person_id.startswith("_"):
            continue

        # Check if person exists
        try:
            result = supabase.table("political_persons") \
                .select("person_id, display_name") \
                .eq("person_id", person_id) \
                .maybe_single() \
                .execute()
        except Exception as e:
            print(f"⚠️  Error querying {person_id}: {e}")
            not_found += 1
            continue

        if not result or not result.data:
            print(f"⚠️  Not found: {person_id}")
            not_found += 1
            continue

        current_name = result.data.get("display_name", "")

        if current_name == display_name:
            print(f"⏭️  Already correct: {person_id} → {display_name}")
            skipped += 1
            continue

        print(f"{'[DRY RUN] ' if dry_run else ''}✏️  {person_id}")
        print(f"      Before: {current_name}")
        print(f"      After:  {display_name}")

        if not dry_run:
            update_result = supabase.table("political_persons") \
                .update({"display_name": display_name}) \
                .eq("person_id", person_id) \
                .execute()

            if update_result.data:
                updated += 1
            else:
                print(f"      ❌ Update failed!")
        else:
            updated += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✏️  Updated:   {updated}")
    print(f"⏭️  Skipped:   {skipped}")
    print(f"⚠️  Not found: {not_found}")

    if dry_run:
        print("\nTo apply changes, run without --dry-run flag")

def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    apply_overlay(dry_run=dry_run)

if __name__ == "__main__":
    main()
