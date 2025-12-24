#!/usr/bin/env python3
"""
Clean up old cycle data from Supabase
Keeps only 2024 and 2026 cycles
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Prefer': 'count=exact'
}

print("=" * 100)
print("SUPABASE CLEANUP: Remove 2018, 2020, 2022 Cycle Data")
print("=" * 100)

# First, show what will be deleted
print("\n1. PREVIEW: What will be deleted")
print("-" * 100)

cycles_to_delete = [2018, 2020, 2022]
total_to_delete = 0

for cycle in cycles_to_delete:
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?cycle=eq.{cycle}&limit=1"
    response = requests.get(url, headers=headers, timeout=10)

    if 'content-range' in response.headers:
        count = int(response.headers['content-range'].split('/')[-1])
        total_to_delete += count
        print(f"  Cycle {cycle}: {count:,} records")

print(f"\nTotal records to delete: {total_to_delete:,}")

# Show what will be kept
print("\n2. PREVIEW: What will be KEPT")
print("-" * 100)

cycles_to_keep = [2024, 2026]
total_to_keep = 0

for cycle in cycles_to_keep:
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?cycle=eq.{cycle}&limit=1"
    response = requests.get(url, headers=headers, timeout=10)

    if 'content-range' in response.headers:
        count = int(response.headers['content-range'].split('/')[-1])
        total_to_keep += count
        print(f"  Cycle {cycle}: {count:,} records")

print(f"\nTotal records to keep: {total_to_keep:,}")

# Ask for confirmation
print("\n" + "=" * 100)
print("CONFIRMATION REQUIRED")
print("=" * 100)
print(f"\nThis will DELETE {total_to_delete:,} records for cycles 2018, 2020, and 2022.")
print(f"This will KEEP {total_to_keep:,} records for cycles 2024 and 2026.")
print("\nThis action CANNOT be undone!")

response = input("\nType 'DELETE' to proceed: ")

if response != 'DELETE':
    print("\n❌ Deletion cancelled. No changes made.")
    exit(0)

# Proceed with deletion
print("\n3. DELETING OLD CYCLE DATA")
print("-" * 100)

delete_headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Prefer': 'return=minimal'
}

deleted_total = 0

for cycle in cycles_to_delete:
    print(f"\nDeleting cycle {cycle}...")

    # Delete in the URL with filter
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?cycle=eq.{cycle}"

    try:
        response = requests.delete(url, headers=delete_headers, timeout=60)

        if response.status_code in [200, 201, 204]:
            print(f"  ✓ Cycle {cycle} deleted")
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:200]}")

# Verify deletion
print("\n4. VERIFICATION")
print("-" * 100)

for cycle in cycles_to_delete:
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?cycle=eq.{cycle}&limit=1"
    response = requests.get(url, headers=headers, timeout=10)

    if 'content-range' in response.headers:
        count = int(response.headers['content-range'].split('/')[-1])
        if count == 0:
            print(f"  ✓ Cycle {cycle}: 0 records (deleted successfully)")
        else:
            print(f"  ⚠️  Cycle {cycle}: {count:,} records remaining")

print("\n" + "=" * 100)
print("CLEANUP COMPLETE")
print("=" * 100)
print("\nRemaining data:")
for cycle in cycles_to_keep:
    url = f"{SUPABASE_URL}/rest/v1/quarterly_financials?cycle=eq.{cycle}&limit=1"
    response = requests.get(url, headers=headers, timeout=10)

    if 'content-range' in response.headers:
        count = int(response.headers['content-range'].split('/')[-1])
        print(f"  ✓ Cycle {cycle}: {count:,} records")

print("\n✅ Database cleaned! Only 2024 and 2026 data remains.")
