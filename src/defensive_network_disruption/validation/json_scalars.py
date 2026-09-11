"""Internal deterministic JSON-boundary normalization for numerical scalars."""
from __future__ import annotations

import math

import numpy as np


def json_native(value):
    """Return nested JSON-compatible values without stringifying numerics."""
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite_json_scalar")
        return value
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("json_object_keys_must_be_strings")
        return {key: json_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(item) for item in value]
    raise TypeError("unsupported_json_value")
