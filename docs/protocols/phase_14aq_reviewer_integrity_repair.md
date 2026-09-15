# Phase 14aq — Reviewer-integrity repair and retained-evidence revalidation

Date: 2026-09-14. Planning: OFF; Turbo: ON; Model: Sol Light.
Starting authority: `2f3d9d4099a4c057d68c20a3231cc8a5e64c4d97`.
Local, tracking and live GitHub heads were clean and synchronized before mutation.
Preserve annotated `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question and boundary

Repair only Session 14ap's reviewer/output-generation defect and establish an
independent publication validator. Revalidate the unchanged Session 14ao
retained evidence once in a new namespace, then classify what that evidence
supports. Session 14ap remains **G — INVALID / readiness 4** and its code,
outputs, report and manifest remain historical evidence.

This phase performs no field evaluation, numerical integration, quadrature,
geometry reconstruction, empirical access, scientific-summary inspection,
tolerance change or verifier change. The reviewer and validator use only the
allowlisted Session 14ao retained reference, onset, level, comparison and piece
records already authorized by Phase 14ap, plus the locked SciPy source text for
documentary warning semantics. No missing numerical value may be regenerated.

## Historical defect

In
`src/defensive_network_disruption/validation/terminal_error_review.py`, function
`review_records`, the validation loop at the start of the function iterates as
`for index, (level, pieces, tolerance) in ...`. A later public-row loop omits
`tolerance` from its `zip` but serializes the still-bound ambient variable as
`"tolerance": tolerance`. The stale value is the final frozen request,
`2e-15`; therefore all six rows in Session 14ap's `level_summary.csv` contain
`2e-15`. The intended source is each retained level record's validated
`level["tolerance"]`, corresponding to `1e-13`, `5e-14`, `2e-14`, `1e-14`,
`5e-15`, and `2e-15`.

Static inspection establishes six affected tolerance cells. No broader output
corruption is presumed. Session 14ap's publication checker called the same
`review_records` and `public_package` row-construction path, so it independently
verified hashes but reproduced the same semantic defect.

## Retained authority

Bind the unchanged Phase 14ap allowlist and verify every file before decoding:

- Session 14ao manifest SHA-256
  `367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3`;
- Session 14ao private-index SHA-256
  `23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955`;
- exact 68-record selection-mapping SHA-256
  `66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a`;
- locked SciPy 1.18.1 `_quadpack_py.py` SHA-256
  `c59e4133f23ef272e488204c217caf36a38b5921fe0ffeeb2a8f1b804f5ba0d9`;
- lock SHA-256
  `c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c`;
- Session 14ap manifest SHA-256
  `a3462a0ad83397d268bdf1e3e82d224bf0e95585ac4b222a9c34b8333b8aa99a`.

The review requires five completed levels, the sixth warning level, six
comparison records and 54 piece records. Exact estimates, errors, coordinates,
widths, callback traces and warning-piece values remain private and hash-bound.
The retained geometry record, other Session 14 records and scientific products
are prohibited.

## Repaired reviewer contract

The new reviewer accepts one validated retained level record at a time. It
passes that record's own `tolerance` explicitly into its public row. It must not
use ambient iteration state, global mutable state or assumed reconstruction.
The explicit flow is:

`validated retained level record -> reviewer row -> serialized public row`.

For every level the retained private record contains the level index, requested
tolerance, estimate availability and aggregate kind, reported error,
evaluation/terminal-interval/subdivision counts, warning and termination state,
adjacent estimate/error changes, and all trace-identity layers. Public rows
retain Phase 14ap's privacy boundary: exact estimates, reported errors and
differences are represented by availability, equality, behavior and gate flags,
with exact quantities stored only under ignored `local/` evidence.

The warning-level historical aggregate remains unavailable. A reviewer-derived
`math.fsum` is permitted only when all returned piece estimates are retained and
must remain distinctly labeled. This is standard-library arithmetic over
retained values, not numerical function evaluation.

## Independent publication validator

Implement the validator in a separate module. It must not import or call the
reviewer's row-construction or public-package helpers. Shared code is limited to
immutable schema names, frozen level identifiers/tolerances, canonical JSON,
strict file parsing and hashing; none derives row values.

The validator independently maps each allowlisted raw level, comparison and
piece record to expected public fields using the frozen protocol. It compares
the persisted rows and JSON documents directly, verifies exact level order and
cardinality, recomputes the private-index and manifest hashes, and rejects any
missing, duplicated, shifted or fabricated evidence. It must identify the exact
rows and fields that fail.

Mandatory negative controls include the historical all-`2e-15` defect, one
swapped tolerance, one duplicated tolerance, one missing level, shifted level
numbers, warning attached to the wrong row, a stale estimate-derived flag, a
wrong error-derived field and a malformed unavailable marker. Each corruption
must fail independent validation and cannot produce an accepted classification.

## Evidence reduction and decisions

After independent validation succeeds, re-evaluate the retained evidence rather
than importing Session 14ap's provisional conclusion. Keep separate:

1. stability of returned estimates;
2. behavior of reported errors relative to each corrected request;
3. satisfaction of the existing reference/agreement and warning-free contract.

Trace identity requires direct ordered equality of callback nodes and values,
per-piece trace hashes, ordered piece-hash sequences, terminal arrays,
subdivision topology and level trace hashes. Map the retained warning to the
locked SciPy source. Its wording establishes the integrator's reported
condition, not the true numerical error.

Classify in this order: **G** for integrity/execution failure; **E** for two
independent numerical mechanisms; **D** for retained estimate drift beyond
`1e-10`; **C** for a retained roundoff/subdivision limitation identified by
termination metadata and locked-source semantics; **B** for stable estimates
with an unsatisfied terminal-error or agreement condition and no more specific
mechanism; **A** only when independent retained authority establishes accuracy
within the existing gate and certification alone remains; **F** when evidence
is insufficient.

Readiness is: A -> 1; B/C -> 2 unless method revision is independently required,
then 3; D/E -> 3; G -> 4; F -> 2 only if one bounded evidence item resolves the
main ambiguity, otherwise 4.

When evidence is incomplete, name exactly the first missing item in this order:
warning-level returned component; initialized warning-level local-error vector
or termination metadata; one independently bounded reference for the sanitized
warning-producing terminal interval; one unchanged-method next-level record
that demonstrably performs additional work.

## Execution, outputs and closure

Use a standard-library-only internal reviewer, an independent validator and a
runner exposing `preflight`, `review` and `publication-check`. Guard imports and
routes against NumPy/SciPy numerical modules, geometry, field, integration,
production and empirical loaders. Use a create-once marker, atomic writes and an
independent failure record.

Execute one retained-evidence revalidation after the protocol and tested-tooling
commits. Read retained evidence once, generate the repaired package, validate it
independently, hash-close it, and only then classify. An unexpected failure after
exposure is preserved without repair or rerun.

Create exactly these public files under
`outputs/continuous_occlusion_terminal_error_revalidation/`:

- `level_summary.csv`
- `terminal_subdivision_summary.json`
- `error_contribution_summary.csv`
- `warning_semantics.json`
- `missing_evidence.json`
- `publication_validation.json`
- `qc.json`
- `manifest.json`

Exact retained and derived values remain in ignored `local/` evidence with a
hash-bound private index. Public outputs contain counts, flags, sanitized
ordinals, hashes and classifications only.

Before execution, test the repaired source flow, missing retained fields,
reviewer/validator separation, every corruption oracle, deterministic bytes,
scope guards, marker collision and failure closure. Then run focused, relevant
and full tests, compilation, schema/hash validation, privacy checks, links,
historical preservation, staged inspection and `git diff --check`.

Preserve exactly three commits: frozen protocol; tested tooling; closed evidence,
report and append-only research-log entry. Push, require green Python 3.11,
Python 3.13 and distribution CI, verify synchronized heads and the unchanged
release tag, recommend exactly one bounded next action, and stop.
