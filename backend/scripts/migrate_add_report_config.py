"""
Migration script to add report_config JSON column to profile table
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path
import json

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

def migrate():
    """Add report_config JSON column to profile table"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            logger.info("Adding report_config column to profile table...")

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
                logger.info("✓ Initialized existing profiles with default report configuration")
            else:
                logger.info("⊘ report_config column already exists")

            conn.commit()
            logger.info("✅ Migration completed successfully!")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
