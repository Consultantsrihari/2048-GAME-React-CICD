import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app

client = TestClient(app)

# Mock token data
mock_admin_token = {
    "user_id": "1",
    "email": "admin@autocompany.com",
    "role": "admin"
}

mock_user_token = {
    "user_id": "3",
    "email": "customer@autocompany.com",
    "role": "customer"
}

class TestUsersAPI:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "users-api"

    @patch("src.main.verify_token")
    def test_get_my_profile(self, mock_verify):
        """Test getting current user's profile"""
        mock_verify.return_value = mock_user_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "3"
        assert data["email"] == "customer@autocompany.com"
        assert data["first_name"] == "Jane"

    @patch("src.main.verify_token")
    def test_update_my_profile(self, mock_verify):
        """Test updating current user's profile"""
        mock_verify.return_value = mock_user_token
        
        update_data = {
            "first_name": "Janet",
            "phone": "+1-555-9999"
        }
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.put("/users/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Janet"
        assert data["phone"] == "+1-555-9999"

    @patch("src.main.verify_token")
    def test_get_user_profile_admin(self, mock_verify):
        """Test getting user profile as admin"""
        mock_verify.return_value = mock_admin_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users/2", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "2"
        assert data["email"] == "dealer@autocompany.com"

    @patch("src.main.verify_token")
    def test_get_user_profile_forbidden(self, mock_verify):
        """Test getting another user's profile as non-admin"""
        mock_verify.return_value = mock_user_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users/2", headers=headers)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied"

    @patch("src.main.verify_token")
    def test_list_users_admin(self, mock_verify):
        """Test listing users as admin"""
        mock_verify.return_value = mock_admin_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    @patch("src.main.verify_token")
    def test_list_users_forbidden(self, mock_verify):
        """Test listing users as non-admin"""
        mock_verify.return_value = mock_user_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users", headers=headers)
        
        assert response.status_code == 403

    @patch("src.main.verify_token")
    def test_create_user_profile(self, mock_verify):
        """Test creating user profile as admin"""
        mock_verify.return_value = mock_admin_token
        
        profile_data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1-555-1234"
        }
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.post("/users", json=profile_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"

    @patch("src.main.verify_token")
    def test_search_users(self, mock_verify):
        """Test searching users"""
        mock_verify.return_value = mock_admin_token
        
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/users/search?q=admin", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["query"] == "admin"