"""
Database cloning service for multi-tenant setup
"""
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger
from datetime import datetime
import uuid

from app.config import settings
from app.database.models import Base, User, Role, Permission, Profile, user_roles, role_permissions
from app.auth.security import get_password_hash

class DatabaseService:
    """Service for managing company-specific databases"""

    @staticmethod
    def generate_company_db_name(company_name: str) -> str:
        """
        Generate a unique database filename for a company

        Args:
            company_name: Name of the company

        Returns:
            Database filename (e.g., 'company_acme_corp_uuid.db')
        """
        # Sanitize company name (remove special chars, replace spaces)
        safe_name = "".join(c if c.isalnum() else "_" for c in company_name.lower())
        safe_name = safe_name[:50]  # Limit length

        # Add UUID for uniqueness
        unique_id = str(uuid.uuid4())[:8]

        db_name = f"company_{safe_name}_{unique_id}.db"
        return db_name

    @staticmethod
    def get_company_db_path(db_name: str) -> str:
        """
        Get full path to company database file

        Args:
            db_name: Database filename

        Returns:
            Full path to database file
        """
        data_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
        return str(data_dir / db_name)

    @staticmethod
    def create_company_database(company_name: str, admin_user_data: dict, profile_data: dict = None) -> str:
        """
        Create a new company-specific database with only admin user and profile

        Args:
            company_name: Name of the company
            admin_user_data: Dictionary with admin user information
                - username: str
                - email: str
                - hashed_password: str
                - full_name: str
                - company: str
            profile_data: Optional dictionary with company profile information
                - industry: str
                - location: str
                - sustainability_target_kp1: int
                - sustainability_target_kp2: float
                - budget: float
                - historical_data_path: str (optional)

        Returns:
            Database filename (not full path)

        Raises:
            Exception: If database creation fails
        """
        try:
            # Generate unique database name
            db_name = DatabaseService.generate_company_db_name(company_name)
            db_path = DatabaseService.get_company_db_path(db_name)

            logger.info(f"Creating company database: {db_name}")

            # Create database URL
            company_db_url = f"sqlite:///{db_path}"

            # Create engine for new database
            company_engine = create_engine(
                company_db_url,
                connect_args={"check_same_thread": False}
            )

            # Create all tables (empty)
            logger.info("Creating database schema...")
            Base.metadata.create_all(bind=company_engine)

            # Create session
            CompanySession = sessionmaker(autocommit=False, autoflush=False, bind=company_engine)
            db = CompanySession()

            try:
                # Seed roles and permissions (same as primary DB)
                logger.info("Seeding roles and permissions...")
                DatabaseService._seed_roles_and_permissions(db)

                # Create only the admin user
                logger.info(f"Creating admin user: {admin_user_data['username']}")
                admin_user = User(
                    username=admin_user_data['username'],
                    email=admin_user_data['email'],
                    hashed_password=admin_user_data['hashed_password'],
                    full_name=admin_user_data['full_name'],
                    company=admin_user_data['company'],
                    is_active=True,
                    is_first_login=False,  # Already completed setup
                    setup_completed_at=datetime.utcnow(),
                    company_database_name=db_name
                )

                # Assign admin role
                admin_role = db.query(Role).filter(Role.name == "admin").first()
                if admin_role:
                    admin_user.roles.append(admin_role)

                db.add(admin_user)
                db.flush()  # Flush to get admin_user.id

                # Create profile in company database if profile data provided
                if profile_data:
                    logger.info(f"Creating company profile in company database")
                    profile = Profile(
                        user_id=admin_user.id,
                        industry=profile_data['industry'],
                        location=profile_data['location'],
                        sustainability_target_kp1=profile_data['sustainability_target_kp1'],
                        sustainability_target_kp2=profile_data['sustainability_target_kp2'],
                        budget=profile_data['budget'],
                        historical_data_path=profile_data.get('historical_data_path')
                    )
                    db.add(profile)

                db.commit()

                logger.info(f"✓ Company database created: {db_name}")
                return db_name

            except Exception as e:
                db.rollback()
                logger.error(f"Failed to setup company database: {e}")
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to create company database: {e}")
            # Clean up partial database file if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
            raise

    @staticmethod
    def _seed_roles_and_permissions(db):
        """
        Seed roles and permissions in a new database
        This mirrors the logic from app.database.db.seed_roles_and_permissions
        """
        # Define permissions
        permissions_data = [
            # Document permissions
            {"name": "documents:create", "description": "Create documents", "resource": "documents", "action": "create"},
            {"name": "documents:read", "description": "Read documents", "resource": "documents", "action": "read"},
            {"name": "documents:update", "description": "Update documents", "resource": "documents", "action": "update"},
            {"name": "documents:delete", "description": "Delete documents", "resource": "documents", "action": "delete"},

            # Agent permissions
            {"name": "agents:read", "description": "View agent status", "resource": "agents", "action": "read"},
            {"name": "agents:execute", "description": "Execute agents", "resource": "agents", "action": "execute"},

            # Chat permissions
            {"name": "chat:create", "description": "Create conversations", "resource": "chat", "action": "create"},
            {"name": "chat:read", "description": "Read conversations", "resource": "chat", "action": "read"},
            {"name": "chat:delete", "description": "Delete conversations", "resource": "chat", "action": "delete"},

            # User management permissions
            {"name": "users:create", "description": "Create users", "resource": "users", "action": "create"},
            {"name": "users:read", "description": "Read users", "resource": "users", "action": "read"},
            {"name": "users:update", "description": "Update users", "resource": "users", "action": "update"},
            {"name": "users:delete", "description": "Delete users", "resource": "users", "action": "delete"},

            # Explainability permissions
            {"name": "explain:view", "description": "View explanations", "resource": "explain", "action": "view"},
            {"name": "explain:detailed", "description": "Access detailed explanations", "resource": "explain", "action": "detailed"},
        ]

        # Create permissions
        permission_map = {}
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            db.add(permission)
            db.flush()
            permission_map[perm_data["name"]] = permission

        # Define roles with their permissions
        roles_data = [
            {
                "name": "super_admin",
                "description": "Super administrator with full system access",
                "permissions": list(permission_map.keys())  # All permissions
            },
            {
                "name": "admin",
                "description": "Administrator with document and agent management",
                "permissions": [
                    "documents:create", "documents:read", "documents:update", "documents:delete",
                    "agents:read", "agents:execute",
                    "chat:create", "chat:read", "chat:delete",
                    "users:read",
                    "explain:view", "explain:detailed"
                ]
            },
            {
                "name": "authenticated_user",
                "description": "Regular authenticated user",
                "permissions": [
                    "documents:read",
                    "agents:read",
                    "chat:create", "chat:read", "chat:delete",
                    "explain:view"
                ]
            }
        ]

        # Create roles and assign permissions
        for role_data in roles_data:
            role = Role(name=role_data["name"], description=role_data["description"])

            # Assign permissions
            for perm_name in role_data["permissions"]:
                if perm_name in permission_map:
                    role.permissions.append(permission_map[perm_name])

            db.add(role)

        db.commit()
        logger.info("✓ Roles and permissions seeded")

    @staticmethod
    def get_engine_for_user(user: User):
        """
        Get database engine for a specific user

        Args:
            user: User object

        Returns:
            SQLAlchemy engine for user's database
        """
        if user.company_database_name:
            # User has a company-specific database
            db_path = DatabaseService.get_company_db_path(user.company_database_name)
            db_url = f"sqlite:///{db_path}"
        else:
            # Use primary database
            db_url = settings.DATABASE_URL

        return create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )
