"""Rules that decide when pest activity should raise an alert (Task 8.4).

Plain Python, no Django imports. The Django management command
`check_pest_levels` loads the data and calls `evaluate_activity`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class AlertType(StrEnum):
    HIGH_ACTIVITY = "HighActivity"
    UNSEASONAL = "Unseasonal"
    INVASIVE_SPECIES = "InvasiveSpecies"


class Severity(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass(frozen=True)
class ActivitySummary:
    """Sightings of one species in one district over the last 30 days."""

    district_id: int
    species_id: int
    sighting_count: int
    last_seen: date
    is_invasive: bool
    peak_season_start: int | None = None  # month 1-12
    peak_season_end: int | None = None


@dataclass(frozen=True)
class AlertDecision:
    alert_type: AlertType
    severity: Severity
    reason: str


def in_peak_season(month: int, start: int | None, end: int | None) -> bool:
    """True if `month` is inside the species' peak season.

    Seasons can wrap round the new year, e.g. rats: September (9) to March (3).
    A species with no season set is treated as active all year.
    """
    if start is None or end is None:
        return True
    if start <= end:
        return start <= month <= end
    return month >= start or month <= end


def _high_activity_severity(count: int, threshold: int) -> Severity | None:
    if count >= threshold * 2:
        return Severity.HIGH
    if count >= threshold:
        return Severity.MEDIUM
    return None


def evaluate_activity(summary: ActivitySummary, threshold: int) -> list[AlertDecision]:
    """Return the alerts this activity should raise (possibly none).

    `threshold` is the number of sightings in 30 days that counts as high activity.
    The value still has to be agreed by the group (Task 9.8); it is a setting.
    """
    if threshold < 1:
        raise ValueError("threshold must be at least 1")

    decisions: list[AlertDecision] = []

    severity = _high_activity_severity(summary.sighting_count, threshold)
    if severity is not None:
        decisions.append(AlertDecision(
            AlertType.HIGH_ACTIVITY, severity,
            f"{summary.sighting_count} sightings in 30 days (threshold {threshold})",
        ))

    if summary.sighting_count > 0 and not in_peak_season(
        summary.last_seen.month, summary.peak_season_start, summary.peak_season_end
    ):
        decisions.append(AlertDecision(
            AlertType.UNSEASONAL, Severity.MEDIUM,
            "Seen outside its normal peak season",
        ))

    if summary.is_invasive and summary.sighting_count > 0:
        decisions.append(AlertDecision(
            AlertType.INVASIVE_SPECIES, Severity.HIGH,
            "Invasive species reported",
        ))

    return decisions
