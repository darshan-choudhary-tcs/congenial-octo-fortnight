"""
Database migration script to add 'scope' column to documents table
and set existing documents to 'user' scope
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from loguru import logger

from app.database.db import SessionLocal, engine
from app.database.models import Document

def migrate_add_scope_column():
    """Add scope column to documents table and set defaults"""

    logger.info("Starting migration: Add scope column to documents table")

    db = SessionLocal()

    try:
        # Check if scope column already exists
        result = db.execute(text("PRAGMA table_info(documents)"))
        columns = [row[1] for row in result.fetchall()]

        if 'scope' in columns:
            logger.info("Column 'scope' already exists in documents table")
        else:
            # Add scope column with default value 'user'
            logger.info("Adding 'scope' column to documents table...")
            db.execute(text("ALTER TABLE documents ADD COLUMN scope VARCHAR DEFAULT 'user'"))
            db.commit()
            logger.info("✓ Column 'scope' added successfully")

        # Update existing documents without scope to 'user'
        logger.info("Updating existing documents to set scope='user'...")
        result = db.execute(text("""
            UPDATE documents
            SET scope = 'user'
            WHERE scope IS NULL
        """))
        db.commit()

        updated_count = result.rowcount
        logger.info(f"✓ Updated {updated_count} documents to scope='user'")

        # Verify migration
        total_docs = db.query(Document).count()
        user_scope_docs = db.query(Document).filter(Document.scope == 'user').count()
        global_scope_docs = db.query(Document).filter(Document.scope == 'global').count()

        logger.info("\nMigration Summary:")
        logger.info(f"  Total documents: {total_docs}")
        logger.info(f"  User scope: {user_scope_docs}")
        logger.info(f"  Global scope: {global_scope_docs}")
        logger.info("\n✓ Migration completed successfully!")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Document Scope Column Migration")
    logger.info("=" * 60)

    success = migrate_add_scope_column()

    if success:
        logger.info("\nMigration completed. You can now:")
        logger.info("  1. Upload documents with scope='user' (default)")
        logger.info("  2. Upload global documents via /api/v1/documents/global/upload (admin only)")
        logger.info("  3. Users will search both global + their own documents")
        sys.exit(0)
    else:
        logger.error("\nMigration failed. Please check the errors above.")
        sys.exit(1)
