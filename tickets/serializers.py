from rest_framework import serializers
from tickets.models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    qr_code = serializers.ImageField(read_only=True, use_url=True)
    booking_info = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "reference",
            "booking",
            "ticket_type",
            "ticket_code",
            "qr_code",
            "is_used",
            "created_at",
            "updated_at",
            "booking_info",
        ]

    def get_booking_info(self, obj):
        info = {
            "name": obj.booking.name,
            "email": obj.booking.email,
            "phone": obj.booking.phone,
            "quantity": obj.booking.quantity,
            "amount": obj.booking.amount,
            "status": obj.booking.status,
            "booking_code": obj.booking.booking_code,
            "event": obj.booking.event,
            "payment_status": obj.booking.payment_status,
            "payment_status_description": obj.booking.payment_status_description,
            "payment_method": obj.booking.payment_method,
            "confirmation_code": obj.booking.confirmation_code,
            "payment_account": obj.booking.payment_account,
            "currency": obj.booking.currency,
            "payment_date": obj.booking.payment_date,
            "mpesa_receipt_number": obj.booking.mpesa_receipt_number,
            "mpesa_phone_number": obj.booking.mpesa_phone_number,
            "reference": obj.booking.reference,
        }

        request = self.context.get("request")
        is_manager = False
        if request and request.user and request.user.is_authenticated:
            if request.user.is_superuser or (
                hasattr(request.user, "is_event_manager")
                and request.user.is_event_manager
                and obj.ticket_type.event.manager == request.user
            ):
                is_manager = True

        if not is_manager:
            sensitive_fields = [
                "payment_account",
                "mpesa_receipt_number",
                "mpesa_phone_number",
                "payment_method",
                "payment_date",
                "payment_status_description",
            ]
            for field in sensitive_fields:
                info.pop(field, None)

        return info
