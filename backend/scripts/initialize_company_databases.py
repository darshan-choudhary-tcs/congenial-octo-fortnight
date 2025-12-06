"""
Initialize empty company databases with profile table structure
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path
import glob
import json

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from app.database.models import Base

def get_default_report_config():
    """Returns default report configuration"""
    return {
        "energy_weights": {"solar": 0.35, "wind": 0.35, "hydro": 0.30},
        "price_optimization_weights": {"cost": 0.35, "reliability": 0.35, "sustainability": 0.30},
        "portfolio_decision_weights": {"esg_score": 0.40, "budget_fit": 0.35, "technical_feasibility": 0.25},
        "confidence_threshold": 0.7,
        "enable_fallback_options": True,
        "max_renewable_sources": 4
    }

def initialize_company_database(db_path: str, db_name: str):
    """Initialize a company database with all necessary tables"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Initializing: {db_name}")
    logger.info(f"{'='*60}")

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    with engine.connect() as conn:
        try:
            # Check what tables exist
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result]

            logger.info(f"Existing tables: {existing_tables if existing_tables else 'None'}")

            # If profile table doesn't exist, create it
            if 'profile' not in existing_tables:
                logger.info("Creating profile table...")

                # Create profile table with all columns including report_config
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS profile (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        industry TEXT NOT NULL,
                        location TEXT NOT NULL,
                        sustainability_target_kp1 INTEGER NOT NULL,
                        sustainability_target_kp2 REAL NOT NULL,
                        historical_data_path TEXT,
                        chroma_collection_name TEXT,
                        historical_data_processed_at DATETIME,
                        historical_data_chunk_count INTEGER DEFAULT 0,
                        budget REAL NOT NULL,
                        report_config TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("✓ Created profile table")

                # Create default profile for the first user (user_id will be determined by primary DB)
                # We'll leave it empty for now since we don't know the user_id
                logger.info("⚠️  Profile table created but empty - user needs to complete onboarding")

            else:
                # Profile table exists, check if report_config column exists
                result = conn.execute(text("PRAGMA table_info(profile)"))
                columns = [row[1] for row in result]

                if 'report_config' not in columns:
                    logger.info("Adding report_config column to existing profile table...")
                    conn.execute(text("ALTER TABLE profile ADD COLUMN report_config TEXT"))

                    # Update existing profiles
                    default_config = json.dumps(get_default_report_config())
                    conn.execute(
                        text("UPDATE profile SET report_config = :config WHERE report_config IS NULL"),
                        {"config": default_config}
                    )
                    logger.info("✓ Added report_config column and initialized existing profiles")
                else:
                    logger.info("✓ Profile table already has report_config column")

                # Check if there are any profiles
                result = conn.execute(text("SELECT COUNT(*) FROM profile"))
                count = result.fetchone()[0]
                logger.info(f"Profile table has {count} record(s)")

            conn.commit()
            logger.info(f"✅ Initialization completed for {db_name}")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Initialization failed for {db_name}: {e}")
            raise

def initialize_all():
    """Initialize all company databases"""
    logger.info("Starting database initialization...")

    # Find all company databases
    db_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
    company_dbs = glob.glob(str(db_dir / "company_*.db"))

    if not company_dbs:
        logger.warning("\n⚠️  No company databases found")
        return

    logger.info(f"\n📊 Found {len(company_dbs)} company database(s)")

    # Initialize each company database
    for db_path in company_dbs:
        db_name = Path(db_path).name
        initialize_company_database(db_path, db_name)

    logger.info("\n" + "="*60)
    logger.info("✅ ALL DATABASES INITIALIZED!")
    logger.info("="*60)
    logger.info("\n⚠️  NOTE: Users with empty profiles still need to complete onboarding to populate their profile data.")

if __name__ == "__main__":
    initialize_all()
