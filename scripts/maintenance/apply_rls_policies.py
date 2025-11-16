#!/usr/bin/env python3
"""
Apply Row Level Security policies to protect database from unauthorized modifications.

This script:
1. Enables RLS on all public tables
2. Creates policies that allow public READ but only service role can WRITE
3. Protects data integrity while keeping campaign finance data publicly viewable
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Service role key required

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_sql_file(filepath):
    """Read and execute SQL file."""
    print(f"Reading SQL from {filepath}...")
    with open(filepath, 'r') as f:
        sql = f.read()

    # Split into individual statements (basic split on semicolons)
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    print(f"\nExecuting {len(statements)} SQL statements...\n")

    errors = []
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            continue

        try:
            # Show what we're doing
            first_line = statement.split('\n')[0][:80]
            print(f"{i}. {first_line}...")

            result = supabase.rpc('exec_sql', {'query': statement}).execute()
            print(f"   ✓ Success")

        except Exception as e:
            error_msg = str(e)[:200]
            print(f"   ⚠️  Error: {error_msg}")
            errors.append((statement[:100], error_msg))

    return errors

def main():
    print("=" * 80)
    print("APPLYING ROW LEVEL SECURITY POLICIES")
    print("=" * 80)
    print("\nThis will:")
    print("  1. Enable RLS on all public tables")
    print("  2. Allow public READ access (SELECT)")
    print("  3. Block public WRITE access (INSERT/UPDATE/DELETE)")
    print("  4. Only allow writes from service role (your backend scripts)")
    print("\n" + "=" * 80)

    # Check we have service role key
    if not SUPABASE_KEY:
        print("❌ ERROR: SUPABASE_KEY not found in .env")
        print("This requires the service_role key, not the anon key.")
        return

    # Find the SQL file
    sql_file = os.path.join(os.path.dirname(__file__), '../../sql/enable_rls_policies.sql')

    if not os.path.exists(sql_file):
        print(f"❌ ERROR: SQL file not found at {sql_file}")
        return

    # Run the SQL
    errors = run_sql_file(sql_file)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if errors:
        print(f"⚠️  Completed with {len(errors)} errors:")
        for stmt, error in errors[:3]:
            print(f"\n  Statement: {stmt}...")
            print(f"  Error: {error}")
        if len(errors) > 3:
            print(f"\n  ... and {len(errors) - 3} more errors")
    else:
        print("✅ All RLS policies applied successfully!")
        print("\nYour database is now protected:")
        print("  ✓ Public can READ all campaign finance data")
        print("  ✓ Public CANNOT modify data")
        print("  ✓ Only service role (backend scripts) can write")
        print("\nSupabase security warnings should now be resolved.")

if __name__ == "__main__":
    main()
