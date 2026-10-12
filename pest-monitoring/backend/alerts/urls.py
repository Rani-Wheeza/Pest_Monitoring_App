from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.MyNotificationsView.as_view(), name="notification-list"),
    path("notifications/<int:notification_id>/read/", views.MarkReadView.as_view(), name="notification-read"),
]
