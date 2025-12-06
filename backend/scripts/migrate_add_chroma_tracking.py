"""
Database migration script to add ChromaDB tracking columns to profile table
in company databases for historical data ingestion tracking
"""
import sys
import os
from pathlib import Path
import glob

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from loguru import logger

from app.config import settings

def get_data_directory():
    """Get the data directory path"""
    # The data directory is in the backend folder
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / "data"
    return str(data_dir)

def migrate_company_database(db_path: str):
    """Add ChromaDB tracking columns to a company database"""

    db_name = os.path.basename(db_path).replace('.db', '')
    logger.info(f"\nMigrating database: {db_name}")

    # Create engine for this database
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )

    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(profile)"))
            columns = [row[1] for row in result.fetchall()]

            columns_to_add = []

            if 'chroma_collection_name' not in columns:
                columns_to_add.append('chroma_collection_name')

            if 'historical_data_processed_at' not in columns:
                columns_to_add.append('historical_data_processed_at')

            if 'historical_data_chunk_count' not in columns:
                columns_to_add.append('historical_data_chunk_count')

            if not columns_to_add:
                logger.info(f"  ✓ All ChromaDB tracking columns already exist")
                return True

            # Add missing columns
            for column in columns_to_add:
                logger.info(f"  Adding column '{column}'...")

                if column == 'chroma_collection_name':
                    conn.execute(text("ALTER TABLE profile ADD COLUMN chroma_collection_name VARCHAR"))
                elif column == 'historical_data_processed_at':
                    conn.execute(text("ALTER TABLE profile ADD COLUMN historical_data_processed_at DATETIME"))
                elif column == 'historical_data_chunk_count':
                    conn.execute(text("ALTER TABLE profile ADD COLUMN historical_data_chunk_count INTEGER DEFAULT 0"))

                conn.commit()
                logger.info(f"  ✓ Column '{column}' added successfully")

            logger.info(f"✓ Migration completed for {db_name}")
            return True

    except Exception as e:
        logger.error(f"  Migration failed for {db_name}: {e}")
        return False
    finally:
        engine.dispose()

def migrate_all_company_databases():
    """Migrate all company databases"""

    logger.info("=" * 60)
    logger.info("ChromaDB Tracking Columns Migration")
    logger.info("=" * 60)

    # Find all company database files
    data_dir = get_data_directory()
    logger.info(f"Looking for company databases in: {data_dir}")
    pattern = os.path.join(data_dir, "company_*.db")
    db_files = glob.glob(pattern)

    if not db_files:
        logger.warning(f"No company databases found in {data_dir}")
        logger.info("This is normal if no companies have completed setup yet.")
        return True

    logger.info(f"\nFound {len(db_files)} company database(s)")

    success_count = 0
    failed_count = 0

    for db_path in db_files:
        if migrate_company_database(db_path):
            success_count += 1
        else:
            failed_count += 1

    logger.info("\n" + "=" * 60)
    logger.info("Migration Summary:")
    logger.info(f"  Total databases: {len(db_files)}")
    logger.info(f"  Successfully migrated: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info("=" * 60)

    return failed_count == 0

if __name__ == "__main__":
    logger.info("Starting ChromaDB tracking migration for company databases...")

    success = migrate_all_company_databases()

    if success:
        logger.info("\n✓ All migrations completed successfully!")
        logger.info("\nNew Profile table columns:")
        logger.info("  - chroma_collection_name: Stores the company-scoped ChromaDB collection name")
        logger.info("  - historical_data_processed_at: Timestamp when historical data was ingested")
        logger.info("  - historical_data_chunk_count: Number of chunks stored in ChromaDB")
        logger.info("\nThese columns enable:")
        logger.info("  1. Tracking which ChromaDB collection belongs to each company")
        logger.info("  2. Monitoring historical data ingestion status")
        logger.info("  3. Reprocessing detection and analytics")
        sys.exit(0)
    else:
        logger.error("\n✗ Some migrations failed. Please check the errors above.")
        sys.exit(1)
