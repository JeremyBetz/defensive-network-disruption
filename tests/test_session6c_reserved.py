import ast
import base64
import hashlib
import inspect
import json
import socket
import tempfile
import unittest
import urllib.error
from pathlib import Path

from defensive_network_disruption.data.session6c_source import (
    IntegrityError,
    LfsPointer,
    Session6cSourceClient,
    TransportError,
    TreeEntry,
    git_blob_oid,
    parse_lfs_pointer,
    safe_destination,
    source_path,
    verify_blob,
)


def pointer(digest="a" * 64, size=90_729_279, ending="\n"):
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{digest}\n"
        f"size {size}{ending}"
    ).encode("ascii")


class Response:
    def __init__(self, url, body=b"", *, declared=None):
        self.url = url
        self.body = body
        self.offset = 0
        self.headers = {} if declared is None else {"Content-Length": str(declared)}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self.body) - self.offset
        result = self.body[self.offset:self.offset + size]
        self.offset += len(result)
        return result


class Opener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.urls = []

    def open(self, request, timeout):
        self.urls.append(request.full_url)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class GitLfsRepairTests(unittest.TestCase):
    def test_ordinary_blob_and_object_type(self):
        body = b'{"ordinary":true}\n'
        entry = TreeEntry("x", "blob", git_blob_oid(body), len(body))
        envelope = {"sha": entry.git_oid, "size": len(body), "encoding": "base64", "content": base64.b64encode(body).decode()}
        self.assertEqual(verify_blob(entry, envelope, decoded_limit=1024), body)
        with self.assertRaisesRegex(IntegrityError, "unexpected_object_type"):
            verify_blob(TreeEntry("x", "tree", entry.git_oid, len(body)), envelope, decoded_limit=1024)

    def test_valid_pointer_oid_size_and_syntax(self):
        content = pointer(size=0, ending="\r\n\r\n")
        parsed = parse_lfs_pointer(content)
        self.assertEqual((parsed.payload_sha256, parsed.payload_size), ("a" * 64, 0))

    def test_pointer_git_oid_and_byte_count_mismatches(self):
        content = pointer()
        good = TreeEntry("x", "blob", git_blob_oid(content), len(content))
        envelope = {"sha": good.git_oid, "size": len(content), "encoding": "base64", "content": base64.b64encode(content).decode()}
        verify_blob(good, envelope, decoded_limit=1024)
        with self.assertRaisesRegex(IntegrityError, "oid_mismatch"):
            verify_blob(TreeEntry("x", "blob", "0" * 40, len(content)), {**envelope, "sha": "0" * 40}, decoded_limit=1024)
        with self.assertRaisesRegex(IntegrityError, "size_mismatch"):
            verify_blob(TreeEntry("x", "blob", good.git_oid, len(content) + 1), {**envelope, "size": len(content) + 1}, decoded_limit=1024)

    def test_malformed_and_oversized_pointers(self):
        invalid = (
            b"no\n",
            pointer(digest="A" * 64),
            pointer(size=-1),
            pointer(ending="\nextra\n"),
            pointer() + b"x" * 1000,
        )
        for content in invalid:
            with self.subTest(content=content[:20]), self.assertRaises(IntegrityError):
                parse_lfs_pointer(content)

    def test_lfs_identity_and_declared_size_comparisons(self):
        payload = b"synthetic"
        expected = LfsPointer(hashlib.sha256(payload).hexdigest(), len(payload))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), expected.payload_sha256)
        self.assertNotEqual(hashlib.sha256(payload + b"x").hexdigest(), expected.payload_sha256)
        self.assertNotEqual(len(payload) + 1, expected.payload_size)

    def test_historical_contents_size_case_is_separated(self):
        content = pointer(size=90_729_279)
        self.assertEqual(len(content), 133)
        entry = TreeEntry("x", "blob", git_blob_oid(content), 133)
        envelope = {"sha": entry.git_oid, "size": 133, "encoding": "base64", "content": base64.b64encode(content).decode()}
        self.assertEqual(verify_blob(entry, envelope, decoded_limit=1024), content)
        self.assertNotEqual(len(content), 90_729_279)

    def test_frozen_session6_still_rejects_historical_case(self):
        from defensive_network_disruption.data import session6_source as old
        path = "data/matches/1874553/1874553_tracking_extrapolated.jsonl"
        content = pointer(size=90_729_279)
        oid = old.git_blob_sha1(content)
        contents_url = f"https://api.github.com/repos/{old.OWNER_REPO}/contents/{path}?ref={old.SOURCE_COMMIT}"
        blob_url = f"https://api.github.com/repos/{old.OWNER_REPO}/git/blobs/{oid}"
        metadata = Response(contents_url, json.dumps({"path": path, "type": "file", "sha": oid, "size": 90_729_279}).encode())
        envelope = Response(blob_url, json.dumps({"sha": oid, "encoding": "base64", "content": base64.b64encode(content).decode()}).encode())
        with self.assertRaisesRegex(RuntimeError, "Git blob hash or size mismatch"):
            old._blob(path, "token", Opener([metadata, envelope]))

    def test_materialized_file_does_not_change_pointer_object(self):
        content = pointer()
        materialized = b'{"tracking":true}\n'
        self.assertNotEqual(git_blob_oid(content), git_blob_oid(materialized))
        self.assertEqual(parse_lfs_pointer(content).payload_size, 90_729_279)


