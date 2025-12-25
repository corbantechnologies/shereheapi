from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/company/", include("company.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/tickettypes/", include("tickettypes.urls")),
    path("api/v1/bookings/", include("bookings.urls")),
    path("api/v1/tickets/", include("tickets.urls")),
    path("api/v1/mpesa/", include("mpesa.urls")),
]
