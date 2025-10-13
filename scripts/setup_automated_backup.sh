#!/bin/bash

# Automated Backup Setup Script
# This sets up automated daily backups using cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Setting up automated database backups..."
echo "📁 Project directory: $PROJECT_DIR"

# Create cron job entry
CRON_ENTRY="0 2 * * * cd $PROJECT_DIR && ./scripts/backup_db.sh --format custom --retention 7 >> $PROJECT_DIR/logs/backup.log 2>&1"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

echo "📋 Cron entry to be added:"
echo "   $CRON_ENTRY"
echo ""
echo "This will:"
echo "   ⏰ Run daily at 2:00 AM"
echo "   📦 Create custom format backups"  
echo "   🧹 Keep backups for 7 days"
echo "   📝 Log output to logs/backup.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup_db.sh"; then
    echo "⚠️  Backup cron job already exists. Current crontab:"
    crontab -l | grep backup_db.sh
    echo ""
    echo "🤔 Do you want to replace it? [y/N]"
    read -r REPLACE
    if [[ ! "$REPLACE" =~ ^[Yy]$ ]]; then
        echo "❌ Automated setup cancelled"
        exit 1
    fi
    # Remove existing backup entries
    crontab -l | grep -v backup_db.sh | crontab -
fi

# Add new cron job
echo "➕ Adding cron job..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Automated backup setup complete!"
echo ""
echo "📋 To verify:"
echo "   crontab -l"
echo ""
echo "📝 To check backup logs:"
echo "   tail -f $PROJECT_DIR/logs/backup.log"
echo ""
echo "🔄 To run manual backup now:"
echo "   cd $PROJECT_DIR && ./scripts/backup_db.sh --format custom --verbose"