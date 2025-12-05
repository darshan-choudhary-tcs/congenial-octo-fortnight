"""
Database initialization and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
from loguru import logger
from contextvars import ContextVar
from pathlib import Path

from app.config import settings
from app.database.models import Base, User, Role, Permission, user_roles, role_permissions

# Create engine for primary database with proper pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_size=20,  # Increased from default 5
    max_overflow=40,  # Increased from default 10
    pool_timeout=60,  # Increased from default 30
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create session factory for primary database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Context variable to store current user's database path
_user_db_context: ContextVar[Optional[str]] = ContextVar('user_db_context', default=None)

# Cache for database engines to avoid recreating them
_engine_cache = {}

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Uses user's company database if context is set, otherwise uses primary database.
    """
    # Check if we have a user-specific database context
    user_db_path = _user_db_context.get()

    if user_db_path:
        # Use cached engine or create new one
        if user_db_path not in _engine_cache:
            user_db_url = f"sqlite:///{user_db_path}"
            _engine_cache[user_db_path] = create_engine(
                user_db_url,
                connect_args={"check_same_thread": False},
                pool_size=10,
                max_overflow=20,
                pool_timeout=60,
                pool_pre_ping=True,
                pool_recycle=3600
            )

        UserSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine_cache[user_db_path]
        )
        db = UserSessionLocal()
        logger.debug(f"Using company database: {user_db_path}")
    else:
        # Use primary database
        db = SessionLocal()
        logger.debug("Using primary database")

    try:
        yield db
    finally:
        db.close()

def get_primary_db() -> Generator[Session, None, None]:
    """
    Dependency for getting primary database session.
    Always uses the primary database, regardless of user context.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_user_db_context(company_database_name: Optional[str]):
    """
    Set the database context for the current user.

    Args:
        company_database_name: Name of the company database file, or None for primary DB
    """
    if company_database_name:
        # Get full path to company database
        data_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
        db_path = str(data_dir / company_database_name)
        _user_db_context.set(db_path)
    else:
        _user_db_context.set(None)

def clear_user_db_context():
    """Clear the database context (revert to primary database)"""
    _user_db_context.set(None)

def get_session_for_db(company_database_name: str) -> Session:
    """
    Get a database session for a specific company database.

    Args:
        company_database_name: Name of the company database file

    Returns:
        SQLAlchemy Session for the company database
    """
    data_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
    db_path = str(data_dir / company_database_name)

    # Use cached engine or create new one
    if db_path not in _engine_cache:
        user_db_url = f"sqlite:///{db_path}"
        _engine_cache[db_path] = create_engine(
            user_db_url,
            connect_args={"check_same_thread": False},
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_pre_ping=True,
            pool_recycle=3600
        )

    CompanySessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine_cache[db_path]
    )
    return CompanySessionLocal()

def init_db():
    """Initialize database with tables and seed data"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Seed initial data
    db = SessionLocal()
    try:
        # Check if roles exist
        if db.query(Role).count() == 0:
            logger.info("Seeding initial roles and permissions...")
            seed_roles_and_permissions(db)

        # Check if super admin user exists
        if db.query(User).filter(User.username == "superadmin").first() is None:
            logger.info("Creating default users...")
            create_default_users(db)

        logger.info("Database initialization completed!")
    finally:
        db.close()

def seed_roles_and_permissions(db: Session):
    """Seed initial roles and permissions"""

    # Define permissions
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

    permissions = {}
    for perm_data in permissions_data:
        perm = Permission(**perm_data)
        db.add(perm)
        permissions[perm_data["name"]] = perm

    db.flush()

    # Define roles with their permissions
    roles_data = [
        {
            "name": "super_admin",
            "description": "Super Administrator with full system access including user management",
            "permissions": list(permissions.keys())  # All permissions
        },
        {
            "name": "admin",
            "description": "Administrator with full access to documents and agents",
            "permissions": [
                "documents:create", "documents:read", "documents:update", "documents:delete",
                "agents:execute", "agents:read", "agents:configure",
                "chat:use", "chat:history",
                "explain:view", "explain:detailed"
            ]
        },
        {
            "name": "authenticated_user",
            "description": "Authenticated user with basic access",
            "permissions": [
                "documents:read",
                "agents:read",
                "chat:use", "chat:history",
                "explain:view"
            ]
        }
    ]

    for role_data in roles_data:
        role = Role(name=role_data["name"], description=role_data["description"])
        role.permissions = [permissions[perm_name] for perm_name in role_data["permissions"]]
        db.add(role)

    db.commit()
    logger.info(f"Created {len(roles_data)} roles and {len(permissions_data)} permissions")

def create_default_users(db: Session):
    """Create default users for testing"""
    # Import here to avoid circular dependency
    from app.auth.security import get_password_hash

    # Get roles
    super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    authenticated_user_role = db.query(Role).filter(Role.name == "authenticated_user").first()

    users_data = [
        {
            "username": "superadmin",
            "email": "superadmin@example.com",
            "password": "superadmin123",
            "full_name": "Super Administrator",
            "company": "System",
            "roles": [super_admin_role],
            "is_first_login": False
        }
    ]

    for user_data in users_data:
        password = user_data.pop("password")
        roles = user_data.pop("roles")

        user = User(
            **user_data,
            hashed_password=get_password_hash(password),
            is_active=True
        )
        user.roles = roles
        db.add(user)

    db.commit()
    logger.info(f"Created {len(users_data)} default users")
