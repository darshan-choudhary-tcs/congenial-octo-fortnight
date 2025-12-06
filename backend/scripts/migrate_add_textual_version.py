"""
Migration script to add textual_version column to saved_reports table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect, text, Column, JSON
from app.config import settings
from app.database.models import Base
from loguru import logger


def add_textual_version_column():
    """Add textual_version column to saved_reports table in main database"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Check if table exists
    if 'saved_reports' not in inspector.get_table_names():
        logger.warning("saved_reports table does not exist")
        return

    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('saved_reports')]
    if 'textual_version' in columns:
        logger.info("textual_version column already exists in main database")
        return

    logger.info("Adding textual_version column to saved_reports table...")

    with engine.connect() as conn:
        # SQLite doesn't support ALTER TABLE ADD COLUMN with complex types directly
        # But we can add JSON column
        conn.execute(text("ALTER TABLE saved_reports ADD COLUMN textual_version TEXT"))
        conn.commit()

    logger.info("✓ textual_version column added to main database")


def add_textual_version_to_company_databases():
    """Add textual_version column to saved_reports in all company-scoped databases"""
    from app.database.db import get_db
    from app.database.models import User

    # Get main database connection
    main_engine = create_engine(settings.DATABASE_URL)
    db = next(get_db())

    try:
        # Get all users with company databases
        users = db.query(User).filter(User.company_database_name.isnot(None)).all()

        logger.info(f"Found {len(users)} company databases to migrate")

        for user in users:
            if user.company_database_name:
                try:
                    company_db_path = os.path.join(
                        os.path.dirname(settings.DATABASE_URL.replace('sqlite:///', '')),
                        user.company_database_name
                    )
                    company_db_url = f"sqlite:///{company_db_path}"

                    company_engine = create_engine(company_db_url)
                    company_inspector = inspect(company_engine)

                    # Check if saved_reports table exists
                    if 'saved_reports' not in company_inspector.get_table_names():
                        logger.info(f"  Skipping {user.company_database_name} - no saved_reports table")
                        company_engine.dispose()
                        continue

                    # Check if column already exists
                    columns = [col['name'] for col in company_inspector.get_columns('saved_reports')]
                    if 'textual_version' not in columns:
                        with company_engine.connect() as conn:
                            conn.execute(text("ALTER TABLE saved_reports ADD COLUMN textual_version TEXT"))
                            conn.commit()
                        logger.info(f"✓ Added textual_version column to {user.company_database_name}")
                    else:
                        logger.info(f"  textual_version column already exists in {user.company_database_name}")

                    company_engine.dispose()

                except Exception as e:
                    logger.error(f"✗ Failed to migrate {user.company_database_name}: {str(e)}")

        logger.info("✓ Company database migration completed")

    except Exception as e:
        logger.error(f"✗ Error during company database migration: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting textual_version column migration...")

    # Add to main database
    add_textual_version_column()

    # Add to company databases
    add_textual_version_to_company_databases()

    logger.info("Migration completed successfully!")
