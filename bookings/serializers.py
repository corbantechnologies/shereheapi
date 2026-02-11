from rest_framework import serializers

from bookings.models import Booking
from tickettypes.models import TicketType
from leads.models import Lead
from tickets.serializers import TicketSerializer
from coupons.models import Coupon
from django.utils import timezone


class BookingSerializer(serializers.ModelSerializer):
    ticket_type = serializers.SlugRelatedField(
        slug_field="ticket_type_code", queryset=TicketType.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    ticket_type_info = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(write_only=True, required=False)
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
            "coupon_code",
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

        # Coupon Validation
        coupon_code = attrs.get("coupon_code")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError(
                    {"coupon_code": "Invalid coupon code"}
                )

            if not coupon.is_active:
                raise serializers.ValidationError({"coupon_code": "Coupon is inactive"})

            if coupon.valid_from > timezone.now() or coupon.valid_to < timezone.now():
                raise serializers.ValidationError({"coupon_code": "Coupon is expired"})

            if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon usage limit reached"}
                )

            # Check Event
            if coupon.event != ticket_type.event:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon is not valid for this event"}
                )

            # Check Ticket Type
            if (
                coupon.ticket_type.exists()
                and ticket_type not in coupon.ticket_type.all()
            ):
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon is not valid for this ticket type"}
                )

            attrs["coupon"] = coupon

        return attrs

    def create(self, validated_data):
        # Remove coupon_code from validated_data as it's not a field on the model
        if "coupon_code" in validated_data:
            del validated_data["coupon_code"]

        booking = Booking.objects.create(**validated_data)
        booking.save()

        # Increment coupon usage
        if booking.coupon:
            booking.coupon.save()  # The save method increments usage_count

        Lead.objects.create(
            name=booking.name,
            email=booking.email,
            phone=booking.phone,
            message=f"Booking for {booking.quantity} tickets of {booking.ticket_type.name} by {booking.name} ({booking.phone}) for the event {booking.ticket_type.event.name}",
        )
        return booking
