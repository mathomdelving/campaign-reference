#!/usr/bin/env python3
"""
Load quarterly financial data into Supabase
"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError('Missing SUPABASE_URL or SUPABASE_KEY environment variables')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_quarterly_financials_table():
    """Create the quarterly_financials table if it doesn't exist"""
    print("Creating quarterly_financials table...")

    # Note: Supabase Python client doesn't support DDL directly
    # You need to run this SQL in the Supabase SQL Editor:
    sql = """
    CREATE TABLE IF NOT EXISTS quarterly_financials (
        id BIGSERIAL PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        name TEXT NOT NULL,
        party TEXT,
        state TEXT,
        district TEXT,
        office TEXT,
        cycle INTEGER NOT NULL,
        committee_id TEXT,
        filing_id BIGINT,
        report_type TEXT,
        coverage_start_date DATE,
        coverage_end_date DATE,
        total_receipts NUMERIC(12,2),
        total_disbursements NUMERIC(12,2),
        cash_beginning NUMERIC(12,2),
        cash_ending NUMERIC(12,2),
        is_amendment BOOLEAN,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Create indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_quarterly_candidate_id ON quarterly_financials(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_quarterly_cycle ON quarterly_financials(cycle);
    CREATE INDEX IF NOT EXISTS idx_quarterly_coverage_end ON quarterly_financials(coverage_end_date);
    CREATE INDEX IF NOT EXISTS idx_quarterly_state_district ON quarterly_financials(state, district);

    -- Add foreign key constraint to candidates table
    ALTER TABLE quarterly_financials
    ADD CONSTRAINT fk_quarterly_candidate
    FOREIGN KEY (candidate_id)
    REFERENCES candidates(candidate_id);
    """

    print("\nPlease run the following SQL in your Supabase SQL Editor:")
    print("=" * 80)
    print(sql)
    print("=" * 80)
    return sql

def load_quarterly_data():
    """Load quarterly financial data from JSON file"""
    print("\nLoading quarterly data from JSON...")

    # Load JSON file
    with open('quarterly_financials_2026.json', 'r') as f:
        data = json.load(f)

    print(f"Found {len(data)} quarterly records")

    # Insert data in batches
    BATCH_SIZE = 1000
    total_inserted = 0

    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]

        try:
            response = supabase.table('quarterly_financials').insert(batch).execute()
            total_inserted += len(batch)
            print(f"Inserted batch {i//BATCH_SIZE + 1}: {total_inserted}/{len(data)} records")
        except Exception as e:
            print(f"Error inserting batch {i//BATCH_SIZE + 1}: {e}")
            # Continue with next batch
            continue

    print(f"\nTotal records inserted: {total_inserted}")
    return total_inserted

if __name__ == '__main__':
    print("=" * 80)
    print("Quarterly Financials Data Loader")
    print("=" * 80)

    # Step 1: Show SQL to create table
    create_quarterly_financials_table()

    # Wait for user confirmation
    print("\n" + "=" * 80)
    response = input("Have you created the table in Supabase? (yes/no): ")

    if response.lower() == 'yes':
        # Step 2: Load data
        load_quarterly_data()
        print("\n✓ Quarterly data loaded successfully!")
    else:
        print("\nPlease create the table first, then run this script again.")
