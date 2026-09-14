# Session 14al — VerifiedEnvelope diagnostic evidence serialization

**Date:** 2026-09-13

**Execution:** valid, synthetic only

**Classification:** **A — VerifiedEnvelope DIAGNOSTIC SERIALIZATION REPAIRED**

**Readiness:** **1 — READY FOR A FRESH SINGLE-EDGE COMPARATOR DIAGNOSIS**

Session 14al repaired the tooling defect that invalidated Session 14ak. A
representative synthetic object first reproduced the preserved failure:
`VerifiedEnvelope` survived 14ak's generic `plain()` traversal and Python's JSON
encoder rejected it as not serializable. The new internal path uses an explicit
schema for the envelope and every governed nested structural type required by
the complete 14ak-shaped evidence payload.

The repair does not alter or reinterpret Session 14ak. No development geometry,
state, receiver, provider product, R8 partial result, target, model or option
share was opened. Numerical modules and the 14ak script, manifest and emergency
record retain their frozen hashes.

## Projection and evidence boundary

The canonical envelope projection contains its verified switches, certified tie
intervals, maximizing-defender set, canonical partition sequence and grid count.
Switches retain canonical locations, owner blocks, crossing pairs, flags and
envelope value. Tie boundaries retain their outside/inside adjacent floats,
direction, pair and owner set. Certified onsets, certified root transitions and
bounded integral intervals have separate explicit projections because the full
14ak payload also contained those types.

Owner and crossing-pair sets serialize in ascending integer order. Partition
order remains governed sequence order. Finite floats keep their existing Python
float values with no rounding or string conversion. Nonfinite values fail.
Mappings require plain string keys; unordered containers, arbitrary arrays,
unknown objects and arbitrary dataclasses fail rather than being coerced.

Raw solver results remain labelled provenance inside onset or root-transition
diagnostics. They do not become canonical equality merely because their records
are JSON-safe. Semantic envelope equivalence compares the explicit canonical
projection to the source object's governed fields; reconstructing a live Python
object is unnecessary.

Canonical encoding sorts keys, uses compact separators, rejects NaN and adds one
LF. Two complete payload encodings were byte-identical with SHA-256
`049c101f3bfd7f9dc65215f6fd875e1d9c505a6b4fae9ad0d7eae138439da549`.
The same bytes passed create-once private evidence writing and manifest closure.

## Failure controls and invariance

Eight negative controls covered an unknown object, an unordered set, three
nonfinite values, an unsupported NumPy array, a non-string mapping key and a
duplicate owner set. Every control was rejected. A later unsupported object in
an otherwise valid payload still preserved the primary exception and traceback
through the independent emergency writer, and no false success manifest was
created.

Hash checks confirmed that field evaluation, envelope detection, owner
certification, canonical partitions, bounded-residual integration, production
verification and representation-retry modules did not change. The historical
14ak runner, invalid manifest and emergency record also remained byte-identical.
No field or integration function ran during the governed audit.

## Twenty-nine-item handoff

1. Starting HEAD: `05070c7dde5114840e4f4678a5db20cf395cbbb6`.
2. Ending HEAD: reported after the closure commit.
3. Protocol: [Phase 14al](protocols/phase_14al_verified_envelope_serialization.md), commit `5d63e4788776a1422601c95d06521b79a0ba0c9c`, SHA-256 `2f60cdf4a2dc7bd2f7427a10ba6cb08cbd5c2a68f07cce13742389875b3efa12`.
4. Historical defect: 14ak's `plain()` left a `VerifiedEnvelope` instance in the private payload, causing `TypeError` during JSON serialization.
5. Pre-repair reproduction: passed synthetically with the same class and root error category; no historical empirical object was used.
6. Envelope field inventory: switches, tie intervals, maximizing defenders, partitions and grid intervals are canonical diagnostic authority; raw solver values are provenance; derived counts are retained only where required; empirical values are outside 14al.
7. Canonical schema: version 1, type `verified_envelope`, explicit governed fields and JSON primitives only.
8. Nested inventory: `VerifiedSwitch`, `CertifiedTieInterval`, `CertifiedBoundary`, `CertifiedOnset`, `CertifiedRootTransition` and `IntegralInterval` have explicit projections; see [inventory](../outputs/session14_verified_envelope_serialization/nested_type_inventory.csv).
9. Owner ordering: semantic sets become ascending unique integer lists; crossing pairs are internally and externally sorted.
10. Float handling: preserve finite values without rounding or stringification; reject NaN and infinities.
11. Raw/canonical distinction: raw root/onset solver values remain diagnostic provenance and are excluded from canonical structural equality.
12. Standalone result: envelope projection and semantic comparison passed.
13. Full payload regression: the complete 14ak-shaped nesting serialized, including the original embedded-envelope location.
14. Deterministic bytes: repeated complete payload serialization was byte-identical.
15. Manifest/hash closure: passed; every public output and the private synthetic payload are hash-bound.
16. Unsupported-object controls: object, set, array, non-string-key mapping and malformed owner set all failed closed.
17. Nonfinite controls: NaN, positive infinity and negative infinity all failed closed.
18. Emergency regression: primary exception and traceback preserved, emergency record written and success manifest absent.
19. Numerical invariance: all ten frozen implementation/historical artifact hashes matched; no numerical path executed.
20. Classification: **A — VerifiedEnvelope DIAGNOSTIC SERIALIZATION REPAIRED**.
21. Readiness: **1 — READY FOR A FRESH SINGLE-EDGE COMPARATOR DIAGNOSIS**.
22. Empirical access: none; the audit was entirely synthetic.
23. Historical preservation: Session 14R8 and Session 14ak scientific values and artifacts were untouched.
24. Tests: focused, relevant and full-suite totals are reported at final delivery.
25. Python 3.11 CI: reported after the closure push.
26. Python 3.13 CI: reported after the closure push.
27. Distribution CI: reported after the closure push.
28. Commits and synchronization: reported at final delivery.
29. Recommendation: separately govern a fresh single-edge comparator diagnosis on retained Session 14R8 authority, state ordinal 4, receiver ordinal 7, candidate `constant_width`, using the repaired diagnostic evidence serialization path.

The claim ledger, package, field mathematics, numerical contracts and release
remain unchanged. The recommendation is not executed in Session 14al.
