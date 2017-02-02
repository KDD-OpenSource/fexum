from django.test import TestCase
from users.serializers import UserSerializer
from users.tests.factories import UserFactory


class TestUserSerializer(TestCase):
    def test_serialize(self):
        user = UserFactory()
        serializer = UserSerializer(instance=user)
        data =  serializer.data

        self.assertEqual(data.pop('username'), user.username)
        self.assertEqual(len(data), 0)
