"""
Database initialization and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from loguru import logger

from app.config import settings
from app.database.models import Base, User, Role, Permission, user_roles, role_permissions

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

        # Check if admin user exists
        if db.query(User).filter(User.username == "admin").first() is None:
            logger.info("Creating default admin user...")
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
            "name": "admin",
            "description": "Administrator with full access",
            "permissions": list(permissions.keys())  # All permissions
        },
        {
            "name": "analyst",
            "description": "Analyst with document and agent access",
            "permissions": [
                "documents:create", "documents:read", "documents:update", "documents:delete",
                "agents:execute", "agents:read",
                "chat:use", "chat:history",
                "explain:view", "explain:detailed"
            ]
        },
        {
            "name": "viewer",
            "description": "Viewer with read-only access",
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
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    analyst_role = db.query(Role).filter(Role.name == "analyst").first()
    viewer_role = db.query(Role).filter(Role.name == "viewer").first()

    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "System Administrator",
            "roles": [admin_role]
        },
        {
            "username": "analyst1",
            "email": "analyst1@example.com",
            "password": "analyst123",
            "full_name": "John Analyst",
            "roles": [analyst_role]
        },
        {
            "username": "viewer1",
            "email": "viewer1@example.com",
            "password": "viewer123",
            "full_name": "Jane Viewer",
            "roles": [viewer_role]
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
