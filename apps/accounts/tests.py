# Python modules

# Django modules

# Django Rest Framework modules
from rest_framework import status

# Third-party modules
import pytest

# Project modules
from apps.accounts.models import User


# =============================================================================
# User Registration Tests
# =============================================================================


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_registration_success(self, api_client, db):
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]

    def test_registration_duplicate_email(self, api_client, user):
        """Test registration fails with duplicate email."""
        data = {
            "email": user.email,
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_registration_password_mismatch(self, api_client, db):
        """Test registration fails when passwords don't match."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_registration_weak_password(self, api_client, db):
        """Test registration fails with weak password."""
        data = {
            "email": "test@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_registration_invalid_email(self, api_client, db):
        """Test registration fails with invalid email format."""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_registration_missing_email(self, api_client, db):
        """Test registration fails without email."""
        data = {
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post("/api/auth/register", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# User Login Tests
# =============================================================================


class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, api_client, user):
        """Test successful login returns JWT tokens."""
        data = {
            "email": user.email,
            "password": "SecurePass123!",
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_login_wrong_password(self, api_client, user):
        """Test login fails with wrong password."""
        data = {
            "email": user.email,
            "password": "WrongPassword123!",
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client, db):
        """Test login fails with non-existent user."""
        data = {
            "email": "nonexistent@example.com",
            "password": "SomePass123!",
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_password(self, api_client, user):
        """Test login fails without password."""
        data = {
            "email": user.email,
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_email(self, api_client, db):
        """Test login fails without email."""
        data = {
            "password": "SomePass123!",
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, db):
        """Test login fails for inactive user."""
        inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="SecurePass123!",
            is_active=False,
        )
        data = {
            "email": inactive_user.email,
            "password": "SecurePass123!",
        }
        response = api_client.post("/api/auth/login", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# User Profile Tests
# =============================================================================


class TestUserProfile:
    """Tests for user profile endpoint."""

    def test_profile_get_success(self, authenticated_client, user):
        """Test getting profile when authenticated."""
        response = authenticated_client.get("/api/auth/profile")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name

    def test_profile_unauthorized(self, api_client, db):
        """Test profile endpoint requires authentication."""
        response = api_client.get("/api/auth/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_update_success(self, authenticated_client, user):
        """Test updating profile."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }
        response = authenticated_client.patch(
            "/api/auth/profile",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

    def test_profile_update_unauthorized(self, api_client, db):
        """Test profile update requires authentication."""
        data = {"first_name": "Hacker"}
        response = api_client.patch("/api/auth/profile", data=data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_cannot_change_email(self, authenticated_client, user):
        """Test email cannot be changed via profile update."""
        original_email = user.email
        data = {"email": "newemail@example.com"}
        response = authenticated_client.patch(
            "/api/auth/profile",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email == original_email


# =============================================================================
# Change Password Tests
# =============================================================================


class TestChangePassword:
    """Tests for change password endpoint."""

    def test_change_password_success(self, authenticated_client, user):
        """Test password can be changed with valid data."""
        data = {
            "old_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
            "new_password_confirm": "NewSecurePass456!",
        }
        response = authenticated_client.post(
            "/api/auth/change-password",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewSecurePass456!")

    def test_change_password_wrong_old(self, authenticated_client, user):
        """Test change password fails with wrong old password."""
        data = {
            "old_password": "WrongOldPass123!",
            "new_password": "NewSecurePass456!",
            "new_password_confirm": "NewSecurePass456!",
        }
        response = authenticated_client.post(
            "/api/auth/change-password",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, authenticated_client, user):
        """Test change password fails when new passwords don't match."""
        data = {
            "old_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
            "new_password_confirm": "DifferentPass789!",
        }
        response = authenticated_client.post(
            "/api/auth/change-password",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_unauthorized(self, api_client, db):
        """Test change password requires authentication."""
        data = {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!",
        }
        response = api_client.post(
            "/api/auth/change-password",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_weak_new_password(self, authenticated_client, user):
        """Test change password fails with weak new password."""
        data = {
            "old_password": "SecurePass123!",
            "new_password": "123",
            "new_password_confirm": "123",
        }
        response = authenticated_client.post(
            "/api/auth/change-password",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
