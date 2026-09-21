"""Synthetic-only terminal-cell authority for prospective evidence retention.

The module accepts exact derived coefficients.  It has no geometry loader,
field callback, owner certification, localization, or empirical identifier.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math

from .r9j_reference import Bounds, down, exp_negative, smooth, sqrt_bounds, up

SCHEMA_VERSION = 1
SERIALIZATION = "canonical-json-v1"
FORMULA = {
    "candidate": "constant_width",
    "field": "smooth(dot*t/sqrt(q)-sqrt(q))*exp(-cross2*t*t/(8*q))",
    "fraction_encoding": "lowest-terms-signed-decimal",
    "interval_scale": "2^-256",
}


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def digest(value) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()


FORMULA_SHA256 = digest(FORMULA)


def _hash(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
            item not in "0123456789abcdef" for item in value):
        raise ValueError("authority_hash")
    return value


def fraction_record(value: F) -> dict:
    value = F(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def parse_fraction(value) -> F:
    if set(value) != {"numerator", "denominator"}:
        raise ValueError("fraction_schema")
    if not all(isinstance(value[key], str) for key in value):
        raise ValueError("fraction_type")
    try:
        numerator = int(value["numerator"])
        denominator = int(value["denominator"])
    except ValueError as error:
        raise ValueError("fraction_decimal") from error
    if denominator <= 0:
        raise ValueError("fraction_denominator")
    result = F(numerator, denominator)
    if fraction_record(result) != value:
        raise ValueError("fraction_noncanonical")
    return result


@dataclass(frozen=True)
class Coefficients:
    q: F
    dot: F
    cross2: F

    def __post_init__(self):
        if any(type(value) is not F for value in (self.q, self.dot, self.cross2)):
            raise ValueError("coefficient_type")
        if self.q <= F.from_float(1e-9) ** 2 or self.cross2 < 0:
            raise ValueError("coefficient_range")

    def payload(self) -> dict:
        return {"q": fraction_record(self.q), "dot": fraction_record(self.dot),
                "cross2": fraction_record(self.cross2)}

    @property
    def authority_sha256(self) -> str:
        return digest({"candidate": "constant_width", **self.payload()})

    @classmethod
    def from_record(cls, value):
        if set(value) != {"q", "dot", "cross2", "authority_sha256"}:
            raise ValueError("coefficient_schema")
        result = cls(*(parse_fraction(value[key]) for key in ("q", "dot", "cross2")))
        if _hash(value["authority_sha256"]) != result.authority_sha256:
            raise ValueError("coefficient_hash")
        return result

    def record(self) -> dict:
        return {**self.payload(), "authority_sha256": self.authority_sha256}

    def bounds(self, left: F, right: F) -> tuple[Bounds, Bounds | None]:
        t = Bounds(F(left), F(right))
        rho = sqrt_bounds(self.q)
        alpha = Bounds.point(self.dot) / rho
        ell = alpha * t - rho
        gate = Bounds(down(smooth(ell.lo)), up(smooth(ell.hi)))
        lam = self.cross2 / (8 * self.q)
        gaussian = Bounds(exp_negative(lam * right * right).lo,
                          exp_negative(lam * left * left).hi)
        value = gate * gaussian
        derivative = None
        if ell.hi <= 0:
            derivative = Bounds.point(0)
        elif ell.lo >= 0 and (ell.hi <= 1 or ell.lo >= 1):
            gate_prime = (6 * ell * (Bounds.point(1) - ell) * alpha
                          if ell.hi <= 1 else Bounds.point(0))
            gaussian_prime = Bounds.point(-self.cross2 / (4 * self.q)) * t
            derivative = gaussian * (gate_prime + gate * gaussian_prime)
        return value, derivative


SOURCE_KEYS = (
    "r9v_private_index_sha256", "boundary_capture_sha256",
    "ordered_partition_sha256", "selected_edge_sha256",
    "reference_implementation_sha256",
)


def create_authority(*, ordinal: int, depth: int, left: F, right: F,
                     pair: tuple[Coefficients, Coefficients],
                     competitors: tuple[Coefficients, ...], source: dict) -> dict:
    if type(ordinal) is not int or ordinal < 0 or type(depth) is not int or depth < 0:
        raise ValueError("cell_identity")
    left, right = F(left), F(right)
    if not 0 <= left < right <= 1:
        raise ValueError("cell_bounds")
    if len(pair) != 2 or pair[0].authority_sha256 != pair[1].authority_sha256:
        raise ValueError("pair_authority")
    if not competitors:
        raise ValueError("competitors_required")
    if set(source) != set(SOURCE_KEYS):
        raise ValueError("source_schema")
    source = {key: _hash(source[key]) for key in SOURCE_KEYS}
    coefficients = {item.authority_sha256: item for item in (*pair, *competitors)}
    ordered = [coefficients[key].record() for key in sorted(coefficients)]
    pair_hashes = [item.authority_sha256 for item in pair]
    competitor_hashes = sorted({item.authority_sha256 for item in competitors})
    base = {
        "schema_version": SCHEMA_VERSION,
        "serialization": SERIALIZATION,
        "candidate": "constant_width",
        "formula_authority_sha256": FORMULA_SHA256,
        "cell": {"ordinal": ordinal, "depth": depth,
                 "left": fraction_record(left), "right": fraction_record(right)},
        "coefficients": ordered,
        "pair": pair_hashes,
        "competitors": competitor_hashes,
        "source_authority": source,
    }
    return {**base, "provenance_sha256": digest(base)}


def load_authority(value) -> tuple[dict, tuple[Coefficients, Coefficients], tuple[Coefficients, ...]]:
    required = {"schema_version", "serialization", "candidate",
                "formula_authority_sha256", "cell", "coefficients", "pair",
                "competitors", "source_authority", "provenance_sha256"}
    if set(value) != required:
        raise ValueError("terminal_authority_schema")
    if value["schema_version"] != SCHEMA_VERSION or value["serialization"] != SERIALIZATION:
        raise ValueError("terminal_authority_version")
    if value["candidate"] != "constant_width" or value["formula_authority_sha256"] != FORMULA_SHA256:
        raise ValueError("terminal_formula_authority")
    cell = value["cell"]
    if set(cell) != {"ordinal", "depth", "left", "right"} or type(cell["ordinal"]) is not int or type(cell["depth"]) is not int:
        raise ValueError("terminal_cell_schema")
    left, right = parse_fraction(cell["left"]), parse_fraction(cell["right"])
    if cell["ordinal"] < 0 or cell["depth"] < 0 or not 0 <= left < right <= 1:
        raise ValueError("terminal_cell_values")
    if set(value["source_authority"]) != set(SOURCE_KEYS):
        raise ValueError("terminal_source_schema")
    for item in value["source_authority"].values():
        _hash(item)
    records = value["coefficients"]
    if not isinstance(records, list) or not records:
        raise ValueError("terminal_coefficients")
    parsed = [Coefficients.from_record(item) for item in records]
    lookup = {item.authority_sha256: item for item in parsed}
    if len(lookup) != len(parsed) or list(lookup) != sorted(lookup):
        raise ValueError("terminal_coefficient_order")
    if not isinstance(value["pair"], list) or len(value["pair"]) != 2:
        raise ValueError("terminal_pair_schema")
    if not isinstance(value["competitors"], list) or not value["competitors"] or value["competitors"] != sorted(set(value["competitors"])):
        raise ValueError("terminal_competitor_schema")
    try:
        pair = tuple(lookup[_hash(item)] for item in value["pair"])
        competitors = tuple(lookup[_hash(item)] for item in value["competitors"])
    except KeyError as error:
        raise ValueError("terminal_coefficient_reference") from error
    if pair[0].authority_sha256 != pair[1].authority_sha256:
        raise ValueError("terminal_pair_authority")
    base = {key: value[key] for key in required - {"provenance_sha256"}}
    if _hash(value["provenance_sha256"]) != digest(base):
        raise ValueError("terminal_provenance")
    # Canonical byte equality rejects alternate but semantically similar encodings.
    if canonical(value) != canonical(create_authority(
            ordinal=cell["ordinal"], depth=cell["depth"], left=left, right=right,
            pair=pair, competitors=competitors, source=value["source_authority"])):
        raise ValueError("terminal_noncanonical")
    return {"ordinal": cell["ordinal"], "depth": cell["depth"],
            "left": left, "right": right}, pair, competitors


def derive_leaf_bounds(outer_left: F, outer_right: F,
                       depths: tuple[int, ...], ordinal: int) -> tuple[F, F]:
    outer_left, outer_right = F(outer_left), F(outer_right)
    if not 0 <= outer_left < outer_right <= 1 or not depths or not 0 <= ordinal < len(depths):
        raise ValueError("partition_authority")
    if any(type(depth) is not int or depth < 0 or depth > 256 for depth in depths):
        raise ValueError("partition_depth")
    span = outer_right - outer_left
    widths = tuple(span / (1 << depth) for depth in depths)
    if sum(widths, F(0)) != span:
        raise ValueError("partition_coverage")
    left = outer_left + sum(widths[:ordinal], F(0))
    return left, left + widths[ordinal]


def classify_terminal(value, *, max_depth=48, max_leaves=4096) -> dict:
    cell, pair, competitors = load_authority(value)
    left, right = cell["left"], cell["right"]
    representative = pair[0]
    if any(item.authority_sha256 == representative.authority_sha256 for item in competitors):
        return {"classification": "TD", "leaves": 1, "max_depth": 0,
                "pair_equal": True, "complete": True}
    if not 0 <= max_depth <= 80 or not 1 <= max_leaves <= 65_536:
        raise ValueError("refinement_limits")

    def relation(first: Coefficients, second: Coefficients, a: F, b: F):
        x, _ = first.bounds(a, b); y, _ = second.bounds(a, b)
        difference = x - y
        return 1 if difference.lo > 0 else -1 if difference.hi < 0 else 0

    endpoint_relations = []
    for competitor in competitors:
        endpoint_relations.append((relation(representative, competitor, left, left),
                                   relation(representative, competitor, right, right)))
    if any(a * b == -1 for a, b in endpoint_relations):
        return {"classification": "TC", "leaves": 1, "max_depth": 0,
                "pair_equal": True, "complete": True}
    if all(relation(representative, item, left, right) > 0 for item in competitors):
        return {"classification": "TA", "leaves": 1, "max_depth": 0,
                "pair_equal": True, "complete": True}
    if any(relation(representative, item, left, right) < 0 for item in competitors):
        return {"classification": "TB", "leaves": 1, "max_depth": 0,
                "pair_equal": True, "complete": True}

    pending = [(left, right, 0)]; settled = []
    while pending:
        a, b, depth = pending.pop()
        statuses = [relation(representative, item, a, b) for item in competitors]
        status = "pair" if all(item > 0 for item in statuses) else "third" if any(item < 0 for item in statuses) else "unresolved"
        limited = depth >= max_depth or len(settled) + len(pending) + 1 >= max_leaves
        if status == "unresolved" and not limited:
            midpoint = (a + b) / 2
            pending.extend(((midpoint, b, depth + 1), (a, midpoint, depth + 1)))
        else:
            settled.append((a, b, depth, status))
    states = {item[3] for item in settled}
    if states == {"pair"}: classification = "TA"
    elif states == {"third"}: classification = "TB"
    elif "pair" in states and "third" in states: classification = "TC"
    else: classification = "TE"
    return {"classification": classification, "leaves": len(settled),
            "max_depth": max(item[2] for item in settled), "pair_equal": True,
            "complete": "unresolved" not in states}


def synthetic_sufficiency() -> list[dict]:
    """Provider-free round trips; all source objects are discarded before use."""
    source = {key: digest(("synthetic:" + key).encode()) for key in SOURCE_KEYS}

    def coefficients(dot, cross2):
        return Coefficients(F(1), F(dot), F(cross2))

    def evidence(pair, competitors):
        value = create_authority(ordinal=1, depth=2, left=F(1, 2), right=F(1),
                                 pair=(pair, pair), competitors=tuple(competitors),
                                 source=source)
        # The JSON boundary proves no Python source object is retained by the loader.
        return json.loads(canonical(value))

    fixtures = (
        ("pair_globally_maximal", "TA", evidence(coefficients(4, 8), (coefficients(4, 16),)), {}),
        ("third_defender_dominant", "TB", evidence(coefficients(4, 16), (coefficients(4, 8),)), {}),
        ("dominance_switch", "TC", evidence(coefficients(3, F(4, 5)), (coefficients(4, 16),)), {}),
        ("equality_inside_cell", "TD", evidence(coefficients(4, 8), (coefficients(4, 8),)), {}),
        ("unresolved", "TE", evidence(coefficients(4, 8),
                                      (coefficients(4, F(8) + F(1, 10**30)),)),
         {"max_depth": 0}),
    )
    rows = []
    for name, expected, value, settings in fixtures:
        observed = classify_terminal(value, **settings)["classification"]
        rows.append({"fixture": name, "expected": expected, "observed": observed,
                     "source_discarded": True, "passed": observed == expected})

    base = fixtures[0][2]
    negatives = []
    changed = json.loads(canonical(base)); changed["coefficients"][0]["dot"] = fraction_record(F(5)); negatives.append(("tampered_coefficients", changed))
    changed = json.loads(canonical(base)); changed["cell"]["left"] = fraction_record(F(3, 5)); negatives.append(("tampered_bounds", changed))
    changed = json.loads(canonical(base)); changed["source_authority"][SOURCE_KEYS[0]] = "0" * 64; negatives.append(("wrong_authority_hash", changed))
    changed = json.loads(canonical(base)); changed.pop("competitors"); negatives.append(("missing_field", changed))
    changed = json.loads(canonical(base)); changed["schema_version"] = 2; negatives.append(("version_mismatch", changed))
    changed = json.loads(canonical(base)); changed["cell"]["left"] = {"numerator": "2", "denominator": "4"}; negatives.append(("noncanonical_fraction", changed))
    changed = json.loads(canonical(base)); changed["competitors"] = []; negatives.append(("missing_competitor", changed))
    for name, value in negatives:
        try:
            classify_terminal(value)
        except (KeyError, TypeError, ValueError):
            observed = "blocked"
        else:
            observed = "accepted"
        rows.append({"fixture": name, "expected": "blocked", "observed": observed,
                     "source_discarded": True, "passed": observed == "blocked"})
    return rows
