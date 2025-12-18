from rest_framework import serializers

from tickettypes.models import TicketType
from events.models import Event


class TicketTypeSerializer(serializers.ModelSerializer):
    event = serializers.SlugRelatedField(
        slug_field="event_code", queryset=Event.objects.all()
    )

    class Meta:
        model = TicketType
        fields = [
            "event",
            "name",
            "price",
            "quantity_available",
            "is_limited",
            "ticket_type_code",
            "created_at",
            "updated_at",
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

        return attrs
