"""
Tests for admin endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestAdminEndpoints:
    """Test admin API endpoints"""

    def test_list_users_as_admin(self, client: TestClient, admin_headers, test_user, test_admin):
        """Test listing users as admin"""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least test_user and test_admin

    def test_list_users_as_regular_user(self, client: TestClient, auth_headers):
        """Test listing users as regular user (should fail)"""
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_get_user_by_id(self, client: TestClient, admin_headers, test_user, test_admin):
        """Test getting specific user by ID"""
        response = client.get(f"/api/v1/admin/users/{test_admin.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "adminuser"
        assert data["email"] == "admin@example.com"

    def test_create_user_as_admin(self, client: TestClient, admin_headers, test_roles):
        """Test creating user as admin"""
        response = client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "username": "adminuser",
                "email": "adminuser@example.com",
                "password": "adminpass123",
                "is_active": True,
                "role_ids": [test_roles["user"].id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "adminuser"

    def test_update_user_as_admin(self, client: TestClient, admin_headers, test_admin):
        """Test updating user as admin"""
        response = client.put(
            f"/api/v1/admin/users/{test_admin.id}",
            headers=admin_headers,
            json={
                "email": "modified@example.com",
                "is_active": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "modified@example.com"

    def test_delete_user_as_admin(self, client: TestClient, admin_headers, db_session, test_roles):
        """Test deleting user as admin"""
        # Create a user to delete
        from app.database.models import User
        from app.auth.security import get_password_hash

        delete_user = User(
            username="todelete",
            email="delete@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        delete_user.roles = [test_roles["user"]]
        db_session.add(delete_user)
        db_session.commit()
        db_session.refresh(delete_user)

        response = client.delete(
            f"/api/v1/admin/users/{delete_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_list_roles(self, client: TestClient, admin_headers, test_roles):
        """Test listing all roles"""
        response = client.get("/api/v1/admin/roles", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_system_stats(self, client: TestClient, admin_headers):
        """Test getting system statistics"""
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_documents" in data
        assert "total_conversations" in data

    def test_admin_endpoints_require_admin_role(self, client: TestClient, auth_headers):
        """Test that admin endpoints require admin role"""
        endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/roles",
            "/api/v1/admin/stats"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Endpoint {endpoint} should return 403"
