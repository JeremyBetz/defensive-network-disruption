import ast
import base64
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from defensive_network_disruption.data.git_lfs_integrity import (
    GitHubMetadataClient,
    IntegrityError,
    assess_identity,
    git_blob_oid,
    parse_lfs_pointer,
    project_json_value,
)


def pointer(oid="a" * 64, size=90_729_279):
    return (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{oid}\n"
        f"size {size}\n"
    ).encode("ascii")


def assessment(**changes):
    content = pointer()
    oid = git_blob_oid(content)
    values = {
        "expected_path": "data/matches/example/example_tracking_extrapolated.jsonl",
        "observed_path": "data/matches/example/example_tracking_extrapolated.jsonl",
        "expected_blob_oid": oid,
        "expected_pointer_size": len(content),
        "contents_blob_oid": oid,
        "contents_reported_size": 90_729_279,
        "envelope_blob_oid": oid,
        "envelope_reported_size": len(content),
        "decoded_blob": content,
        "expected_lfs_oid": "a" * 64,
        "expected_lfs_size": 90_729_279,
    }
    values.update(changes)
    return assess_identity(**values)


class GitLfsIdentityTests(unittest.TestCase):
    def test_ordinary_blob_is_distinct_from_lfs_pointer(self):
        ordinary = b'{"ordinary":"blob"}\n'
        self.assertEqual(len(git_blob_oid(ordinary)), 40)
        with self.assertRaisesRegex(IntegrityError, "pointer_malformed"):
            parse_lfs_pointer(ordinary)

    def test_pointer_and_payload_sizes_are_distinct(self):
        result = assessment()
        self.assertEqual(result["git_pointer_size"], 133)
        self.assertEqual(result["pointer"]["payload_size"], 90_729_279)
        self.assertTrue(result["checks"]["contents_size_matches_payload"])
        self.assertFalse(result["checks"]["contents_size_matches_decoded"])

    def test_correct_pointer_sha_and_lfs_oid(self):
        result = assessment()
        self.assertTrue(result["checks"]["decoded_blob_oid_matches"])
        self.assertTrue(result["checks"]["recorded_lfs_oid_matches_pointer"])

    def test_pointer_sha_mismatch_is_separate(self):
        result = assessment(expected_blob_oid="0" * 40)
        self.assertFalse(result["checks"]["decoded_blob_oid_matches"])
        self.assertTrue(result["checks"]["recorded_lfs_oid_matches_pointer"])

    def test_pointer_size_mismatch_is_separate(self):
        result = assessment(expected_pointer_size=999)
        self.assertFalse(result["checks"]["tree_pointer_size_matches_decoded"])
        self.assertTrue(result["checks"]["decoded_blob_oid_matches"])

    def test_lfs_oid_mismatch_is_separate(self):
        result = assessment(expected_lfs_oid="b" * 64)
        self.assertFalse(result["checks"]["recorded_lfs_oid_matches_pointer"])
        self.assertTrue(result["checks"]["recorded_lfs_size_matches_pointer"])

    def test_payload_size_mismatch_uses_synthetic_metadata_only(self):
        result = assessment(expected_lfs_size=123)
        self.assertFalse(result["checks"]["recorded_lfs_size_matches_pointer"])
        self.assertTrue(result["checks"]["recorded_lfs_oid_matches_pointer"])

    def test_materialized_worktree_does_not_replace_pointer_identity(self):
        pointer_bytes = pointer()
        materialized = b'{"synthetic_tracking_row":true}\n'
        self.assertNotEqual(git_blob_oid(pointer_bytes), git_blob_oid(materialized))
        result = assessment(decoded_blob=pointer_bytes)
        self.assertTrue(result["checks"]["decoded_blob_oid_matches"])

    def test_wrong_path_object_association_is_separate(self):
        result = assessment(observed_path="data/matches/wrong/wrong_tracking_extrapolated.jsonl")
        self.assertFalse(result["checks"]["path_matches"])
        result = assessment(contents_blob_oid="0" * 40)
        self.assertFalse(result["checks"]["tree_vs_contents_blob_oid"])

    def test_malformed_and_oversized_pointers_fail_distinctly(self):
        with self.assertRaisesRegex(IntegrityError, "pointer_malformed"):
            parse_lfs_pointer(b"not a pointer\n")
        with self.assertRaisesRegex(IntegrityError, "pointer_oversized"):
            parse_lfs_pointer(pointer() + b"x" * 1000)

    def test_projected_json_value_does_not_decode_neighbor(self):
        value, _ = project_json_value('{"wanted":{"x":1},"neighbor":{"secret":2}}', "wanted")
        self.assertEqual(value, {"x": 1})
        self.assertNotIn("secret", value)


