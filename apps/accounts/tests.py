from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.accounts.models import User


class UserRegistrationTestCase(APITestCase):
    """Tests for user registration endpoint."""

    def test_registration_success(self):
        """Test successful user registration."""
        url = reverse('accounts:register')
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email."""
        User.objects.create_user(email='existing@example.com', password='pass123')
        url = reverse('accounts:register')
        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        url = reverse('accounts:register')
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)


class UserLoginTestCase(APITestCase):
    """Tests for user login endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login returns JWT tokens."""
        url = reverse('accounts:login')
        data = {
            'email': 'user@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        url = reverse('accounts:login')
        data = {
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login fails with non-existent user."""
        url = reverse('accounts:login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTestCase(APITestCase):
    """Tests for user profile endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='testpass123',
            first_name='Profile',
            last_name='User'
        )

    def test_profile_unauthorized(self):
        """Test profile endpoint requires authentication."""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authorized(self):
        """Test profile endpoint returns user data when authenticated."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@example.com')
        self.assertEqual(response.data['first_name'], 'Profile')

    def test_profile_update(self):
        """Test profile can be updated."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')


class ChangePasswordTestCase(APITestCase):
    """Tests for change password endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='changepwd@example.com',
            password='OldPass123!'
        )

    def test_change_password_success(self):
        """Test password can be changed with valid data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:change_password')
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456!'))

    def test_change_password_wrong_old(self):
        """Test change password fails with wrong old password."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:change_password')
        data = {
            'old_password': 'WrongOld123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
