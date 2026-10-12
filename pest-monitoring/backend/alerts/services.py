"""Threshold check and notification delivery (US-06, Task 8.4).

Run every hour by a Kubernetes CronJob: `python manage.py check_pest_levels`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Max
from django.utils import timezone

from domain.alerts import ActivitySummary, AlertDecision, evaluate_activity
from reference.models import PestSpecies
from sightings.models import PestSighting, SightingStatus

from .models import Notification, PestAlert
from .senders import default_sender

WINDOW_DAYS = 30


@dataclass
class CheckResult:
    alerts_created: int = 0
    alerts_updated: int = 0
    notifications_sent: int = 0
    notifications_failed: int = 0
    details: list[str] = field(default_factory=list)


def activity_summaries(now: datetime) -> list[ActivitySummary]:
    """Valid sightings per district and species in the last 30 days (like vw_DistrictActivity30d)."""
    rows = (PestSighting.objects
            .filter(observed_at__gte=now - timedelta(days=WINDOW_DAYS), district__isnull=False)
            .exclude(status=SightingStatus.REJECTED)
            .values("district_id", "species_id")
            .annotate(count=Count("id"), last_seen=Max("observed_at")))
    species = {s.pk: s for s in PestSpecies.objects.filter(pk__in={r["species_id"] for r in rows})}
    summaries = []
    for row in rows:
        sp = species[row["species_id"]]
        summaries.append(ActivitySummary(
            district_id=row["district_id"], species_id=row["species_id"], sighting_count=row["count"],
            last_seen=timezone.localtime(row["last_seen"]).date(), is_invasive=sp.is_invasive,
            peak_season_start=sp.peak_season_start_month, peak_season_end=sp.peak_season_end_month,
        ))
    return summaries


def _recipients(district_id: int):
    return get_user_model().objects.filter(district_id=district_id, consent_to_updates=True, is_active=True)


def _record_alert(summary: ActivitySummary, decision: AlertDecision, now: datetime, result: CheckResult):
    """Create a new alert, or update the open one so users are not alerted twice."""
    existing = PestAlert.objects.filter(district_id=summary.district_id, species_id=summary.species_id,
                                        alert_type=decision.alert_type.value, closed_at__isnull=True).first()
    if existing:
        existing.sighting_count = summary.sighting_count
        existing.severity = decision.severity.value
        existing.window_end = now
        existing.save(update_fields=["sighting_count", "severity", "window_end"])
        result.alerts_updated += 1
        return None

    alert = PestAlert.objects.create(
        district_id=summary.district_id, species_id=summary.species_id,
        alert_type=decision.alert_type.value, severity=decision.severity.value,
        sighting_count=summary.sighting_count, window_start=now - timedelta(days=WINDOW_DAYS), window_end=now,
    )
    result.alerts_created += 1
    result.details.append(f"{alert}: {decision.reason}")
    return alert


def _notify(alert: PestAlert) -> list[Notification]:
    title = f"{alert.get_alert_type_display()} alert: {alert.species} in {alert.district}"
    body = f"{alert.sighting_count} sightings reported in the last {WINDOW_DAYS} days."
    return [Notification.objects.create(user=user, type=Notification.Type.PEST_ALERT, alert=alert,
                                        title=title[:150], body=body)
            for user in _recipients(alert.district_id)]


def deliver_pending(sender=None, now: datetime | None = None, result: CheckResult | None = None) -> CheckResult:
    """Send every notification not yet sent. Failures stay pending and are retried next run."""
    sender = sender or default_sender()
    now = now or timezone.now()
    result = result or CheckResult()
    for notification in Notification.objects.filter(sent_at__isnull=True, channel=Notification.Channel.PUSH):
        ok, status = sender.send(notification)
        notification.delivery_status = status
        if ok:
            notification.sent_at = now
            result.notifications_sent += 1
        else:
            result.notifications_failed += 1
        notification.save(update_fields=["delivery_status", "sent_at"])
    return result


def run_threshold_check(threshold: int, now: datetime | None = None, sender=None) -> CheckResult:
    now = now or timezone.now()
    result = CheckResult()
    with transaction.atomic():
        for summary in activity_summaries(now):
            for decision in evaluate_activity(summary, threshold):
                alert = _record_alert(summary, decision, now, result)
                if alert is not None:
                    _notify(alert)
    return deliver_pending(sender=sender, now=now, result=result)
