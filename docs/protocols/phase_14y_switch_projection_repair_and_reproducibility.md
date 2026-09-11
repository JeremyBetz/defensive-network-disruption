# Phase 14y — Switch-record projection repair and reproducibility rerun

Status: **FROZEN BEFORE IMPLEMENTATION OR DIAGNOSTIC EXECUTION**  
Date: 2026-09-11

Session 14y begins from synchronized `890c9142f59e5c3c760d70090e8d18ccc7e0b974`; `v0.1.0` remains at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. Session 14x remains historically H/4 and immutable.

Session 14x failed because its diagnostic serializer requested nonexistent `VerifiedSwitch.left_owners` and `right_owners`. The immutable production record exposes `location`, `owners_before`, `owners_at`, `owners_after`, `crossing_pairs`, `endpoint`, `multiway`, and `envelope_value`. This phase changes only the diagnostic projection to serialize those real fields with deterministic diagnostic-only owner and pair ordering. It does not add aliases or modify the production type, switch detection, fields, partitions, controlled Simpson, micro-interval routing, references, dependencies, tolerances, locks, or historical equality tests.

Tests must exercise the real `VerifiedSwitch` schema and the exact diagnostic projection path, including ordinary, exact-switch, multiway, identical-side, ownerless-side, and permutation-mapped cases. They must prove deterministic JSON and unchanged historical numerical authority. Any production value, partition, switch root, accepted interval, routing, residual bound, or historical expected byte change blocks execution.

After the repair commit, run exactly one local diagnostic inherited from Phase 14x. It recomputes 108 synthetic historical vectors and 366 ordered components through the unchanged `256`–`16384` controlled-Simpson ladder, recording accepted resolution, convergence deltas, float64 values and bits, signed zero, routing, switches, tie enclosures, residuals, and sanitized environment metadata. An unexpected local failure is preserved and prevents CI dispatch.

After local success, push the tested repair and manually dispatch the existing dedicated Python 3.13 diagnostic workflow exactly once. Verify and preserve its hash-labelled base64 JSON record. Compare all components, ladder levels, partitions, switch locations and `owners_before`/`owners_at`/`owners_after`, tie enclosures, routing, residuals, dependency versions and numerical backends. The independent adaptive verifier does not define the production vector.

Bitwise, algorithmic, and numerical reproducibility are separate verdicts. Numerical reproducibility uses only existing authority: controlled-Simpson convergence at `1e-7` and production/reference agreement at `1e-6`. No new tolerance is selected. Classification precedence and A–H meanings remain those frozen in Phase 14x; readiness remains 1–4. C requires identical algorithm paths, resolutions and routing plus differences inside existing numerical authority.

Publish the ten named artifacts under `outputs/cross_platform_vector_reproducibility_14y/` and bind the CI record hash. Records contain synthetic fixture names and sanitized environments only. No development state, target, outcome, model, option share, protected/reserved/withheld data, pose, xT, progression, or Session 14R partial output may be accessed.

Any unexpected governed failure is preserved without repair or rerun. No historical equality-test, tolerance, dependency pin, production implementation, or Session 14R change is authorized. A/B/C with readiness 1 recommends only a separately governed cross-platform equivalence-contract repair, followed by fresh Session 14R authorization if that repair passes.
