"""
Migration script for adding consent fields to persons table (2026).

Adds parental_permission_2026 and photo_consent_2026 boolean columns
to the persons table. Existing rows receive FALSE as the default.

Usage:
    cd backend && python migrations/add_consent_fields_2026.py

Safety:
- Only adds new columns with safe defaults
- Never drops or modifies existing columns
- Idempotent (safe to run multiple times)
"""

import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine, text
from app.config import settings


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :table AND column_name = :col
                )
            """),
            {"table": table_name, "col": column_name},
        )
        return result.scalar()


def add_consent_fields():
    database_url = settings.database_url
    print(f"Starting migration: add consent fields (2026)")
    print(f"Database: {database_url.split('@')[-1] if '@' in database_url else 'Local'}")

    engine = create_engine(database_url)

    new_columns = [
        {
            "name": "parental_permission_2026",
            "sql": "ALTER TABLE persons ADD COLUMN parental_permission_2026 BOOLEAN NOT NULL DEFAULT FALSE",
        },
        {
            "name": "photo_consent_2026",
            "sql": "ALTER TABLE persons ADD COLUMN photo_consent_2026 BOOLEAN NOT NULL DEFAULT FALSE",
        },
    ]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for col in new_columns:
                if check_column_exists(engine, "persons", col["name"]):
                    print(f"Column '{col['name']}' already exists — skipping")
                    continue
                print(f"Adding column: {col['name']}")
                conn.execute(text(col["sql"]))
                print(f"Added column: {col['name']}")
            trans.commit()
            print("Migration completed successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
            print("Rollback instructions:")
            for col in new_columns:
                print(f"  ALTER TABLE persons DROP COLUMN IF EXISTS {col['name']};")
            return False

    # Verify
    print("\nVerifying:")
    for col in new_columns:
        exists = check_column_exists(engine, "persons", col["name"])
        print(f"  {'OK' if exists else 'MISSING'}: {col['name']}")

    return True


def main():
    print("=" * 60)
    print("YOUTHAROOT DB MIGRATION — Add consent fields 2026")
    print("=" * 60)
    response = input("\nThis will modify the database. Continue? (y/N): ")
    if response.lower() not in ("y", "yes"):
        print("Migration cancelled.")
        return
    success = add_consent_fields()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
