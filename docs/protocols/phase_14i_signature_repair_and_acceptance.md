# Phase 14i — mapped_signature ordering repair and synthetic production-wiring acceptance

Status: **FROZEN BEFORE IMPLEMENTATION AND GOVERNED SYNTHETIC EXECUTION**
Date: 2026-09-11

## Authority and question

This synthetic-only phase begins from the later clean synchronized repository
authority `79fade89cf28d09a981d1953680c49b4fcfeccf1`. The handoff's expected
`1e5d5ef2b111ba37b4972ec6566bd7e5851c51d8` is its immediate ancestor before
the completed public-repository audit and is not used as a rollback point.
Annotated `v0.1.0` must remain at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

Session 14h prospectively localized Session 14g's exact failure to the
`sorted(...)` call in `mapped_signature()`: mapped tie records contain `None`
for an endpoint boundary and a tuple for a certified interior boundary. Python
cannot order those values. The question is whether a minimal canonical ordering
repair removes that container defect without changing numerical behavior and
allows the unchanged production-verification path to satisfy its complete
synthetic acceptance contract.

Session 14g remains **INVALID** and Session 14h remains **LOCALIZED — EXACT
TYPEERROR SOURCE ESTABLISHED**. This phase does not amend either result.

## Scope and prohibited access

Permitted inputs are committed Session 14-series code, synthetic fixtures,
synthetic references and aggregate authorities. No development population,
provider product, target, M0/M1/M2 model, option share, reserved or withheld
record, pose, xT or progression record may be opened. Session 14R, empirical
field analysis and behavioral validation remain unauthorized.

Field formulas, candidate definitions, switch/tie detection, integration
algorithms, reference values, tolerances, dependencies, released APIs and
package version are frozen. Historical files and outputs remain byte-identical
except for the append-only research-log addition at closure.

## Canonical signature ordering

`mapped_signature()` continues to return the same switch and tie record shapes.
It must not replace returned `None`, stringify values or alter tie records.
Sorting alone uses an internal canonical tagged key:

```text
(boundary_kind, boundary_payload)
```

Every key has a comparable integer tag and tuple payload. The frozen boundary
tags are:

1. left domain endpoint;
2. certified numeric boundary;
3. right domain endpoint.

A missing start boundary means the tie interval begins at the left domain
endpoint. A missing end boundary means it ends at the right domain endpoint.
These two meanings are derived from the record field, remain distinct in the
sort key and continue to be represented by `None` in the returned signature.
There is no other supported absent/non-applicable boundary form.

Certified boundary payload ordering uses the existing mapped values in this
order: outside float, inside float, direction string, mapped pair and mapped
owner set. Tie records then order by normalized start key, normalized end key,
mapped owners and mapped pairs. Every nested owner and pair ordinal is mapped
through the supplied inverse permutation and sorted numerically. This defines a
total deterministic order independent of input record order and original
defender ordinal while preserving every equivalence field.

## Minimal implementation and regression gate

The implementation may add only a small private boundary-order helper, the
explicit `mapped_signature()` sort key, directly necessary annotations or
docstrings, a separate Session 14i runner and new discoverable Session 14i tests.
No switching, tie certification, integration, readiness, field or tolerance code
may change.

Before governed execution, tests must establish:

- the unchanged `multiway_plateau` completes signature construction and retains
  all endpoint, interior and multiway tie information;
- the historical implementation reconstructed in a test fails on that fixture
  with the same heterogeneous-comparison `TypeError`;
- left endpoint, right endpoint, both endpoints, endpoint tie interval, isolated
  point tie, multiway plateau and multiple distinct tie-interval signatures have
  deterministic total ordering;
- every required permutation, including all `multiway_plateau` defender
  permutations, maps to the identical canonical signature without identity
  tie-breaking;
- field values, roots, certified enclosures, partitions, union/maximum values,
  controlled Simpson vectors and reference values are unchanged from committed
  authority wherever those quantities apply;
