"""Independent exact-rational enclosure for one retained terminal interval.

This internal module deliberately has no NumPy, SciPy, data-loader, model, or
production-integration imports.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Mapping


AGREEMENT = 1e-10
ORACLE_TOLERANCE = 1e-12
MAX_ORDER = 256
PUBLIC_FILES = (
    "interval_authority.json", "reference_method.json", "reference_result.json",
    "retained_comparison.json", "qc.json",
)

_STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"')
_SCALAR = re.compile(r'(?:-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null)')


class ReferenceError(ValueError):
    """A sanitized interval-reference contract failure."""


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_load(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ReferenceError("duplicate_key")
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ReferenceError("nonfinite")))
    except (OSError, json.JSONDecodeError) as error:
        raise ReferenceError("record_invalid") from error


def atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def create_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical(value))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


class JsonView:
    """Validate JSON syntax while decoding only explicitly selected spans."""

    def __init__(self, text: str):
        self.text = text
        try:
            end = self.skip(self.ws(0))
            if self.ws(end) != len(text):
                raise ValueError
        except (IndexError, ValueError, RecursionError) as error:
            raise ReferenceError("json_syntax") from error

    def ws(self, index: int) -> int:
        while index < len(self.text) and self.text[index] in " \r\n\t":
            index += 1
        return index

    def skip(self, index: int, depth: int = 0) -> int:
        if depth > 64:
            raise ValueError
        index = self.ws(index)
        token = self.text[index]
        if token == '"':
            match = _STRING.match(self.text, index)
            if not match:
                raise ValueError
            return match.end()
        if token in "{[":
            close = "}" if token == "{" else "]"
            index = self.ws(index + 1)
            if self.text[index] == close:
                return index + 1
            while True:
                if token == "{":
                    if self.text[index] != '"':
                        raise ValueError
                    index = self.ws(self.skip(index, depth + 1))
                    if self.text[index] != ":":
                        raise ValueError
                    index = self.ws(index + 1)
                index = self.ws(self.skip(index, depth + 1))
                if self.text[index] == close:
                    return index + 1
                if self.text[index] != ",":
                    raise ValueError
                index = self.ws(index + 1)
        match = _SCALAR.match(self.text, index)
        if not match:
            raise ValueError
        return match.end()

    def fields(self, start: int = 0) -> dict[str, tuple[int, int]]:
        index = self.ws(start)
        if self.text[index] != "{":
            raise ReferenceError("object_required")
        result = {}
        index = self.ws(index + 1)
        if self.text[index] == "}":
            return result
        while True:
            end = self.skip(index)
            key = json.loads(self.text[index:end])
            if key in result:
                raise ReferenceError("duplicate_key")
            index = self.ws(end)
            if self.text[index] != ":":
                raise ReferenceError("json_colon")
            index = self.ws(index + 1)
            end = self.skip(index)
            result[key] = (index, end)
            index = self.ws(end)
            if self.text[index] == "}":
                return result
            if self.text[index] != ",":
                raise ReferenceError("json_separator")
            index = self.ws(index + 1)

    def items(self, span: tuple[int, int]):
        index = self.ws(span[0])
        if self.text[index] != "[":
            raise ReferenceError("array_required")
        index = self.ws(index + 1)
        if self.text[index] == "]":
            return
        while True:
            end = self.skip(index)
            yield index, end
            index = self.ws(end)
            if self.text[index] == "]":
                return
            if self.text[index] != ",":
                raise ReferenceError("json_separator")
            index = self.ws(index + 1)

    def read(self, span: tuple[int, int]) -> Any:
        return json.loads(self.text[slice(*span)])


def _point(value: Any) -> tuple[float, float]:
    if (not isinstance(value, list) or len(value) != 2 or
            any(isinstance(item, bool) or not isinstance(item, (int, float)) or
                not math.isfinite(item) for item in value)):
        raise ReferenceError("point_invalid")
    return float(value[0]), float(value[1])


def restricted_geometry(text: str, owner: int) -> dict[str, tuple[float, float]]:
    """Decode only carrier, receiver, and one retained defender ordinal."""
    if isinstance(owner, bool) or not isinstance(owner, int) or owner < 0:
        raise ReferenceError("owner_invalid")
    view = JsonView(text)
    fields = view.fields()
    if set(fields) != {"alias", "carrier", "receiver", "defenders"}:
        raise ReferenceError("geometry_schema")
    selected = None
    count = 0
    for count, span in enumerate(view.items(fields["defenders"]), start=1):
        if count - 1 == owner:
            selected = _point(view.read(span))
    if selected is None:
        raise ReferenceError("owner_missing")
    return {"carrier": _point(view.read(fields["carrier"])),
            "receiver": _point(view.read(fields["receiver"])),
            "defender": selected, "defender_count": count}


def structural_authority(structure: Mapping[str, Any], onset_record: Mapping[str, Any],
                         left: float, right: float) -> dict[str, Any]:
    if not (math.isfinite(left) and math.isfinite(right) and 0 <= left < right <= 1):
        raise ReferenceError("interval_invalid")
    switches = structure.get("switches")
    onsets = structure.get("onsets")
    envelope = structure.get("envelope")
    if not isinstance(switches, list) or not isinstance(onsets, list) or not isinstance(envelope, dict):
        raise ReferenceError("structure_schema")
    if envelope.get("tie_intervals") != []:
        for tie in envelope.get("tie_intervals", []):
            if max(left, tie["start"]) < min(right, tie["end"]):
                raise ReferenceError("interior_tie")
    interior = [item for item in switches if left < item.get("first_post_switch", -1) < right]
    if interior:
        raise ReferenceError("interior_switch")
    preceding = [item for item in switches if item.get("first_post_switch", math.inf) <= left]
    if not preceding or len(preceding[-1].get("owners_after", [])) != 1:
        raise ReferenceError("single_owner_unavailable")
    owner = preceding[-1]["owners_after"][0]
    full = [item for item in onsets if item.get("defender_index") == owner and item.get("branch") == 1]
    if len(full) != 1 or full[0].get("first_post_branch", math.inf) > left:
        raise ReferenceError("owner_not_fully_active")
    partitions = onset_record.get("partitions")
    if not isinstance(partitions, list) or left not in partitions or right not in partitions:
        raise ReferenceError("interval_not_retained_partition")
    if any(left < float(value) < right for value in partitions):
        raise ReferenceError("interior_onset")
    return {"owner": owner, "single_owner": True, "fully_active": True,
            "interior_switches": 0, "interior_ties": 0, "interior_onsets": 0}


def exact_lambda(geometry: Mapping[str, Any]) -> Fraction:
    origin = tuple(Fraction.from_float(x) for x in geometry["carrier"])
    receiver = tuple(Fraction.from_float(x) for x in geometry["receiver"])
    defender = tuple(Fraction.from_float(x) for x in geometry["defender"])
    vx, vy = receiver[0] - origin[0], receiver[1] - origin[1]
    dx, dy = defender[0] - origin[0], defender[1] - origin[1]
    radius2 = dx * dx + dy * dy
    if radius2 <= Fraction.from_float(1e-9) ** 2:
        raise ReferenceError("origin_defender_invalid")
    cross = vx * dy - vy * dx
    return cross * cross / (8 * radius2)


def scalar_value(rate: Fraction, t: float) -> float:
    if not math.isfinite(t):
        raise ReferenceError("scalar_input_nonfinite")
    exponent = rate * Fraction.from_float(float(t)) ** 2
    return math.exp(-float(exponent))


def reconstruction_check(rate: Fraction, trace: Any) -> dict[str, Any]:
    if not isinstance(trace, list) or not trace:
        raise ReferenceError("trace_missing")
    maximum_error = 0.0
    for item in trace:
        if (not isinstance(item, list) or len(item) != 2 or
                any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                    not math.isfinite(value) for value in item)):
            raise ReferenceError("trace_invalid")
        actual = scalar_value(rate, float(item[0]))
        expected = float(item[1])
        error = abs(actual - expected)
        maximum_error = max(maximum_error, error)
        if not math.isclose(actual, expected, abs_tol=ORACLE_TOLERANCE,
                            rel_tol=ORACLE_TOLERANCE):
            raise ReferenceError("scalar_reconstruction_mismatch")
    return {"callback_count": len(trace), "maximum_error": maximum_error,
            "absolute_tolerance": ORACLE_TOLERANCE,
            "relative_tolerance": ORACLE_TOLERANCE, "passed": True}


def outward_lower(value: Fraction) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ReferenceError("bound_nonfinite")
    if Fraction.from_float(result) > value:
        result = math.nextafter(result, -math.inf)
    return result


def outward_upper(value: Fraction) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ReferenceError("bound_nonfinite")
    if Fraction.from_float(result) < value:
        result = math.nextafter(result, math.inf)
    return result


def taylor_enclosure(rate: Fraction, left: float, right: float,
                     *, agreement: float = AGREEMENT,
                     max_order: int = MAX_ORDER) -> dict[str, Any]:
    if rate < 0 or not (math.isfinite(left) and math.isfinite(right) and 0 <= left <= right):
        raise ReferenceError("enclosure_input")
    if not math.isfinite(agreement) or agreement <= 0 or max_order < 0:
        raise ReferenceError("enclosure_contract")
    a, b = Fraction.from_float(left), Fraction.from_float(right)
    total = Fraction(0)
    factorial = 1
    power = Fraction(1)
    for order in range(max_order + 1):
        if order:
            power *= -rate
            factorial *= order
        degree = 2 * order + 1
        total += power * (b ** degree - a ** degree) / (factorial * degree)
        remainder_order = order + 1
        remainder = (rate ** remainder_order *
                     (b ** (2 * remainder_order + 1) - a ** (2 * remainder_order + 1)) /
                     (math.factorial(remainder_order) * (2 * remainder_order + 1)))
        exact_lower, exact_upper = total - remainder, total + remainder
        lower, upper = outward_lower(exact_lower), outward_upper(exact_upper)
        if upper - lower <= agreement:
            return {"available": True, "order": order, "lower": lower, "upper": upper,
                    "width": upper - lower, "exact_lower": exact_lower,
                    "exact_upper": exact_upper, "remainder": remainder}
    return {"available": False, "order": max_order, "reason": "order_cap",
            "lower": lower, "upper": upper, "width": upper - lower,
            "exact_lower": exact_lower, "exact_upper": exact_upper,
            "remainder": remainder}


def point_interval_distance(value: float, lower: float, upper: float) -> float:
    if not all(math.isfinite(item) for item in (value, lower, upper)) or lower > upper:
        raise ReferenceError("comparison_invalid")
    return lower - value if value < lower else value - upper if value > upper else 0.0


def compare_retained(estimate: float, reported_error: float,
                     enclosure: Mapping[str, Any]) -> dict[str, Any]:
    if not enclosure.get("available"):
        return {"available": False, "reason": enclosure.get("reason", "reference_unavailable")}
    lower, upper = float(enclosure["lower"]), float(enclosure["upper"])
    distance = point_interval_distance(float(estimate), lower, upper)
    width = upper - lower
    within = distance <= AGREEMENT
    return {"available": True, "retained_estimate": float(estimate),
            "retained_reported_error": float(reported_error), "lower": lower, "upper": upper,
            "bound_width": width, "point_to_interval_distance": distance,
            "inside_bound": lower <= estimate <= upper,
            "within_existing_authority": within and width <= AGREEMENT,
            "agreement_authority": AGREEMENT,
            "bound_width_to_authority_ratio": width / AGREEMENT}


def validate_public_package(directory: Path) -> dict[str, Any]:
    manifest = strict_load(directory / "manifest.json")
    if set(manifest) != {"schema_version", "status", "authority", "outputs", "private_index_sha256"}:
        raise ReferenceError("manifest_schema")
    if manifest["schema_version"] != 1 or manifest["status"] != "closed":
        raise ReferenceError("manifest_status")
    if set(manifest["outputs"]) != set(PUBLIC_FILES):
        raise ReferenceError("manifest_outputs")
    for name, expected in manifest["outputs"].items():
        if sha(directory / name) != expected:
            raise ReferenceError("output_hash")
    qc = strict_load(directory / "qc.json")
    required = {"schema_version", "status", "execution_valid", "classification", "readiness",
                "intervals_evaluated", "full_edges_recomputed", "additional_states_or_edges",
                "scientific_products_opened", "prohibited_accesses", "private_index_sha256"}
    if set(qc) != required or qc["status"] != "closed" or not qc["execution_valid"]:
        raise ReferenceError("qc_schema")
    if qc["intervals_evaluated"] != 1 or qc["full_edges_recomputed"] != 0 or qc["additional_states_or_edges"] != 0:
        raise ReferenceError("scope_counts")
    if qc["scientific_products_opened"] != 0 or qc["prohibited_accesses"] != 0:
        raise ReferenceError("scope_access")
    if qc["private_index_sha256"] != manifest["private_index_sha256"]:
        raise ReferenceError("private_binding")
    result = strict_load(directory / "reference_result.json")
    comparison = strict_load(directory / "retained_comparison.json")
    if result.get("classification") != qc["classification"] or result.get("readiness") != qc["readiness"]:
        raise ReferenceError("decision_mismatch")
    if comparison.get("within_existing_authority") != (qc["classification"] == "A"):
        raise ReferenceError("classification_support")
    return qc


__all__ = [
    "AGREEMENT", "MAX_ORDER", "ORACLE_TOLERANCE", "PUBLIC_FILES", "ReferenceError",
    "atomic", "canonical", "compare_retained", "create_once", "digest", "exact_lambda",
    "outward_lower", "outward_upper", "point_interval_distance", "reconstruction_check",
    "restricted_geometry", "scalar_value", "sha", "strict_load", "structural_authority",
    "taylor_enclosure", "validate_public_package",
]
