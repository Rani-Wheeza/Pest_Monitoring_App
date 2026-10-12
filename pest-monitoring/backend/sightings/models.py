"""Pest sightings, their photos and status history (Task 5, section C)."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class SightingStatus(models.TextChoices):
    AWAITING_REVIEW = "AwaitingReview"
    IN_REVIEW = "InReview"
    CONFIRMED = "Confirmed"
    ASSIGNED = "Assigned"
    RESPONSE_SCHEDULED = "ResponseScheduled"
    DEPLOYED = "Deployed"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class Priority(models.TextChoices):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# Statuses shown on the public map (reviewed and still open).
PUBLIC_MAP_STATUSES = [SightingStatus.CONFIRMED, SightingStatus.ASSIGNED,
                       SightingStatus.RESPONSE_SCHEDULED, SightingStatus.DEPLOYED]
CLOSED_STATUSES = [SightingStatus.RESOLVED, SightingStatus.REJECTED]


class PestSighting(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="sightings")
    contact_email = models.EmailField(blank=True)
    species = models.ForeignKey("reference.PestSpecies", on_delete=models.PROTECT, related_name="sightings")
    count_min = models.PositiveIntegerField()
    count_max = models.PositiveIntegerField()
    description = models.CharField(max_length=1000)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_accuracy_m = models.PositiveIntegerField(null=True, blank=True)
    street_or_landmark = models.CharField(max_length=200)
    suburb_or_postcode = models.CharField(max_length=100)
    district = models.ForeignKey("reference.District", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="sightings")
    observed_at = models.DateTimeField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, blank=True)
    status = models.CharField(max_length=20, choices=SightingStatus.choices,
                              default=SightingStatus.AWAITING_REVIEW)
    rejection_reason = models.CharField(max_length=200, blank=True)
    reporter_confirmed = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField("reference.Tag", blank=True, db_table="PestSightingTag")

    class Meta:
        db_table = "PestSighting"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status", "priority"], name="ix_sighting_status_priority"),
            models.Index(fields=["district", "observed_at"], name="ix_sighting_district_date"),
            models.Index(fields=["species", "observed_at"], name="ix_sighting_species_date"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(count_min__gte=1), name="ck_sighting_count_min"),
            models.CheckConstraint(condition=Q(count_max__gte=F("count_min")), name="ck_sighting_count_range"),
            models.CheckConstraint(condition=Q(reporter__isnull=False) | ~Q(contact_email=""),
                                   name="ck_sighting_contact"),
        ]

    def __str__(self) -> str:
        return f"{self.reference} {self.species}"

    @property
    def reference(self) -> str:
        return f"PP-{self.pk}"


class SightingMedia(models.Model):
    """A photo attached to a sighting. Only images are supported (no video or audio)."""

    class MediaType(models.TextChoices):
        IMAGE = "Image"

    sighting = models.ForeignKey(PestSighting, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)
    file = models.FileField(upload_to="sightings/%Y/%m/")
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "SightingMedia"

    def __str__(self) -> str:
        return f"Photo {self.pk} for PP-{self.sighting_id}"


class SightingStatusHistory(models.Model):
    sighting = models.ForeignKey(PestSighting, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "SightingStatusHistory"
        ordering = ["changed_at"]

    def __str__(self) -> str:
        return f"PP-{self.sighting_id}: {self.from_status or 'new'} -> {self.to_status}"
