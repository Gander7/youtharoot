#!/bin/bash

# PostgreSQL Database Backup Script with Best Practices
# Usage: ./backup_db.sh [options]
# Options:
#   --format custom    Use custom format (recommended for large DBs)
#   --format plain     Use plain SQL format (default, human readable)
#   --compress         Force compression regardless of format
#   --retention DAYS   Keep backups for N days (default: 30)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Default configuration
BACKUP_FORMAT="plain"
FORCE_COMPRESS=false
RETENTION_DAYS=30
VERBOSE=false

# Parse command line options
while [[ $# -gt 0 ]]; do
    case $1 in
        --format)
            BACKUP_FORMAT="$2"
            shift 2
            ;;
        --compress)
            FORCE_COMPRESS=true
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--format plain|custom] [--compress] [--retention DAYS] [--verbose]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Validate DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo "❌ DATABASE_URL not found. Please set it in your .env file."
    exit 1
fi

# Check pg_dump version compatibility
echo "🔍 Checking PostgreSQL version compatibility..."
PG_DUMP_VERSION=$(pg_dump --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "📦 Local pg_dump version: $PG_DUMP_VERSION"

# Try to get server version (this might fail if connection issues exist)
SERVER_VERSION=$(psql "$DATABASE_URL" -t -c "SELECT version();" 2>/dev/null | grep -oE 'PostgreSQL [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+' || echo "unknown")
if [ "$SERVER_VERSION" != "unknown" ]; then
    echo "🗄️  Server PostgreSQL version: $SERVER_VERSION"
    
    # Compare major versions
    PG_DUMP_MAJOR=$(echo "$PG_DUMP_VERSION" | cut -d. -f1)
    SERVER_MAJOR=$(echo "$SERVER_VERSION" | cut -d. -f1)
    
    if [ "$PG_DUMP_MAJOR" -lt "$SERVER_MAJOR" ]; then
        echo "⚠️  WARNING: pg_dump version ($PG_DUMP_VERSION) is older than server ($SERVER_VERSION)"
        echo "💡 Consider upgrading PostgreSQL client tools:"
        echo "   sudo apt update && sudo apt install postgresql-client-$SERVER_MAJOR"
        echo ""
        echo "🤔 Do you want to continue anyway? (This might fail) [y/N]"
        read -r CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            echo "❌ Backup cancelled due to version mismatch"
            exit 1
        fi
    fi
else
    echo "⚠️  Could not determine server version (connection might be needed)"
fi

# Set backup directory
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Set backup filename based on format
if [ "$BACKUP_FORMAT" = "custom" ]; then
    BACKUP_FILE="$BACKUP_DIR/youtharoot_backup_$TIMESTAMP.dump"
    BACKUP_EXTENSION="dump"
else
    BACKUP_FILE="$BACKUP_DIR/youtharoot_backup_$TIMESTAMP.sql"
    BACKUP_EXTENSION="sql"
fi

# Prepare pg_dump options
PG_DUMP_OPTS=(
    --verbose                    # Show progress
    --no-password               # Don't prompt for password (use URL)
    --lock-wait-timeout=60000   # Wait max 60s for locks
)

# Add format-specific options
if [ "$BACKUP_FORMAT" = "custom" ]; then
    PG_DUMP_OPTS+=(
        --format=custom          # Binary format, smaller, faster restore
        --compress=6             # Compression level 6 (good balance of size/speed)
        --no-owner              # Don't include ownership (better portability)
        --no-privileges         # Don't include privileges (avoid permission issues)
        # Note: For production use, consider:
        # --exclude-table-data for large log/session tables
        # --schema-only for schema-only backups
        # --data-only for data-only backups
    )
else
    PG_DUMP_OPTS+=(
        --format=plain           # SQL format, human readable
        --no-owner              # Don't include ownership commands
        --no-privileges         # Don't include privilege commands
        # Plain format is better for:
        # - Small databases
        # - Version control
        # - Manual inspection/editing
    )
fi

echo "🔄 Creating PostgreSQL backup..."
echo "📋 Database: $(echo "$DATABASE_URL" | sed 's/:\/\/.*@/:\/\/***@/')"
echo "📁 Format: $BACKUP_FORMAT"
echo "📄 File: $BACKUP_FILE"

# Create backup with error handling
echo "🔄 Running: pg_dump ${PG_DUMP_OPTS[*]} [DATABASE_URL]"
if pg_dump "${PG_DUMP_OPTS[@]}" "$DATABASE_URL" > "$BACKUP_FILE"; then
    echo "✅ Backup created successfully: $BACKUP_FILE"
    
    # Compress if plain format or forced
    if [ "$BACKUP_FORMAT" = "plain" ] || [ "$FORCE_COMPRESS" = true ]; then
        if [ "$BACKUP_FORMAT" = "plain" ]; then
            echo "📦 Compressing backup..."
            gzip "$BACKUP_FILE"
            BACKUP_FILE="$BACKUP_FILE.gz"
            echo "✅ Backup compressed: $BACKUP_FILE"
        fi
    fi
    
    # Show backup info
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "📊 Backup size: $BACKUP_SIZE"
    echo "📍 Location: $(realpath "$BACKUP_FILE")"
    
    # Test backup integrity (for custom format only)
    if [ "$BACKUP_FORMAT" = "custom" ]; then
        echo "🔍 Testing backup integrity..."
        if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
            echo "✅ Backup integrity verified"
        else
            echo "⚠️  Warning: Backup integrity check failed"
        fi
    fi
    
    # Clean up old backups
    if [ "$RETENTION_DAYS" -gt 0 ]; then
        echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
        find "$BACKUP_DIR" -name "youtharoot_backup_*" -type f -mtime +$RETENTION_DAYS -delete
        REMAINING_COUNT=$(find "$BACKUP_DIR" -name "youtharoot_backup_*" -type f | wc -l)
        echo "📦 $REMAINING_COUNT backup(s) remaining"
    fi
    
    echo "🎉 Backup completed successfully!"
    
else
    echo "❌ Backup failed!"
    # Clean up partial backup file
    [ -f "$BACKUP_FILE" ] && rm -f "$BACKUP_FILE"
    exit 1
fi