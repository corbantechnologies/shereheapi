from django.urls import path

from events.views import EventListCreateView, EventRetrieveUpdateDestroyView

app_name = "events"

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path(
        "<str:event_code>/",
        EventRetrieveUpdateDestroyView.as_view(),
        name="event-retrieve-update-destroy",
    ),
]
