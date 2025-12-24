#!/usr/bin/env python3
import requests, os, json
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

r = requests.get(
    f'{SUPABASE_URL}/rest/v1/quarterly_financials',
    params={'candidate_id': 'eq.H0CA25154', 'cycle': 'eq.2022', 'select': '*', 'order': 'id.desc', 'limit': 5},
    headers=headers
)

print(json.dumps(r.json(), indent=2))
