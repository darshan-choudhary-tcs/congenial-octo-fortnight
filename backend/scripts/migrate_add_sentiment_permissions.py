"""
Add sentiment:analyze permission to the database

This migration creates the sentiment:analyze permission and assigns it to
admin and analyst roles.

Run this script: python backend/scripts/migrate_add_sentiment_permissions.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Permission, Role
from loguru import logger

def run_migration():
    """Create sentiment:analyze permission and assign to roles"""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if permission already exists
        existing_perm = db.query(Permission).filter(
            Permission.name == "sentiment:analyze"
        ).first()
        
        if existing_perm:
            logger.info("Permission 'sentiment:analyze' already exists")
            permission = existing_perm
        else:
            # Create sentiment:analyze permission
            permission = Permission(
                name="sentiment:analyze",
                description="Analyze sentiment in text and CSV data",
                resource="sentiment",
                action="analyze"
            )
            db.add(permission)
            db.commit()
            logger.info("✅ Permission 'sentiment:analyze' created")
        
        # Assign to admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            if permission not in admin_role.permissions:
                admin_role.permissions.append(permission)
                db.commit()
                logger.info("✅ Added 'sentiment:analyze' to role: admin")
            else:
                logger.info("Role 'admin' already has 'sentiment:analyze'")
        else:
            logger.warning("⚠️  Role 'admin' not found")
        
        # Assign to analyst role
        analyst_role = db.query(Role).filter(Role.name == "analyst").first()
        if analyst_role:
            if permission not in analyst_role.permissions:
                analyst_role.permissions.append(permission)
                db.commit()
                logger.info("✅ Added 'sentiment:analyze' to role: analyst")
            else:
                logger.info("Role 'analyst' already has 'sentiment:analyze'")
        else:
            logger.warning("⚠️  Role 'analyst' not found")
        
        logger.info("\nMigration completed successfully!")
        logger.info("Users with 'admin' or 'analyst' roles can now access sentiment analysis.")
        logger.info("⚠️  Users need to logout and login again for changes to take effect.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Running sentiment analysis permissions migration...")
    run_migration()
