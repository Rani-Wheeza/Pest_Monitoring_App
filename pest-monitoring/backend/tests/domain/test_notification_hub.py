"""Unit tests for domain.notification_hub."""
import base64
import hashlib
import hmac
import unittest
import urllib.parse

from domain.notification_hub import messages_url, parse_connection_string, sas_token, user_tag

CONN = ("Endpoint=sb://pestns.servicebus.windows.net/;"
        "SharedAccessKeyName=DefaultFullSharedAccessSignature;SharedAccessKey=c2VjcmV0a2V5")


class ConnectionStringTests(unittest.TestCase):
    def test_parse(self):
        conn = parse_connection_string(CONN)
        self.assertEqual(conn.endpoint, "https://pestns.servicebus.windows.net/")
        self.assertEqual(conn.key_name, "DefaultFullSharedAccessSignature")

    def test_missing_key_raises(self):
        with self.assertRaises(ValueError):
            parse_connection_string("Endpoint=sb://x.servicebus.windows.net/")

    def test_messages_url(self):
        url = messages_url(parse_connection_string(CONN), "pest-alerts")
        self.assertEqual(url, "https://pestns.servicebus.windows.net/pest-alerts/messages/?api-version=2015-01")


class SasTokenTests(unittest.TestCase):
    def test_token_signature_is_correct(self):
        uri = "https://pestns.servicebus.windows.net/pest-alerts/messages/"
        token = sas_token(uri, "keyname", "secret", ttl_seconds=60, now=1_000_000)
        fields = dict(p.split("=", 1) for p in token.removeprefix("SharedAccessSignature ").split("&"))
        self.assertEqual(fields["se"], "1000060")
        self.assertEqual(fields["skn"], "keyname")
        expected = base64.b64encode(hmac.new(b"secret", f"{fields['sr']}\n1000060".encode(),
                                             hashlib.sha256).digest()).decode()
        self.assertEqual(urllib.parse.unquote(fields["sig"]), expected)

    def test_user_tag(self):
        self.assertEqual(user_tag(42), "user_42")


if __name__ == "__main__":
    unittest.main()
