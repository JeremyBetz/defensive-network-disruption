"""Session 2 source identity, path firewall, and projected field contracts."""

from __future__ import annotations

from pathlib import Path

SOURCE_COMMIT = "02a396ffd09b283c9f092fdedeff11da6d535b66"
DEVELOPMENT_MATCHES = frozenset({
    "1886347", "1899585", "1925299", "1996435", "2006229",
    "2011166", "2013725", "2015213", "2017461",
})
PRODUCT_SUFFIXES = {
    "metadata": "match.json",
    "tracking": "tracking_extrapolated.jsonl",
    "events": "dynamic_events.csv",
}


def source_path(match_id: str, product: str) -> str:
    """Return a pinned-repository relative path after enforcing the firewall."""
    match_id = str(match_id)
    if match_id not in DEVELOPMENT_MATCHES:
        raise PermissionError(f"match is outside the Session 2 development allowlist: {match_id}")
    try:
        suffix = PRODUCT_SUFFIXES[product]
    except KeyError as exc:
        raise PermissionError(f"product is outside the Session 2 allowlist: {product}") from exc
    return f"data/matches/{match_id}/{match_id}_{suffix}"


def safe_destination(root: Path, match_id: str, product: str) -> Path:
    """Resolve a local destination and reject symlinks or path escapes."""
    relative = source_path(match_id, product)
    root = root.resolve()
    cursor = root
    for part in Path(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PermissionError("symlink destinations are prohibited")
    candidate = cursor.resolve(strict=False)
    if root not in candidate.parents:
        raise PermissionError("destination escapes Session 2 data root")
    return candidate
