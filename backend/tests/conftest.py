"""
Pytest configuration and fixtures for testing
"""
import os
import sys
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.db import Base, get_db
from app.database.models import User, Role, Permission
from app.auth.security import get_password_hash
from main import app

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_permissions(db_session: Session):
    """Create test permissions"""
    permissions = [
        Permission(name="documents:read", description="Read documents"),
        Permission(name="documents:write", description="Write documents"),
        Permission(name="documents:delete", description="Delete documents"),
        Permission(name="chat:access", description="Access chat"),
        Permission(name="admin:access", description="Access admin panel"),
    ]
    for perm in permissions:
        db_session.add(perm)
    db_session.commit()
    return permissions


@pytest.fixture(scope="function")
def test_roles(db_session: Session, test_permissions):
    """Create test roles with permissions"""
    # User role
    user_role = Role(name="user", description="Regular user")
    user_role.permissions = [p for p in test_permissions if not p.name.startswith("admin")]
    db_session.add(user_role)

    # Admin role
    admin_role = Role(name="admin", description="Administrator")
    admin_role.permissions = test_permissions
    db_session.add(admin_role)

    db_session.commit()
    return {"user": user_role, "admin": admin_role}


@pytest.fixture(scope="function")
def test_user(client: TestClient, test_roles) -> dict:
    """Create a test user via API"""
    # Register user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    if response.status_code == 200:
        return response.json()
    # User might already exist from previous test, that's ok
    return {"username": "testuser", "email": "test@example.com"}


@pytest.fixture(scope="function")
def test_admin(client: TestClient, db_session: Session, test_roles) -> User:
    """Create a test admin user directly in DB (can't create via API)"""
    # Check if admin already exists
    admin = db_session.query(User).filter(User.username == "adminuser").first()
    if admin:
        return admin

    admin = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True
    )
    admin.roles = [test_roles["admin"]]
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def user_token(client: TestClient, test_user) -> str:
    """Get authentication token for test user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client: TestClient, test_admin) -> str:
    """Get authentication token for admin user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "adminuser", "password": "adminpass123"}
    )
    if response.status_code != 200:
        raise Exception(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(user_token: str) -> dict:
    """Get authorization headers for test user"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """Get authorization headers for admin user"""
    return {"Authorization": f"Bearer {admin_token}"}
