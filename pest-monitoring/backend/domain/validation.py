"""Validation rules for a pest sighting report (Task 8.2).

This module is plain Python: it must not import Django or DRF.
The rule is enforced on every build by import-linter (see pyproject.toml).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

MAX_DESCRIPTION_LENGTH = 1000
MAX_LANDMARK_LENGTH = 200
MAX_POSTCODE_LENGTH = 100
# Small allowance for clock differences between the phone and the server.
FUTURE_TOLERANCE = timedelta(minutes=5)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class SightingInput:
    """Everything the user sends when submitting a sighting."""

    species_id: int | None
    count_min: int | None
    count_max: int | None
    description: str
    latitude: float | None
    longitude: float | None
    street_or_landmark: str
    suburb_or_postcode: str
    observed_at: datetime | None
    reporter_confirmed: bool
    is_anonymous: bool
    contact_email: str | None = None


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


def _required_text(value: str | None, field: str, max_length: int, errors: list[FieldError]) -> None:
    if value is None or not value.strip():
        errors.append(FieldError(field, "This field is required."))
    elif len(value) > max_length:
        errors.append(FieldError(field, f"Must be {max_length} characters or fewer."))


def _validate_count(data: SightingInput, errors: list[FieldError]) -> None:
    if data.count_min is None or data.count_max is None:
        errors.append(FieldError("count", "Say how many you saw."))
        return
    if data.count_min < 1:
        errors.append(FieldError("count", "The count must be at least 1."))
    if data.count_max < data.count_min:
        errors.append(FieldError("count", "The maximum cannot be lower than the minimum."))


def _validate_location(data: SightingInput, errors: list[FieldError]) -> None:
    if data.latitude is None or data.longitude is None:
        errors.append(FieldError("location", "Drop a pin on the map."))
        return
    if not -90 <= data.latitude <= 90:
        errors.append(FieldError("latitude", "Latitude must be between -90 and 90."))
    if not -180 <= data.longitude <= 180:
        errors.append(FieldError("longitude", "Longitude must be between -180 and 180."))


def _validate_contact(data: SightingInput, errors: list[FieldError]) -> None:
    if not data.is_anonymous:
        return
    if not data.contact_email or not _EMAIL_RE.match(data.contact_email):
        errors.append(FieldError("contact_email", "Anonymous reports need a valid contact email."))


def validate_sighting(data: SightingInput, now: datetime) -> list[FieldError]:
    """Return every problem with the report. An empty list means the report is valid."""
    errors: list[FieldError] = []

    if data.species_id is None:
        errors.append(FieldError("species_id", "Choose the pest you saw."))
    _validate_count(data, errors)
    _required_text(data.description, "description", MAX_DESCRIPTION_LENGTH, errors)
    _validate_location(data, errors)
    _required_text(data.street_or_landmark, "street_or_landmark", MAX_LANDMARK_LENGTH, errors)
    _required_text(data.suburb_or_postcode, "suburb_or_postcode", MAX_POSTCODE_LENGTH, errors)

    if data.observed_at is not None and data.observed_at > now + FUTURE_TOLERANCE:
        errors.append(FieldError("observed_at", "The sighting time cannot be in the future."))

    if not data.reporter_confirmed:
        errors.append(FieldError("reporter_confirmed", "Confirm the report is accurate."))

    _validate_contact(data, errors)
    return errors


def parse_count_range(text: str) -> tuple[int, int]:
    """Turn the form's "How many?" value into (min, max).

    Accepts "1", "2-5" or "10+" (stored as 10 to 10 so the database stays numeric).
    """
    cleaned = text.strip().replace(" ", "")
    if cleaned.endswith("+"):
        value = int(cleaned[:-1])
        return value, value
    if "-" in cleaned:
        low, high = cleaned.split("-", 1)
        return int(low), int(high)
    value = int(cleaned)
    return value, value
