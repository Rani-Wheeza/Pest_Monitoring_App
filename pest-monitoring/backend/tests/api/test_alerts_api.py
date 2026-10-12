"""Tests for US-06 (receive pest alert): threshold check, notifications, delivery.

The pigeon fixture has no peak season, so these results do not depend on the month the tests run in.
"""
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from alerts.models import Notification, PestAlert
from alerts.services import run_threshold_check
from reference.models import PestSpecies
from sightings.models import PestSighting

pytestmark = pytest.mark.django_db


class FakeSender:
    def __init__(self, ok=True):
        self.ok, self.sent = ok, []

    def send(self, notification):
        self.sent.append(notification)
        return self.ok, "HTTP 201" if self.ok else "HTTP 500"


def make_sightings(n, species, district, reporter, days_ago=1):
    when = timezone.now() - timedelta(days=days_ago)
    for _ in range(n):
        PestSighting.objects.create(reporter=reporter, species=species, district=district, count_min=1,
                                    count_max=1, description="seen", latitude=52.27, longitude=-9.70,
                                    street_or_landmark="Lane", suburb_or_postcode="Riverside",
                                    observed_at=when, reporter_confirmed=True)


def test_threshold_breach_creates_alert_and_notifies(resident, other_resident, pigeon, district):
    make_sightings(10, pigeon, district, resident)
    sender = FakeSender()
    result = run_threshold_check(threshold=10, sender=sender)

    alert = PestAlert.objects.get()
    assert (alert.alert_type, alert.severity, alert.sighting_count) == ("HighActivity", "Medium", 10)
    # only users in the district who agreed to updates are notified
    assert [n.user for n in Notification.objects.all()] == [resident]
    assert result.alerts_created == 1 and result.notifications_sent == 1
    assert Notification.objects.get().sent_at is not None


def test_below_threshold_no_alert(resident, pigeon, district):
    make_sightings(9, pigeon, district, resident)
    run_threshold_check(threshold=10, sender=FakeSender())
    assert PestAlert.objects.count() == 0


def test_second_run_updates_instead_of_duplicating(resident, pigeon, district):
    make_sightings(10, pigeon, district, resident)
    run_threshold_check(threshold=10, sender=FakeSender())
    make_sightings(10, pigeon, district, resident)
    result = run_threshold_check(threshold=10, sender=FakeSender())

    alert = PestAlert.objects.get()
    assert alert.severity == "High" and alert.sighting_count == 20
    assert result.alerts_updated == 1 and result.alerts_created == 0
    assert Notification.objects.count() == 1  # users are not alerted twice


def test_rejected_and_old_sightings_ignored(resident, pigeon, district):
    make_sightings(10, pigeon, district, resident, days_ago=40)
    make_sightings(10, pigeon, district, resident)
    PestSighting.objects.filter(observed_at__gte=timezone.now() - timedelta(days=2)).update(status="Rejected")
    run_threshold_check(threshold=10, sender=FakeSender())
    assert PestAlert.objects.count() == 0


def test_invasive_species_alert(resident, district):
    squirrel = PestSpecies.objects.create(common_name="Grey squirrel", category="Rodent", is_invasive=True)
    make_sightings(1, squirrel, district, resident)
    run_threshold_check(threshold=10, sender=FakeSender())
    assert PestAlert.objects.get().alert_type == "InvasiveSpecies"


def test_failed_delivery_is_retried(resident, pigeon, district):
    make_sightings(10, pigeon, district, resident)
    result = run_threshold_check(threshold=10, sender=FakeSender(ok=False))
    assert result.notifications_failed == 1
    assert Notification.objects.get().sent_at is None

    retry = run_threshold_check(threshold=10, sender=FakeSender(ok=True))
    assert retry.notifications_sent == 1
    assert Notification.objects.get().sent_at is not None


def test_management_command_runs(resident, pigeon, district, capsys):
    make_sightings(10, pigeon, district, resident)
    call_command("check_pest_levels", "--threshold", "10")
    assert "Alerts created: 1" in capsys.readouterr().out


def test_user_sees_and_marks_notifications(client_for, resident, other_resident, pigeon, district):
    make_sightings(10, pigeon, district, resident)
    run_threshold_check(threshold=10, sender=FakeSender())
    client = client_for(resident)
    items = client.get("/api/notifications/").json()["results"]
    assert len(items) == 1 and items[0]["read_at"] is None

    assert client.post(f"/api/notifications/{items[0]['id']}/read/").json() == {"marked_read": True}
    assert client_for(other_resident).post(f"/api/notifications/{items[0]['id']}/read/").status_code == 404
