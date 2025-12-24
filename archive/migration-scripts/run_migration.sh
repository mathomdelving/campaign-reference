#!/bin/bash

# ============================================================================
# Run Database Migration - Political Persons System
# ============================================================================
# This script helps you run the political persons migration.
#
# Usage:
#   ./scripts/run_migration.sh [migrate|rollback|populate|verify]
#
# Commands:
#   migrate   - Run the migration SQL
#   rollback  - Undo the migration
#   populate  - Populate initial data (requires migration to be run first)
#   verify    - Check migration status
# ============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

MIGRATION_FILE="$PROJECT_ROOT/sql/migrations/001_create_political_persons.sql"
ROLLBACK_FILE="$PROJECT_ROOT/sql/migrations/001_rollback_political_persons.sql"
POPULATE_SCRIPT="$PROJECT_ROOT/scripts/populate_political_persons.js"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required environment variables
check_env() {
    if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
        echo -e "${RED}Error: NEXT_PUBLIC_SUPABASE_URL not set${NC}"
        echo "Set it in apps/labs/.env.local or export it"
        exit 1
    fi

    if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] && [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
        echo -e "${RED}Error: SUPABASE_SERVICE_ROLE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY not set${NC}"
        echo "Set it in apps/labs/.env.local or export it"
        exit 1
    fi
}

# Load environment variables from .env.local if it exists
load_env() {
    if [ -f "$PROJECT_ROOT/apps/labs/.env.local" ]; then
        echo -e "${GREEN}Loading environment from apps/labs/.env.local${NC}"
        set -a
        source "$PROJECT_ROOT/apps/labs/.env.local"
        set +a
    fi
}

# Run migration
run_migrate() {
    echo -e "${GREEN}Running migration: 001_create_political_persons${NC}"
    echo ""
    echo "This will create:"
    echo "  - political_persons table"
    echo "  - committee_designations table"
    echo "  - person_id column in candidates table"
    echo "  - principal_committees view"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi

    echo ""
    echo "Please run the migration manually via Supabase Dashboard:"
    echo "1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql"
    echo "2. Copy the contents of: $MIGRATION_FILE"
    echo "3. Paste and execute the SQL"
    echo ""
    echo "Or use psql if you have direct database access."
}

# Run rollback
run_rollback() {
    echo -e "${YELLOW}WARNING: This will delete all political_persons data!${NC}"
    echo ""
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi

    echo ""
    echo "Please run the rollback manually via Supabase Dashboard:"
    echo "1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql"
    echo "2. Copy the contents of: $ROLLBACK_FILE"
    echo "3. Paste and execute the SQL"
}

# Populate data
run_populate() {
    echo -e "${GREEN}Populating political persons data${NC}"
    echo ""
    echo "This will:"
    echo "  - Create person records for Sherrod Brown and Ruben Gallego"
    echo "  - Link their candidate_ids"
    echo "  - Fetch committee designations from FEC API"
    echo ""
    echo "Note: This may take several minutes due to API rate limits"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi

    cd "$PROJECT_ROOT"
    node "$POPULATE_SCRIPT"
}

# Verify migration
run_verify() {
    echo -e "${GREEN}Migration status check${NC}"
    echo ""
    echo "Please run these queries in Supabase Dashboard to verify:"
    echo ""
    echo "-- Check political_persons table exists"
    echo "SELECT COUNT(*) as person_count FROM political_persons;"
    echo ""
    echo "-- Check candidates with person_id"
    echo "SELECT COUNT(*) as linked_candidates FROM candidates WHERE person_id IS NOT NULL;"
    echo ""
    echo "-- Check committee designations"
    echo "SELECT COUNT(*) as designation_count FROM committee_designations;"
    echo ""
    echo "-- View Sherrod Brown's principal committees"
    echo "SELECT * FROM principal_committees WHERE person_id = 'sherrod-brown-oh' ORDER BY cycle;"
}

# Main
main() {
    load_env
    check_env

    case "${1:-}" in
        migrate)
            run_migrate
            ;;
        rollback)
            run_rollback
            ;;
        populate)
            run_populate
            ;;
        verify)
            run_verify
            ;;
        *)
            echo "Usage: $0 [migrate|rollback|populate|verify]"
            echo ""
            echo "Commands:"
            echo "  migrate   - Run the migration SQL"
            echo "  rollback  - Undo the migration"
            echo "  populate  - Populate initial data"
            echo "  verify    - Check migration status"
            exit 1
            ;;
    esac
}

main "$@"
