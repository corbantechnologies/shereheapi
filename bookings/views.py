from rest_framework import generics
from rest_framework.permissions import AllowAny

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
        return Booking.objects.filter(
            ticket_type__event__company__manager=self.request.user
        )


class BookingDetailView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [
        IsEventManagerOwnerOrReadOnly,
    ]
    lookup_field = "reference"

    
