# Phase 14ac — Cross-platform final-float equivalence contract review

Status: **FROZEN BEFORE COMPARISON-TEST CHANGES**

Date: 2026-09-11

Session 14ac begins from synchronized `df7dca7b83aaaa3b2fbce965af1a81be5abecd93`; `v0.1.0` remains peeled to `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. Session 14ab remains historically **C — comparator repair reveals a real final-vector difference**, readiness 3. Session 14R remains paused.

## Question and boundaries

This synthetic-only phase asks what cross-platform equivalence property the historical production vector should enforce when canonical algorithmic behavior is identical but final float64 values differ at machine scale. It may change only test-support comparison code and the two historical assertions that currently require exact Python float equality. Field formulas, root canonicalization, partitions, routing, joint Simpson, residual handling, accepted-resolution logic, scientific tolerances, reference values, dependencies, released APIs and production numerical modules remain byte-identical.

No empirical development state, provider product, target, outcome, model, option share, protected/reserved/withheld material, pose, xT, progression material or Session 14R partial output may be accessed.

## Existing authorities

Exact canonical equality remains required for partitions and their float bits, canonical onset and switch records, certified tie enclosures, owner sets, routing, residual bounds, accepted interval count, and component identity/order. Raw Brent values remain diagnostic provenance and are excluded from canonical structural equality under Phase 14ab.

The current historical checks pass a parsed dictionary containing `intervals` and a Python dictionary of parsed float `estimates` into `verify_case()`. `micro_interval_verifier.py` requires integer equality and Python dictionary equality. Four one-ULP final values therefore raise `GateFailure("historical_vector_changed")`; serialized JSON and array tolerances are not involved.

The governed numerical authorities are unchanged:

- controlled Simpson accepts the first finer vector for which every component changes by at most `1e-7`;
- production/reference absolute error must be at most `1e-6`;
- the 366-component closed reference authority currently has maximum observed absolute error `4.1576548232002963e-08`.

Session 14ab froze these divergent records:

| Fixture | Candidate/component | Local | Python 3.13 CI | Absolute drift | ULP |
| --- | --- | ---: | ---: | ---: | ---: |
| `equal_minimum_three` | isotropic/union | `0.4268168846242686` | `0.42681688462426853` | `5.551115123125783e-17` | 1 |
| `star_edge_4` | constant_width/individual_4 | `0.2243752034242107` | `0.22437520342421066` | `2.7755575615628914e-17` | 1 |
| `star_edge_4` | constant_width/union | `0.2243752034242107` | `0.22437520342421066` | `2.7755575615628914e-17` | 1 |
| `star_edge_4` | constant_width/maximum | `0.2243752034242107` | `0.22437520342421066` | `2.7755575615628914e-17` | 1 |

All four retain identical canonical structural metadata and accepted resolutions. The first record uses 512 intervals with reference `0.4268168846593185`; the other three use 1,024 intervals with reference `0.22437517451824526`.

## Candidate contracts and selected rule

Evaluate exact bits, the selected scale-aware float64 rule, the `1e-7` convergence gate and the `1e-6` reference gate. The latter two remain scientific acceptance authorities and comparator candidates only; they are not silently adopted as regression tolerances.

The prospectively selected regression rule is

`abs(actual - expected) <= 64 * epsilon64 * max(1, abs(actual), abs(expected))`.

The factor 64 predates the observed Session 14ab differences and is already used in governed project numerical checks. It expresses bounded float64 evaluation variation while remaining more than seven orders of magnitude tighter than the controlled-integration gate. Selection is valid only if the rule accepts all four governed differences, rejects every frozen material negative control and preserves exact structural checks. Otherwise close without substituting another tolerance.

Final `+0.0` and `-0.0` are numerically equivalent under this rule; their bits remain diagnostic. This is justified because their numerical value and every downstream arithmetic result are equal. NaN and either infinity are always rejected, including like-signed pairs.

## Analysis and negative controls

Summarize the closed 366-component reference errors overall and by candidate and component family at inverse-ECDF 5/25/50/75/95 percentiles, minimum, maximum and count. Record each divergent component's reference errors, convergence delta and structural equality. Compare maximum platform drift with maximum production/reference error.

Each candidate contract is tested against exact equality, one-ULP variation, signed zero and these failures: a final component beyond the selected 64-epsilon bound; changes beyond `1e-7` and near/beyond `1e-6`; missing, added or reordered components; changed accepted resolution; changed partition, canonical root, owner, routing or residual authority; wrong Simpson coefficient; dropped component; altered field value. A candidate is unacceptable if a required negative control passes.

## Bounded test-only repair

If and only if the selected rule passes the frozen analysis, add a reusable helper under test support and change only:

- `test_session14v_micro_interval.Session14vMicroIntervalTests.test_complete_historical_synthetic_acceptance`;
- `test_session14w_failure_evidence.Session14wMicroIntervalTests.test_complete_historical_synthetic_acceptance`.

Each test shall execute the unchanged production calculation without supplying the stale exact-float historical assertion, then compare the returned interval, component order and final values with historical authority through the helper. The helper reports the failing component, tolerance, absolute/relative difference, ULP distance, signed-zero state and maximum difference. It does not use `numpy.allclose` or change production code.

## Outputs, decisions and stop rules

Publish `authority_summary.json`, `divergent_components.csv`, `reference_error_summary.json`, `candidate_contracts.json`, `negative_control_results.csv`, `equality_contract.json`, `qc.json` and `manifest.json` under `outputs/final_float_equivalence_contract/`, plus the final report and one append-only research-log entry. Outputs are synthetic, finite, sanitized, atomic and hash-bound.

Choose exactly one classification A–H and readiness 1–4 as specified in the Session 14ac handoff. **A — final-float numerical equivalence contract justified and validated**, readiness 1, requires exact structural equality, successful derivation, both repaired historical tests, unchanged production numerics and references, green full local and ordinary Python 3.11/Python 3.13/distribution CI. Unexpected failure after evidence exposure is preserved without widening the bound or attempting another contract.

Preserve distinct commits for this protocol, contract tooling, derived pre-repair authority, test-only repair and closed report. Verify hashes and history, compilation, focused/relevant/full tests, publication safety, documentation links, staged contents and `git diff --check`. Push reviewed checkpoints and verify synchronized heads and the release tag. Do not execute Session 14R. On A/readiness 1, recommend exactly **separately govern a fresh Session 14R empirical representation retry**.
