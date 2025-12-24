#!/bin/bash
#
# Auto-Chain Remaining Cycles After 2022 Completes
# =================================================
# This script monitors the 2022 data collection process and automatically
# starts the remaining cycles (2024, 2020, 2018) when 2022 completes.
#
# Usage:
#   ./auto_chain_remaining_cycles.sh
#

# PID of the running 2024 collection process (will be set when started)
PID_2024=""

echo "================================================================================"
echo "AUTO-CHAIN MONITOR - Waiting for 2024 to Complete"
echo "================================================================================"
echo "Started: $(date)"
echo ""
echo "When 2024 completes, will automatically run:"
echo "  - Cycle 2022 (~10 hours)"
echo "  - Cycle 2020 (~10 hours)"
echo "  - Cycle 2018 (~10 hours)"
echo ""
echo "Total estimated time: ~30 hours"
echo "================================================================================"
echo ""

# Run all cycles in chronological order
echo "================================================================================"
echo "STARTING ALL CYCLES IN ORDER: 2024, 2022, 2020, 2018"
echo "================================================================================"
echo "Started: $(date)"
echo ""

# Run the chain script with all cycles in chronological order
./run_all_historical_cycles.sh 2024 2022 2020 2018

echo ""
echo "================================================================================"
echo "ALL CYCLES COMPLETE!"
echo "================================================================================"
echo "Total completion time: $(date)"
echo ""
echo "Next steps:"
echo "  1. Validate data quality for all cycles"
echo "  2. Check benchmark candidates (Fetterman, Oz, Ryan, etc.)"
echo "  3. Verify frontend displays historical data correctly"
echo "================================================================================"
