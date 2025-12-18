from django.contrib import admin

from events.models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "manager",
        "start_date",
        "end_date",
        "venue",
        "capacity",
        "event_code",
        "is_closed",
    )
    list_filter = ("manager", "is_closed", "capacity", "event_code", "company")
    search_fields = ("name", "manager__username")


admin.site.register(Event, EventAdmin)
