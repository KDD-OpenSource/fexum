from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from users.serializers import UserSerializer
from rest_framework.permissions import AllowAny


class LogoutView(APIView):
    def delete(self, request):
        token = request.auth
        Token.objects.get(key=token).delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UserRegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
