from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from users.serializers import UserSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import login, logout
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import login, logout
from users.authentication import CustomBaseAuthentication


class AuthLoginView(APIView):
    authentication_classes = (CustomBaseAuthentication, SessionAuthentication)

    def post(self, request):
        login(request, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class AuthLogoutView(APIView):
    def delete(self, request):
        logout(request)
        return Response(status=HTTP_204_NO_CONTENT)


class UserRegisterView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = () # TODO: Remove

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
