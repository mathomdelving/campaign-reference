#!/bin/bash

################################################################################
# FEC Data Backfill - Overnight Auto-Sequential Script
################################################################################
# This script will automatically run all remaining cycles (2024, 2022, 2020, 2018)
# sequentially, one after another. Safe to run overnight.
#
# Features:
# - Automatically chains cycles
# - Logs everything to backfill.log
# - Handles errors gracefully
# - Shows progress timestamps
#
# Usage: ./backfill_all_cycles_overnight.sh
################################################################################

# Configuration
LOGFILE="backfill_overnight.log"
PYTHON="python3"
SCRIPT="fetch_all_filings.py"
CYCLES=(2024 2022 2020 2018)

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOGFILE"
}

log_colored() {
    local color=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${color}[$timestamp] $message${NC}" | tee -a "$LOGFILE"
}

# Start message
clear
log_colored "$GREEN" "=========================================="
log_colored "$GREEN" "FEC BACKFILL - OVERNIGHT RUN STARTING"
log_colored "$GREEN" "=========================================="
log ""
log "Cycles to process: ${CYCLES[@]}"
log "Log file: $LOGFILE"
log "Started at: $(date)"
log ""

# Keep computer awake (macOS)
log_colored "$YELLOW" "Starting caffeinate to prevent sleep..."
caffeinate -i -w $$ &
CAFFEINATE_PID=$!
log "Caffeinate PID: $CAFFEINATE_PID"
log ""

# Track overall stats
TOTAL_START=$(date +%s)
COMPLETED_CYCLES=0
FAILED_CYCLES=0

# Process each cycle
for CYCLE in "${CYCLES[@]}"; do
    CYCLE_START=$(date +%s)

    log_colored "$YELLOW" "=========================================="
    log_colored "$YELLOW" "STARTING CYCLE $CYCLE"
    log_colored "$YELLOW" "=========================================="

    # Check if script exists
    if [ ! -f "$SCRIPT" ]; then
        log_colored "$RED" "ERROR: $SCRIPT not found!"
        FAILED_CYCLES=$((FAILED_CYCLES + 1))
        continue
    fi

    # Run the fetch script
    log "Executing: $PYTHON $SCRIPT --cycle $CYCLE"
    log ""

    $PYTHON $SCRIPT --cycle $CYCLE 2>&1 | tee -a "$LOGFILE"
    EXIT_CODE=${PIPESTATUS[0]}

    CYCLE_END=$(date +%s)
    CYCLE_DURATION=$((CYCLE_END - CYCLE_START))
    CYCLE_MINUTES=$((CYCLE_DURATION / 60))

    log ""
    if [ $EXIT_CODE -eq 0 ]; then
        log_colored "$GREEN" "✓ Cycle $CYCLE completed successfully"
        log_colored "$GREEN" "  Duration: ${CYCLE_MINUTES} minutes"
        COMPLETED_CYCLES=$((COMPLETED_CYCLES + 1))
    else
        log_colored "$RED" "✗ Cycle $CYCLE failed with exit code $EXIT_CODE"
        log_colored "$RED" "  Duration: ${CYCLE_MINUTES} minutes"
        FAILED_CYCLES=$((FAILED_CYCLES + 1))
    fi

    log ""

    # Brief pause between cycles
    if [ "$CYCLE" != "${CYCLES[-1]}" ]; then
        log "Waiting 10 seconds before next cycle..."
        sleep 10
        log ""
    fi
done

# Calculate total duration
TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))
TOTAL_HOURS=$((TOTAL_DURATION / 3600))
TOTAL_MINUTES=$(((TOTAL_DURATION % 3600) / 60))

# Final summary
log ""
log_colored "$GREEN" "=========================================="
log_colored "$GREEN" "BACKFILL COMPLETE"
log_colored "$GREEN" "=========================================="
log "Finished at: $(date)"
log "Total duration: ${TOTAL_HOURS}h ${TOTAL_MINUTES}m"
log "Cycles completed: $COMPLETED_CYCLES"
log "Cycles failed: $FAILED_CYCLES"
log ""

if [ $FAILED_CYCLES -eq 0 ]; then
    log_colored "$GREEN" "✓ All cycles completed successfully!"
else
    log_colored "$YELLOW" "⚠ Some cycles failed. Check log for details."
fi

log ""
log "Full log available at: $LOGFILE"
log_colored "$GREEN" "=========================================="

# Stop caffeinate
if [ ! -z "$CAFFEINATE_PID" ]; then
    kill $CAFFEINATE_PID 2>/dev/null
    log "Stopped caffeinate (PID: $CAFFEINATE_PID)"
fi

exit $FAILED_CYCLES
