"""Prospective independent-certificate evidence contract; no empirical routes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Iterable


AGREEMENT = 1e-10
ELIGIBLE_WARNING_CLASS = "scipy.integrate._quadpack_py.IntegrationWarning"
ELIGIBLE_WARNING_MESSAGE = (
    "The occurrence of roundoff error is detected, which prevents the requested "
    "tolerance from being achieved. The error may be underestimated."
)
ELIGIBLE_WARNING_SHA256 = "3f2b9b58ff1c98b7c27fff799d18b42a6dd19e50c2b5f6b60a0b80bfb2798ab3"
SUCCESS_STATUS = "independently_certified_after_roundoff_warning"
METHOD_ID = "session14ar_exact_rational_taylor_lagrange_v1"
AUTHORITY_ID = "session14ar_terminal_interval_8"
AUTHORITY_SHA256 = "d98447c98ab0f04ef2c608b98b9554cecf47ed167bf1fc91775fa53bab6c2dd6"
SOURCE_MANIFEST_SHA256 = "bb3d352e9b43b579f897e36f4f000f3fb770701fe11877f23af76a36668d97b4"
METHOD_AUTHORITY_SHA256 = "49a6f5cb2d7370cc37725ebf11164cc12f721e83f3bca746fd3dada5bd87d62d"
INDEPENDENCE_STATEMENT = (
    "Exact rational Taylor antiderivative with rigorous integrated Lagrange remainder; "
    "no adaptive or production integration."
)


class CertificateError(RuntimeError):
    """A fail-closed certificate-contract error."""


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_load(path: Path) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CertificateError("duplicate_key")
            result[key] = value
        return result
    value = json.loads(path.read_text(), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(CertificateError("nonfinite_json")))
    if type(value) is not dict:
        raise CertificateError("object_required")
    return value


def float_bits(value: float) -> str:
    if type(value) is not float or not math.isfinite(value):
        raise CertificateError("finite_float_required")
    return struct.pack(">d", value).hex()


@dataclass(frozen=True)
class IntegralRequest:
    interval_identity: str
    left_endpoint_binary64: str
    right_endpoint_binary64: str
    field_family: str
    frozen_parameters: tuple[tuple[str, float], ...]
    combination: str
    integrand_specification_hash: str
    structural_partition_authority_hash: str
    method_id: str
    provenance_hash: str
    governing_tolerance: float


@dataclass(frozen=True)
class IndependentIntegralCertificate:
    schema_version: int
    authority_id: str
    authority_sha256: str
    source_manifest_sha256: str
    interval_identity: str
    left_endpoint_binary64: str
    right_endpoint_binary64: str
    field_family: str
    frozen_parameters: tuple[tuple[str, float], ...]
    combination: str
    integrand_specification_hash: str
    structural_partition_authority_hash: str
    lower_bound: float
    upper_bound: float
    method_id: str
    method_authority_hash: str
    independence_statement: str
    provenance_hash: str
    governing_tolerance: float


@dataclass(frozen=True)
class AdaptiveObservation:
    estimate: float
    warning_class: str
    warning_message_sha256: str
    request: IntegralRequest


@dataclass(frozen=True)
class PieceEvidence:
    branch: str
    estimate: float
    lower: float
    upper: float
    adaptive_warning_count: int
    independently_certified_count: int
    blocking_warning_count: int
    status: str


@dataclass(frozen=True)
class ProspectiveVerificationReadiness:
    certificate_registry_valid: bool
    exact_authority_matching_valid: bool
    warning_policy_valid: bool
    aggregation_valid: bool
    ordinary_quadrature_regression_valid: bool
    micro_residual_regression_valid: bool
    synthetic_numerical_regressions_valid: bool
    cases_108_complete: bool
    references_366_complete: bool
    permutations_399_complete: bool
    failure_enforcement_valid: bool
    deterministic: bool
    integrity_valid: bool
    independent_certification_observed: bool
    uncertified_blocking_warning_count: int

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name == "uncertified_blocking_warning_count":
                if type(value) is not int or value < 0:
                    raise TypeError(item.name)
            elif type(value) is not bool:
                raise TypeError(item.name)

    @property
    def ready(self) -> bool:
        checks = [getattr(self, item.name) for item in fields(self)
                  if item.name != "uncertified_blocking_warning_count"]
        return all(checks) and self.uncertified_blocking_warning_count == 0


def _exact_keys(record: dict, expected: set[str], reason: str) -> None:
    if set(record) != expected:
        raise CertificateError(reason)


def _finite(value: object, reason: str) -> float:
    if type(value) not in (int, float) or type(value) is bool:
        raise CertificateError(reason)
    result = float(value)
    if not math.isfinite(result):
        raise CertificateError(reason)
    return result


def _integrand_spec(interval: dict) -> dict:
    hashes = interval["record_hashes"]
    return {
        "interval_identity": "sanitized_terminal_interval_8",
        "left_endpoint_binary64": float_bits(float(interval["normalized_left"])),
        "right_endpoint_binary64": float_bits(float(interval["normalized_right"])),
        "field_family": interval["field_family"],
        "frozen_parameters": [["onset_metres", float(interval["onset_metres"])],
                              ["sigma_metres", float(interval["sigma_metres"])]],
        "combination": interval["combination"],
        "selected_geometry_authority_hash": hashes["000010_selected_geometry.json"],
        "retained_interval_authority_hash": hashes["000121_piece.json"],
        "onset_authority_hash": hashes["000003_onsets.json"],
        "structural_partition_authority_hash": hashes["000020_structure.json"],
    }


def load_session14ar_certificate(root: Path) -> tuple[IndependentIntegralCertificate, AdaptiveObservation, dict]:
    folder = root / "outputs/continuous_occlusion_terminal_interval_reference"
    paths = {name: folder / name for name in (
        "interval_authority.json", "reference_method.json", "reference_result.json",
        "retained_comparison.json", "manifest.json")}
    expected = {
        "interval_authority.json": "ed56a0b44e07f4ece23056257b6909bb8a4ddd7f6a4b1ac72a7a2cb79d963847",
        "reference_method.json": METHOD_AUTHORITY_SHA256,
        "reference_result.json": AUTHORITY_SHA256,
        "retained_comparison.json": "14bd4e920ca369f270b758b80fce8fa237515df2b0e18becb8b8651a65a3974d",
        "manifest.json": SOURCE_MANIFEST_SHA256,
    }
    for name, digest in expected.items():
        if sha(paths[name]) != digest:
            raise CertificateError("stale_authority:" + name)
    interval = strict_load(paths["interval_authority.json"])
    method = strict_load(paths["reference_method.json"])
    result = strict_load(paths["reference_result.json"])
    comparison = strict_load(paths["retained_comparison.json"])
    manifest = strict_load(paths["manifest.json"])
    if manifest.get("outputs") != {name: expected[name] for name in expected if name != "manifest.json" and name != "qc.json"}:
        # The manifest also binds qc; validate the four contract inputs directly instead.
        for name in ("interval_authority.json", "reference_method.json", "reference_result.json", "retained_comparison.json"):
            if manifest.get("outputs", {}).get(name) != expected[name]:
                raise CertificateError("manifest_output_hash")
    if (result != {**result} or result.get("lower") != 0.21369535129402328 or
            result.get("upper") != 0.21369535131181636 or
            result.get("bound_width") != 1.7793072570881918e-11 or
            comparison.get("retained_estimate") != 0.21369535129415176):
        raise CertificateError("session14ar_values")
    if method.get("method") != "exact_rational_integrated_exponential_taylor_enclosure" or not method.get("independent"):
        raise CertificateError("method_authority")
    spec = _integrand_spec(interval)
    spec_hash = sha_bytes(canonical(spec))
    provenance = {
        "interval_authority_sha256": expected["interval_authority.json"],
        "reference_method_sha256": expected["reference_method.json"],
        "reference_result_sha256": expected["reference_result.json"],
        "retained_comparison_sha256": expected["retained_comparison.json"],
        "private_index_sha256": manifest["private_index_sha256"],
    }
    provenance_hash = sha_bytes(canonical(provenance))
    parameters = tuple((name, value) for name, value in spec["frozen_parameters"])
    certificate = IndependentIntegralCertificate(
        1, AUTHORITY_ID, expected["reference_result.json"], expected["manifest.json"],
        spec["interval_identity"], spec["left_endpoint_binary64"],
        spec["right_endpoint_binary64"], spec["field_family"], parameters,
        spec["combination"], spec_hash, spec["structural_partition_authority_hash"],
        float(result["lower"]), float(result["upper"]), METHOD_ID,
        expected["reference_method.json"],
        INDEPENDENCE_STATEMENT,
        provenance_hash, AGREEMENT)
    request = IntegralRequest(
        certificate.interval_identity, certificate.left_endpoint_binary64,
        certificate.right_endpoint_binary64, certificate.field_family,
        certificate.frozen_parameters, certificate.combination,
        certificate.integrand_specification_hash,
        certificate.structural_partition_authority_hash, certificate.method_id,
        certificate.provenance_hash, certificate.governing_tolerance)
    observation = AdaptiveObservation(float(comparison["retained_estimate"]),
        ELIGIBLE_WARNING_CLASS, str(comparison["warning_message_sha256"]), request)
    return certificate, observation, {"expected_hashes": expected, "integrand_specification": spec,
                                      "provenance": provenance}


def validate_certificate(certificate: IndependentIntegralCertificate, request: IntegralRequest) -> None:
    if type(certificate) is not IndependentIntegralCertificate or type(request) is not IntegralRequest:
        raise CertificateError("certificate_type")
    if (certificate.schema_version != 1 or certificate.authority_id != AUTHORITY_ID or
            certificate.authority_sha256 != AUTHORITY_SHA256 or
            certificate.source_manifest_sha256 != SOURCE_MANIFEST_SHA256 or
            certificate.method_authority_hash != METHOD_AUTHORITY_SHA256 or
            certificate.independence_statement != INDEPENDENCE_STATEMENT):
        raise CertificateError("certificate_authority")
    pairs = ((certificate.interval_identity, request.interval_identity, "interval_identity"),
             (certificate.left_endpoint_binary64, request.left_endpoint_binary64, "left_endpoint"),
             (certificate.right_endpoint_binary64, request.right_endpoint_binary64, "right_endpoint"),
             (certificate.field_family, request.field_family, "field_family"),
             (certificate.frozen_parameters, request.frozen_parameters, "frozen_parameters"),
             (certificate.combination, request.combination, "combination"),
             (certificate.integrand_specification_hash, request.integrand_specification_hash, "integrand"),
             (certificate.structural_partition_authority_hash, request.structural_partition_authority_hash, "structure"),
             (certificate.method_id, request.method_id, "method"),
             (certificate.provenance_hash, request.provenance_hash, "provenance"),
             (certificate.governing_tolerance, request.governing_tolerance, "tolerance"))
    for actual, wanted, reason in pairs:
        if actual != wanted:
            raise CertificateError("authority_mismatch:" + reason)
    if certificate.method_id != METHOD_ID or certificate.governing_tolerance != AGREEMENT:
        raise CertificateError("unapproved_authority")
    for value in (certificate.lower_bound, certificate.upper_bound):
        _finite(value, "nonfinite_bound")
    if certificate.upper_bound < certificate.lower_bound:
        raise CertificateError("reversed_bounds")
    if certificate.upper_bound - certificate.lower_bound > AGREEMENT:
        raise CertificateError("certificate_too_wide")


def ordinary_piece(value: float) -> PieceEvidence:
    value = _finite(value, "ordinary_nonfinite")
    return PieceEvidence("ordinary", value, value, value, 0, 0, 0, "warning_free")


def micro_residual_piece(lower: float, upper: float, estimate: float = 0.0) -> PieceEvidence:
    lower = _finite(lower, "micro_nonfinite")
    upper = _finite(upper, "micro_nonfinite")
    estimate = _finite(estimate, "micro_nonfinite")
    if upper < lower or not lower <= estimate <= upper:
        raise CertificateError("micro_interval")
    return PieceEvidence("micro_residual", estimate, lower, upper, 0, 0, 0,
                         "bounded_residual")


def certify_warning(observation: AdaptiveObservation,
                    certificate: IndependentIntegralCertificate | None) -> PieceEvidence:
    if observation.warning_class != ELIGIBLE_WARNING_CLASS or observation.warning_message_sha256 != ELIGIBLE_WARNING_SHA256:
        raise CertificateError("ineligible_warning")
    if certificate is None:
        raise CertificateError("certificate_unavailable")
    validate_certificate(certificate, observation.request)
    estimate = _finite(observation.estimate, "adaptive_nonfinite")
    if not certificate.lower_bound <= estimate <= certificate.upper_bound:
        raise CertificateError("estimate_outside_certificate")
    return PieceEvidence("independent_certificate", estimate, certificate.lower_bound,
                         certificate.upper_bound, 1, 1, 0, SUCCESS_STATUS)


def blocking_piece(reason: str) -> PieceEvidence:
    if not reason:
        raise CertificateError("blocking_reason")
    return PieceEvidence("blocking", 0.0, 0.0, 0.0, 1, 0, 1, reason)


def aggregate_pieces(pieces: Iterable[PieceEvidence]) -> dict:
    items = tuple(pieces)
    if not items:
        raise CertificateError("no_pieces")
    if any(item.branch == "blocking" or item.blocking_warning_count for item in items):
        raise CertificateError("blocking_piece")
    lower_stable = math.fsum(item.lower for item in items)
    upper_stable = math.fsum(item.upper for item in items)
    estimate = math.fsum(item.estimate for item in items)
    if not all(math.isfinite(x) for x in (lower_stable, upper_stable, estimate)):
        raise CertificateError("aggregate_nonfinite")
    lower = math.nextafter(lower_stable, -math.inf)
    upper = math.nextafter(upper_stable, math.inf)
    return {
        "adaptive_warning_count": sum(x.adaptive_warning_count for x in items),
        "independently_certified_count": sum(x.independently_certified_count for x in items),
        "blocking_warning_count": sum(x.blocking_warning_count for x in items),
        "ordinary_piece_count": sum(x.branch == "ordinary" for x in items),
        "micro_residual_piece_count": sum(x.branch == "micro_residual" for x in items),
        "certificate_piece_count": sum(x.branch == "independent_certificate" for x in items),
        "production_estimate": estimate,
        "aggregate_lower": lower,
        "aggregate_upper": upper,
        "final_evidence_status": (SUCCESS_STATUS if any(x.branch == "independent_certificate" for x in items)
                                  else "historical_warning_free_or_bounded_residual"),
        "outward_rounding_levels": 1,
    }


def certificate_record(certificate: IndependentIntegralCertificate) -> dict:
    record = asdict(certificate)
    record["frozen_parameters"] = [list(pair) for pair in certificate.frozen_parameters]
    return record
