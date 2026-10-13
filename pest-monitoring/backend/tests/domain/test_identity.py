"""Unit tests for domain.identity (US-01 acceptance criteria).

A throw-away RSA key stands in for Microsoft Entra ID's signing key.
"""
import time
import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from domain.identity import InvalidTokenError, decode_access_token, identity_from_claims, role_from_claims

AUDIENCE = "api://pest-monitoring"
ISSUER = "https://login.microsoftonline.com/tenant-id/v2.0"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(key=KEY, **overrides):
    now = int(time.time())
    claims = {"oid": "11111111-2222-3333-4444-555555555555", "aud": AUDIENCE, "iss": ISSUER,
              "iat": now, "exp": now + 3600, "preferred_username": "Aisha@Example.com",
              "given_name": "Aisha", "family_name": "Rahman"}
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


class DecodeTokenTests(unittest.TestCase):
    def test_valid_token(self):
        claims = decode_access_token(make_token(), KEY.public_key(), AUDIENCE, ISSUER)
        self.assertEqual(claims["given_name"], "Aisha")

    def test_wrong_signature_rejected(self):
        with self.assertRaises(InvalidTokenError):
            decode_access_token(make_token(key=OTHER_KEY), KEY.public_key(), AUDIENCE, ISSUER)

    def test_expired_token_rejected(self):
        old = make_token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600)
        with self.assertRaises(InvalidTokenError):
            decode_access_token(old, KEY.public_key(), AUDIENCE, ISSUER)

    def test_token_for_another_app_rejected(self):
        with self.assertRaises(InvalidTokenError):
            decode_access_token(make_token(aud="api://other-app"), KEY.public_key(), AUDIENCE, ISSUER)

    def test_wrong_issuer_rejected(self):
        with self.assertRaises(InvalidTokenError):
            decode_access_token(make_token(iss="https://evil.example"), KEY.public_key(), AUDIENCE, ISSUER)

    def test_garbage_rejected(self):
        with self.assertRaises(InvalidTokenError):
            decode_access_token("not.a.token", KEY.public_key(), AUDIENCE, ISSUER)


class ClaimsTests(unittest.TestCase):
    def test_default_role_is_user(self):
        self.assertEqual(role_from_claims({}), "User")

    def test_highest_role_wins(self):
        self.assertEqual(role_from_claims({"roles": ["User", "Worker"]}), "Worker")
        self.assertEqual(role_from_claims({"roles": ["Worker", "Admin"]}), "Admin")

    def test_unknown_roles_ignored(self):
        self.assertEqual(role_from_claims({"roles": ["Hacker"]}), "User")

    def test_identity_from_claims(self):
        identity = identity_from_claims({"oid": "abc", "preferred_username": "Aisha@Example.com",
                                         "given_name": "Aisha", "family_name": "Rahman",
                                         "roles": ["Surveyor"]})
        self.assertEqual(identity.email, "aisha@example.com")
        self.assertEqual(identity.role, "Surveyor")
        self.assertEqual(identity.object_id, "abc")


if __name__ == "__main__":
    unittest.main()
