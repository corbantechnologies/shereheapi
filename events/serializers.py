from rest_framework import serializers
from django.contrib.auth import get_user_model

from events.models import Event
from events.utils import send_event_created_email
from company.models import Company

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    company = serializers.SlugRelatedField(
        queryset=Company.objects.all(), slug_field="company_code"
    )
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "created_by",
            "company",
            "name",
            "description",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "venue",
            "capacity",
            "image",
            "is_closed",
            "cancellation_policy",
            "identity",
            "event_code",
            "created_at",
            "updated_at",
            "reference",
        ]

    def validate(self, attrs):
        # Validate date range
        if attrs.get("end_date") and attrs.get("start_date"):
            if attrs["end_date"] < attrs["start_date"]:
                raise serializers.ValidationError("End date must be after start date.")

        # Validate time range (if end_date matches start_date)
        if (
            attrs.get("end_date") == attrs.get("start_date")
            and attrs.get("end_time")
            and attrs.get("start_time")
            and attrs["end_time"] <= attrs["start_time"]
        ):
            raise serializers.ValidationError(
                "End time must be after start time on the same day."
            )

        # # Validate ticket_types if provided
        # ticket_types = attrs.get("ticket_types")
        # if ticket_types:  # Only validate if ticket_types is provided
        #     # Validate ticket type quantities against event capacity
        #     if attrs.get("capacity"):
        #         total_tickets = sum(
        #             tt.get("quantity_available", attrs["capacity"] or 0)
        #             for tt in ticket_types
        #             if tt.get("quantity_available") is not None
        #         )
        #         if total_tickets > attrs["capacity"]:
        #             raise serializers.ValidationError(
        #                 "Total ticket quantities cannot exceed event capacity."
        #             )

        return attrs

    def create(self, validated_data):
        event = super().create(validated_data)
        send_event_created_email(event.created_by, event)
        return event
