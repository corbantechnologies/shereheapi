from django.urls import path

from events.views import EventListCreateView, EventRetrieveUpdateDestroyView
from tickets.scan_views import (
    TicketScanView,
    GateStatsView,
    GateAttendeeSearchView,
    GateManualCheckInView,
)

from events.settlement_views import (
    EventSettlementView,
    EventPayoutRequestView,
)

app_name = "events"

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path(
        "<str:event_code>/",
        EventRetrieveUpdateDestroyView.as_view(),
        name="event-retrieve-update-destroy",
    ),
    path(
        "<str:event_code>/scan/",
        TicketScanView.as_view(),
        name="event-scan",
    ),
    path(
        "<str:event_code>/gate-stats/",
        GateStatsView.as_view(),
        name="event-gate-stats",
    ),
    path(
        "<str:event_code>/attendees/",
        GateAttendeeSearchView.as_view(),
        name="event-attendees",
    ),
    path(
        "<str:event_code>/manual-checkin/",
        GateManualCheckInView.as_view(),
        name="event-manual-checkin",
    ),
    path(
        "<str:event_code>/settlement/",
        EventSettlementView.as_view(),
        name="event-settlement",
    ),
    path(
        "<str:event_code>/payout-request/",
        EventPayoutRequestView.as_view(),
        name="event-payout-request",
    ),
]

