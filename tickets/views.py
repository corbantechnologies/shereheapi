from rest_framework import generics

from tickets.models import Ticket
from tickets.serializers import TicketSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class TicketListView(generics.ListAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]

    def get_queryset(self):
        return Ticket.objects.filter(booking__event__company__manager=self.request.user)


class TicketDetailView(generics.RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "reference"
