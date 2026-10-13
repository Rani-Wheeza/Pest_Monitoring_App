"""Business logic for sightings (service layer).

Views call these functions; these functions call the domain rules and the
repository layer. Nothing here knows about HTTP.
"""
from __future__ import annotations

from datetime import datetime

from django.core.files.base import ContentFile
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction
from django.utils import timezone

from domain.geo import BoundingBox, to_feature_collection
from domain.images import ImageRejectedError, clean_image
from domain.validation import FieldError, SightingInput, validate_sighting

from . import repositories as repo
from .exceptions import DomainValidationError, NotAllowedError
from .models import PestSighting, SightingStatus

MAX_PHOTOS_PER_SIGHTING = 3
UPLOAD_TOKEN_MAX_AGE = 30 * 60  # anonymous reporters have 30 minutes to add a photo
_signer = TimestampSigner(salt="sighting-photo-upload")


@transaction.atomic
def submit_sighting(data: SightingInput, tag_ids: list[int], reporter=None,
                    now: datetime | None = None) -> PestSighting:
    """US-02: validate and store a new sighting with status AwaitingReview."""
    now = now or timezone.now()
    errors = validate_sighting(data, now)

    species = repo.get_active_species(data.species_id) if data.species_id is not None else None
    if data.species_id is not None and species is None:
        errors.append(FieldError("species_id", "Unknown pest species."))
    tags = repo.get_tags(tag_ids)
    if len(tags) != len(set(tag_ids)):
        errors.append(FieldError("tag_ids", "One or more tags do not exist."))
    if errors:
        raise DomainValidationError(errors)

    district = repo.nearest_district(data.latitude, data.longitude)
    if district is None and reporter is not None:
        district = reporter.district

    sighting = repo.create_sighting(
        reporter=reporter,
        contact_email=(data.contact_email or "") if reporter is None else "",
        species=species,
        count_min=data.count_min,
        count_max=data.count_max,
        description=data.description.strip(),
        latitude=round(data.latitude, 6),
        longitude=round(data.longitude, 6),
        street_or_landmark=data.street_or_landmark.strip(),
        suburb_or_postcode=data.suburb_or_postcode.strip(),
        district=district,
        observed_at=data.observed_at or now,
        reporter_confirmed=data.reporter_confirmed,
        tags=tags,
    )
    repo.add_history(sighting, "", SightingStatus.AWAITING_REVIEW, changed_by=reporter, note="Submitted")
    return sighting


def make_upload_token(sighting: PestSighting) -> str:
    """Lets an anonymous reporter attach a photo straight after submitting."""
    return _signer.sign(str(sighting.pk))


def _token_matches(token: str | None, sighting: PestSighting) -> bool:
    if not token:
        return False
    try:
        return _signer.unsign(token, max_age=UPLOAD_TOKEN_MAX_AGE) == str(sighting.pk)
    except (BadSignature, SignatureExpired):
        return False


def can_view(user, sighting: PestSighting) -> bool:
    if user is None or not user.is_authenticated:
        return False
    return user.is_worker or sighting.reporter_id == user.pk


@transaction.atomic
def attach_photo(sighting: PestSighting, raw: bytes, user=None, upload_token: str | None = None):
    """US-03: check, clean (remove GPS/EXIF) and store a photo for a sighting."""
    is_owner = user is not None and user.is_authenticated and sighting.reporter_id == user.pk
    is_worker = user is not None and user.is_authenticated and user.is_worker
    if not (is_owner or is_worker or _token_matches(upload_token, sighting)):
        raise NotAllowedError("You can only add photos to your own sightings.")
    if sighting.status in (SightingStatus.RESOLVED, SightingStatus.REJECTED):
        raise DomainValidationError([FieldError("photo", "This sighting is closed.")])
    if repo.count_media(sighting) >= MAX_PHOTOS_PER_SIGHTING:
        message = f"A sighting can have at most {MAX_PHOTOS_PER_SIGHTING} photos."
        raise DomainValidationError([FieldError("photo", message)])

    try:
        image = clean_image(raw)
    except ImageRejectedError as exc:
        raise DomainValidationError([FieldError("photo", str(exc))]) from exc

    file = ContentFile(image.content, name=f"{sighting.pk}.{image.extension}")
    return repo.add_media(sighting, file, image.content_type, len(image.content))


REVIEW_DECISIONS = {"confirm": SightingStatus.CONFIRMED, "reject": SightingStatus.REJECTED}


@transaction.atomic
def review_sighting(sighting: PestSighting, decision: str, worker,
                    priority: str = "", reason: str = "") -> PestSighting:
    """A worker confirms (with a priority) or rejects (with a reason) a new sighting."""
    if not worker.is_worker:
        raise NotAllowedError("Only workers can review sightings.")
    if sighting.status not in (SightingStatus.AWAITING_REVIEW, SightingStatus.IN_REVIEW):
        raise DomainValidationError([FieldError("status", "This sighting has already been reviewed.")])
    if decision not in REVIEW_DECISIONS:
        raise DomainValidationError([FieldError("decision", "Use 'confirm' or 'reject'.")])
    if decision == "confirm" and not priority:
        raise DomainValidationError([FieldError("priority", "Set a priority when confirming.")])
    if decision == "reject" and not reason.strip():
        raise DomainValidationError([FieldError("reason", "Give a reason when rejecting.")])

    old_status = sighting.status
    sighting.status = REVIEW_DECISIONS[decision]
    fields = ["status"]
    if decision == "confirm":
        sighting.priority = priority
        fields.append("priority")
    else:
        sighting.rejection_reason = reason.strip()
        fields.append("rejection_reason")
    repo.save_status(sighting, fields)
    repo.add_history(sighting, old_status, sighting.status, changed_by=worker, note=reason.strip())
    return sighting


PUBLIC_COORDINATE_DECIMALS = 3  # about 100 m, so the public map never pinpoints a home


def map_features(*, viewer=None, species_id: int | None = None, family: str | None = None,
                 genus: str | None = None, days: int | None = 30, bbox: BoundingBox | None = None) -> dict:
    """US-04 / US-05: GeoJSON for Azure Maps, filtered by species, family or genus."""
    is_worker = bool(viewer and viewer.is_authenticated and viewer.is_worker)
    rows = repo.map_rows(include_unreviewed=is_worker, species_id=species_id, family=family, genus=genus,
                         days=days, bbox=bbox, now=timezone.now())
    shaped = []
    for row in rows:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not is_worker:
            lat, lon = round(lat, PUBLIC_COORDINATE_DECIMALS), round(lon, PUBLIC_COORDINATE_DECIMALS)
        shaped.append({
            "id": row["id"], "latitude": lat, "longitude": lon,
            "species": row["species__common_name"], "family": row["species__family"],
            "genus": row["species__genus"], "priority": row["priority"] or "Low",
            "status": row["status"], "observed_at": row["observed_at"].isoformat(),
        })
    return to_feature_collection(shaped)
