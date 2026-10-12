"""Microsoft Entra ID token handling (Task 4, US-01).

`decode_access_token` checks the signature, audience, issuer and expiry of the
access token that MSAL Angular sends. `identity_from_claims` turns the token's
claims into the details we store. No Django imports here.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt

# App roles defined on the Entra app registration -> our Role values (Task 5).
ROLE_PRIORITY = ["Admin", "Worker", "Surveyor", "PestControlExpert", "User"]
DEFAULT_ROLE = "User"


class InvalidToken(Exception):
    """The token is missing, expired, forged or meant for another app."""


@dataclass(frozen=True)
class Identity:
    object_id: str
    email: str
    first_name: str
    last_name: str
    role: str


def decode_access_token(token: str, signing_key, audience: str, issuer: str) -> dict:
    try:
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "aud", "iss", "oid"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc


def role_from_claims(claims: dict) -> str:
    """Pick the most powerful role the user has been given in Entra ID."""
    granted = set(claims.get("roles") or [])
    for role in ROLE_PRIORITY:
        if role in granted:
            return role
    return DEFAULT_ROLE


def identity_from_claims(claims: dict) -> Identity:
    email = claims.get("preferred_username") or claims.get("email") or claims.get("upn") or ""
    return Identity(
        object_id=str(claims["oid"]),
        email=email.lower(),
        first_name=claims.get("given_name", ""),
        last_name=claims.get("family_name", ""),
        role=role_from_claims(claims),
    )
