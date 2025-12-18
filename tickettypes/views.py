from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from tickettypes.models import TicketType
from tickettypes.serializers import TicketTypeSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class TicketTypeListCreateView(generics.ListCreateAPIView):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]


class TicketTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "ticket_type_code"
