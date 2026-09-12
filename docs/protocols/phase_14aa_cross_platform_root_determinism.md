# Phase 14aa — Cross-platform root determinism

Status: **FROZEN BEFORE IMPLEMENTATION OR NEW NUMERICAL PROBES**
Date: 2026-09-11

Session 14aa begins from synchronized `79f327072bce3381e79e2ff68b9d2e35d7ad0112`; the annotated `v0.1.0` tag remains peeled to `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. All Session 14 through 14z protocols, implementations, outputs, failures and classifications remain historical authority.

## Question and boundary

This synthetic-only phase asks whether certified structural boundaries can make the production verification path deterministic across supported platforms. It may repair only the representation and consumption of analytical directional onsets and numerically solved maximum-envelope switches.

Field formulas, parameters, ownership semantics, the uniform joint-Simpson calculation, convergence and reference tolerances, dependencies, lockfile, released API, package version and scientific claims are frozen. No empirical population, provider product, target, outcome, model, option share, protected or withheld material, pose, xT, progression data, or Session 14R partial scientific output may be accessed.

## Frozen divergent-coordinate authority

The inputs are the authenticated Session 14z local diagnostic (SHA-256 `3faa15e81e4f1913ed28fd45bca4628b209ca66945da47e9a6d2c20117057f70`) and Python 3.13 CI diagnostic (SHA-256 `36a7026122d41bcce24c0d4e14edae2350d56ccdad581246a99170f126664bd8`). The comparison contains 108 fixture/candidate vectors and 366 ordered components. Ownership, tie topology, micro-interval routing, residual bounds and accepted Simpson resolutions agree.

Exactly seven vectors have different structural coordinates:

- `star_edge_1`, `star_edge_2` and `star_edge_3`, each for `expanding` and `constant_width`, contain directional onsets `0.8999999999999998` (`3feccccccccccccb`) and `0.9447213595499956` (`3fee3b2849e33249`) locally, versus `0.9` (`3feccccccccccccd`) and `0.9447213595499958` (`3fee3b2849e3324b`) in CI.
- `star_edge_4/isotropic` contains a switch at `0.14285714285714282` (`3fc2492492492491`) locally versus `0.14285714285714285` (`3fc2492492492492`) in CI. The owner transition is `[0] → [0,3] → [3]` on both platforms.

Current source inspection establishes the testable mechanism. `directional_breakpoints()` uses scalar `math.hypot` for origin-defender length but NumPy array arithmetic and `np.dot` for the remaining onset calculation. Six vectors inherit two-ULP onset differences from that path. The seventh inherits a one-ULP raw result from SciPy `brentq`. Sorting, partition construction and width subtraction propagate these coordinates without originating them. These findings are frozen hypotheses until the governed comparison closes.

The local environment is macOS 26.6.2 arm64, CPython 3.13.15, NumPy 2.5.3, SciPy 1.18.1 and Accelerate. The CI environment is Linux x86_64, CPython 3.13.15, NumPy 2.5.3, SciPy 1.18.1 and SciPy OpenBLAS 0.3.34.106.0. Both use lock hash `c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c`.

## Deterministic structural-boundary contract

A new internal, unreleased module will produce repaired boundary records. Historical modules and outputs remain byte-identical. The Session 14aa diagnostic adapter alone consumes these records.

### Envelope switches

Each switch record contains the raw solver result, last pre-switch float, any exact-zero interval, first post-switch float, owners before/at/after, and crossing defender pairs. Beginning with the inherited Brent bracket and result, the verifier searches with `numpy.nextafter` and bisects ordered finite-float indices to certify the transition.

Certification requires:

- the inherited pre/at/post maximal-owner semantics;
- the raw ordering of every crossing pair before and after the transition;
- any representable floats between the strict-order regions to be exact equality values;
- unchanged residual, grouping and `1e-12` deduplication gates; and
- identical mapped records under every defender permutation.

The canonical switch coordinate is the first representable float on the post-switch branch as `t` increases. It is never an average or an incidental Brent return bit. Ambiguous certification fails closed.

### Directional onsets

For origin `b`, receiver `q`, defender `d`, and the unchanged directional coordinate `ell`, compute coordinate differences as Python float64 scalars. Use `math.hypot` and `math.fsum` in a fixed order to evaluate the algebraically equivalent `ell=0` and `ell=1` onset equations. Certify each branch transition in float space and retain the first representable float on the post-onset branch. This changes neither the directional formula nor its mathematical breakpoint.

### Partition records

Preserve certified tie-enclosure endpoints exactly. Sort records by canonical float bits and tagged precedence: domain endpoint, certified onset, certified switch, certified tie endpoint. Apply the inherited `1e-12` deduplication rule to ordinary coincident records but never collapse adjacent certified tie endpoints. Feed the resulting coordinates into independent maximum partition and routing verification. Uniform joint-Simpson grids and component estimates remain unchanged.

## Prospective implementation and tests

Freeze synthetic oracles for exactly representable and between-float roots, shallow and steep crossings, onset- and endpoint-adjacent roots, multiple roots, equality plateaus and the two observed one-ULP Brent seeds. Both observed seeds must produce one certified enclosure and canonical coordinate locally. Tests must cover raw pair ordering, exact-zero intervals, ambiguous transitions, mapped owners, tie preservation, tagged ordering and fail-closed behavior.

Before governed execution, regress all 108 vectors, 366 references and 399 mapped permutations. Require unchanged owners, tie topology, micro-interval routing, residual bounds, accepted resolution and existing numerical agreement. Joint-Simpson accepted component values and interval choices must equal the unchanged implementation on the same platform.

The isolated runner exposes `preflight`, `local-diagnostic`, `compare` and `publication-check`. It has no empirical, acquisition, model, scoring or Session 14R route. The implementation is committed before the single governed local diagnostic.

## Governed cross-platform execution

After local success, push the tested checkpoint and dispatch exactly one Python 3.13 workflow. It uses the pinned checkout, Python and uv actions and Session 14z's authenticated file-artifact transport.

- Artifact: `session14aa-python313-root-diagnostic`.
- File: `session14aa_ci_diagnostic.json`.
- Transport: one dispatch, one retrieval, exact declared/downloaded SHA-256 verification, no log/base64 fallback.

Compare canonical partitions and enclosures, owner records, tie topology, routing, residuals, accepted resolutions, every ladder component and float bit pattern. Record absolute, relative and ULP differences plus sanitized environments. Structural equality and numerical equality are assessed separately under the existing `1e-7` convergence and `1e-6` reference gates. No component-equality repair or new tolerance is introduced.

Any ambiguity, changed routing, changed accepted resolution, material numerical movement, governed-workflow failure, artifact-integrity failure or unexpected post-exposure defect closes the phase without repair, redispatch or rerun.

## Outputs and decision

Publish exactly these files in `outputs/cross_platform_root_determinism/`:

- `divergent_root_authority.json`
- `canonicalization_oracles.csv`
- `local_diagnostic.json`
- `ci_diagnostic.json`
- `partition_comparison.csv`
- `vector_comparison.csv`
- `environment_comparison.json`
- `qc.json`
- `manifest.json`

Dense traces and execution records remain ignored. The manifest binds this protocol, implementation, environment, historical authorities, workflow run, artifact identity and every closed output hash.

Choose exactly one result:

- **A — CANONICAL PARTITIONS AND FINAL VECTORS BITWISE IDENTICAL**.
- **B — STRUCTURAL PATH IDENTICAL; FINAL MACHINE-SCALE DRIFT WITHIN EXISTING AUTHORITY**.
- **C — BENIGN DRIFT CANNOT BE CANONICALIZED WITHOUT AN ARBITRARY RULE**.
- **D — ENVIRONMENT DIFFERENCES STILL ALTER STRUCTURAL BEHAVIOR**.
- **E — CANONICALIZATION MATERIALLY CHANGES NUMERICAL RESULTS**.
- **F — MULTIPLE ISSUES**.
- **G — EVIDENCE UNRESOLVED**.
- **H — EXECUTION OR INTEGRITY FAILURE**.

Readiness is 1 only when the complete cross-platform production contract passes. Readiness 2 applies when the structural path is exact and only a separately governed final-float equivalence contract remains. Other outcomes receive readiness 3 or 4 according to the demonstrated blocker.

## Closure

Preserve three commits: protocol; tested implementation; closed evidence/report and one append-only research-log entry. Run focused Session 14aa tests, relevant Session 14 tests, the full active suite, compilation, 108/366/399 regressions, schema/hash and privacy checks, documentation links, history preservation, staged review, `git diff --check`, governed CI and ordinary CI. Report tests run, passed and skipped separately.

If A/readiness 1 is earned, recommend exactly: **separately govern a fresh Session 14R empirical representation retry**. If B/readiness 2 is earned, recommend one bounded final-float equivalence-contract repair. Execute neither recommendation.
