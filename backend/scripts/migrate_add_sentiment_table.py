"""
Add Sentiment Analysis table to database

This migration creates the sentiment_analysis_results table for storing
sentiment analysis results and configurations.

Run this script: python backend/scripts/migrate_add_sentiment_table.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import settings
from loguru import logger

def run_migration():
    """Create sentiment_analysis_results table"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid VARCHAR NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL,
        completed_at TIMESTAMP,
        input_type VARCHAR NOT NULL,
        text_input TEXT,
        original_file_path VARCHAR,
        result_file_path VARCHAR,
        original_filename VARCHAR,
        text_column VARCHAR,
        sentiment_column VARCHAR DEFAULT 'sentiment',
        confidence_column VARCHAR DEFAULT 'sentiment_confidence',
        results JSON,
        total_rows INTEGER,
        positive_count INTEGER DEFAULT 0,
        negative_count INTEGER DEFAULT 0,
        neutral_count INTEGER DEFAULT 0,
        average_confidence FLOAT,
        status VARCHAR DEFAULT 'pending',
        error_message TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    try:
        with engine.begin() as conn:
            logger.info("Creating sentiment_analysis_results table...")
            conn.execute(text(create_table_sql))
            logger.info("✅ Table created successfully")
            
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Running sentiment analysis table migration...")
    run_migration()
