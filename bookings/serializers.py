from rest_framework import serializers

from bookings.models import Booking
from tickettypes.models import TicketType
from leads.models import Lead
from tickets.serializers import TicketSerializer


class BookingSerializer(serializers.ModelSerializer):
    ticket_type = serializers.SlugRelatedField(
        slug_field="ticket_type_code", queryset=TicketType.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    ticket_type_info = serializers.SerializerMethodField()
    # TODO: Add tickets
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "name",
            "email",
            "phone",
            "quantity",
            "amount",
            "status",
            "booking_code",
            "event",
            "payment_status",
            "payment_status_description",
            "payment_method",
            "confirmation_code",
            "payment_account",
            "currency",
            "payment_date",
            "mpesa_receipt_number",
            "mpesa_phone_number",
            "ticket_type",
            "created_at",
            "updated_at",
            "reference",
            "tickets",
            "ticket_type_info",
        ]

    def get_ticket_type_info(self, obj):
        return {
            "ticket_type_code": obj.ticket_type.ticket_type_code,
            "name": obj.ticket_type.name,
            "price": obj.ticket_type.price,
        }

    def validate(self, attrs):
        ticket_type = attrs.get("ticket_type")
        quantity = attrs.get("quantity")

        if ticket_type.is_limited and ticket_type.quantity_available is not None:
            if quantity > ticket_type.quantity_available:
                raise serializers.ValidationError(
                    f"Only {ticket_type.quantity_available} tickets are available for this ticket type."
                )

        return attrs

    def create(self, validated_data):
        booking = Booking.objects.create(**validated_data)
        booking.save()
        Lead.objects.create(
            name=booking.name,
            email=booking.email,
            phone=booking.phone,
            message=f"Booking for {booking.quantity} tickets of {booking.ticket_type.name} by {booking.name} ({booking.phone}) for the event {booking.ticket_type.event.name}",
        )
        return booking
