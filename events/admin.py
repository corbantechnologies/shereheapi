from django.contrib import admin

from events.models import Event, PayoutRequest


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "manager",
        "start_date",
        "end_date",
        "venue",
        "capacity",
        "event_code",
        "is_published",
        "is_closed",
        "gate_passcode",
    )
    list_filter = ("manager", "is_published", "is_closed", "capacity", "event_code", "company")
    search_fields = ("name", "manager__username", "event_code")


class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "event",
        "company",
        "requested_by",
        "amount_requested",
        "net_payout_amount",
        "payout_phone",
        "status",
        "mpesa_transaction_id",
        "created_at",
        "disbursed_at",
    )
    list_filter = ("status", "created_at", "disbursed_at")
    search_fields = (
        "reference",
        "event__name",
        "payout_phone",
        "mpesa_transaction_id",
        "requested_by__email",
    )


admin.site.register(Event, EventAdmin)
admin.site.register(PayoutRequest, PayoutRequestAdmin)

