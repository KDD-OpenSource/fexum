from factory import DjangoModelFactory, Sequence, SubFactory, PostGenerationMethodCall
from users.models import User
from rest_framework.authtoken.models import Token


TEST_PASSWORD = 'asdf1234'


class UserFactory(DjangoModelFactory):

    class Meta:
        model = User

    username = Sequence(lambda x: 'user_{0}'.format(x))
    password = PostGenerationMethodCall('set_password', TEST_PASSWORD)
    email = Sequence(lambda x: 'user_{0}@example.com'.format(x))


class TokenFactory(DjangoModelFactory):
    class Meta:
        model = Token

    user = SubFactory(UserFactory)
