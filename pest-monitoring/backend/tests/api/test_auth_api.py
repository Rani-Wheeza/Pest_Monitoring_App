"""Tests for US-01 (sign in with Microsoft Entra ID) and the /api/me/ endpoint."""
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework.test import APIClient

from accounts.models import User

pytestmark = pytest.mark.django_db

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
AUDIENCE = "api://pest-monitoring"
ISSUER = "https://login.microsoftonline.com/test-tenant/v2.0"


class FakeJwks:
    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=KEY.public_key())


@pytest.fixture
def entra(settings, monkeypatch):
    settings.ENTRA_TENANT_ID = "test-tenant"
    settings.ENTRA_API_AUDIENCE = AUDIENCE
    settings.ENTRA_ISSUER = ISSUER
    monkeypatch.setattr("accounts.authentication._jwks_client", lambda url: FakeJwks())


def token(**overrides):
    now = int(time.time())
    claims = {"oid": "6f1d2c1e-0000-4000-8000-000000000001", "aud": AUDIENCE, "iss": ISSUER,
              "iat": now, "exp": now + 600, "preferred_username": "aisha@example.com",
              "given_name": "Aisha", "family_name": "Rahman"}
    claims.update(overrides)
    return jwt.encode(claims, KEY, algorithm="RS256")


def bearer(value):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {value}")
    return client


def test_valid_token_signs_in_and_creates_user(entra):
    response = bearer(token()).get("/api/me/")
    assert response.status_code == 200, response.content
    assert response.json()["email"] == "aisha@example.com"
    assert response.json()["role"] == "User"
    assert User.objects.filter(entra_object_id="6f1d2c1e-0000-4000-8000-000000000001").exists()


def test_role_comes_from_entra_app_roles(entra):
    assert bearer(token(roles=["Worker"])).get("/api/me/").json()["role"] == "Worker"


def test_role_change_in_entra_is_synced(entra):
    bearer(token()).get("/api/me/")
    bearer(token(roles=["Admin"])).get("/api/me/")
    assert User.objects.get().role == "Admin"


def test_expired_token_rejected(entra):
    old = token(iat=int(time.time()) - 3600, exp=int(time.time()) - 60)
    assert bearer(old).get("/api/me/").status_code == 401


def test_token_for_other_app_rejected(entra):
    assert bearer(token(aud="api://someone-else")).get("/api/me/").status_code == 401


def test_no_token_is_401(entra):
    assert APIClient().get("/api/me/").status_code == 401


def test_disabled_account_rejected(entra):
    bearer(token()).get("/api/me/")
    User.objects.update(is_active=False)
    assert bearer(token()).get("/api/me/").status_code == 401


def test_profile_update_cannot_change_role(entra):
    client = bearer(token())
    response = client.patch("/api/me/", {"postcode": "V92", "role": "Admin"}, format="json")
    assert response.status_code == 200
    assert response.json()["postcode"] == "V92"
    assert response.json()["role"] == "User"
