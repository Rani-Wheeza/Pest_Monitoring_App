from django.contrib import admin

from .models import Notification, PestAlert


@admin.register(PestAlert)
class PestAlertAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "species", "district", "severity", "sighting_count", "created_at", "closed_at")
    list_filter = ("alert_type", "severity", "district")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "sent_at", "delivery_status", "read_at")
    list_filter = ("type", "delivery_status")
