"""Tests for the Notification Hubs sender (no real network call) and the seed command."""
from types import SimpleNamespace

import pytest
import requests
from django.core.management import call_command

from alerts.senders import ConsoleSender, NotificationHubSender, default_sender
from reference.models import District, PestSpecies, Tag

CONN = "Endpoint=sb://pestns.servicebus.windows.net/;SharedAccessKeyName=send;SharedAccessKey=c2VjcmV0"
NOTE = SimpleNamespace(user_id=7, title="High activity", body="10 sightings")


def test_hub_sender_posts_template_to_users_devices(monkeypatch):
    calls = {}

    def fake_post(url, data, headers, timeout):
        calls.update(url=url, data=data, headers=headers)
        return SimpleNamespace(status_code=201)

    monkeypatch.setattr(requests, "post", fake_post)
    ok, status = NotificationHubSender(CONN, "pest-alerts").send(NOTE)

    assert (ok, status) == (True, "HTTP 201")
    assert calls["url"] == "https://pestns.servicebus.windows.net/pest-alerts/messages/?api-version=2015-01"
    assert calls["headers"]["ServiceBusNotification-Tags"] == "user_7"
    assert calls["headers"]["Authorization"].startswith("SharedAccessSignature sr=")
    assert b"High activity" in calls["data"]


def test_hub_sender_reports_http_failure(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: SimpleNamespace(status_code=500))
    assert NotificationHubSender(CONN, "pest-alerts").send(NOTE) == (False, "HTTP 500")


def test_hub_sender_reports_network_failure(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    assert NotificationHubSender(CONN, "pest-alerts").send(NOTE) == (False, "network error")


def test_default_sender_is_console_without_settings(settings):
    settings.NOTIFICATION_HUB_CONNECTION_STRING = ""
    assert isinstance(default_sender(), ConsoleSender)


def test_default_sender_uses_hub_when_configured(settings):
    settings.NOTIFICATION_HUB_CONNECTION_STRING = CONN
    settings.NOTIFICATION_HUB_NAME = "pest-alerts"
    assert isinstance(default_sender(), NotificationHubSender)


@pytest.mark.django_db
def test_seed_command_is_repeatable():
    call_command("seed_reference_data")
    call_command("seed_reference_data")
    assert District.objects.count() == 4
    assert PestSpecies.objects.filter(common_name="Grey squirrel", is_invasive=True).exists()
    assert Tag.objects.count() == 6


@pytest.mark.django_db
def test_tag_and_district_lists(anon_client):
    call_command("seed_reference_data")
    assert len(anon_client.get("/api/tags/").json()) == 6
    assert len(anon_client.get("/api/districts/").json()) == 4
