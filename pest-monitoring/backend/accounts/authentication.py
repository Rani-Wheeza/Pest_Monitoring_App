"""DRF authentication using Microsoft Entra ID access tokens (US-01).

Angular (MSAL) sends `Authorization: Bearer <token>`. We check the token with the
tenant's public signing keys, then find or create the matching user.
If ENTRA_TENANT_ID is not set (local development and tests), this class is skipped.
"""
from __future__ import annotations

from functools import lru_cache

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from domain.identity import InvalidTokenError, decode_access_token, identity_from_claims

from .models import User


@lru_cache(maxsize=1)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True)


def user_for_identity(identity) -> User:
    user, created = User.objects.get_or_create(
        entra_object_id=identity.object_id,
        defaults={"username": identity.email or identity.object_id, "email": identity.email,
                  "first_name": identity.first_name, "last_name": identity.last_name,
                  "role": identity.role},
    )
    if not created and user.role != identity.role:
        user.role = identity.role  # roles are managed in Entra ID, so keep them in sync
        user.save(update_fields=["role"])
    return user


class EntraJWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        if not settings.ENTRA_TENANT_ID:
            return None
        header = authentication.get_authorization_header(request).decode()
        if not header.startswith(self.keyword + " "):
            return None
        token = header[len(self.keyword) + 1:]
        try:
            signing_key = _jwks_client(settings.ENTRA_JWKS_URL).get_signing_key_from_jwt(token).key
            claims = decode_access_token(token, signing_key, settings.ENTRA_API_AUDIENCE, settings.ENTRA_ISSUER)
        except (InvalidTokenError, jwt.PyJWTError) as exc:
            raise exceptions.AuthenticationFailed("Invalid or expired sign-in token.") from exc
        user = user_for_identity(identity_from_claims(claims))
        if not user.is_active:
            raise exceptions.AuthenticationFailed("This account is disabled.")
        return user, claims

    def authenticate_header(self, request):
        return self.keyword
