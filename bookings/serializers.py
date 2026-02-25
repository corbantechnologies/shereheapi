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
    coupon = serializers.SlugRelatedField(
        slug_field="code", queryset=Coupon.objects.all(), required=False
    )
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
            "coupon",
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

        status = ticket_type.status
        if status == "PAUSED":
            raise serializers.ValidationError(
                {
                    "ticket_type": "This ticket type is currently paused and not available for sale."
                }
            )
        elif status == "UPCOMING":
            raise serializers.ValidationError(
                {"ticket_type": "Sales for this ticket type have not started yet."}
            )
        elif status == "ENDED":
            raise serializers.ValidationError(
                {"ticket_type": "Sales for this ticket type have ended."}
            )
        elif status == "SOLD_OUT":
            raise serializers.ValidationError(
                {"ticket_type": "This ticket type is sold out."}
            )

        total_type_tickets_sold = ticket_type.tickets_sold
        total_event_tickets_sold = sum(
            t.tickets_sold for t in ticket_type.event.ticket_types.all()
        )

        if ticket_type.is_limited and ticket_type.quantity_available is not None:
            if quantity + total_type_tickets_sold > ticket_type.quantity_available:
                available = ticket_type.quantity_available - total_type_tickets_sold
                raise serializers.ValidationError(
                    {
                        "ticket_type": f"Only {max(0, available)} tickets remaining for this ticket type."
                    }
                )

        if ticket_type.event.capacity is not None:
            if quantity + total_event_tickets_sold > ticket_type.event.capacity:
                available = ticket_type.event.capacity - total_event_tickets_sold
                raise serializers.ValidationError(
                    {
                        "ticket_type": f"Event capacity reached. Only {max(0, available)} total tickets remaining for this event."
                    }
                )

        # Coupon Validation
        coupon = attrs.get("coupon")
        if coupon:
            # Coupon is already a model instance from SlugRelatedField validation
            if not coupon.is_active:
                raise serializers.ValidationError({"coupon": "Coupon is inactive"})

            if coupon.valid_from > timezone.now():
                raise serializers.ValidationError(
                    {"coupon": "Coupon is not yet active"}
                )

            if coupon.valid_to < timezone.now():
                raise serializers.ValidationError({"coupon": "Coupon has expired"})

            if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
                raise serializers.ValidationError(
                    {"coupon": "Coupon usage limit reached"}
                )

            # Check Event
            if coupon.event != ticket_type.event:
                raise serializers.ValidationError(
                    {"coupon": "Coupon is not valid for this event"}
                )

            # Check Ticket Type
            if (
                coupon.ticket_type.exists()
                and ticket_type not in coupon.ticket_type.all()
            ):
                raise serializers.ValidationError(
                    {"coupon": "Coupon is not valid for this ticket type"}
                )

            attrs["coupon"] = coupon

        return attrs

    def create(self, validated_data):
        # Coupon is now a field on the Booking model, so we keep it in validated_data

        booking = Booking.objects.create(**validated_data)
        booking.save()

        # Increment coupon usage
        if booking.coupon:
            booking.coupon.usage_count += 1
            booking.coupon.save()

            # check if usage limit reached
            if (
                booking.coupon.usage_limit > 0
                and booking.coupon.usage_count >= booking.coupon.usage_limit
            ):
                booking.coupon.is_active = False
                booking.coupon.save()

        Lead.objects.create(
            name=booking.name,
            email=booking.email,
            phone=booking.phone,
            message=f"Booking for {booking.quantity} tickets of {booking.ticket_type.name} by {booking.name} ({booking.phone}) for the event {booking.ticket_type.event.name}",
        )
        return booking
