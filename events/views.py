from rest_framework import generics

from events.models import Event
from events.serializers import EventSerializer
from company.permissions import IsEventManagerOwnerOrReadOnly


class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        # if the user is the event owner/manager, show all events; if not, show only published events
        if self.request.user.is_authenticated and getattr(
            self.request.user, "is_event_manager", False
        ):
            queryset = queryset.filter(manager=self.request.user)
        else:
            queryset = queryset.filter(is_published=True)
        return queryset


class EventRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsEventManagerOwnerOrReadOnly]
    lookup_field = "event_code"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and getattr(
            self.request.user, "is_event_manager", False
        ):
            queryset = queryset.filter(manager=self.request.user)
        else:
            queryset = queryset.filter(is_published=True)
        return queryset

    def destroy(self, request, *args, **kwargs):
        # only allow the event owner/manager to delete the event
        # Events cannot be deleted, only unpublished and closed as they have bookings and ticket types and data
        if self.request.user.is_event_manager:
            instance = self.get_object()
            instance.is_published = False
            instance.is_closed = True
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
