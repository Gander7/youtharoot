# Youth Attendance - Database Backup Quick Reference

## 🚀 Essential Commands

### Create Backup
```bash
# Recommended for production use
./backend/scripts/backup_db.sh --format custom --retention 7

# Simple backup
./backend/scripts/backup_db.sh
```

### Verify Backup
```bash
# Check what's in your backup (row counts)
./backend/scripts/show_backup_rows.sh backend/backups/your_backup_file.dump
```

### List Backups
```bash
# Show all backups
ls -la backend/scripts/backups/

# Show newest backup
ls -t backend/scripts/backups/*.dump | head -1
```

### Restore Backup (DESTRUCTIVE)
```bash
# ⚠️ WARNING: This replaces ALL data in your database
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_URL" backend/backups/your_backup_file.dump
```

## 📂 Files You Need

### ✅ Keep These Files:
- `backend/scripts/backup_db.sh` - Main backup script
- `backend/scripts/show_backup_rows.sh` - Verify backup contents  
- `backend/scripts/setup_automated_backup.sh` - Setup daily backups
- `backend/scripts/README.md` - Full documentation
- `backend/scripts/backups/` - Your backup files directory

### 🗑️ Cleaned Up:
- Removed test/experimental backup scripts
- Removed redundant verification tools
- Kept only production-ready tools

## 🎯 Best Practices (2025)

1. **Use custom format for production**: `--format custom`
2. **Set retention policy**: `--retention 7` (keeps 7 days of backups)
3. **Verify backups regularly**: Use `show_backup_rows.sh`
4. **Automate backups**: Use `setup_automated_backup.sh`
5. **Test restores**: Practice disaster recovery procedures

## 🛡️ Your Current Backup Status

✅ **Working backup created**: `youtharoot_backup_20251013_154703.dump` (31KB)  
✅ **Contains**: 284 rows across 4 tables (events, persons, users, event_persons)  
✅ **Verified**: Perfect match with live database  
✅ **Ready for production use**

For detailed documentation, see `backend/scripts/README.md`