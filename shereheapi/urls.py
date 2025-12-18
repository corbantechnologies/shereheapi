from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/company/", include("company.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/tickettypes/", include("tickettypes.urls")),
]
