"""
Migration script to add low_confidence_warning column to messages table
Run this script to update the database schema
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def migrate_add_low_confidence_warning():
    """Add low_confidence_warning column to messages table"""

    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('messages') WHERE name='low_confidence_warning'"
            ))
            column_exists = result.scalar() > 0

            if column_exists:
                print("✓ Column 'low_confidence_warning' already exists in messages table")
                return

            # Add the column
            print("Adding 'low_confidence_warning' column to messages table...")
            conn.execute(text(
                "ALTER TABLE messages ADD COLUMN low_confidence_warning BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print("✓ Successfully added 'low_confidence_warning' column to messages table")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("=" * 80)
    print("Database Migration: Add low_confidence_warning Column")
    print("=" * 80)
    migrate_add_low_confidence_warning()
    print("\nMigration completed successfully!")
