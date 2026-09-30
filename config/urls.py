"""نشانی‌های اصلی پروژه."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("skills/", include("skills.urls")),
    path("exchanges/", include("exchanges.urls")),
    path("manage-panel/", include("dashboard.urls")),
    path("", include("config.home_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
