"""
Migrate all company databases with report_config column
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path
import json
import os
import glob

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

def get_default_report_config():
    """Returns default report configuration with balanced weights"""
    return {
        "energy_weights": {
            "solar": 0.30,
            "wind": 0.25,
            "hydro": 0.25,
            "biomass": 0.20
        },
        "price_optimization_weights": {
            "cost": 0.35,
            "reliability": 0.35,
            "sustainability": 0.30
        },
        "portfolio_decision_weights": {
            "esg_score": 0.40,
            "budget_fit": 0.35,
            "technical_feasibility": 0.25
        },
        "confidence_threshold": 0.7,
        "enable_fallback_options": True,
        "max_renewable_sources": 4
    }

def migrate_database(db_url: str, db_name: str):
    """Migrate a single database"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Migrating: {db_name}")
    logger.info(f"{'='*60}")

    engine = create_engine(db_url)

    with engine.connect() as conn:
        try:
            # Check if profile table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='profile'"))
            if not result.fetchone():
                logger.warning(f"⊘ Profile table does not exist in {db_name}, skipping...")
                return

            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(profile)"))
            columns = [row[1] for row in result]

            if 'report_config' not in columns:
                # Add JSON column
                conn.execute(text("ALTER TABLE profile ADD COLUMN report_config TEXT"))
                logger.info("✓ Added report_config column")

                # Initialize existing profiles with default configuration
                default_config = json.dumps(get_default_report_config())
                conn.execute(
                    text("UPDATE profile SET report_config = :config WHERE report_config IS NULL"),
                    {"config": default_config}
                )

                # Count updated profiles
                result = conn.execute(text("SELECT COUNT(*) FROM profile WHERE report_config IS NOT NULL"))
                count = result.fetchone()[0]
                logger.info(f"✓ Initialized {count} profile(s) with default report configuration")
            else:
                logger.info("⊘ report_config column already exists")

            conn.commit()
            logger.info(f"✅ Migration completed for {db_name}!")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration failed for {db_name}: {e}")
            raise

def migrate_all():
    """Migrate primary database and all company databases"""
    logger.info("Starting migration for all databases...")

    # 1. Migrate primary database
    logger.info("\n" + "="*60)
    logger.info("MIGRATING PRIMARY DATABASE")
    logger.info("="*60)
    migrate_database(settings.DATABASE_URL, "PRIMARY (rag.db)")

    # 2. Find all company databases
    # Database files are stored in the same directory as the primary database
    db_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
    company_dbs = glob.glob(str(db_dir / "company_*.db"))

    if not company_dbs:
        logger.warning("\n⚠️  No company databases found")
        return

    logger.info(f"\n📊 Found {len(company_dbs)} company database(s)")

    # 3. Migrate each company database
    for db_path in company_dbs:
        db_name = Path(db_path).name
        db_url = f"sqlite:///{db_path}"
        migrate_database(db_url, db_name)

    logger.info("\n" + "="*60)
    logger.info("✅ ALL MIGRATIONS COMPLETED!")
    logger.info("="*60)

if __name__ == "__main__":
    migrate_all()
