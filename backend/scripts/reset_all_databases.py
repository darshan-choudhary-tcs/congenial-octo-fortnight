"""
Complete Database Reset Utility
Deletes all databases including:
- Primary SQLite database (data_store.db)
- All company-specific databases
- ChromaDB vector database
- Uploaded files
- Token files
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.models import Base, User, Role, Permission
from app.auth.security import get_password_hash

def create_primary_database_with_superadmin():
    """Create primary database with only superadmin user"""

    # Get database path
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    # Ensure data directory exists
    data_dir = Path(db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create engine and tables
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Create super_admin role with all permissions
        permissions_data = [
            # Document permissions
            {"name": "documents:create", "description": "Create documents", "resource": "documents", "action": "create"},
            {"name": "documents:read", "description": "Read documents", "resource": "documents", "action": "read"},
            {"name": "documents:update", "description": "Update documents", "resource": "documents", "action": "update"},
            {"name": "documents:delete", "description": "Delete documents", "resource": "documents", "action": "delete"},
            # Agent permissions
            {"name": "agents:execute", "description": "Execute agents", "resource": "agents", "action": "execute"},
            {"name": "agents:read", "description": "Read agent logs", "resource": "agents", "action": "read"},
            {"name": "agents:configure", "description": "Configure agents", "resource": "agents", "action": "configure"},
            # User management permissions
            {"name": "users:create", "description": "Create users", "resource": "users", "action": "create"},
            {"name": "users:read", "description": "Read users", "resource": "users", "action": "read"},
            {"name": "users:update", "description": "Update users", "resource": "users", "action": "update"},
            {"name": "users:delete", "description": "Delete users", "resource": "users", "action": "delete"},
            # Chat permissions
            {"name": "chat:use", "description": "Use chat interface", "resource": "chat", "action": "use"},
            {"name": "chat:history", "description": "View chat history", "resource": "chat", "action": "read"},
            # Explainability permissions
            {"name": "explain:view", "description": "View explanations", "resource": "explainability", "action": "read"},
            {"name": "explain:detailed", "description": "View detailed explanations", "resource": "explainability", "action": "detailed"},
        ]

        permissions = []
        for perm_data in permissions_data:
            perm = Permission(**perm_data)
            db.add(perm)
            permissions.append(perm)

        db.flush()

        # Create super_admin role
        super_admin_role = Role(
            name="super_admin",
            description="Super Administrator with full system access"
        )
        super_admin_role.permissions = permissions
        db.add(super_admin_role)
        db.flush()

        # Create superadmin user
        superadmin = User(
            username="superadmin",
            email="superadmin@example.com",
            hashed_password=get_password_hash("superadmin123"),
            full_name="Super Administrator",
            company="System",
            is_active=True,
            is_first_login=False,
            setup_completed_at=datetime.utcnow()
        )
        superadmin.roles = [super_admin_role]
        db.add(superadmin)

        db.commit()
        logger.info("✅ Created superadmin user with all permissions")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        db.close()

def reset_all_databases():
    """Delete all databases and related files"""

    logger.info("=" * 70)
    logger.info("COMPLETE DATABASE RESET UTILITY")
    logger.info("=" * 70)

    # Get base directory
    base_dir = Path(__file__).parent.parent

    # Define paths
    data_dir = base_dir / "data"
    chroma_dir = base_dir / settings.CHROMA_PERSIST_DIR.lstrip('./')
    uploads_dir = base_dir / "uploads"
    token_dir = base_dir / "token"

    # Show what will be deleted
    logger.warning("\n⚠️  WARNING: This will delete ALL of the following:\n")

    items_to_delete = []

    # Check for SQLite databases in data directory
    if data_dir.exists():
        db_files = list(data_dir.glob("*.db"))
        if db_files:
            logger.warning(f"📁 SQLite Databases in {data_dir}:")
            for db_file in db_files:
                logger.warning(f"   - {db_file.name}")
                items_to_delete.append(db_file)

    # Check for ChromaDB
    if chroma_dir.exists():
        logger.warning(f"\n📁 ChromaDB (Vector Database) in {chroma_dir}:")
        logger.warning(f"   - Entire directory and all collections")
        items_to_delete.append(chroma_dir)

    # Check for uploads
    if uploads_dir.exists():
        upload_files = list(uploads_dir.glob("*"))
        if upload_files:
            logger.warning(f"\n📁 Uploaded Files in {uploads_dir}:")
            logger.warning(f"   - {len(upload_files)} file(s)")
            items_to_delete.append(uploads_dir)

    # Check for tokens
    if token_dir.exists():
        token_files = list(token_dir.glob("*"))
        if token_files:
            logger.warning(f"\n📁 Token Files in {token_dir}:")
            logger.warning(f"   - {len(token_files)} file(s)")
            items_to_delete.append(token_dir)

    if not items_to_delete:
        logger.info("\n✅ No databases or files found to delete.")
        return

    logger.warning("\n⚠️  This action cannot be undone!")
    response = input("\nType 'DELETE ALL' (in capitals) to proceed: ")

    if response != 'DELETE ALL':
        logger.info("❌ Database reset cancelled.")
        return

    # Start deletion
    logger.info("\n🗑️  Starting deletion process...\n")

    deleted_count = 0
    error_count = 0

    # Delete SQLite databases
    if data_dir.exists():
        db_files = list(data_dir.glob("*.db"))
        for db_file in db_files:
            try:
                db_file.unlink()
                logger.success(f"✅ Deleted: {db_file.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to delete {db_file.name}: {e}")
                error_count += 1

    # Delete ChromaDB
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            logger.success(f"✅ Deleted: ChromaDB directory")
            deleted_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to delete ChromaDB: {e}")
            error_count += 1

    # Delete uploads
    if uploads_dir.exists():
        try:
            shutil.rmtree(uploads_dir)
            # Recreate empty directory
            uploads_dir.mkdir(exist_ok=True)
            logger.success(f"✅ Cleared: Uploads directory")
            deleted_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to clear uploads: {e}")
            error_count += 1

    # Delete tokens
    if token_dir.exists():
        try:
            shutil.rmtree(token_dir)
            # Recreate empty directory
            token_dir.mkdir(exist_ok=True)
            logger.success(f"✅ Cleared: Token directory")
            deleted_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to clear tokens: {e}")
            error_count += 1

    # Summary
    logger.info("\n" + "=" * 70)
    if error_count == 0:
        logger.success("✅ ALL DATABASES AND FILES DELETED SUCCESSFULLY!")
    else:
        logger.warning(f"⚠️  DELETION COMPLETED WITH {error_count} ERROR(S)")
    logger.info("=" * 70)

    logger.info(f"\n📊 Summary:")
    logger.info(f"   - Items deleted: {deleted_count}")
    logger.info(f"   - Errors: {error_count}")

    logger.info("\n💡 Next Steps:")
    logger.info("   1. Restart the backend server")
    logger.info("   2. The databases will be recreated automatically on startup")
    logger.info("   3. You'll need to create new users and upload documents again")

    logger.info("\n📝 Note:")
    logger.info("   - Empty 'uploads' and 'token' directories have been recreated")
    logger.info("   - The 'data' directory structure remains intact")

    # Recreate primary database with superadmin user
    logger.info("\n🔨 Creating new primary database with superadmin user...")
    try:
        create_primary_database_with_superadmin()
        logger.success("✅ Primary database created successfully")
        logger.info("\n📋 Superadmin User Created:")
        logger.info("   Username: superadmin")
        logger.info("   Password: superadmin123")
        logger.info("   Email: superadmin@example.com")
        logger.info("\n⚠️  Please change this password after first login!")
    except Exception as e:
        logger.error(f"❌ Failed to create primary database: {e}")
        logger.error("   You'll need to restart the backend server to initialize the database")

def main():
    """Main entry point with option menu"""

    logger.info("\n" + "=" * 70)
    logger.info("DATABASE RESET UTILITY - OPTIONS")
    logger.info("=" * 70)

    print("\nWhat would you like to do?")
    print("1. Delete ALL databases and files (complete reset)")
    print("2. Delete only SQLite databases")
    print("3. Delete only ChromaDB (vector database)")
    print("4. Delete only uploaded files")
    print("5. Cancel")

    choice = input("\nEnter your choice (1-5): ")

    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    chroma_dir = base_dir / settings.CHROMA_PERSIST_DIR.lstrip('./')
    uploads_dir = base_dir / "uploads"

    if choice == "1":
        reset_all_databases()

    elif choice == "2":
        logger.warning("\n⚠️  This will delete all SQLite databases")
        response = input("Type 'yes' to proceed: ")
        if response.lower() == 'yes':
            if data_dir.exists():
                db_files = list(data_dir.glob("*.db"))
                for db_file in db_files:
                    try:
                        db_file.unlink()
                        logger.success(f"✅ Deleted: {db_file.name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to delete {db_file.name}: {e}")
            logger.success("✅ SQLite databases deleted")

            # Recreate primary database
            logger.info("\n🔨 Creating new primary database with superadmin user...")
            try:
                create_primary_database_with_superadmin()
                logger.success("✅ Primary database created successfully")
                logger.info("\n📋 Superadmin User Created:")
                logger.info("   Username: superadmin")
                logger.info("   Password: superadmin123")
                logger.info("   Email: superadmin@example.com")
            except Exception as e:
                logger.error(f"❌ Failed to create primary database: {e}")
        else:
            logger.info("❌ Cancelled")

    elif choice == "3":
        logger.warning("\n⚠️  This will delete the entire ChromaDB vector database")
        response = input("Type 'yes' to proceed: ")
        if response.lower() == 'yes':
            if chroma_dir.exists():
                try:
                    shutil.rmtree(chroma_dir)
                    logger.success("✅ ChromaDB deleted")
                except Exception as e:
                    logger.error(f"❌ Failed to delete ChromaDB: {e}")
            else:
                logger.info("ℹ️  ChromaDB directory not found")
        else:
            logger.info("❌ Cancelled")

    elif choice == "4":
        logger.warning("\n⚠️  This will delete all uploaded files")
        response = input("Type 'yes' to proceed: ")
        if response.lower() == 'yes':
            if uploads_dir.exists():
                try:
                    shutil.rmtree(uploads_dir)
                    uploads_dir.mkdir(exist_ok=True)
                    logger.success("✅ Uploaded files deleted")
                except Exception as e:
                    logger.error(f"❌ Failed to delete uploads: {e}")
            else:
                logger.info("ℹ️  Uploads directory not found")
        else:
            logger.info("❌ Cancelled")

    elif choice == "5":
        logger.info("❌ Operation cancelled")

    else:
        logger.error("❌ Invalid choice")

if __name__ == "__main__":
    main()
