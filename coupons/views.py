from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly
from tickettypes.models import TicketType


class CouponListCreateView(generics.ListCreateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Coupon.objects.all()
        event_code = self.request.query_params.get("event_code")
        if event_code:
            queryset = queryset.filter(event__event_code=event_code)
        return queryset

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class CouponRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "reference"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CouponValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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

        if coupon.valid_from > timezone.now().date():
            return Response(
                {"error": "Coupon is not yet active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if coupon.valid_to < timezone.now().date():
            return Response(
                {"error": "Coupon has expired"}, status=status.HTTP_400_BAD_REQUEST
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
