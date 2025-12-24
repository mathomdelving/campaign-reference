#!/bin/bash

################################################################################
# Chain remaining cycles (2020, 2018) after 2022 completes
################################################################################

echo "Waiting for 2022 to complete..."
wait

echo ""
echo "=========================================="
echo "Starting 2020 cycle at $(date)"
echo "=========================================="
python3 fetch_all_filings.py --cycle 2020

echo ""
echo "=========================================="
echo "Starting 2018 cycle at $(date)"
echo "=========================================="
python3 fetch_all_filings.py --cycle 2018

echo ""
echo "=========================================="
echo "ALL CYCLES COMPLETE at $(date)"
echo "=========================================="
