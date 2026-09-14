# Phase 14al — VerifiedEnvelope diagnostic evidence serialization

**Frozen:** 2026-09-13  
**Starting authority:** `05070c7dde5114840e4f4678a5db20cf395cbbb6`  
**Scope:** synthetic and tooling-only serialization repair

## Question and retained failure

Session 14al asks whether the private diagnostic-evidence path can serialize a
`VerifiedEnvelope` explicitly, deterministically and fail-closed without changing
any numerical behavior. Session 14ak remains **H — INVALID EXECUTION**, readiness
4 and publication P5. Its sole governed diagnosis opened state ordinal 4,
receiver ordinal 7 and candidate `constant_width`, then failed while writing
private evidence with `TypeError: Object of type VerifiedEnvelope is not JSON
serializable`. No 14ak value is recovered, interpreted or rerun here.

The repair is synthetic only. It may inspect source definitions and construct
new synthetic objects. It may not open any development geometry, provider data,
R8 partial product, target, model, share, protected, reserved or withheld value.
Session 14ak code, outputs and emergency evidence remain byte-identical.

## Canonical projection contract

The new internal projector accepts only these governed structural dataclasses:

- `VerifiedEnvelope`: `switches`, `tie_intervals`, `maximizing_defenders`,
  `partitions`, and `grid_intervals`.
- `VerifiedSwitch`: location, before/at/after owner sets, crossing pairs,
  endpoint and multiway flags, and envelope value.
- `CertifiedTieInterval`: optional start/end certified boundaries, owner set and
  crossing pairs.
- `CertifiedBoundary`: outside/inside float endpoints, direction, pair and
  owner set.

The envelope schema version is `1` and its type tag is `verified_envelope`.
Owner sets and crossing-pair sets are emitted in ascending deterministic order;
their semantic set meaning is preserved. Partitions retain their governed
sequence. Raw solver provenance is outside this canonical envelope projection
and remains a separately labelled diagnostic record if a future caller supplies
it. It does not participate in canonical structural equality.

All output consists only of dictionaries, lists, strings, integers, finite
float64-compatible floats, literal booleans and null. Ordinary finite values are
neither rounded nor stringified. Booleans are not accepted where integers are
required. Nonfinite values, malformed owner sets or crossing pairs, duplicate
owners, invalid directions, missing required fields and unsupported nested
objects fail closed. The projector does not use `str`, `repr`, `__dict__`,
pickle, arbitrary dataclass recursion or unordered-container fallback.

Semantic equivalence requires every canonical diagnostic field to match the
source object exactly after container normalization. Reconstruction of a live
object is not required. The full Session 14ak-shaped private payload must pass
the same explicit recursive evidence projector at the location where the
envelope was embedded. Only approved JSON primitives, mappings with string
keys, sequences, NumPy scalar primitives and the governed structural types are
accepted.

Canonical bytes use sorted keys, compact separators, `allow_nan=False`, UTF-8
and one terminal newline. Repeated projections and serialization must produce
identical bytes and SHA-256 hashes.

## Prospective evidence and failure behavior

Before the repaired path is exercised, a synthetic object with the same nested
class structure must reproduce the historical root failure through the preserved
14ak `plain()` behavior and canonical JSON encoding. The repair must then pass:

1. standalone envelope projection and semantic comparison;
2. every nested structural projection;
3. complete 14ak-shaped payload serialization at the original nesting site;
4. byte-identical repetition and stable SHA-256;
5. 14ak-style atomic private evidence write and manifest/hash closure;
6. negative controls for unsupported objects and containers, malformed owners,
   missing required fields and nonfinite numbers;
7. an emergency-publication regression that preserves the primary exception and
   traceback and emits no success manifest.

The one governed audit is protected by a persistent exclusive marker and cannot
be resumed or rerun. An unexpected failure preserves an independent emergency
record and closes invalid. Public evidence is synthetic, aggregate and free of
local paths or empirical values. Private test traces and execution records remain
ignored.

## Numerical invariance

This phase adds a new internal serialization module and isolated runner only.
It must not modify field evaluation, switch detection, owner certification,
partition construction, quadrature or comparator gates. The following starting
hashes are frozen as invariance authority:

- `occlusion_fields.py`: `d7fd23bc131d0db2686ef27475a128fdca78aea88616c4494609962c165533aa`
- `verification_repair.py`: `417233c6baf694b35d4ce835fe1164ed9730a54df81e2cb8b6deb06911a330cd`
- `root_partition_determinism.py`: `8709706de798277c172d5f4a874856fad1ebb4321caf1f004be9e24ba622f0af`
- `onset_owner_certification.py`: `d62dc611a759b03c68098c7628568d3f9e78fd59d995a4f555dd6ed325171b97`
- `micro_interval_verifier.py`: `55389fd78d7c546bb1b4c830cdb434932fce6f67dcc8042a2427e44dc77c2b0e`
- `production_verification.py`: `6d4eeddf0c7537ecbea027e1c308e4f573b2cf0f4bb71a0b3b839e2382f75a6c`
- `representation_retry.py`: `96dbdfe6030582e69f837a1343fb1e68952ed34992c957f243507bdc5b2c2f99`

The historical 14ak script hash remains
`48eb9ff8c1637cbdcd148f65403614d1314a36302862135c9b088c22ec066f04`;
its manifest remains
`5352fa30bf8e4c0ac67aee8cecb1e5fdbbf2f703e79bca9d2f8c9a01e9c03896`;
and its emergency record remains
`fda86bc1e35557ee313d47ffe1c54a44f7fa9893434dc1732fb43c92926b91c8`.

## Outputs, decisions and closure

The governed audit writes exactly ten public artifacts under
`outputs/session14_verified_envelope_serialization/`: failure reproduction,
schema, nested inventory, deterministic serialization, payload regression,
negative controls, emergency regression, numerical invariance, QC and manifest.
Strict schemas and file hashes are validated without rebinding changed evidence.

Choose exactly one classification: **A** repaired; **B** nested diagnostic types
remain unserializable; **C** schema ambiguous; **D** hash/manifest closure
defective; **E** multiple issues; or **F** invalid/unresolved. Choose readiness
independently from 1 ready for a fresh single-edge diagnosis, 2 ready after one
small repair, 3 publication design needs revision, or 4 more evidence required.

Classification A/readiness 1 requires the reproduced pre-repair failure, explicit
projection, complete payload serialization, deterministic bytes and hashes,
passing negative controls, intact emergency fallback and unchanged numerical
authority. Otherwise stop on the observed blocker. No comparator diagnosis is
authorized. On A/1, recommend exactly the separately governed fresh single-edge
diagnosis specified in the handoff; do not execute it.
