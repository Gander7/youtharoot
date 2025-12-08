"""
Migration: Update messages.sent_by to VARCHAR(255) for Clerk user IDs
Date: 2025-12-08

SAFETY: This migration is idempotent and data-safe.
- Preserves ALL existing data by converting integers to strings
- Can be run multiple times without data loss
- Checks current schema before making changes
"""

import os
import sys

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine, inspect
from app.config import settings


def check_column_type(conn, table_name: str, column_name: str):
    """Check the current type of a column."""
    result = conn.execute(text("""
        SELECT data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = :table AND column_name = :column
    """), {"table": table_name, "column": column_name})
    
    return result.fetchone()


def foreign_key_exists(conn, constraint_name: str):
    """Check if a foreign key constraint exists."""
    result = conn.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND constraint_name = :constraint_name
    """), {"constraint_name": constraint_name})
    
    return result.fetchone() is not None


def migrate():
    """
    Update messages.sent_by column to support Clerk user IDs.
    
    Changes:
    1. Drop foreign key constraint to users table (if exists)
    2. Convert column from BigInteger to VARCHAR(255)
    3. Make column nullable for flexibility
    4. Preserve all existing data (integers become strings like "1", "2", etc.)
    """
    print("\n" + "="*70)
    print("🔄 MIGRATION: messages.sent_by → VARCHAR(255)")
    print("="*70)
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Step 1: Check current schema
        print("\n📋 Step 1: Checking current schema...")
        column_info = check_column_type(conn, "messages", "sent_by")
        
        if not column_info:
            print("❌ ERROR: sent_by column not found in messages table")
            return
        
        data_type, max_length, is_nullable = column_info
        print(f"   ✓ Current type: {data_type}")
        print(f"   ✓ Max length: {max_length if max_length else 'N/A'}")
        print(f"   ✓ Nullable: {is_nullable}")
        
        # Check if already migrated
        if data_type in ('character varying', 'varchar') and (max_length is None or max_length >= 255):
            print("\n✅ Column already migrated to VARCHAR(255) - no changes needed")
            return
        
        # Step 2: Drop foreign key constraint if it exists
        print("\n📋 Step 2: Removing foreign key constraint (if exists)...")
        fk_constraint_name = "messages_sent_by_fkey"
        
        if foreign_key_exists(conn, fk_constraint_name):
            try:
                conn.execute(text(f"""
                    ALTER TABLE messages 
                    DROP CONSTRAINT {fk_constraint_name}
                """))
                conn.commit()
                print(f"   ✓ Dropped foreign key constraint: {fk_constraint_name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not drop FK constraint: {e}")
                conn.rollback()
        else:
            print(f"   ✓ No foreign key constraint found (already removed or never existed)")
        
        # Step 3: Count existing records
        print("\n📋 Step 3: Checking existing data...")
        result = conn.execute(text("SELECT COUNT(*) FROM messages"))
        record_count = result.fetchone()[0]
        print(f"   ✓ Found {record_count} message records to preserve")
        
        # Step 4: Convert column type
        print("\n📋 Step 4: Converting column to VARCHAR(255)...")
        try:
            # PostgreSQL USING clause converts integers to strings automatically
            conn.execute(text("""
                ALTER TABLE messages 
                ALTER COLUMN sent_by TYPE VARCHAR(255) USING sent_by::text
            """))
            conn.commit()
            print("   ✓ Column type converted to VARCHAR(255)")
        except Exception as e:
            print(f"   ❌ ERROR converting column type: {e}")
            conn.rollback()
            raise
        
        # Step 5: Make column nullable
        print("\n📋 Step 5: Making column nullable...")
        try:
            conn.execute(text("""
                ALTER TABLE messages 
                ALTER COLUMN sent_by DROP NOT NULL
            """))
            conn.commit()
            print("   ✓ Column is now nullable")
        except Exception as e:
            # Not a critical error if it's already nullable
            print(f"   ⚠️  Note: {e}")
            conn.rollback()
        
        # Step 6: Verify migration
        print("\n📋 Step 6: Verifying migration...")
        column_info_after = check_column_type(conn, "messages", "sent_by")
        if column_info_after:
            data_type_after, max_length_after, is_nullable_after = column_info_after
            print(f"   ✓ New type: {data_type_after}")
            print(f"   ✓ Max length: {max_length_after if max_length_after else 'unlimited'}")
            print(f"   ✓ Nullable: {is_nullable_after}")
        
        # Step 7: Verify data preservation
        result = conn.execute(text("SELECT COUNT(*) FROM messages"))
        record_count_after = result.fetchone()[0]
        print(f"   ✓ Records after migration: {record_count_after}")
        
        if record_count == record_count_after:
            print("   ✓ All data preserved successfully!")
        else:
            print(f"   ⚠️  WARNING: Record count mismatch!")
            print(f"      Before: {record_count}, After: {record_count_after}")
    
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nNext steps:")
    print("1. Update db_models.py: messages.sent_by = Column(String(255), nullable=True)")
    print("2. Remove ForeignKey reference in db_models.py")
    print("3. Update any code that references messages.sender relationship")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        sys.exit(1)
