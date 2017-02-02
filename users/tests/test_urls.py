from django.urls import reverse
from django.test import TestCase


class TestLoginUrl(TestCase):
    def test_login_url(self):
        url = reverse('auth-login')
        self.assertEqual(url, '/api/auth/login')


class TestLogoutUrl(TestCase):
    def test_logout_url(self):
        url = reverse('auth-logout')
        self.assertEqual(url, '/api/auth/logout')


class TestRegisterUrl(TestCase):
    def test_register_url(self):
        url = reverse('user-register')
        self.assertEqual(url, '/api/users/register')
