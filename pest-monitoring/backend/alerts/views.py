from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "body", "created_at", "read_at"]


class MyNotificationsView(generics.ListAPIView):
    """GET /api/notifications/ - the signed-in user's alerts (Alerts screen, Task 6.3)."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id: int):
        updated = Notification.objects.filter(pk=notification_id, user=request.user, read_at__isnull=True) \
            .update(read_at=timezone.now())
        exists = Notification.objects.filter(pk=notification_id, user=request.user).exists()
        if not exists:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"marked_read": bool(updated)})
