from django.urls import path
from tickets.views import TicketListView, TicketDetailView

app_name = "tickets"

urlpatterns = [
    path("", TicketListView.as_view(), name="list"),
    path("<str:reference>", TicketDetailView.as_view(), name="detail"),
]
