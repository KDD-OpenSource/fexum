from django.conf.urls import url
from users.views import LogoutView
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    url(r'auth/login$', obtain_auth_token, name='auth-login'),
    url(r'auth/logout$', LogoutView.as_view(), name='auth-logout'),
]
