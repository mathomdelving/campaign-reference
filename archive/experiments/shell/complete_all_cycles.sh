#!/bin/bash

################################################################################
# Complete All Cycles - Full Backfill
################################################################################
# Runs all cycles sequentially to fetch ALL candidates (not just first 1,000)
################################################################################

echo "Waiting for 2024 to complete..."
while ps -p 8c112d > /dev/null 2>&1; do sleep 30; done

echo ""
echo "=========================================="
echo "Starting 2022 complete backfill at $(date)"
echo "=========================================="
python3 fetch_all_filings.py --cycle 2022

echo ""
echo "=========================================="
echo "Starting 2020 complete backfill at $(date)"
echo "=========================================="
python3 fetch_all_filings.py --cycle 2020

echo ""
echo "=========================================="
echo "Starting 2018 complete backfill at $(date)"
echo "=========================================="
python3 fetch_all_filings.py --cycle 2018

echo ""
echo "=========================================="
echo "ALL CYCLES COMPLETE at $(date)"
echo "=========================================="
