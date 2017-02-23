from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer


class CSRFLessSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

    
class CustomBaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return (user, None)
