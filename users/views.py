from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT


class LogoutView(APIView):
    def delete(self, request):
        token = request.token
        Token.objects.get(key=token).delete()
        return Response(status=HTTP_204_NO_CONTENT)
