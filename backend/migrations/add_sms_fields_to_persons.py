"""
Migration script for adding SMS fields to persons table.

This script safely adds SMS-related fields to the existing persons table
using ADDITIVE-ONLY changes to preserve existing data.

Usage:
    python migrations/add_sms_fields_to_persons.py

Safety features:
- Only adds new columns with safe defaults
- Never drops or modifies existing columns
- Idempotent (can be run multiple times safely)
- Includes rollback instructions
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine, text, Column, Boolean
from sqlalchemy.exc import OperationalError
from app.database import get_database_url
from app.config import get_settings

def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        with engine.connect() as conn:
            # PostgreSQL-specific query
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """), {"table_name": table_name, "column_name": column_name})
            return result.scalar()
    except Exception as e:
        print(f"Error checking column {column_name}: {e}")
        return False

def add_sms_fields_to_persons():
    """Add SMS-related fields to the persons table."""
    settings = get_settings()
    database_url = get_database_url()
    
    print(f"🔄 Starting migration: Add SMS fields to persons table")
    print(f"📍 Database: {database_url.split('@')[-1] if '@' in database_url else 'Local'}")
    
    engine = create_engine(database_url)
    
    # Define the new columns to add
    new_columns = [
        {
            "name": "sms_consent",
            "sql": "ALTER TABLE persons ADD COLUMN sms_consent BOOLEAN NOT NULL DEFAULT TRUE"
        },
        {
            "name": "sms_opt_out", 
            "sql": "ALTER TABLE persons ADD COLUMN sms_opt_out BOOLEAN NOT NULL DEFAULT FALSE"
        }
    ]
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                for column in new_columns:
                    column_name = column["name"]
                    
                    # Check if column already exists
                    if check_column_exists(engine, "persons", column_name):
                        print(f"✅ Column '{column_name}' already exists - skipping")
                        continue
                    
                    # Add the column
                    print(f"➕ Adding column: {column_name}")
                    conn.execute(text(column["sql"]))
                    print(f"✅ Successfully added column: {column_name}")
                
                # Commit the transaction
                trans.commit()
                print(f"🎉 Migration completed successfully!")
                
                # Verify the migration
                print(f"\n🔍 Verifying migration...")
                for column in new_columns:
                    exists = check_column_exists(engine, "persons", column["name"])
                    status = "✅" if exists else "❌"
                    print(f"{status} Column '{column['name']}': {'EXISTS' if exists else 'MISSING'}")
                
                # Show sample data
                print(f"\n📊 Sample data from persons table:")
                result = conn.execute(text("""
                    SELECT id, first_name, last_name, person_type, sms_opt_out 
                    FROM persons 
                    LIMIT 3
                """))
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"   ID {row[0]}: {row[1]} {row[2]} ({row[3]}) - SMS Opt Out: {row[4]}")
                else:
                    print("   No data found in persons table")
                    
            except Exception as e:
                # Rollback on error
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"\n🔄 Rollback instructions:")
        print(f"If you need to rollback this migration, run:")
        for column in new_columns:
            print(f"   ALTER TABLE persons DROP COLUMN IF EXISTS {column['name']};")
        return False
    
    return True

def main():
    """Main migration function."""
    print("=" * 60)
    print("🗄️  YOUTH ATTENDANCE DATABASE MIGRATION")
    print("   Adding SMS fields to persons table")
    print("=" * 60)
    
    # Confirm before proceeding
    response = input("\n⚠️  This will modify the database. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    success = add_sms_fields_to_persons()
    
    if success:
        print(f"\n🎊 Migration completed successfully!")
        print(f"📋 New field added to persons table:")
        print(f"   - sms_opt_out: BOOLEAN DEFAULT FALSE (implicit SMS permission)")
        print(f"\n💡 Next steps:")
        print(f"   1. Update your application code to use the new field")
        print(f"   2. Consider adding a UI for users to manage SMS preferences") 
        print(f"   3. Implement phone number validation in your forms")
    else:
        print(f"\n💥 Migration failed! Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()