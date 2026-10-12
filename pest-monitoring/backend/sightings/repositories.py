"""Data-access layer (DAO / repository pattern).

All database queries for sightings live here, so the service layer never builds
queries itself and the storage could change (e.g. SQLite -> Azure SQL) without
touching business logic. import-linter checks this layering on every build.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import QuerySet

from reference.models import District, PestSpecies, Tag

from .models import CLOSED_STATUSES, PUBLIC_MAP_STATUSES, PestSighting, SightingMedia, SightingStatusHistory


def get_active_species(species_id: int) -> PestSpecies | None:
    return PestSpecies.objects.filter(pk=species_id, is_active=True).first()


def get_tags(tag_ids: Iterable[int]) -> list[Tag]:
    return list(Tag.objects.filter(pk__in=list(tag_ids)))


def nearest_district(latitude: float, longitude: float, max_km: float = 25.0) -> District | None:
    """The district whose centre is closest to the pin, if one is within `max_km`."""
    best, best_km = None, max_km
    for district in District.objects.exclude(centre_lat__isnull=True).exclude(centre_lon__isnull=True):
        km = _haversine_km(latitude, longitude, float(district.centre_lat), float(district.centre_lon))
        if km <= best_km:
            best, best_km = district, km
    return best


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def create_sighting(**fields) -> PestSighting:
    tags = fields.pop("tags", [])
    sighting = PestSighting.objects.create(**fields)
    if tags:
        sighting.tags.set(tags)
    return sighting


def add_history(sighting: PestSighting, from_status: str, to_status: str, changed_by=None, note: str = "") -> None:
    SightingStatusHistory.objects.create(sighting=sighting, from_status=from_status, to_status=to_status,
                                         changed_by=changed_by, note=note)


def save_status(sighting: PestSighting, fields: list[str]) -> None:
    sighting.save(update_fields=fields)


def get_sighting(sighting_id: int) -> PestSighting | None:
    return (PestSighting.objects.select_related("species", "reporter", "district")
            .prefetch_related("tags", "media").filter(pk=sighting_id).first())


def sightings_for_reporter(user) -> QuerySet[PestSighting]:
    return (PestSighting.objects.filter(reporter=user)
            .select_related("species").prefetch_related("tags", "media"))


def all_sightings(status: str | None = None, priority: str | None = None) -> QuerySet[PestSighting]:
    qs = PestSighting.objects.select_related("species", "reporter").prefetch_related("tags", "media")
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    return qs


def count_media(sighting: PestSighting) -> int:
    return sighting.media.count()


def add_media(sighting: PestSighting, django_file, content_type: str, size_bytes: int) -> SightingMedia:
    media = SightingMedia(sighting=sighting, content_type=content_type, size_bytes=size_bytes)
    media.file.save(django_file.name, django_file, save=False)
    media.save()
    return media


def map_rows(*, include_unreviewed: bool, species_id: int | None = None, family: str | None = None,
             genus: str | None = None, days: int | None = None, bbox=None, now: datetime | None = None) -> list[dict]:
    qs = PestSighting.objects.exclude(status__in=CLOSED_STATUSES)
    if not include_unreviewed:
        qs = qs.filter(status__in=PUBLIC_MAP_STATUSES)
    if species_id:
        qs = qs.filter(species_id=species_id)
    if family:
        qs = qs.filter(species__family__iexact=family)
    if genus:
        qs = qs.filter(species__genus__iexact=genus)
    if days and now:
        qs = qs.filter(observed_at__gte=now - timedelta(days=days))
    if bbox:
        qs = qs.filter(longitude__gte=Decimal(str(bbox.min_lon)), longitude__lte=Decimal(str(bbox.max_lon)),
                       latitude__gte=Decimal(str(bbox.min_lat)), latitude__lte=Decimal(str(bbox.max_lat)))
    return list(qs.values("id", "latitude", "longitude", "priority", "status", "observed_at",
                          "species__common_name", "species__family", "species__genus")[:2000])
