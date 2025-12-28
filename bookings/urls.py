from django.urls import path

from bookings.views import BookingCreateView, BookingListView, BookingDetailView

app_name = "bookings"

urlpatterns = [
    path("create/event/", BookingCreateView.as_view(), name="create"),
    path("", BookingListView.as_view(), name="list"),
    path("<str:reference>/", BookingDetailView.as_view(), name="detail"),
]
