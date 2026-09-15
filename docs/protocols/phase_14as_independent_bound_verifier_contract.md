# Phase 14as — Independent-bound verifier-evidence contract repair

Date: 2026-09-15. Planning: OFF; Turbo: ON; Model: Sol Medium.
Starting authority: `cc20812c87d3d43506cf4a2b0100660fa51b16bf`.
Local, tracking, and live GitHub `main` were clean and synchronized before
mutation. Preserve annotated `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question and boundary

Session 14ar closed **A — independent bound confirms retained interval estimate
within existing authority / readiness 1**. It established a rigorous enclosure
for the retained warning-producing terminal interval 8 without using SciPy,
NumPy integration, adaptive quadrature, or production Simpson. This phase asks
only when such prospectively authorized independent evidence may satisfy the
independent maximum verifier after adaptive quadrature reports roundoff.

This is evidence-contract engineering. It changes no field, estimator,
tolerance, dependency, released API, scientific result, or historical artifact.
Do not run Session 14R, reconstruct empirical geometry, reopen a state or edge,
inspect partial scientific outputs, or access targets, models, shares, outcomes,
provider products, protected data, or withheld evidence. The governed acceptance
must report zero empirical states and edges opened.

## Eligible warning and authority

The sole eligible adaptive status is SciPy `IntegrationWarning` with the exact
committed message:

> The occurrence of roundoff error is detected, which prevents the requested
> tolerance from being achieved. The error may be underestimated.

Its UTF-8 SHA-256 is
`3f2b9b58ff1c98b7c27fff799d18b42a6dd19e50c2b5f6b60a0b80bfb2798ab3`.
Both class and message hash must match. The warning remains a warning in all
records. Divergence, nonfinite values, subdivision exhaustion of unknown cause,
invalid integrands, discontinuity, root or partition failure, other warning
messages, other warning classes, and exceptions remain blocking.

Session 14ar is the sole approved certificate authority. Bind its manifest and
public output hashes before accepting its registered evidence. No certificate
is calculated in this phase. No fallback automatically creates a Taylor or
other certificate for a new warning. Future certificates require separate
prospective authority.

## Certificate contract

Add an internal immutable `IndependentIntegralCertificate`, not exported at the
package root, with exactly these semantic fields:

- `schema_version`;
- `authority_id` and `authority_sha256`;
- `source_manifest_sha256`;
- `interval_identity`, `left_endpoint_binary64`, and
  `right_endpoint_binary64`;
- `field_family`, immutable `frozen_parameters`, and `combination`;
- `integrand_specification_hash`;
- `structural_partition_authority_hash`;
- `lower_bound` and `upper_bound`;
- `method_id`, `method_authority_hash`, `independence_statement`, and
  `provenance_hash`;
- `governing_tolerance`.

The registered Session 14ar integrand fingerprint is the canonical SHA-256 of
its sanitized interval identity, endpoint bits, field family and parameters,
combination, structural authority, selected-geometry authority, retained
interval authority, and onset authority. Registration reads only committed
evidence; it does not recompute the certificate or geometry.

A lookup succeeds only when interval identity, endpoint bits, field family,
parameters, combination, integrand fingerprint, structural authority, method,
provenance, and governing tolerance match exactly. Booleans are not accepted as
numeric values. All bounds and adaptive estimates must be finite. Bounds must
be ordered. Similar geometry, approximate endpoints, tolerance matching, or use
on another interval is forbidden. An authority is stale when any bound source
or registered hash differs.

For an eligible warning, retain the warning and adaptive estimate, locate the
exact certificate, require `lower_bound <= adaptive_estimate <= upper_bound`,
and require the realized binary64 width `upper_bound - lower_bound <= 1e-10`.
No epsilon is added. Success returns
`independently_certified_after_roundoff_warning`. Otherwise the interval is
blocking. The adaptive value remains the production point estimate; no bound or
midpoint replaces it.

Width controls use binary64 `1e-10`, its immediate predecessor, and its
immediate successor produced by `math.nextafter`. Equal and below qualify when
all other obligations pass; above fails.

## Piece branches and aggregation

Keep four explicit branches:

1. machine-scale micro-residual pieces retain the existing rigorous residual
   interval;
2. ordinary warning-free adaptive pieces retain their historical point value;
3. the exact eligible warning plus an exact valid certificate retains its point
   estimate and contributes the certificate enclosure;
4. every other warning or failure blocks.

For a complete integral, represent ordinary point contributions as degenerate
closed intervals, preserve micro-residual intervals, and preserve independent
certificate intervals. Sum all lower endpoints and upper endpoints separately
with `math.fsum`, then outward-round the final lower once with
`math.nextafter(..., -math.inf)` and the final upper once with
`math.nextafter(..., math.inf)`. Zero pieces are invalid. Nested aggregation
must not apply a second outward widening. Retain the unchanged production point
estimate as the stable sum of original point estimates, separately from the
verification enclosure.

Machine evidence must report adaptive-warning, independently-certified,
blocking-warning, ordinary-piece, micro-residual-piece, and certificate-piece
counts; aggregate lower and upper bounds; and the final evidence status.

## Prospective readiness

Do not modify historical `VerificationReadiness`. Add an immutable prospective
readiness type whose `ready` property is derived and cannot be supplied. It is
true only when the registry, exact matching, warning policy, conservative
aggregation, ordinary path, micro-residual path, synthetic numerical regression,
108-case count, 366-reference count, 399-permutation count, failure enforcement,
determinism, and integrity checks all pass and the uncertified blocking-warning
count is zero. The object must expose whether independent certification occurred.
No manual override is permitted.

## Regression and controls

The Session 14ar regression reads and hash-checks committed evidence and requires
exactly:

- adaptive estimate `0.21369535129415176`;
- lower bound `0.21369535129402328`;
- upper bound `0.21369535131181636`;
- enclosure width `1.7793072570881918e-11`;
- retained warning class and message hash;
- containment, width acceptance, certificate acceptance, and the frozen success
  status.

It must attest that no numerical calculation or empirical reconstruction route
was invoked. Positive controls cover eligible warning evidence below and at the
width boundary, mixed branch aggregation, outward rounding, deterministic
serialization, and derived readiness. Negative controls cover absent, stale,
mismatched, malformed, reversed, nonfinite, overly wide, or unapproved
certificates; outside estimates; wrong warnings; exceptions; discontinuity;
root and partition failures; and attempted automatic certificate generation.
Every negative control blocks.

Replay the current accepted synthetic authority through the existing onset-aware
production path. Require 108/108 cases, 366/366 references, and 399/399 mapped
permutations, exact canonical structure, component order, accepted resolutions,
and the existing 64-epsilon finite-final-float comparison. Ordinary warning-free
and micro-residual behavior must remain unchanged. No empirical geometry or
invented reference vector enters this regression.

## Execution, outputs, and decisions

Provide an isolated runner with only `preflight`, `accept`, and
`publication-check`, launched through `uv run --locked python`. It validates the
project interpreter, release, committed sources, and retained authority; claims
an exclusive create-once marker; writes atomically; preserves independent
failure evidence; and never regenerates missing evidence during publication
checking.

After the protocol and tested implementation commits, execute exactly one
governed acceptance: load the Session 14ar authority, run its regression, run
positive and negative controls, run 108/366/399, close and hash outputs, and
classify. Any unexpected failure after exposure is preserved without repair or
rerun.

Create exactly these public files under
`outputs/continuous_occlusion_independent_certificate_contract/`:

- `contract.json`;
- `certificate_regression.json`;
- `positive_oracles.csv`;
- `negative_oracles.csv`;
- `synthetic_reference_regression.csv`;
- `readiness.json`;
- `qc.json`;
- `manifest.json`.

Choose exactly one classification: **A — independent-certificate verifier
contract valid**; **B — contract valid but end-to-end wiring still required**;
**C — certificate semantics or aggregation need revision**; **D — independent
certification does not support required authority**; **E — multiple issues**;
or **F — invalid/execution failure**. Choose readiness independently from 1
fresh separately governed Session 14R retry, 2 one bounded wiring check, 3
further verifier revision, or 4 not ready. Do not force A.

Run focused, relevant, and full tests, compilation, 108/366/399 regressions,
schemas and hashes, finite-JSON checks, privacy and publication guards,
documentation links, append-only history checks, staged inspection,
`git diff --check`, and CI. Preserve exactly three commits: this protocol;
tested implementation; closed evidence/report/log. Push and verify synchronized
heads and the release tag.

No claim-ledger change or scientific interpretation is permitted. A/readiness 1
supports exactly this recommendation: **separately govern a fresh Session 14R
empirical representation retry under the repaired independent-certificate
verifier contract.** Do not execute it.
