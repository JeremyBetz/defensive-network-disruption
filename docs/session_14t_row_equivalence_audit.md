# Session 14t — Canonical-to-prepared row equivalence audit

Date: 2026-09-11
Status: **CLOSED — B / readiness 1**

## Decision

**B — Container/ordering difference.** The Session 14s equality gate compared a
tuple-bearing current reconstruction with a list-bearing JSON-decoded preserved
record. Python dictionary equality was therefore false even though the current
reconstruction reproduced the preserved Session 14R prepared line byte for byte.

The mapping insertion order also differed: the current reconstruction retained
construction order, while the preserved line had sorted keys and `json.loads`
retained that serialized order. Dictionary insertion order does not affect
Python dictionary equality, so it was observed representation detail rather than
the cause of the failed equality gate. The nested tuple/list boundaries are the
causal mechanism.

**Repair readiness 1 — equivalence-contract repair only.** The preserved bytes
remain reproducible and semantically authoritative under the frozen preparation
contract. No preparation calculation, numeric value or historical authority
requires repair.

## Evidence

Exactly one empirical row was opened: zero-based canonical and prepared row
ordinal 1, published as neutral state `development_01_state_000002`. No other
row was inspected. Its canonical raw-line SHA-256 is
`c39418f67fd421e7e71a96a54237ab799547364fa7d7346c99f25974002481e5`;
the preserved prepared-line SHA-256 is
`4e896a6174ea54902a9eeeff813951d49fd53299273a3f6b63a30744edd5a52b`.

The comparator found 25 representation differences:

- one mapping insertion-order difference;
- one outer carrier tuple/list boundary;
- one outer receiver collection tuple/list boundary and ten nested receiver
  point tuple/list boundaries;
- one outer defender collection tuple/list boundary and eleven nested defender
  point tuple/list boundaries.

Field names and sequence lengths agreed. There were no missing or optional-key
differences, scalar-type differences, numeric-value differences, signed-zero
differences or float64 bit differences. Maximum numeric absolute difference was
exactly `0.0`. The objects were therefore structurally identical, numerically
identical and semantically equivalent under the frozen contract, while remaining
representation-distinct and unequal under raw Python equality.

The exact historical expression
`json.dumps(row, sort_keys=True, allow_nan=False) + "\n"` produced 410 bytes
whose SHA-256 exactly matched the preserved line. The restricted projection,
historical serialization, preserved bytes and reserialized decoded record all
shared that hash. The first pipeline divergence was the in-memory representation:
tuples produced by the projection became JSON arrays and then Python lists after
decoding.

The current environment exactly matched Session 14R: Python `3.13.15`, NumPy
`2.5.3`, and lockfile SHA-256
`c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c`.
Synthetic equivalents reproduced tuple/list inequality and historical-byte
identity. No environment sensitivity was detected.

## Twenty-nine-item handoff

1. **Starting authority:** clean synchronized
   `a337e26b9d4f297d626e13c77366dcd81b097d84`.
2. **Release authority:** annotated `v0.1.0` remained at
   `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
3. **Historical status:** Session 14R remains D/readiness 3 and Session 14s
   remains G/readiness 4; neither record was rewritten.
4. **Protocol checkpoint:** the Phase 14t protocol was committed before ordinal
   1 was opened.
5. **Implementation checkpoint:** comparator, runner and tests were committed
   before governed execution.
6. **Canonical authority:** SHA-256
   `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
7. **Prepared authority:** SHA-256
   `15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0`.
8. **Session 14R manifest:** SHA-256
   `8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed`.
9. **Session 14s manifest:** SHA-256
   `9bdb96a97e447f834068ca941453d537082a91fcb9653fef1c428ddadc78a61b`.
10. **Authorized scope:** only zero-based row ordinal 1 was read.
11. **Canonical object:** accessed through the unchanged restricted lexical
    projection; labels were skipped before the analytical record existed.
12. **Current reconstruction:** contained mappings, tuples, Python strings and
    Python floats.
13. **Preserved object:** the exact Session 14R line decoded to mappings, lists,
    Python strings and Python floats.
14. **Historical rule:** direct Python dictionary equality returned `false`.
15. **Field names:** identical.
16. **Mapping order:** different because the persisted line used sorted keys;
    this did not cause dictionary inequality.
17. **Missing/optional keys:** none differed.
18. **Nested containers:** 24 tuple/list boundaries differed and caused the raw
    Python inequality.
19. **Sequence order and lengths:** identical.
20. **Scalar types:** identical; no Python/NumPy scalar mismatch occurred.
21. **Numerical values:** exactly identical; maximum absolute difference `0.0`.
22. **Float bits and signed zero:** exactly identical throughout.
23. **Historical bytes:** current reconstruction serialized byte-identically to
    the preserved prepared line.
24. **Representation identity:** false.
25. **Structural, numerical and semantic identity:** all true under their frozen
    definitions.
26. **Environment:** exactly matched the recorded Session 14R Python, NumPy and
    lockfile authorities; synthetic probes found no sensitivity.
27. **Execution boundary:** one empirical row, zero additional rows, zero field
    evaluations, zero integration calls, no models, and no targets or outcomes.
28. **Classification:** B — Container/ordering difference; readiness 1 —
    equivalence-contract repair only.
29. **Publication authority:** the compact output package is closed under
    manifest SHA-256
    `0228ea02567606634c0e6dac3c0004145aa15939e6085c102abe9c07637dc118`.

## Verification and limits

The pre-access synthetic suite covered identical objects, nested tuple/list
differences, Python/NumPy float types, signed zero, mapping and sequence order,
one-bit float changes, serialization-only changes, missing fields, schema
fingerprints, sanitized output paths and the bounded runner surface. Relevant
Session 14R/14s tests also passed before execution. The complete active suite,
compilation, output schemas and hashes, privacy/publication scans, documentation
links, append-only history, staged contents and whitespace checks were reviewed
at closure. Focused Session 14t tests ran 13/13; relevant Session 14R/14s tests
ran 36/36. The full active suite ran 454 tests: 451 passed and three retained
scaffold tests were skipped.

This audit establishes equivalence for the one record implicated by Session 14s.
It does not inspect another row, diagnose the SciPy warning, evaluate a field,
establish general JSON equivalence for arbitrary future schemas, or change any
scientific finding. Coordinates, identities, values, bit traces and exact paths
remain private ignored evidence.

## Sole next action

Separately govern a Session 14s equivalence-contract repair that compares the
current projection's exact historical JSON serialization with the preserved line
bytes, then uses the already verified preserved decoded row for diagnostics. Its
regression must demonstrate Python tuple/list inequality alongside byte-identical
historical serialization. Do not introduce tolerance or sequence-order
normalization.
