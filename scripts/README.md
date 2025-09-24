# Database Backup Scripts

This directory contains scripts for database backup and maintenance operations.

## backup_db.sh

A production-ready PostgreSQL backup script following best practices.

### Usage

```bash
# Basic backup (plain SQL format, compressed)
./backup_db.sh

# Custom binary format (recommended for large databases)
./backup_db.sh --format custom

# Set retention policy (keep backups for 7 days)
./backup_db.sh --retention 7

# Verbose output
./backup_db.sh --verbose
```

### Options

- `--format plain|custom`: Choose backup format
  - `plain`: Human-readable SQL format (default)
  - `custom`: Binary format, smaller and faster to restore
- `--compress`: Force compression (automatic for plain format)
- `--retention DAYS`: Keep backups for N days (default: 30)
- `--verbose`: Show detailed output

### Features

✅ **Error Handling**: Script exits on any error with proper cleanup  
✅ **Format Options**: Support for both plain SQL and custom binary formats  
✅ **Compression**: Automatic compression to save space  
✅ **Retention Policy**: Automatic cleanup of old backups  
✅ **Integrity Testing**: Verifies custom format backups  
✅ **Progress Reporting**: Clear status messages and backup info  
✅ **Security**: Safely handles DATABASE_URL without exposing credentials  

### Environment Setup

The script automatically loads `.env` file if present. Ensure `DATABASE_URL` is set:

```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

### Backup Formats

**Plain Format** (`.sql.gz`):
- Human-readable SQL commands
- Good for small databases
- Can be restored with `psql`
- Automatically compressed

**Custom Format** (`.dump`):
- Binary format, more efficient
- Built-in compression
- Faster backup and restore
- Can restore selectively with `pg_restore`

### Automation

For automated backups, add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/youth-attendance && ./scripts/backup_db.sh --format custom --retention 7
```

### Restore Examples

**Plain format:**
```bash
gunzip youtharoot_backup_20241220_140000.sql.gz
psql "$DATABASE_URL" < youtharoot_backup_20241220_140000.sql
```

**Custom format:**
```bash
pg_restore --verbose --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_URL" youtharoot_backup_20241220_140000.dump
```