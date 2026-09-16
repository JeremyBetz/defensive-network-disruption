# Phase 14R9F — CI-portable retained-authority fixtures

Frozen 2026-09-16 from clean synchronized
`0482ce1a20c038f2174bf88223b8b50ff7831e55`. Preserve Session 14R9E as
**D — blocked / readiness 4**, annotated `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`, and all historical evidence.

## Question and boundary

Determine the minimum CI-portable, privacy-safe authority needed by the three
R9E tests that passed locally but failed in clean Python 3.11 and 3.13 GitHub
checkouts. This phase may inspect the already-authorized ignored records only to
derive allowlisted hashes. It opens no new geometry, executes no R9E empirical
runner, and changes no certificate, field, tolerance, numerical, claim, API, or
dependency contract. Empirical access remains zero states and zero edges.

## Frozen failure inventory

The exact failing tests are
`test_runtime_request_is_derived_from_exact_geometry`,
`test_exact_warning_uses_registered_certificate`, and
`test_unmatched_warning_blocks` in `tests/test_session14r9e.py`. The first two
failed first on ignored Session 14am
`local/000010_selected_geometry.json`; the third failed on ignored Session 14ao
`local/000121_piece.json`. Static tracing also establishes the first two have a
latent ignored dependency on Session 14am `local/000020_structure.json` after
geometry loading succeeds.

The runtime-request test checks empirical provenance plus exact request matching.
The exact-warning test checks certificate orchestration at the adaptive-result
boundary. The unmatched-warning test checks fail-closed warning handling. Local
availability resulted from retained ignored files; clean GitHub checkouts obey
`/outputs/*` and contain only explicitly forced public artifacts.

## Portable proof contract

Use a decomposed proof. Empirical identity is established only from committed
Session 14ar public artifacts and exact hashes. Geometry-to-fingerprint and
mutation behavior use an explicitly synthetic identity. Synthetic values may
not carry Session 14ar identifiers. Together the two layers establish the same
production composition without tracking reconstructive values.

Reuse Session 14ar `interval_authority.json`, `retained_comparison.json`, its
manifest, and the registered certificate for selected-geometry, retained-piece,
onset, full-structure, warning, request, method, provenance, and tolerance
authority. Create one hash-only fixture for the semantic structural projection
that R9E historically compared: ordered partitions; the five ordered onset
fields `defender_index`, `branch`, `last_pre_branch`, `first_post_branch`, and
`raw_scalar_result`; and the eight ordered switch fields `last_pre_switch`,
`exact_zero_start`, `exact_zero_end`, `first_post_switch`, `owners_before`,
`owners_at`, `owners_after`, and `crossing_pairs`.

The fixture schema is exact: `schema_version`, `authority_id`, `source_session`,
`source_manifest_sha256`, `source_artifact_sha256`,
`selected_geometry_authority_hash`, `semantic_projection_sha256`,
`field_selection_specification_sha256`, `purpose`, `derivation_statement`, and
`non_reconstructive_statement`. It contains hashes and prose only: no geometry,
coordinates, normalized boundaries, roots, owner ordinals, event keys,
identities, warning traces, estimates, or scientific summaries.

One deterministic derivation route may read the ignored structure locally and
emit only the allowlisted fixture. An independent validator declares its own
schema, expected committed source hashes, prohibited names, and canonical-byte
rules. It rejects additions, stale or altered authority, noncanonical bytes,
private fallback paths, and non-hash selected values.

## Repair and acceptance

Runtime selected geometry continues to be canonically hashed and matched to the
committed empirical hash. Runtime partitions/onsets/switches are projected and
matched to the portable semantic hash. The resulting request retains Session
14ar's original full structural-authority hash. Remove runtime and test reads of
the ignored structure and warning record. Factor warning resolution at the same
boundary used by `_piece`; preserve warning identity, containment, registry
lookup, and every blocking branch.

The three named tests retain their properties through the decomposed proof.
Clean-checkout validation must make all ignored records unavailable and pass
using tracked content only. Test fixture schema, source binding, allowlist,
determinism, tampering, missing fixture, private fallback, empirical hash
authority, synthetic derivation and mutation, exact warning orchestration, and
unmatched-warning blocking. Run focused R9F, the three historical tests,
relevant R9E tests, the full suite, compilation, privacy, schemas/hashes, links,
history, staged inspection, diff checks, and Python 3.11, Python 3.13, and
distribution CI.

Create exactly eight public artifacts in
`outputs/continuous_occlusion_ci_portability/`: `failing_test_inventory.json`,
`fixture_dependency_map.json`, `minimum_field_analysis.json`,
`privacy_review.json`, `portable_authority_contract.json`,
`clean_checkout_validation.json`, `qc.json`, and `manifest.json`.

Classify A for existing authority alone, B for one valid minimal sanitized
fixture, C for wiring-only synthetic fixtures with separately preserved
provenance, D for a required private/reconstructive authority, E for multiple
fixture modes, F unresolved, or G invalid. Readiness 1 requires the decomposed
proof, clean-checkout success, all three repaired tests, and all required CI.
Unexpected post-exposure failure is preserved without repair or rerun.

Preserve three commits: protocol; tested repair; closed evidence/report/log.
If B/readiness 1 is earned, recommend only a separately governed fresh R9E
empirical execution using the CI-portable tests and existing numerical and
publication authority. Do not execute it.
