# Phase 14t — Canonical-to-prepared row equivalence audit

Status: **FROZEN BEFORE ORDINAL-1 INSPECTION**
Date: 2026-09-11

## Authority and question

This representation-only audit begins from clean synchronized commit
`a337e26b9d4f297d626e13c77366dcd81b097d84`. Annotated release `v0.1.0`
must remain at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

Session 14R remains historically **D — BLOCKED**, readiness 3, and Session 14s
remains **G — UNRESOLVED**, readiness 4. This audit asks only why Session 14s'
historical Python dictionary equality rejected canonical prepared row ordinal 1.
It neither reproduces the SciPy warning nor evaluates an occlusion field.

The frozen source identities are:

- Session 14R manifest SHA-256
  `8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed`;
- Session 14s manifest SHA-256
  `9bdb96a97e447f834068ca941453d537082a91fcb9653fef1c428ddadc78a61b`;
- canonical development population SHA-256
  `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`;
- preserved Session 14R prepared population SHA-256
  `15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0`.

No empirical row may be opened before this protocol and the tested audit
implementation are separately committed.

## Single authorized record and objects

The only authorized empirical record is zero-based row ordinal 1. The runner
must read exactly one line from each frozen file and stop if either line is not
uniquely available. It freezes three objects:

1. the raw canonical JSON line, accessed through the existing restricted lexical
   projection;
2. the current tuple-bearing in-memory reconstruction returned by the unchanged
   Session 14R projection;
3. the exact preserved Session 14R prepared JSON line and its list-bearing
   `json.loads` result.

The historical Session 14s rule is Python dictionary equality between objects 2
and 3. The audit must reproduce that rule exactly before applying any semantic
comparison. No other row, target, outcome, model, option share, field,
integration, provider product, acquisition route, protected/withheld data, pose,
xT or progression material is authorized.

## Frozen comparison contract

Compare in this order, without normalization or tolerance:

1. independently hash the raw canonical line and preserved prepared line;
2. compare field names, mapping insertion order, missing and optional keys,
   nested container types, sequence lengths and scalar types;
3. record each differing path privately, including tuple/list boundaries,
   sequence order, Python/NumPy scalar type, signed zero and float64 bits;
4. compare every numeric value exactly, reporting absolute difference and
   bit-pattern identity;
5. trace
   `canonical JSON → restricted projection → Python prepared object → sorted JSON
   serialization → preserved bytes → JSON-decoded comparison object`;
6. fingerprint every stage with sanitized SHA-256 values and identify the first
   divergence;
7. evaluate the exact historical serialization expression
   `json.dumps(row, sort_keys=True, allow_nan=False) + "\\n"` against the
   preserved line byte-for-byte;
8. decide representation identity, structural identity, numerical identity and
   semantic equivalence as separate booleans.

Structural identity requires the same mappings, sequence lengths and element
order while allowing tuple/list storage types. Numerical identity requires exact
Python numeric equality, float64 bit identity and signed-zero identity. Semantic
equivalence under the frozen preparation contract requires structural and
numerical identity plus byte-identical historical serialization. It does not
permit sorting sequences, coercing values or applying tolerances.

Compare the locked Python and NumPy versions with Session 14R's recorded
environment. Environment-sensitivity probes use synthetic equivalents only;
installing or changing software is forbidden.

## Implementation, privacy and execution

Add one internal representation comparator, synthetic tests and a separate
runner exposing only `preflight`, `audit` and `publication-check`. The runner
requires committed protocol and implementation hashes, a clean tree, frozen
input hashes, an exclusive ignored marker and an absent prior result. The one
governed audit creates its marker before opening ordinal 1 and refuses an
automatic rerun. An integrity or access failure is preserved and stops the audit.

Exact values, identities, coordinates, full paths, raw lines, nested types, bit
patterns and stage traces remain in ignored local evidence. Public evidence may
contain sanitized field paths, type categories, aggregate counts, equality flags,
maximum numeric difference and hashes only. Public outputs must not permit row
reconstruction.

Before the governed audit, synthetic tests cover identical objects, tuple/list
differences, Python and NumPy floats, signed zero, mapping and sequence order,
one-bit float differences, serialization-only differences, nested structures,
missing fields, marker collision, schemas, deterministic fingerprints and the
absence of prohibited routes.

## Outputs, classification and closure

Publish exactly these files under
`outputs/continuous_occlusion_row_equivalence/`:

- `authority_summary.json`
- `schema_comparison.json`
- `field_comparison.csv`
- `pipeline_stage_fingerprints.csv`
- `environment_comparison.json`
- `qc.json`
- `manifest.json`

Close and hash the evidence before interpretation. Apply this precedence:

- **B — Container/ordering difference** when tuple/list or ordering
  representation alone causes Python inequality while sequence order, numeric
  values, bits and historical serialization bytes agree;
- **A — Serialization/representation-only difference** for storage formatting
  without a container/order mechanism and identical semantic values;
- **C — Numeric precision/representation difference**;
- **D — Genuinely different current prepared values**;
- **E — Preserved authority wrong or bound at the wrong layer**;
- **F — Environment sensitivity**;
- **G — Multiple independent mechanisms**;
- **H — Insufficient evidence**.

Readiness is 1 for equivalence-contract repair when historical bytes remain
reproducible and semantically authoritative; 2 for a preparation implementation
repair; 3 for historical-authority review; and 4 when more evidence is required.

If the expected tuple/list mechanism is confirmed, the sole recommendation is a
separately governed change making Session 14s compare the reconstruction's exact
historical JSON serialization with the preserved line bytes and then use the
verified preserved decoded row for diagnostics. Its regression must show Python
tuple/list inequality with byte-identical historical serialization. No repair is
implemented here.

Preserve three commits: protocol; tested tooling; closed evidence/report plus an
append-only research-log entry. Run focused, relevant and full active tests,
compilation, schema/hash, privacy, links, history, staged and diff checks; push,
wait for CI, and verify synchronized heads and the unchanged release tag.
