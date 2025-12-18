from django.conf.urls.static import static
from django.urls import path

from backend import settings
from . import views

app_name = "users"

urlpatterns = [
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)