from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from backend import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('users.urls', namespace="users")),
    path('', include('home.urls', namespace="home")),
]

if settings.DEBUG:
    urlpatterns = [
                      path("__debug__/", include("debug_toolbar.urls")),
                  ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)