"""
Migration: Remove foreign key constraint from message_group_membership.added_by
and convert to String to support Clerk user IDs.

This migration:
1. Drops the foreign key constraint
2. Converts added_by column from BigInteger to String
3. Preserves existing data by converting integers to strings
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def run_migration():
    """Execute the migration"""
    
    if settings.DATABASE_TYPE != 'postgresql':
        print("⚠️  This migration only applies to PostgreSQL databases")
        return
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        print("🔍 Checking current schema...")
        
        # Check if the foreign key constraint exists
        inspector = inspect(engine)
        fkeys = inspector.get_foreign_keys('message_group_membership')
        has_fkey = any(fk['name'] == 'message_group_membership_added_by_fkey' for fk in fkeys)
        
        if not has_fkey:
            print("✅ Foreign key constraint already removed")
            return
        
        print("📝 Starting migration...")
        
        # Start transaction
        trans = conn.begin()
        
        try:
            # Step 1: Drop the foreign key constraint
            print("  1. Dropping foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                DROP CONSTRAINT IF EXISTS message_group_membership_added_by_fkey;
            """))
            
            # Step 2: Convert column type from BigInteger to String
            # PostgreSQL will automatically convert integers to strings
            print("  2. Converting added_by column to VARCHAR(255)...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                ALTER COLUMN added_by TYPE VARCHAR(255) USING added_by::text;
            """))
            
            # Step 3: Make column nullable to support optional user tracking
            print("  3. Making added_by column nullable...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                ALTER COLUMN added_by DROP NOT NULL;
            """))
            
            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            print("   - Foreign key constraint removed")
            print("   - Column type changed to VARCHAR(255)")
            print("   - Column is now nullable")
            print("   - Existing data preserved (integers converted to strings)")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise

def rollback_migration():
    """Rollback the migration (not recommended - data loss possible)"""
    
    if settings.DATABASE_TYPE != 'postgresql':
        print("⚠️  This rollback only applies to PostgreSQL databases")
        return
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        print("⚠️  WARNING: Rolling back this migration may cause data loss!")
        print("   Clerk user IDs cannot be converted back to integer user IDs")
        
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled")
            return
        
        trans = conn.begin()
        
        try:
            # This rollback will fail if there are non-numeric values
            print("  1. Attempting to convert added_by back to BigInteger...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                ALTER COLUMN added_by TYPE BIGINT USING added_by::bigint;
            """))
            
            print("  2. Making added_by NOT NULL...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                ALTER COLUMN added_by SET NOT NULL;
            """))
            
            print("  3. Re-creating foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE message_group_membership 
                ADD CONSTRAINT message_group_membership_added_by_fkey 
                FOREIGN KEY (added_by) REFERENCES users(id);
            """))
            
            trans.commit()
            print("✅ Rollback completed")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Rollback failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()
