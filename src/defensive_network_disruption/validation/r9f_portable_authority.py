"""Hash-only CI-portable authority for the R9E structural comparison."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURE = Path("tests/authority_fixtures/session14r9e_certificate_authority.json")
INTERVAL = Path("outputs/continuous_occlusion_terminal_interval_reference/interval_authority.json")
MANIFEST = Path("outputs/continuous_occlusion_terminal_interval_reference/manifest.json")
SOURCE_MANIFEST_SHA256 = "bb3d352e9b43b579f897e36f4f000f3fb770701fe11877f23af76a36668d97b4"
SOURCE_STRUCTURE_SHA256 = "791ddcd717c5f08d7c834de127388c81012192c859aa20ce0c96f342fbbe69e6"
SELECTED_GEOMETRY_SHA256 = "fe39401fee30c197082e5513d376308cdfe3eb8fbf35b7bbc7ddb7a749f41d2e"
PURPOSE = "Bind the exact structural semantics historically compared by R9E while keeping retained values private."
DERIVATION = "SHA-256 of the frozen ordered partitions, five onset fields, and eight switch fields selected from the hash-bound Session 14am structural record."
NON_RECONSTRUCTIVE = "Contains authority hashes only and no retained numerical values or identifying records."
ONSET_FIELDS = ("defender_index", "branch", "last_pre_branch", "first_post_branch", "raw_scalar_result")
SWITCH_FIELDS = ("last_pre_switch", "exact_zero_start", "exact_zero_end", "first_post_switch",
                 "owners_before", "owners_at", "owners_after", "crossing_pairs")
KEYS = {"schema_version", "authority_id", "source_session", "source_manifest_sha256",
        "source_artifact_sha256", "selected_geometry_authority_hash",
        "semantic_projection_sha256", "field_selection_specification_sha256", "purpose",
        "derivation_statement", "non_reconstructive_statement"}


class PortableAuthorityError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def selection_specification() -> dict:
    return {"partitions": "ordered_binary64_values", "onset_fields": list(ONSET_FIELDS),
            "switch_fields": list(SWITCH_FIELDS), "sequence_order": "preserved"}


def _plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value


def semantic_projection(partitions, onsets, switches) -> dict:
    def chosen(value, fields):
        record = _plain(value)
        return {name: record[name] for name in fields}
    return {"partitions": list(partitions),
            "onsets": [chosen(value, ONSET_FIELDS) for value in onsets],
            "switches": [chosen(value, SWITCH_FIELDS) for value in switches]}


def semantic_projection_hash(partitions, onsets, switches) -> str:
    return digest(canonical(semantic_projection(partitions, onsets, switches)))


def selected_geometry_hash(context: dict) -> str:
    selected = {"alias": context["alias"],
                "carrier": list(map(float, context["origin"])),
                "defenders": [list(map(float, item)) for item in context["defenders"]],
                "receiver": list(map(float, context["receiver"]))}
    return digest(canonical(selected))


def load_fixture(root: Path) -> dict:
    path = root / FIXTURE
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise PortableAuthorityError("portable_fixture_unavailable") from error
    if type(value) is not dict or set(value) != KEYS or value.get("schema_version") != 1:
        raise PortableAuthorityError("portable_fixture_schema")
    if canonical(value) != path.read_bytes():
        raise PortableAuthorityError("portable_fixture_noncanonical")
    for name in ("source_manifest_sha256", "source_artifact_sha256",
                 "selected_geometry_authority_hash", "semantic_projection_sha256",
                 "field_selection_specification_sha256"):
        if type(value[name]) is not str or len(value[name]) != 64:
            raise PortableAuthorityError("portable_fixture_hash")
    if (value["authority_id"] != "session14ar_terminal_interval_8" or
            value["source_session"] != "14ar" or
            value["source_manifest_sha256"] != SOURCE_MANIFEST_SHA256 or
            value["source_artifact_sha256"] != SOURCE_STRUCTURE_SHA256 or
            value["selected_geometry_authority_hash"] != SELECTED_GEOMETRY_SHA256 or
            value["field_selection_specification_sha256"] != digest(canonical(selection_specification())) or
            value["purpose"] != PURPOSE or value["derivation_statement"] != DERIVATION or
            value["non_reconstructive_statement"] != NON_RECONSTRUCTIVE):
        raise PortableAuthorityError("portable_fixture_authority")
    try:
        manifest_hash = file_digest(root / MANIFEST)
        interval = json.loads((root / INTERVAL).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise PortableAuthorityError("public_source_unavailable") from error
    if manifest_hash != SOURCE_MANIFEST_SHA256:
        raise PortableAuthorityError("source_manifest_stale")
    hashes = interval["record_hashes"]
    if (hashes["000020_structure.json"] != SOURCE_STRUCTURE_SHA256 or
            hashes["000010_selected_geometry.json"] != SELECTED_GEOMETRY_SHA256):
        raise PortableAuthorityError("public_source_mismatch")
    text = path.read_text().lower()
    for prohibited in ("carrier", "receiver", "defenders", "coordinate", "event_key", "owner_ordinal"):
        if prohibited in text:
            raise PortableAuthorityError("reconstructive_field")
    return value


__all__ = ["PortableAuthorityError", "canonical", "digest", "load_fixture",
           "selected_geometry_hash", "selection_specification", "semantic_projection",
           "semantic_projection_hash"]
