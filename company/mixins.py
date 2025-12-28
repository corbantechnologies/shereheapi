from rest_framework import generics


class EventManagerOwnedFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        if user.is_authenticated and user.is_event_manager:
            return queryset.filter(manager=user)

        return queryset
