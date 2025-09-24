#!/bin/bash

# PostgreSQL Database Backup Script
# Usage: ./backup_db.sh

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Set backup directory
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/youtharoot_backup_$TIMESTAMP.sql"

# Backup database
if [ -n "$DATABASE_URL" ]; then
    echo "🔄 Creating database backup..."
    pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Backup created successfully: $BACKUP_FILE"
        
        # Compress the backup
        gzip "$BACKUP_FILE"
        echo "📦 Backup compressed: $BACKUP_FILE.gz"
        
        # Show backup size
        ls -lh "$BACKUP_FILE.gz"
    else
        echo "❌ Backup failed!"
        exit 1
    fi
else
    echo "❌ DATABASE_URL not found. Please set it in your .env file."
    exit 1
fi