class FirewallTests(unittest.TestCase):
    def test_partition_product_and_path_firewall(self):
        allowed = frozenset({"1874553"})
        self.assertIn("1874553_tracking", source_path("1874553", "tracking", allowed))
        for match in ("1953632", "../1874553", "1886347"):
            with self.assertRaises(PermissionError):
                source_path(match, "tracking", allowed)
        with self.assertRaises(PermissionError):
            source_path("1874553", "pose", allowed)

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").symlink_to(root / "outside")
            with self.assertRaises(PermissionError):
                safe_destination(root, "1874553", "metadata", frozenset({"1874553"}))

    def test_wrong_path_revision_and_object_association(self):
        commit = "02a396ffd09b283c9f092fdedeff11da6d535b66"
        commit_url = f"https://api.github.com/repos/SkillCorner/opendata/git/commits/{commit}"
        client = Session6cSourceClient("token", opener=Opener([Response(commit_url, json.dumps({"sha": "b" * 40, "tree": {"sha": "c" * 40}}).encode())]), sleeper=lambda _: None)
        with self.assertRaisesRegex(IntegrityError, "commit_identity_mismatch"):
            client.tree_entries({"x"})

    def test_redirect_and_oversized_response_are_not_retried(self):
        url = "https://api.github.com/test"
        ledger = []
        client = Session6cSourceClient("token", opener=Opener([Response("https://example.invalid", b"{}")]), ledger=lambda *x: ledger.append(x), sleeper=lambda _: None)
        with self.assertRaisesRegex(IntegrityError, "redirect"):
            client._request(url, label="x", maximum=20)
        self.assertEqual(len([x for x in ledger if x[2] == "failed"]), 1)
        client = Session6cSourceClient("token", opener=Opener([Response(url, b"x" * 21)]), sleeper=lambda _: None)
        with self.assertRaisesRegex(IntegrityError, "oversized"):
            client._request(url, label="x", maximum=20)


class RetryTests(unittest.TestCase):
    def test_timeout_and_selected_5xx_retry_with_frozen_waits(self):
        url = "https://api.github.com/test"
        ledger, waits = [], []
        error = urllib.error.HTTPError(url, 503, "busy", {}, None)
        opener = Opener([socket.timeout(), error, Response(url, b"{}", declared=2)])
        client = Session6cSourceClient("token", opener=opener, ledger=lambda *x: ledger.append(x), sleeper=waits.append)
        self.assertEqual(client._request(url, label="fixed", maximum=20), b"{}")
        self.assertEqual(waits, [1.0, 2.0])
        self.assertEqual(len(set(opener.urls)), 1)
        self.assertEqual([x[1] for x in ledger if x[2] == "started"], [1, 2, 3])

    def test_retries_exhaust_and_forbidden_errors_do_not_retry(self):
        url = "https://api.github.com/test"
        client = Session6cSourceClient("token", opener=Opener([socket.timeout(), socket.timeout(), socket.timeout()]), sleeper=lambda _: None)
        with self.assertRaisesRegex(TransportError, "exhausted"):
            client._request(url, label="x", maximum=20)
        error = urllib.error.HTTPError(url, 404, "missing", {}, None)
        opener = Opener([error, Response(url, b"{}")])
        client = Session6cSourceClient("token", opener=opener, sleeper=lambda _: None)
        with self.assertRaises(urllib.error.HTTPError):
            client._request(url, label="x", maximum=20)
        self.assertEqual(len(opener.outcomes), 1)

    def test_completed_truncation_is_integrity_failure_without_retry(self):
        url = "https://api.github.com/test"
        opener = Opener([Response(url, b"x", declared=2), Response(url, b"xx")])
        client = Session6cSourceClient("token", opener=opener, sleeper=lambda _: None)
        with self.assertRaisesRegex(IntegrityError, "completed_response_size_mismatch"):
            client._request(url, label="x", maximum=20)
        self.assertEqual(len(opener.outcomes), 1)

    def test_acquire_uses_fresh_temporary_file_and_discards_failed_bytes(self):
        payload = b"complete"
        digest = hashlib.sha256(payload).hexdigest()
        url = "https://media.githubusercontent.com/media/SkillCorner/opendata/02a396ffd09b283c9f092fdedeff11da6d535b66/x"
        opener = Opener([socket.timeout(), Response(url, payload, declared=len(payload))])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "x"
            client = Session6cSourceClient("token", opener=opener, sleeper=lambda _: None)
            result = client.acquire(TreeEntry("x", "blob", "a" * 40, 1), destination, pointer=LfsPointer(digest, len(payload)), label="x")
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(result["lfs_payload_sha256"], digest)
            self.assertEqual(list(Path(directory).glob(".*.tmp")), [])


class CommandSeparationTests(unittest.TestCase):
    @staticmethod
    def calls(function):
        tree = ast.parse(inspect.getsource(function))
        return {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}

    def test_prepare_cannot_score_and_score_cannot_fit_or_acquire(self):
        import scripts.session_06c_reserved as runner
        self.assertTrue(self.calls(runner.prepare_reserved).isdisjoint({"expected_credits", "score", "fit_final_models", "fit_with_fail_closed_gate"}))
        self.assertTrue(self.calls(runner.score).isdisjoint({"acquire_reserved", "prepare_match_session6", "fit_final_models", "fit_with_fail_closed_gate"}))

    def test_exact_membership_and_distinct_output(self):
        import scripts.session_06c_reserved as runner
        self.assertEqual(len(runner.RESERVED), 10)
        self.assertNotIn(runner.WITHHELD, runner.RESERVED)
        self.assertEqual(runner.OUTPUT.name, "reserved_evaluation_v2")


if __name__ == "__main__":
    unittest.main()
