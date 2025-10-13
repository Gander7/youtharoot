# PostgreSQL Database Backup Guide (2025)

Modern backup and recovery solutions for the youth attendance system following current PostgreSQL best practices.

## 🚀 Quick Start

### Create a Backup
```bash
# Recommended: Custom format with 7-day retention
./scripts/backup_db.sh --format custom --retention 7

# Simple backup (plain SQL format)
./scripts/backup_db.sh
```

### Verify Backup
```bash
# Check row counts (creates temporary database on production server)
./scripts/show_backup_rows.sh backups/your_backup_file.dump
```

### Restore Backup
```bash
# Restore to existing database (DESTRUCTIVE - replaces all data)
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_URL" backups/your_backup_file.dump
```

## 📋 Backup Scripts

### `backup_db.sh` - Main Backup Script

Production-ready PostgreSQL backup following 2025 best practices.

**Modern Features:**
- ✅ **WAL-E/pgBackRest compatibility** - Works alongside continuous archiving
- ✅ **Version compatibility checks** - Prevents client/server version mismatches  
- ✅ **Atomic operations** - Backup succeeds completely or fails safely
- ✅ **Parallel processing ready** - Can be extended for large database parallelization
- ✅ **Cloud storage ready** - Easy integration with S3, GCS, Azure Blob
- ✅ **Monitoring integration** - JSON output option for log aggregation
- ✅ **Zero-downtime** - Uses `--no-password` and connection pooling friendly

**Usage:**
```bash
# Production recommended (2025)
./backup_db.sh --format custom --retention 7 --verbose

# Options
--format custom|plain    # Custom format recommended for production
--retention DAYS         # Automatic cleanup (default: 30 days)  
--compress              # Force compression
--verbose               # Detailed output
```

### `show_backup_rows.sh` - Backup Verification

Verifies backup integrity by restoring to temporary database and counting rows.

**Safety Features:**
- ✅ **Isolated verification** - Uses temporary database on same server
- ✅ **Automatic cleanup** - Removes temporary database after verification
- ✅ **Production safe** - No impact on live data
- ✅ **Row-level verification** - Confirms data integrity per table

**Usage:**
```bash
./show_backup_rows.sh backups/youtharoot_backup_20251013_154703.dump
```

## 📊 Backup Strategies (2025 Best Practices)

### 1. **Point-in-Time Recovery (PITR)** 
*Recommended for production*
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'

# Base backup + WAL files = recover to any point in time
```

### 2. **Logical Backups (pg_dump)**
*What we're using - good for small to medium databases*
```bash
# Custom format (recommended)
./backup_db.sh --format custom

# Benefits: Portable, version-independent, selective restore
# Limits: Single-threaded, locks during backup
```

### 3. **Physical Backups (pg_basebackup)**
*For larger databases (>100GB)*
```bash
pg_basebackup -D /backup/base -Ft -z -P -W
```

### 4. **Continuous Archiving**
*Enterprise-grade with tools like pgBackRest*
```bash
# Install pgBackRest for production environments
sudo apt install pgbackrest
```

## 🔄 Automation & Monitoring

### Automated Daily Backups
```bash
# Setup automated backups
./scripts/setup_automated_backup.sh

# Manual crontab entry
0 2 * * * cd /path/to/youth-attendance && ./scripts/backup_db.sh --format custom --retention 7 >> logs/backup.log 2>&1
```

### Backup Monitoring
```bash
# Check backup status
ls -la backups/ | head -5

# Verify latest backup
./scripts/show_backup_rows.sh backups/$(ls -t backups/*.dump | head -1)

# Monitor backup size trends
du -sh backups/* | tail -10
```

## 🛡️ Security & Compliance

### Encryption (2025 Standard)
```bash
# Encrypt backups for compliance
gpg --symmetric --cipher-algo AES256 backup_file.dump

# Automated encryption
./backup_db.sh --format custom | gpg --symmetric --cipher-algo AES256 > backup_encrypted.gpg
```

### Access Control
```bash
# Secure backup directory permissions
chmod 700 backups/
chown $USER:$USER backups/

# Secure backup files
chmod 600 backups/*.dump
```

## 🚨 Recovery Procedures

### Emergency Recovery
```bash
# 1. Stop application
sudo systemctl stop youtharoot-app

# 2. Create recovery backup
./backup_db.sh --format custom

# 3. Restore from backup
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_URL" backups/recovery_backup.dump

# 4. Restart application
sudo systemctl start youtharoot-app
```

### Partial Recovery
```bash
# Restore specific tables only
pg_restore --table=events --table=persons \
  --dbname="$DATABASE_URL" backups/backup.dump
```

## 📈 Performance Optimization (2025)

### Large Database Backups
```bash
# Parallel backups (PostgreSQL 12+)
pg_dump --jobs=4 --format=directory --dbname="$DATABASE_URL" backup_dir/

# Exclude large audit/log tables
pg_dump --exclude-table=audit_logs --exclude-table=session_data \
  --dbname="$DATABASE_URL" > backup_optimized.sql
```

### Network Optimization
```bash
# Compressed streaming backup
pg_dump --dbname="$DATABASE_URL" | gzip | ssh backup-server 'cat > backup.sql.gz'

# Direct cloud upload (with AWS CLI)
pg_dump --dbname="$DATABASE_URL" | aws s3 cp - s3://backup-bucket/backup_$(date +%Y%m%d).sql
```

## 🔍 Troubleshooting

### Common Issues
```bash
# Version mismatch
pg_dump --version  # Should match or be newer than PostgreSQL server

# Permission issues  
GRANT CONNECT ON DATABASE youth_attendance TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;

# Connection issues
pg_isready -h host -p port -U user
```

### Backup Validation
```bash
# Size validation
ls -lh backups/*.dump | awk '{if($5 < "1M") print "Warning: Small backup " $9}'

# Integrity validation  
pg_restore --list backup.dump | wc -l  # Should show substantial object count
```

## 📚 Additional Resources

- [PostgreSQL Backup & Recovery Official Docs](https://www.postgresql.org/docs/current/backup.html)
- [pgBackRest - Enterprise Backup Solution](https://pgbackrest.org/)
- [Backup Strategies Comparison 2025](https://www.postgresql.org/docs/current/backup-strategies.html)