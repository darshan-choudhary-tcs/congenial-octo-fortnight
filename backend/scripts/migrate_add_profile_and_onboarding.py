"""
Migration script to add profile table and onboarding fields to users table
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

def migrate():
    """Add profile table and onboarding fields"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            # Add new columns to users table
            logger.info("Adding onboarding columns to users table...")

            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]

            if 'is_first_login' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_first_login BOOLEAN DEFAULT 1"))
                logger.info("✓ Added is_first_login column")
            else:
                logger.info("⊘ is_first_login column already exists")

            if 'setup_completed_at' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN setup_completed_at DATETIME"))
                logger.info("✓ Added setup_completed_at column")
            else:
                logger.info("⊘ setup_completed_at column already exists")

            if 'company_database_name' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN company_database_name TEXT"))
                logger.info("✓ Added company_database_name column")
            else:
                logger.info("⊘ company_database_name column already exists")

            # Create profile table
            logger.info("Creating profile table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    industry TEXT NOT NULL,
                    location TEXT NOT NULL,
                    sustainability_target_kp1 INTEGER NOT NULL,
                    sustainability_target_kp2 REAL NOT NULL,
                    historical_data_path TEXT,
                    budget REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("✓ Profile table created")

            # Set is_first_login to False for existing users (except admins)
            logger.info("Updating existing users...")
            conn.execute(text("""
                UPDATE users
                SET is_first_login = 0
                WHERE username IN ('superadmin', 'user1')
            """))
            logger.info("✓ Updated existing non-admin users to is_first_login=False")

            conn.commit()
            logger.info("✅ Migration completed successfully!")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
