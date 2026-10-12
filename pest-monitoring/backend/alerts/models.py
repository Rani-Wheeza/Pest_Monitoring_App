"""Pest alerts and the notifications sent about them (Task 5, sections D and G)."""
from django.conf import settings
from django.db import models


class PestAlert(models.Model):
    class AlertType(models.TextChoices):
        HIGH_ACTIVITY = "HighActivity"
        UNSEASONAL = "Unseasonal"
        INVASIVE_SPECIES = "InvasiveSpecies"

    class Severity(models.TextChoices):
        LOW = "Low"
        MEDIUM = "Medium"
        HIGH = "High"

    district = models.ForeignKey("reference.District", on_delete=models.CASCADE, related_name="alerts")
    species = models.ForeignKey("reference.PestSpecies", null=True, blank=True, on_delete=models.SET_NULL)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    sighting_count = models.PositiveIntegerField()
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "PestAlert"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.alert_type} {self.species} in {self.district}"


class Notification(models.Model):
    class Type(models.TextChoices):
        PEST_ALERT = "PestAlert"
        SIGHTING_STATUS_CHANGED = "SightingStatusChanged"
        HIGH_PRIORITY_MESSAGE = "HighPriorityMessage"

    class Channel(models.TextChoices):
        PUSH = "Push"
        IN_APP = "InApp"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=Type.choices)
    alert = models.ForeignKey(PestAlert, null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.PUSH)
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=40, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "Notification"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} -> user {self.user_id}"
