from rest_framework.permissions import BasePermission


class IsWorker(BasePermission):
    """Workers and admins: review sightings and see all reports (Task 4.3)."""

    message = "Only workers can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_worker)
