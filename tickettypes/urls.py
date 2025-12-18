from django.urls import path
from tickettypes.views import TicketTypeListCreateView, TicketTypeDetailView

app_name = "tickettypes"

urlpatterns = [
    path("", TicketTypeListCreateView.as_view(), name="tickettype-list-create"),
    path(
        "<str:ticket_type_code>",
        TicketTypeDetailView.as_view(),
        name="tickettype-detail",
    ),
]
