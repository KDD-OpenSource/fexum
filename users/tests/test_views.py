from rest_framework.test import APITestCase
from users.tests.factories import UserFactory, TokenFactory, TEST_PASSWORD
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, \
    HTTP_401_UNAUTHORIZED
from rest_framework.authtoken.models import Token
from users.serializers import UserSerializer
from users.models import User


class TestTokenAuthenticationView(APITestCase):
    url = reverse('auth-login')

    def test_authenticate(self):
        user = UserFactory()
        data = {
            'username': user.username,
            'password': TEST_PASSWORD
        }

        self.assertEqual(Token.objects.count(), 0)

        response = self.client.post(self.url, data=data)

        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(response.status_code, HTTP_200_OK)
        response_data = response.json()

        token = Token.objects.get(key=response_data['token'])
        self.assertEqual(token.user, user)

    def test_authenticate_wrong_credentials(self):
        data = {
            'username': 'something',
            'password': 'something'
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'non_field_errors': ['Unable to log in with provided credentials.']})

    def test_authenticate_missing_data(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'username': ['This field is required.'],
                                           'password': ['This field is required.']})


class TestLogoutView(APITestCase):
    url = reverse('auth-logout')

    def test_logout(self):
        token = TokenFactory()

        self.assertEqual(Token.objects.count(), 1)

        self.client.credentials(HTTP_AUTHORIZATION='Token {0}'.format(token.key))
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertEqual(Token.objects.count(), 0)

    def test_logout_unauthenticated(self):
        url = reverse('auth-logout')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestUserRegisterView(APITestCase):
    url = reverse('user-register')

    def test_register(self):
        data = {
            'username': 'username',
            'password': TEST_PASSWORD
        }
        self.assertEqual(User.objects.count(), 0)

        response = self.client.post(self.url, data=data)

        self.assertEqual(User.objects.count(), 1)

        data = UserSerializer(instance=User.objects.first()).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), data)

    def test_register_missing_data(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'password': ['This field is required.'],
                                           'username': ['This field is required.']})

    def test_register_duplicate_data(self):
        user = UserFactory()
        data = {
            'username': user.username,
            'password': TEST_PASSWORD
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'username': ['A user with that username already exists.']})
