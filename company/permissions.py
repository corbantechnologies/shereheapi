from rest_framework.permissions import BasePermission

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class IsEventManagerOwnerOrReadOnly(BasePermission):
    """
    Custom permission to:
    - Allow read-only access to anyone (authenticated or not).
    - Allow creation only to authenticated event managers or superusers.
    - Allow update/delete only if the object belongs to the requesting event manager,
      or if the user is a superuser.
    Assumes your models have a ForeignKey to User named 'manager' (e.g., event.manager).
    """

    def has_permission(self, request, view):
        # Read-only for anyone
        if request.method in SAFE_METHODS:
            return True

        # Write operations (e.g., POST for create) require authenticated event manager or superuser
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_event_manager or request.user.is_superuser)
        )

    def has_object_permission(self, request, view, obj):
        # Read-only for anyone
        if request.method in SAFE_METHODS:
            return True

        # Write operations on existing objects: must be owner OR superuser
        return request.user.is_superuser or (
            request.user.is_event_manager and obj.manager == request.user
        )
