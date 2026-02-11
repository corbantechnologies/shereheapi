from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.utils import timezone

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly
from tickettypes.models import TicketType


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "reference"

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def validate(self, request):
        code = request.data.get("code")
        event_code = request.data.get("event_code")
        ticket_type_code = request.data.get("ticket_type_code")

        if not code or not event_code:
            return Response(
                {"error": "Please provide code and event_code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code"}, status=status.HTTP_404_NOT_FOUND
            )

        if not coupon.is_active:
            return Response(
                {"error": "Coupon is inactive"}, status=status.HTTP_400_BAD_REQUEST
            )

        if coupon.valid_from > timezone.now() or coupon.valid_to < timezone.now():
            return Response(
                {"error": "Coupon is expired"}, status=status.HTTP_400_BAD_REQUEST
            )

        if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
            return Response(
                {"error": "Coupon usage limit reached"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check Event
        if coupon.event.event_code != event_code:
            return Response(
                {"error": "Coupon is not valid for this event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check Ticket Type
        if ticket_type_code:
            try:
                ticket_type = TicketType.objects.get(ticket_type_code=ticket_type_code)
            except TicketType.DoesNotExist:
                return Response(
                    {"error": "Invalid ticket type"}, status=status.HTTP_404_NOT_FOUND
                )

            if (
                coupon.ticket_type.exists()
                and ticket_type not in coupon.ticket_type.all()
            ):
                return Response(
                    {"error": "Coupon is not valid for this ticket type"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            discount_value = coupon.apply_discount(ticket_type)
            discount_amount = ticket_type.price - discount_value
        else:
            # If no ticket type provided, just return coupon info?
            # Or requires ticket type to calculate discount?
            # Logic: If ticket type provided, return exact discount.
            # If not, return general info.
            # For now, let's assume specific booking uses ticket type.
            discount_amount = 0

        return Response(
            {
                "message": "Coupon applied successfully",
                "discount_amount": discount_amount,
                "discount_value": coupon.discount_value,
                "discount_type": coupon.discount_type,
            },
            status=status.HTTP_200_OK,
        )
