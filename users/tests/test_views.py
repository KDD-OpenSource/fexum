from rest_framework.test import APITestCase
from users.tests.factories import UserFactory, TokenFactory, TEST_PASSWORD
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.authtoken.models import Token


class TestTokenAuthenticationView(APITestCase):
    def test_authenticate(self):
        user = UserFactory()
        data = {
            'username': user.username,
            'password': TEST_PASSWORD
        }

        self.assertEqual(Token.objects.count(), 0)

        url = reverse('auth-login')
        response = self.client.post(url, data=data)

        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(response.status_code, HTTP_200_OK)
        response_data = response.json()

        token = Token.objects.get(key=response_data['token'])
        self.assertEqual(token.user, user)

    def test_authenticate_wrong_credentials(self):
        pass

    def test_authenticate_missing_data(self):
        pass


class TestLogoutView(APITestCase):
    def test_logout(self):
        token = TokenFactory()

        self.assertEqual(Token.objects.count(), 1)

        url = reverse('auth-logout')
        self.client.credentials(HTTP_AUTHORIZATION='Token {0}'.format(token.key))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertEqual(Token.objects.count(), 0)

    def test_logout_unauthenticated(self):
        pass
