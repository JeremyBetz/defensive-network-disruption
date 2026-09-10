import ast
import importlib.util
import inspect
import io
import json
import socket
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from defensive_network_disruption.data import session6d_tls as tls


class Response:
    code = 200
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *args):
        raise AssertionError("HEAD must never read a payload body")


class TransportTests(unittest.TestCase):
    def test_trusted_hostname_normal_context(self):
        context = ssl.create_default_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        with patch.object(tls, "opener") as factory:
            factory.return_value.open.return_value = Response()
            result = tls.head_probe("https://github.com/test")
            self.assertEqual(result["status"], "verified")
            self.assertFalse(result["body_read"])
            self.assertEqual(factory.return_value.open.call_args.args[0].method, "HEAD")

    def cert_failure(self, code):
        error = ssl.SSLCertVerificationError(1, "synthetic certificate failure")
        error.verify_code = code
        return tls.failure(error)

    def test_hostname_mismatch_hard_failure(self):
        result = self.cert_failure(62)
        self.assertEqual(result["category"], "hostname_mismatch")
        self.assertFalse(result["retryable"])

    def test_untrusted_issuer_hard_failure(self):
        self.assertEqual(self.cert_failure(20)["category"], "untrusted_issuer")

    def test_expired_certificate_hard_failure(self):
        self.assertEqual(self.cert_failure(10)["category"], "expired_certificate")

    def test_official_delivery_origin_allowed_but_redirect_not_followed(self):
        url = "https://objects.example.com/file?signature=secret"
        self.assertEqual(tls.approved_delivery(url, {"https://objects.example.com"}, ["8.8.8.8"]), "https://objects.example.com")
        self.assertIsNone(tls.NoRedirect().redirect_request(None, None, 302, "", {}, url))

    def test_unauthorized_or_private_redirect_rejected(self):
        for url in ("http://objects.example.com/x", "https://user:pass@objects.example.com/x", "https://other.example.com/x"):
            with self.assertRaises(ValueError):
                tls.approved_delivery(url, {"https://objects.example.com"}, ["8.8.8.8"])
        with self.assertRaisesRegex(ValueError, "private_destination"):
            tls.approved_delivery("https://objects.example.com/x", {"https://objects.example.com"}, ["127.0.0.1"])

    def test_proxy_environment_is_presence_only(self):
        result = tls.environment_presence({"HTTPS_PROXY": "https://private:password@proxy.local:123"})
        self.assertTrue(result["HTTPS_PROXY"]["present"])
        self.assertNotIn("password", json.dumps(result))
        self.assertNotIn("proxy.local", json.dumps(result))

    def test_custom_ca_presence_without_paths(self):
        result = tls.environment_presence({"SSL_CERT_FILE": "/Users/private/cert.pem"})
        self.assertTrue(result["SSL_CERT_FILE"]["present"])
        self.assertNotIn("/Users", json.dumps(result))

    def test_timeout(self):
        result = tls.failure(socket.timeout("timed out"))
        self.assertEqual(result["category"], "timeout")
        self.assertFalse(result["retryable"])

    def test_reset(self):
        self.assertEqual(tls.failure(ConnectionResetError())["category"], "connection_reset")

    def test_signed_url_and_credentials_redacted(self):
        for text in ("error https://example.org/file?X-Amz-Signature=secret", "Authorization: secret", "https://username:secret@example.org/path"):
            self.assertNotIn("secret", tls.redact(text))
        self.assertNotIn("/Users/jeremy", tls.redact("error at /Users/jeremy/path/file"))

    def test_each_frozen_component_is_immutable(self):
        expected = tls.TUPLES["reserved_01"]
        self.assertEqual(tls.identity("reserved_01", expected), expected)
        for key in expected:
            changed = dict(expected, **{key: 1 if key == "size" else "changed"})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "identity_changed"):
                tls.identity("reserved_01", changed)

    def test_batch_only_projects_one_expected_object(self):
        expected = tls.TUPLES["reserved_01"]
        obj = {"oid": expected["oid"], "size": expected["size"], "actions": {"download": {"href": "https://objects.example.com/file?secret=hidden", "header": {"Authorization": "hidden"}}}}
        result, transient_url = tls.project_batch({"objects": [obj]}, "reserved_01")
        self.assertTrue(result["identity_matches"])
        self.assertNotIn("hidden", json.dumps(result))
        self.assertIn("hidden", transient_url)
        with self.assertRaises(ValueError):
            tls.project_batch({"objects": [{**obj, "size": 5}]}, "reserved_01")

    def test_head_has_no_body_reader_and_no_get_fallback(self):
        tree = ast.parse(inspect.getsource(tls.head_probe))
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertNotIn("read", calls)
        self.assertNotIn("metadata_read", inspect.getsource(tls.head_probe))

    def test_audit_imports_no_scientific_routes(self):
        for name in ("scripts/session_06d_lfs_tls_integrity.py", "src/defensive_network_disruption/data/session6d_tls.py"):
            tree = ast.parse(Path(name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for banned in ("session6_population", "receiver_choices", "ranking_metrics", "choice_model", "session5", "session_06_reserved", "numpy", "scipy"):
                        self.assertNotIn(banned, module)

    def test_delivery_does_not_return_signed_url_in_public_projection(self):
        with patch.object(tls, "batch_metadata", return_value=({"delivery_origin": "https://example.com"}, "https://example.com/file?sig=secret")):
            value = tls.worker({"kind": "batch", "alias": "reserved_01"})
        public = {key: value for key, value in value.items() if key != "_private_url"}
        self.assertNotIn("secret", json.dumps(public))

    def test_budget_and_secrets_in_actual_ledger_writer(self):
        import scripts.session_06d_lfs_tls_integrity as runner
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner, "LOCAL", Path(tmp)), patch.object(runner, "LEDGER", Path(tmp) / "ledger.jsonl"), patch.object(runner, "git", return_value="a" * 40):
            result = runner.network("fixture", lambda: {"status": "ok", "_private_url": "https://example.com/?secret=hidden"})
            self.assertIn("_private_url", result)
            self.assertNotIn("hidden", runner.LEDGER.read_text())
            self.assertEqual(runner.budget_used(), 1)
            with self.assertRaisesRegex(RuntimeError, "budget_exhausted"):
                runner.network("too_many", lambda: {}, 24)

    def test_metadata_bounded(self):
        response = Response()
        response.headers = {"Content-Length": "65537"}
        with self.assertRaisesRegex(ValueError, "metadata_oversized"):
            tls.metadata_read(response)

    def test_official_docs_only(self):
        with self.assertRaisesRegex(ValueError, "not_allowlisted"):
            tls.doc_metadata("https://media.githubusercontent.com/payload")


if __name__ == "__main__":
    unittest.main()
