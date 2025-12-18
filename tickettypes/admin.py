from django.contrib import admin

from tickettypes.models import TicketType


class TicketTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event",
        "price",
        "quantity_available",
        "is_limited",
        "ticket_type_code",
    )
    list_filter = ("event", "is_limited")
    search_fields = ("name", "event__name")


admin.site.register(TicketType, TicketTypeAdmin)
