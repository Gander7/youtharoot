#!/bin/bash

# Working Backup Row Counter - Shows actual row counts per table
# Usage: ./show_backup_rows.sh <backup_file>

set -euo pipefail

BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/youtharoot_backup_20251013_154703.dump"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔍 Checking backup row counts..."

# Check if it's a custom format backup
if ! file "$BACKUP_FILE" | grep -q "PostgreSQL custom database dump" >/dev/null 2>&1; then
    echo "❌ This script only works with custom format backups (.dump files)"
    exit 1
fi

# Create a unique temporary database name
TEMP_DB="temp_backup_verify_$(date +%s)_$$"
echo "🔧 Creating temporary database: $TEMP_DB"

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
    echo "❌ DATABASE_URL not found. Please set it in your .env file."
    exit 1
fi

# Extract connection details
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*://[^@]*@\([^:/]*\).*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*://[^@]*@[^:]*:\([0-9]*\)/.*|\1|p')
DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')

# Set cleanup trap (with notification)
cleanup() {
    echo "🧹 Dropping temporary database: $TEMP_DB"
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -q -c "DROP DATABASE IF EXISTS \"$TEMP_DB\";" 2>/dev/null || true
}
trap cleanup EXIT

# Create temporary database (silently)
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -q -c "CREATE DATABASE \"$TEMP_DB\";" 2>/dev/null || {
    echo "❌ Failed to create temporary database"
    exit 1
}
# Restore backup to temporary database (quietly)
TEMP_DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$TEMP_DB"
pg_restore --no-owner --no-privileges --dbname="$TEMP_DATABASE_URL" "$BACKUP_FILE" 2>/dev/null || {
    echo "❌ Failed to restore backup to temporary database"
    exit 1
}

# Get row counts from restored backup
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEMP_DB" -q -c "
SELECT 'events' as \"Table\", count(*) as \"Rows\" FROM events
UNION ALL
SELECT 'event_persons' as \"Table\", count(*) as \"Rows\" FROM event_persons  
UNION ALL
SELECT 'persons' as \"Table\", count(*) as \"Rows\" FROM persons
UNION ALL
SELECT 'users' as \"Table\", count(*) as \"Rows\" FROM users
ORDER BY \"Table\";
" 2>/dev/null