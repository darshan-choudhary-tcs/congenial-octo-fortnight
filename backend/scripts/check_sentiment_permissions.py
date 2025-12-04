"""
Check if sentiment:analyze permission exists and which roles have it
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Permission, Role, User
from loguru import logger

def check_permissions():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if sentiment:analyze permission exists
        sentiment_perm = db.query(Permission).filter(
            Permission.name == "sentiment:analyze"
        ).first()
        
        if not sentiment_perm:
            logger.warning("❌ Permission 'sentiment:analyze' not found!")
            logger.info("Run: python scripts/migrate_add_sentiment_permissions.py")
            return
        
        logger.info(f"✅ Permission 'sentiment:analyze' exists (ID: {sentiment_perm.id})")
        
        # Check which roles have this permission
        roles_with_perm = db.query(Role).join(Role.permissions).filter(
            Permission.name == "sentiment:analyze"
        ).all()
        
        if roles_with_perm:
            logger.info(f"✅ Roles with sentiment:analyze permission:")
            for role in roles_with_perm:
                logger.info(f"   - {role.name}")
                
                # Count users with this role
                users_count = db.query(User).join(User.roles).filter(
                    Role.id == role.id
                ).count()
                logger.info(f"     ({users_count} users have this role)")
        else:
            logger.warning("❌ No roles have the sentiment:analyze permission!")
        
        # List all users and their roles
        logger.info("\n📋 All users and their roles:")
        all_users = db.query(User).all()
        for user in all_users:
            role_names = [role.name for role in user.roles]
            has_sentiment = any(
                "sentiment:analyze" in [p.name for p in role.permissions]
                for role in user.roles
            )
            status = "✅" if has_sentiment else "❌"
            logger.info(f"   {status} {user.username} - Roles: {', '.join(role_names)}")
        
        logger.info("\n💡 If your user doesn't have access:")
        logger.info("   1. Logout and login again to refresh permissions")
        logger.info("   2. Or have an admin assign you the 'admin' or 'analyst' role")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Checking sentiment analysis permissions...")
    check_permissions()
