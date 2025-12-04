"""
Migration script to add selected_document_ids column to conversations table
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import settings
from loguru import logger

def migrate():
    """Add selected_document_ids JSON column to conversations table"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)

        logger.info("Starting migration: Add selected_document_ids to conversations")

        with engine.begin() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM pragma_table_info('conversations')
                WHERE name='selected_document_ids'
            """))

            column_exists = result.scalar() > 0

            if column_exists:
                logger.info("Column 'selected_document_ids' already exists, skipping migration")
                return

            # Add the column
            conn.execute(text("""
                ALTER TABLE conversations
                ADD COLUMN selected_document_ids JSON DEFAULT NULL
            """))

            logger.info("Successfully added 'selected_document_ids' column to conversations table")
            logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
