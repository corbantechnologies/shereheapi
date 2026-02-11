from rest_framework import serializers

from coupons.models import Coupon
from events.models import Event
from tickettypes.models import TicketType


class CouponSerializer(serializers.ModelSerializer):
    manager = serializers.CharField(source="manager.username", read_only=True)
    event = serializers.SlugRelatedField(
        slug_field="event_code", queryset=Event.objects.all()
    )
    ticket_type = serializers.SlugRelatedField(
        slug_field="ticket_type_code",
        queryset=TicketType.objects.all(),
        many=True,
        required=False,
    )
    event_details = serializers.SerializerMethodField()

    def get_event_details(self, obj):
        return {
            "company": obj.event.company.name,
            "event_code": obj.event.event_code,
            "name": obj.event.name,
            "start_date": obj.event.start_date,
            "end_date": obj.event.end_date,
        }

    def validate(self, attrs):
        event = attrs.get("event")
        ticket_types = attrs.get("ticket_type", [])

        if ticket_types:
            for ticket_type in ticket_types:
                if ticket_type.event != event:
                    raise serializers.ValidationError(
                        f"Ticket type {ticket_type.name} does not belong to event {event.name}"
                    )
        return attrs

    class Meta:
        model = Coupon
        fields = (
            "id",
            "manager",
            "event",
            "ticket_type",
            "name",
            "code",
            "discount_value",
            "discount_type",
            "valid_from",
            "valid_to",
            "usage_limit",
            "usage_count",
            "is_active",
            "created_at",
            "updated_at",
            "reference",
            "event_details",
        )
