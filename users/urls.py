from django.conf.urls import url
from users.views import AuthLoginView, AuthLogoutView, UserRegisterView


urlpatterns = [
    url(r'auth/login', AuthLoginView.as_view(), name='auth-login'),
    url(r'auth/logout', AuthLogoutView.as_view(), name='auth-logout'),
    url(r'users/register$', UserRegisterView.as_view(), name='user-register'),
]
