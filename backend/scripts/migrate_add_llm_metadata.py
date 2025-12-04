"""
Migration script to add LLM-generated metadata fields to documents table
Run this script to add: auto_summary, auto_keywords, auto_topics, content_type,
summarization_model, summarization_tokens, and summarized_at columns
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.exc import OperationalError
from loguru import logger

from app.database.db import engine, Base
from app.database.models import Document

def add_llm_metadata_columns():
    """Add LLM metadata columns to documents table"""

    columns_to_add = [
        ("auto_summary", "TEXT"),
        ("auto_keywords", "JSON"),
        ("auto_topics", "JSON"),
        ("content_type", "VARCHAR"),
        ("summarization_model", "VARCHAR"),
        ("summarization_tokens", "INTEGER"),
        ("summarized_at", "TIMESTAMP"),
    ]

    with engine.connect() as conn:
        for column_name, sql_type in columns_to_add:
            try:
                # For SQLite, try to add column directly
                # If it fails with duplicate error, it means it already exists
                from sqlalchemy import text
                sql = text(f"ALTER TABLE documents ADD COLUMN {column_name} {sql_type}")
                conn.execute(sql)
                conn.commit()
                logger.info(f"✓ Added column: {column_name}")

            except OperationalError as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info(f"✓ Column already exists: {column_name}")
                else:
                    logger.error(f"✗ Error adding column {column_name}: {e}")
                    raise
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate" in error_msg or "already exists" in error_msg:
                    logger.info(f"✓ Column already exists: {column_name}")
                else:
                    logger.error(f"✗ Error adding column {column_name}: {e}")
                    raise

if __name__ == "__main__":
    logger.info("Starting migration: Add LLM metadata columns to documents table")
    try:
        add_llm_metadata_columns()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