- relevant Session 14g/14h tests, compilation and `git diff --check` pass.

Any numerical difference stops the phase before governed acceptance.

## Inherited production acceptance

The production route remains:

```text
synthetic state → field evaluation → switch detection → certified enclosure
validation → partition construction → independent maximum verification →
unchanged joint Simpson vector → reference verification → actual failure
propagation → immutable machine readiness → runner decision
```

Joint Simpson retains uniform interval counts 256, 512, 1024, 2048, 4096, 8192
and 16384. It accepts the first finer vector only when every governed component
changes by at most `1e-7`. Certified partitions do not change joint sampling.
Independent maximum verification retains the approved piecewise/adaptive/direct
checks and their existing tolerances. An uncertified partition, failed root,
reference disagreement, warning or switching inconsistency fails closed.

Exactly one governed run is permitted after the protocol and tested repair are
committed. It must claim an exclusive ignored marker before calculation and must
complete 108/108 frozen maximum cases, 366/366 component references, 399/399
required permutation comparisons and the actual upstream failure-enforcement
suite. Negative paths include continuity/oracle failure, detector/root failure,
uncertified tie partition, missing reference, controlled-integration failure,
warning, permutation mismatch, nondeterminism, integrity failure and marker
collision. Every failure must prevent accepted output and readiness.

The immutable `VerificationReadiness.ready` conjunction is the sole readiness
authority. No report or caller can override it. A valid control reaches true only
after every observed obligation succeeds through the wired route.

## Outputs, failure and decisions

The runner exposes only `preflight`, `audit` and `publication-check`. It writes
the following new public package under
`outputs/continuous_occlusion_production_acceptance/`:

- `repair_summary.json`
- `engineering_checks.csv`
- `reference_comparison.csv`
- `permutation_summary.csv`
- `failure_injection.json`
- `readiness.json`
- `qc.json`
- `manifest.json`

Dense traces, full tracebacks, access records and execution markers remain
ignored. Output schemas are strict, JSON values finite, CSVs LF-terminated and
all public files aggregate and synthetic. The manifest binds protocol,
implementation, environment, historical inputs and output hashes without
recursion.

If an unexpected failure occurs after governed execution begins, preserve the
active fixture, stage/substage, bounded type/shape summary, exception, traceback,
completed checks and marker state; publish a valid failure package; stop without
repair or rerun.

Classification is exactly one of:

- **PASS — PRODUCTION VERIFICATION WIRING ACCEPTED; SESSION 14R MAY RESUME** only
  when the repair and numerical-identity gates pass, all 108 cases, 366
  references and 399 permutations pass, actual failure propagation passes,
  readiness is true and execution integrity holds;
- **BLOCKED — ADDITIONAL BOUNDED REPAIR REQUIRED** for another demonstrated
  bounded defect;
- **UNRESOLVED — PRODUCTION ACCEPTANCE NOT ESTABLISHED** when evidence remains
  incomplete;
- **INVALID — EXECUTION OR INTEGRITY FAILURE** when the governed execution
  contract fails.

PASS means only that production verification is ready for a separately governed
Session 14R. It does not validate occlusion, cover shadows, suppression,
interception, attribution or defender value. The claim ledger remains unchanged.

## Validation and closure

Run focused Session 14i tests, relevant Session 14-series tests, the full active
suite, compilation, numerical identity checks, schemas/hashes, publication and
privacy guards, documentation links, append-only history checks, staged review,
`git diff --check` and CI. Preserve three commits: this protocol; tested repair;
closed evidence/report and append-only research-log entry. Push only reviewed
artifacts, verify clean local/tracking/live heads and the unchanged release tag,
then stop.

On PASS, recommend exactly the already completed public-repository audit before
resuming Session 14R; because that audit is now historical authority at the
Session 14i starting commit, the handoff must state that it is already complete
and recommend no automatic Session 14R execution. On any other classification,
recommend one bounded repair or evidence action tied to the failure.
