"""Tests for US-01: username/password sign-in with API tokens (replaces Entra ID sign-in)."""
import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-battery"


@pytest.fixture
def aisha(resident):
    resident.set_password(PASSWORD)
    resident.save()
    return resident


def login(client, username, password):
    return client.post("/api/login/", {"username": username, "password": password}, format="json")


def with_token(key):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
    return client


def test_login_returns_token_and_profile(anon_client, aisha):
    response = login(anon_client, "aisha", PASSWORD)
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["token"] == Token.objects.get(user=aisha).key
    assert body["user"]["username"] == "aisha"
    assert body["user"]["role"] == "User"


def test_wrong_password_is_rejected(anon_client, aisha):
    response = login(anon_client, "aisha", "wrong-password")
    assert response.status_code == 400
    assert not Token.objects.exists()


def test_inactive_account_cannot_sign_in(anon_client, aisha):
    aisha.is_active = False
    aisha.save()
    assert login(anon_client, "aisha", PASSWORD).status_code == 400


def test_token_signs_in_api_calls(anon_client, aisha):
    key = login(anon_client, "aisha", PASSWORD).json()["token"]
    response = with_token(key).get("/api/me/")
    assert response.status_code == 200
    assert response.json()["email"] == "aisha@example.com"


def test_signing_in_twice_reuses_the_token(anon_client, aisha):
    first = login(anon_client, "aisha", PASSWORD).json()["token"]
    second = login(anon_client, "aisha", PASSWORD).json()["token"]
    assert first == second


def test_logout_deletes_the_token(anon_client, aisha):
    key = login(anon_client, "aisha", PASSWORD).json()["token"]
    client = with_token(key)
    assert client.post("/api/logout/").status_code == 204
    assert client.get("/api/me/").status_code == 401


def test_logout_needs_a_signed_in_user(anon_client):
    assert anon_client.post("/api/logout/").status_code == 401
