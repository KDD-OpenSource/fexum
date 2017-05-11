from django.contrib import admin
from django.conf.urls import url, include


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('features.urls')),
    url(r'^api/', include('users.urls')),
    url(r'^api/', include('tasks.urls')),
]