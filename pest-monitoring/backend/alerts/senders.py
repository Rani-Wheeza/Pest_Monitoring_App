"""Ways of delivering a notification. Chosen by settings (Strategy pattern)."""
from __future__ import annotations

import json
import logging

import requests
from django.conf import settings

from domain.notification_hub import messages_url, parse_connection_string, sas_token, user_tag

log = logging.getLogger(__name__)


class ConsoleSender:
    """Used locally and in tests: writes the notification to the log instead of sending it."""

    def send(self, notification) -> tuple[bool, str]:
        log.info("Notification to user %s: %s - %s", notification.user_id, notification.title, notification.body)
        return True, "logged"


class NotificationHubSender:
    """Sends through Azure Notification Hubs' REST API to all devices tagged for the user."""

    def __init__(self, connection_string: str, hub_name: str, timeout: float = 10.0):
        self.connection = parse_connection_string(connection_string)
        self.hub_name = hub_name
        self.timeout = timeout

    def send(self, notification) -> tuple[bool, str]:
        url = messages_url(self.connection, self.hub_name)
        resource = url.split("?")[0]
        headers = {
            "Authorization": sas_token(resource, self.connection.key_name, self.connection.key),
            "Content-Type": "application/json;charset=utf-8",
            "ServiceBusNotification-Format": "template",
            "ServiceBusNotification-Tags": user_tag(notification.user_id),
        }
        body = json.dumps({"title": notification.title, "body": notification.body})
        try:
            response = requests.post(url, data=body.encode(), headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            log.warning("Notification Hubs request failed: %s", exc)
            return False, "network error"
        return response.status_code in (200, 201), f"HTTP {response.status_code}"


def default_sender():
    if settings.NOTIFICATION_HUB_CONNECTION_STRING and settings.NOTIFICATION_HUB_NAME:
        return NotificationHubSender(settings.NOTIFICATION_HUB_CONNECTION_STRING, settings.NOTIFICATION_HUB_NAME)
    return ConsoleSender()
