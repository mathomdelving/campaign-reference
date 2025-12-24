#!/bin/bash
#
# Run All Historical Cycles Sequentially
# =======================================
# This script runs data collection for all historical cycles in order.
# Each cycle waits for the previous one to complete before starting.
#
# Usage:
#   ./run_all_historical_cycles.sh
#
# To run specific cycles only:
#   ./run_all_historical_cycles.sh 2024 2020 2018
#

set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

# Cycles to run (default: all remaining after 2022)
CYCLES="${@:-2024 2020 2018}"

echo "================================================================================"
echo "HISTORICAL FEC DATA COLLECTION - SEQUENTIAL RUN"
echo "================================================================================"
echo "Cycles to collect: $CYCLES"
echo "Started: $(date)"
echo "================================================================================"
echo ""

# Function to run a single cycle
run_cycle() {
    local cycle=$1
    local log_file="fetch_${cycle}_complete.log"

    echo ""
    echo "================================================================================"
    echo "STARTING CYCLE: $cycle"
    echo "================================================================================"
    echo "Time: $(date)"
    echo "Log file: $log_file"
    echo ""

    # Run the collection script
    python3 -u fetch_historical_complete.py --cycle $cycle > "$log_file" 2>&1

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Cycle $cycle completed successfully!"
        echo "   Finished: $(date)"
        echo ""
    else
        echo ""
        echo "❌ Cycle $cycle failed with exit code: $exit_code"
        echo "   Check log file: $log_file"
        echo ""
        return $exit_code
    fi
}

# Run each cycle sequentially
for cycle in $CYCLES; do
    run_cycle $cycle
done

echo ""
echo "================================================================================"
echo "ALL CYCLES COMPLETED"
echo "================================================================================"
echo "Finished: $(date)"
echo ""
echo "Summary of log files:"
for cycle in $CYCLES; do
    echo "  - fetch_${cycle}_complete.log"
done
echo ""
echo "Progress file: historical_collection_progress.json"
echo "================================================================================"
