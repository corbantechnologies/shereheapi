from rest_framework import generics

from events.models import Event
from events.serializers import EventSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EventRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "event_code"