class FakeResponse:
    def __init__(self, url, body, *, declared=None):
        self._url = url
        self._body = body
        self.headers = {} if declared is None else {"Content-Length": str(declared)}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self._url

    def read(self, maximum):
        return self._body[:maximum]


class FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        return self.response


class MetadataClientTests(unittest.TestCase):
    def test_response_url_change_is_rejected(self):
        response = FakeResponse("https://example.invalid/redirect", b"{}")
        client = GitHubMetadataClient("token", opener=FakeOpener(response))
        with self.assertRaisesRegex(PermissionError, "response_url_changed"):
            client.commit_tree("SkillCorner/opendata", "a" * 40)

    def test_oversized_response_is_rejected_before_body_read(self):
        url = "https://api.github.com/repos/SkillCorner/opendata/git/commits/" + "a" * 40
        response = FakeResponse(url, b"{}", declared=2_000_001)
        client = GitHubMetadataClient("token", opener=FakeOpener(response))
        with self.assertRaisesRegex(IntegrityError, "api_response_oversized"):
            client.commit_tree("SkillCorner/opendata", "a" * 40)

    def test_blob_decode_is_bounded(self):
        oid = "a" * 40
        url = f"https://api.github.com/repos/SkillCorner/opendata/git/blobs/{oid}"
        body = json.dumps({
            "sha": oid, "encoding": "base64", "size": 2000,
            "content": base64.b64encode(b"x" * 2000).decode(),
        }).encode()
        client = GitHubMetadataClient("token", opener=FakeOpener(FakeResponse(url, body)))
        with self.assertRaisesRegex(IntegrityError, "decoded_blob_oversized"):
            client.blob("SkillCorner/opendata", oid, label="synthetic", decoded_limit=1024)


class Session6bFirewallTests(unittest.TestCase):
    def test_runner_has_no_science_or_tracking_payload_import(self):
        import scripts.session_06b_tracking_integrity as runner
        self.assertEqual(runner.forbidden_imports(), [])
        helper_source = Path(runner.IMPLEMENTATION_FILES[1]).read_text()
        self.assertNotIn("media.githubusercontent.com", helper_source)
        self.assertNotIn("objects/batch", helper_source)
        self.assertNotIn("load_projected_match", helper_source)
        self.assertNotIn("expected_credits", helper_source)
        tree = ast.parse(inspect.getsource(runner.review))
        called = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue(called.isdisjoint({"prepare_match_session6", "fit_final_models", "score"}))

    def test_fixed_alias_and_path_allowlist(self):
        import scripts.session_06b_tracking_integrity as runner
        self.assertEqual(set(runner.FILES), {"reserved_01", "development_01"})
        self.assertEqual(runner.FILES["reserved_01"]["match_id"], "1874553")
        self.assertEqual(runner.FILES["development_01"]["match_id"], "1886347")

    def test_lfs_attribute_matching(self):
        import scripts.session_06b_tracking_integrity as runner
        path = "data/matches/example/example_tracking_extrapolated.jsonl"
        self.assertTrue(runner.lfs_attribute_applies(["*.jsonl filter=lfs diff=lfs merge=lfs -text"], path))
        self.assertFalse(runner.lfs_attribute_applies(["*.csv filter=lfs diff=lfs merge=lfs -text"], path))


if __name__ == "__main__":
    unittest.main()
