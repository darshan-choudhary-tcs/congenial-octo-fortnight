"""
Migration script to add saved_reports table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect, text
from app.config import settings
from app.database.models import Base, SavedReport
from loguru import logger


def add_saved_reports_table():
    """Add saved_reports table to main database"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Check if table already exists
    if 'saved_reports' in inspector.get_table_names():
        logger.info("saved_reports table already exists")
        return

    logger.info("Creating saved_reports table...")

    # Create the table
    SavedReport.__table__.create(engine)

    logger.info("✓ saved_reports table created successfully")


def add_saved_reports_to_company_databases():
    """Add saved_reports table to all company-scoped databases"""
    from app.database.db import get_db
    from app.database.models import User

    # Get main database connection
    engine = create_engine(settings.DATABASE_URL)
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

                    # Check if table already exists
                    if 'saved_reports' not in company_inspector.get_table_names():
                        SavedReport.__table__.create(company_engine)
                        logger.info(f"✓ Added saved_reports table to {user.company_database_name}")
                    else:
                        logger.info(f"  saved_reports table already exists in {user.company_database_name}")

                    company_engine.dispose()

                except Exception as e:
                    logger.error(f"✗ Failed to migrate {user.company_database_name}: {str(e)}")

        logger.info("✓ Company database migration completed")

    except Exception as e:
        logger.error(f"✗ Error during company database migration: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting saved_reports table migration...")

    # Add to main database
    add_saved_reports_table()

    # Add to company databases
    add_saved_reports_to_company_databases()

    logger.info("Migration completed successfully!")
