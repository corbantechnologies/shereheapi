from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import timedelta

from bookings.serializers import BookingSerializer
from bookings.models import Booking
from company.permissions import IsEventManagerOwnerOrReadOnly


class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [
        AllowAny,
    ]


class BookingListView(generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]

    def get_queryset(self):
        # Base queryset for organizer's bookings
        queryset = Booking.objects.filter(
            ticket_type__event__company__manager=self.request.user
        )

        # Defualt expiration threshold (30 minutes)
        threshold_time = timezone.now() - timedelta(minutes=15)

        # Exclude bookings that are PENDING and older than the threshold
        return queryset.exclude(status="PENDING", created_at__lt=threshold_time)


class BookingDetailView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]
    lookup_field = "reference"

    
