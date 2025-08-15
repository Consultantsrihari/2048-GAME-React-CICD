import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestAuthAPI:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-api"

    def test_login_success(self):
        """Test successful login"""
        login_data = {
            "email": "admin@autocompany.com",
            "password": "admin123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 24 * 3600

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "admin@autocompany.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@autocompany.com",
            "password": "password123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_register_success(self):
        """Test successful user registration"""
        register_data = {
            "email": "newuser@autocompany.com",
            "password": "password123",
            "role": "customer"
        }
        response = client.post("/auth/register", json=register_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@autocompany.com"
        assert data["role"] == "customer"
        assert data["is_active"] is True

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        register_data = {
            "email": "admin@autocompany.com",
            "password": "password123",
            "role": "customer"
        }
        response = client.post("/auth/register", json=register_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_verify_token_success(self):
        """Test token verification with valid token"""
        # First login to get token
        login_data = {
            "email": "admin@autocompany.com",
            "password": "admin123"
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Verify token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/verify", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@autocompany.com"
        assert data["role"] == "admin"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/verify", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_list_users_admin(self):
        """Test listing users as admin"""
        # Login as admin
        login_data = {
            "email": "admin@autocompany.com",
            "password": "admin123"
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # List users
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_list_users_non_admin(self):
        """Test listing users as non-admin user"""
        # Login as customer
        login_data = {
            "email": "customer@autocompany.com",
            "password": "customer123"
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Try to list users
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"