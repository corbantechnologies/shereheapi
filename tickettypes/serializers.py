from rest_framework import serializers

from tickettypes.models import TicketType
from events.models import Event
from bookings.serializers import BookingSerializer


class TicketTypeSerializer(serializers.ModelSerializer):
    event = serializers.SlugRelatedField(
        slug_field="event_code", queryset=Event.objects.all()
    )
    bookings = BookingSerializer(many=True, read_only=True)
    tickets_sold = serializers.IntegerField(read_only=True)

    class Meta:
        model = TicketType
        fields = [
            "event",
            "name",
            "price",
            "quantity_available",
            "is_limited",
            "sales_start",
            "sales_end",
            "is_active",
            "status",
            "ticket_type_code",
            "created_at",
            "updated_at",
            "reference",
            "bookings",
            "tickets_sold",
        ]

    def validate(self, attrs):
        # Ensure price is non-negative
        if attrs.get("price", 0) < 0:
            raise serializers.ValidationError("Price cannot be negative.")

        # Ensure quantity_available, if provided, is positive
        if (
            attrs.get("quantity_available") is not None
            and attrs["quantity_available"] < 1
        ):
            raise serializers.ValidationError("Quantity available must be at least 1.")

        # Validate ticket type quantity against event capacity
        event = attrs.get("event")
        if event and event.capacity:
            # Sum quantities of existing ticket types for the event
            total_tickets = sum(
                tt.quantity_available
                for tt in TicketType.objects.filter(event=event)
                if tt.quantity_available is not None
            )
            # Add the quantity from the current ticket type being validated
            current_quantity = attrs.get("quantity_available", 0) or 0
            # If updating, exclude the current ticket type's quantity from the sum
            if self.instance:
                total_tickets -= self.instance.quantity_available or 0
            total_tickets += current_quantity
            if total_tickets > event.capacity:
                raise serializers.ValidationError(
                    f"Total ticket quantities ({total_tickets}) exceed event capacity ({event.capacity})."
                )

        # Timeframes Validation
        sales_start = attrs.get("sales_start")
        sales_end = attrs.get("sales_end")

        # In case of partial update, fallback to existing instance values
        if self.instance:
            sales_start = (
                sales_start if "sales_start" in attrs else self.instance.sales_start
            )
            sales_end = sales_end if "sales_end" in attrs else self.instance.sales_end
            event = event if "event" in attrs else self.instance.event

        if sales_start and sales_end:
            if sales_start >= sales_end:
                raise serializers.ValidationError(
                    {"sales_end": "Sales end date must be after sales start date."}
                )

        # Validate against Event dates if event is resolved
        if event:
            import datetime

            event_cutoff_date = event.end_date if event.end_date else event.start_date

            if event_cutoff_date:
                # To be lenient, we'll allow selling *on* the end date, so we check if start > cutoff
                # or end > cutoff directly with dates.

                if sales_start and sales_start > event_cutoff_date:
                    raise serializers.ValidationError(
                        {
                            "sales_start": "Sales must start before or on the day the event concludes."
                        }
                    )

                if sales_end and sales_end > event_cutoff_date:
                    raise serializers.ValidationError(
                        {
                            "sales_end": "Sales must end before or on the day the event concludes."
                        }
                    )

        return attrs


class TicketTypeInlineSerializer(TicketTypeSerializer):
    """
    Serializer for ticket types when nested within an event.
    The event field is read-only because it's inferred from the parent event.
    """

    event = serializers.SlugRelatedField(slug_field="event_code", read_only=True)
