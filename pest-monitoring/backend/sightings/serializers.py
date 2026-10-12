"""Turns JSON into domain input and models into JSON.

Serializers only check the *shape* of the data (types, formats). The business
rules (required fields, ranges, future dates...) live in domain.validation so
they are tested once and give the same messages everywhere.
"""
from rest_framework import serializers

from domain.validation import SightingInput, parse_count_range

from .models import PestSighting, Priority, SightingMedia


class SightingCreateSerializer(serializers.Serializer):
    species_id = serializers.IntegerField(required=False, allow_null=True)
    count = serializers.CharField(required=False, allow_blank=True, help_text='"1", "2-5" or "10+"')
    description = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    location_accuracy_m = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    street_or_landmark = serializers.CharField(required=False, allow_blank=True)
    suburb_or_postcode = serializers.CharField(required=False, allow_blank=True)
    observed_at = serializers.DateTimeField(required=False, allow_null=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    reporter_confirmed = serializers.BooleanField(required=False, default=False)
    contact_email = serializers.CharField(required=False, allow_blank=True)

    def validate_count(self, value):
        if not value:
            return None
        try:
            return parse_count_range(value)
        except ValueError as exc:
            raise serializers.ValidationError('Use a number or a range such as "2-5".') from exc

    def to_domain(self, is_anonymous: bool) -> SightingInput:
        d = self.validated_data
        count = d.get("count") or (None, None)
        return SightingInput(
            species_id=d.get("species_id"),
            count_min=count[0], count_max=count[1],
            description=d.get("description", ""),
            latitude=d.get("latitude"), longitude=d.get("longitude"),
            street_or_landmark=d.get("street_or_landmark", ""),
            suburb_or_postcode=d.get("suburb_or_postcode", ""),
            observed_at=d.get("observed_at"),
            reporter_confirmed=d.get("reporter_confirmed", False),
            is_anonymous=is_anonymous,
            contact_email=d.get("contact_email") or None,
        )


class SightingMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = SightingMedia
        fields = ["id", "media_type", "content_type", "size_bytes", "uploaded_at", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request and url.startswith("/") else url


class SightingSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(read_only=True)
    species = serializers.CharField(source="species.common_name", read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    photos = SightingMediaSerializer(source="media", many=True, read_only=True)
    resident_status = serializers.SerializerMethodField()

    class Meta:
        model = PestSighting
        fields = ["id", "reference", "species", "count_min", "count_max", "description",
                  "latitude", "longitude", "location_accuracy_m", "street_or_landmark", "suburb_or_postcode",
                  "observed_at", "submitted_at", "status", "resident_status", "priority",
                  "rejection_reason", "tags", "photos"]

    def get_resident_status(self, obj) -> str:
        """The three simple labels residents see (Task 6.3)."""
        if obj.status in ("AwaitingReview", "InReview"):
            return "Awaiting review"
        if obj.status in ("Resolved",):
            return "Resolved"
        if obj.status == "Rejected":
            return "Not accepted"
        return "Response scheduled"


class ReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["confirm", "reject"])
    priority = serializers.ChoiceField(choices=Priority.choices, required=False, allow_blank=True, default="")
    reason = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)


class MapQuerySerializer(serializers.Serializer):
    species_id = serializers.IntegerField(required=False)
    family = serializers.CharField(required=False, max_length=100)
    genus = serializers.CharField(required=False, max_length=100)
    days = serializers.IntegerField(required=False, min_value=1, max_value=365, default=30)
    bbox = serializers.CharField(required=False, help_text="minLon,minLat,maxLon,maxLat")
