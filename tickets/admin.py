from django.contrib import admin

from tickets.models import Ticket


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking",
        "ticket_type",
        "ticket_code",
        "qr_code",
        "is_used",
        "created_at",
        "updated_at",
    )


admin.site.register(Ticket, TicketAdmin)
