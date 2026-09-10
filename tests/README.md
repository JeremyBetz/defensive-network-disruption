# Test scope

Run the active suite from the repository root:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

The suite covers package/import firewalls, data and identity contracts, timing,
coordinates, finite-segment geometry, conditional-choice fitting, ranking and tie
rules, attenuation, Git/LFS transport integrity, execution-state gates,
publication checks, and synthetic session lifecycles. Tests use synthetic
fixtures and do not download or require competition data.

Three original scaffold placeholder tests remain deliberately skipped for their
initial coordinate, line/segment, and generic-network contracts. Their presence
does not negate the later session-specific production tests, and neither passed
nor skipped software tests are scientific validation.

Add a test only after its interface and expected behavior are specified. Use
clearly synthetic geometry for numerical cases; do not copy real match rows into
the repository. Protocol-specific tests preserve historical behavior and should
not be rewritten merely because a later authority took a different path.
