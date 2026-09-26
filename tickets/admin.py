from django.contrib import admin

from tickets.models import Ticket, TicketScanLog


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking",
        "ticket_type",
        "ticket_code",
        "is_used",
        "gate_station",
        "used_at",
        "created_at",
    )
    list_filter = ("is_used", "gate_station", "created_at")
    search_fields = ("ticket_code", "reference", "booking__name", "booking__phone")


class TicketScanLogAdmin(admin.ModelAdmin):
    list_display = (
        "event_code",
        "scanned_code",
        "status",
        "gate_station",
        "ticket",
        "scanned_by",
        "created_at",
    )
    list_filter = ("status", "gate_station", "created_at")
    search_fields = ("scanned_code", "event_code", "notes")


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketScanLog, TicketScanLogAdmin)

