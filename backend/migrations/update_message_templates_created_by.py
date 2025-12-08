"""
Migration: Update message_templates.created_by to VARCHAR(255) for Clerk user IDs
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


def unique_constraint_exists(conn, constraint_name: str):
    """Check if a unique constraint exists."""
    result = conn.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'UNIQUE'
        AND constraint_name = :constraint_name
    """), {"constraint_name": constraint_name})
    
    return result.fetchone() is not None


def migrate():
    """
    Update message_templates.created_by column to support Clerk user IDs.
    
    Changes:
    1. Drop foreign key constraint to users table (if exists)
    2. Drop and recreate unique constraint for (name, created_by)
    3. Convert column from BigInteger to VARCHAR(255)
    4. Make column nullable for flexibility
    5. Preserve all existing data (integers become strings like "1", "2", etc.)
    """
    print("\n" + "="*70)
    print("🔄 MIGRATION: message_templates.created_by → VARCHAR(255)")
    print("="*70)
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Step 1: Check current schema
        print("\n📋 Step 1: Checking current schema...")
        column_info = check_column_type(conn, "message_templates", "created_by")
        
        if not column_info:
            print("❌ ERROR: created_by column not found in message_templates table")
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
        fk_constraint_name = "message_templates_created_by_fkey"
        
        if foreign_key_exists(conn, fk_constraint_name):
            try:
                conn.execute(text(f"""
                    ALTER TABLE message_templates 
                    DROP CONSTRAINT {fk_constraint_name}
                """))
                conn.commit()
                print(f"   ✓ Dropped foreign key constraint: {fk_constraint_name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not drop FK constraint: {e}")
                conn.rollback()
        else:
            print(f"   ✓ No foreign key constraint found (already removed or never existed)")
        
        # Step 3: Drop unique constraint (will recreate after type change)
        print("\n📋 Step 3: Temporarily removing unique constraint...")
        unique_constraint_name = "uq_template_name_per_user"
        unique_constraint_existed = False
        
        if unique_constraint_exists(conn, unique_constraint_name):
            try:
                conn.execute(text(f"""
                    ALTER TABLE message_templates 
                    DROP CONSTRAINT {unique_constraint_name}
                """))
                conn.commit()
                unique_constraint_existed = True
                print(f"   ✓ Dropped unique constraint: {unique_constraint_name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not drop unique constraint: {e}")
                conn.rollback()
        else:
            print(f"   ✓ No unique constraint found")
        
        # Step 4: Count existing records
        print("\n📋 Step 4: Checking existing data...")
        result = conn.execute(text("SELECT COUNT(*) FROM message_templates"))
        record_count = result.fetchone()[0]
        print(f"   ✓ Found {record_count} template records to preserve")
        
        # Step 5: Convert column type
        print("\n📋 Step 5: Converting column to VARCHAR(255)...")
        try:
            # PostgreSQL USING clause converts integers to strings automatically
            conn.execute(text("""
                ALTER TABLE message_templates 
                ALTER COLUMN created_by TYPE VARCHAR(255) USING created_by::text
            """))
            conn.commit()
            print("   ✓ Column type converted to VARCHAR(255)")
        except Exception as e:
            print(f"   ❌ ERROR converting column type: {e}")
            conn.rollback()
            raise
        
        # Step 6: Make column nullable
        print("\n📋 Step 6: Making column nullable...")
        try:
            conn.execute(text("""
                ALTER TABLE message_templates 
                ALTER COLUMN created_by DROP NOT NULL
            """))
            conn.commit()
            print("   ✓ Column is now nullable")
        except Exception as e:
            # Not a critical error if it's already nullable
            print(f"   ⚠️  Note: {e}")
            conn.rollback()
        
        # Step 7: Recreate unique constraint if it existed
        if unique_constraint_existed:
            print("\n📋 Step 7: Recreating unique constraint...")
            try:
                conn.execute(text(f"""
                    ALTER TABLE message_templates 
                    ADD CONSTRAINT {unique_constraint_name} 
                    UNIQUE (name, created_by)
                """))
                conn.commit()
                print(f"   ✓ Recreated unique constraint: {unique_constraint_name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not recreate unique constraint: {e}")
                print(f"      You may need to manually recreate it after resolving any duplicate data")
                conn.rollback()
        
        # Step 8: Verify migration
        print("\n📋 Step 8: Verifying migration...")
        column_info_after = check_column_type(conn, "message_templates", "created_by")
        if column_info_after:
            data_type_after, max_length_after, is_nullable_after = column_info_after
            print(f"   ✓ New type: {data_type_after}")
            print(f"   ✓ Max length: {max_length_after if max_length_after else 'unlimited'}")
            print(f"   ✓ Nullable: {is_nullable_after}")
        
        # Step 9: Verify data preservation
        result = conn.execute(text("SELECT COUNT(*) FROM message_templates"))
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
    print("1. Update db_models.py: message_templates.created_by = Column(String(255), nullable=True)")
    print("2. Remove ForeignKey reference in db_models.py")
    print("3. Update any code that references message_templates.creator relationship")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        sys.exit(1)
