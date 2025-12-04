"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication API endpoints"""

    def test_register_new_user(self, client: TestClient, test_roles):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "pass123"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpass"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost", "password": "pass123"}
        )
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, auth_headers, test_user):
        """Test getting current authenticated user"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "roles" in data
        assert "permissions" in data

    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_update_profile(self, client: TestClient, auth_headers):
        """Test updating user profile"""
        response = client.put(
            "/api/v1/auth/profile",
            headers=auth_headers,
            json={"email": "updated@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    def test_change_password(self, client: TestClient, auth_headers):
        """Test changing password"""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpass123",
                "new_password": "newtestpass123"
            }
        )
        assert response.status_code == 200

        # Try logging in with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "newtestpass123"}
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test changing password with wrong current password"""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpass",
                "new_password": "newtestpass123"
            }
        )
        assert response.status_code == 400
