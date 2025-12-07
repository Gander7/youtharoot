"""
Migration: Update message_groups.created_by to be nullable and String type for Clerk IDs
Date: 2025-12-07
"""
from sqlalchemy import text, create_engine
from app.config import settings


def migrate():
    """Update message_groups.created_by column to support Clerk user IDs."""
    print("🔄 Migrating message_groups.created_by column...")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check if column exists and needs migration
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'message_groups' AND column_name = 'created_by'
        """))
        
        column_info = result.fetchone()
        
        if not column_info:
            print("⚠️ created_by column not found, skipping migration")
            return
        
        print(f"   Current type: {column_info[1]}, nullable: {column_info[2]}")
        
        # Drop foreign key constraint if it exists
        try:
            conn.execute(text("""
                ALTER TABLE message_groups 
                DROP CONSTRAINT IF EXISTS message_groups_created_by_fkey
            """))
            conn.commit()
            print("✅ Dropped foreign key constraint")
        except Exception as e:
            print(f"⚠️ Could not drop FK constraint (may not exist): {e}")
        
        # Change column to nullable VARCHAR
        try:
            conn.execute(text("""
                ALTER TABLE message_groups 
                ALTER COLUMN created_by DROP NOT NULL,
                ALTER COLUMN created_by TYPE VARCHAR(255) USING created_by::VARCHAR
            """))
            conn.commit()
            print("✅ Updated created_by column to VARCHAR(255) and nullable")
        except Exception as e:
            print(f"❌ Error updating column: {e}")
            raise


if __name__ == "__main__":
    migrate()
