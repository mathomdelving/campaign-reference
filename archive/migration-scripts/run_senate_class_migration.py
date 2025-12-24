#!/usr/bin/env python3
"""
Run the senate_class column migration.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read the migration SQL
migration_path = "sql/add_senate_class_column.sql"

print(f"Running migration: {migration_path}")

# Note: Supabase Python client doesn't support raw SQL execution for DDL
# We need to use the SQL editor in Supabase dashboard or use psycopg2

print("\n" + "="*70)
print("IMPORTANT: SQL Migration Instructions")
print("="*70)
print("\nThe Supabase Python client doesn't support DDL operations.")
print("Please run the following SQL in your Supabase SQL Editor:")
print("\n" + "="*70)

with open(migration_path, 'r') as f:
    sql = f.read()
    print(sql)

print("="*70)
print("\nAfter running the SQL, run: python3 scripts/populate_senate_class.py")
print("="*70)
