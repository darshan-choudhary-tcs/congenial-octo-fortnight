"""
Migration script to add saved reports permissions to existing roles
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Role, Permission, User
from loguru import logger


def add_permissions_to_main_database():
    """Add saved reports permissions to roles in main database"""
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Define new permissions
        new_permissions = [
            {
                "name": "reports:save",
                "description": "Save generated reports",
                "resource": "reports",
                "action": "save"
            },
            {
                "name": "reports:view_saved",
                "description": "View saved reports",
                "resource": "reports",
                "action": "view_saved"
            },
            {
                "name": "reports:export",
                "description": "Export reports to PDF",
                "resource": "reports",
                "action": "export"
            },
        ]

        # Create permissions if they don't exist
        created_perms = {}
        for perm_data in new_permissions:
            existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not existing_perm:
                new_perm = Permission(**perm_data)
                db.add(new_perm)
                db.flush()
                created_perms[perm_data["name"]] = new_perm
                logger.info(f"Created permission: {perm_data['name']}")
            else:
                created_perms[perm_data["name"]] = existing_perm
                logger.info(f"Permission already exists: {perm_data['name']}")

        # Add permissions to admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            for perm_name, perm in created_perms.items():
                if perm not in admin_role.permissions:
                    admin_role.permissions.append(perm)
                    logger.info(f"Added {perm_name} to admin role")

        # Add permissions to authenticated_user role
        auth_user_role = db.query(Role).filter(Role.name == "authenticated_user").first()
        if auth_user_role:
            for perm_name, perm in created_perms.items():
                if perm not in auth_user_role.permissions:
                    auth_user_role.permissions.append(perm)
                    logger.info(f"Added {perm_name} to authenticated_user role")

        db.commit()
        logger.info("✓ Main database permissions updated successfully")

    except Exception as e:
        logger.error(f"✗ Error updating main database: {str(e)}")
        db.rollback()
    finally:
        db.close()


def add_permissions_to_company_databases():
    """Add saved reports permissions to roles in all company databases"""
    from app.database.db import get_db

    # Get main database connection to find all company databases
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    main_db = Session()

    try:
        # Get all users with company databases
        users = main_db.query(User).filter(User.company_database_name.isnot(None)).all()

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
                    CompanySession = sessionmaker(bind=company_engine)
                    company_db = CompanySession()

                    # Define new permissions
                    new_permissions = [
                        {
                            "name": "reports:save",
                            "description": "Save generated reports",
                            "resource": "reports",
                            "action": "save"
                        },
                        {
                            "name": "reports:view_saved",
                            "description": "View saved reports",
                            "resource": "reports",
                            "action": "view_saved"
                        },
                        {
                            "name": "reports:export",
                            "description": "Export reports to PDF",
                            "resource": "reports",
                            "action": "export"
                        },
                    ]

                    # Create permissions if they don't exist
                    created_perms = {}
                    for perm_data in new_permissions:
                        existing_perm = company_db.query(Permission).filter(Permission.name == perm_data["name"]).first()
                        if not existing_perm:
                            new_perm = Permission(**perm_data)
                            company_db.add(new_perm)
                            company_db.flush()
                            created_perms[perm_data["name"]] = new_perm
                        else:
                            created_perms[perm_data["name"]] = existing_perm

                    # Add permissions to admin role
                    admin_role = company_db.query(Role).filter(Role.name == "admin").first()
                    if admin_role:
                        for perm_name, perm in created_perms.items():
                            if perm not in admin_role.permissions:
                                admin_role.permissions.append(perm)

                    # Add permissions to authenticated_user role
                    auth_user_role = company_db.query(Role).filter(Role.name == "authenticated_user").first()
                    if auth_user_role:
                        for perm_name, perm in created_perms.items():
                            if perm not in auth_user_role.permissions:
                                auth_user_role.permissions.append(perm)

                    company_db.commit()
                    company_db.close()
                    company_engine.dispose()

                    logger.info(f"✓ Updated permissions in {user.company_database_name}")

                except Exception as e:
                    logger.error(f"✗ Failed to migrate {user.company_database_name}: {str(e)}")

        logger.info("✓ Company database permissions migration completed")

    except Exception as e:
        logger.error(f"✗ Error during company database migration: {str(e)}")
    finally:
        main_db.close()


if __name__ == "__main__":
    logger.info("Starting saved reports permissions migration...")

    # Add to main database
    add_permissions_to_main_database()

    # Add to company databases
    add_permissions_to_company_databases()

    logger.info("Migration completed successfully!")
