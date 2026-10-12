"""Azure Notification Hubs REST helpers (Task 8.4).

Microsoft does not publish a Python SDK for *sending* through Notification Hubs,
so we call the REST API. This module builds the connection details and the
Shared Access Signature (SAS) token. No Django imports.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse
from dataclasses import dataclass

API_VERSION = "2015-01"


@dataclass(frozen=True)
class HubConnection:
    endpoint: str  # https://<namespace>.servicebus.windows.net/
    key_name: str
    key: str


def parse_connection_string(text: str) -> HubConnection:
    parts = dict(item.split("=", 1) for item in text.strip().strip(";").split(";") if "=" in item)
    try:
        endpoint = parts["Endpoint"].replace("sb://", "https://")
        return HubConnection(endpoint if endpoint.endswith("/") else endpoint + "/",
                             parts["SharedAccessKeyName"], parts["SharedAccessKey"])
    except KeyError as exc:
        raise ValueError(f"Connection string is missing {exc.args[0]}") from exc


def sas_token(resource_uri: str, key_name: str, key: str, ttl_seconds: int = 300, now: float | None = None) -> str:
    expiry = int((now if now is not None else time.time()) + ttl_seconds)
    encoded_uri = urllib.parse.quote(resource_uri.lower(), safe="").lower()
    to_sign = f"{encoded_uri}\n{expiry}".encode()
    signature = base64.b64encode(hmac.new(key.encode(), to_sign, hashlib.sha256).digest()).decode()
    return (f"SharedAccessSignature sr={encoded_uri}&sig={urllib.parse.quote(signature, safe='')}"
            f"&se={expiry}&skn={key_name}")


def messages_url(connection: HubConnection, hub_name: str) -> str:
    return f"{connection.endpoint}{hub_name}/messages/?api-version={API_VERSION}"


def user_tag(user_id: int) -> str:
    """Devices register with this tag so a notification reaches one user's devices only."""
    return f"user_{user_id}"
