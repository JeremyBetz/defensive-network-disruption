# Phase 14u — Prepared-row equivalence-gate repair and resumed warning diagnosis

Status: **FROZEN BEFORE REPAIR IMPLEMENTATION OR NUMERICAL REPRODUCTION**
Date: 2026-09-11

## Authority and bounded question

This phase begins from clean synchronized commit
`ed411671920163ec302f3a8cb92a19b8f42ba576`; annotated release `v0.1.0`
must remain at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
Session 14R remains historically D/readiness 3, Session 14s remains
G/readiness 4, and Session 14t remains B/readiness 1. Their code, evidence and
classifications are immutable.

Session 14u repairs only the representation layer that prevented Session 14s
from reaching its already-authorized numerical question. After that strict gate
passes, it asks: what caused the independent maximum-verification SciPy warning
on the same Session 14R failing state? It does not resume Session 14R analysis.

Frozen identities are the Session 14R, 14s and 14t manifest SHA-256 values
`8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed`,
`9bdb96a97e447f834068ca941453d537082a91fcb9653fef1c428ddadc78a61b`
and `0228ea02567606634c0e6dac3c0004145aa15939e6085c102abe9c07637dc118`;
canonical and prepared population hashes remain
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`
and `15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0`.

## Exact equivalence contract

For the current restricted projection of zero-based row ordinal 1, calculate
exactly:

```python
json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
```

Encode this string as UTF-8 and compare it directly with the exact preserved
Session 14R prepared-line bytes. Only byte equality passes. No tolerance,
tuple/list normalization, fuzzy semantic comparison, sequence sorting or
alternate serializer is allowed.

The regression fixture must demonstrate that a tuple-bearing object and its
JSON-decoded list-bearing form compare unequal in Python while producing
identical historical serialization bytes and passing this gate. Numeric changes,
sequence-order changes, missing fields, signed-zero serialization changes and
changed scalars must fail.

The canonical projection, tuple construction, Session 14R preparation, prepared
population and serialization format remain unchanged. If ordinal 1 does not pass
the strict byte gate, stop without examining the mismatch or any other row.

## Authorized state and resumed diagnosis

The only authorized empirical state remains zero-based ordinal 1, derived from
Session 14R's preserved `states_completed=1` failure authority. Use the same
stable alias, integrity key, candidate order and receiver order. Stop at the
first exact `IntegrationWarning`. If it does not reproduce, inspect no other
state and close unresolved.

After gate success only, the runner may:

- locate the first warning in frozen order `isotropic`, `expanding`,
  `constant_width` and canonical receiver order;
- run unchanged joint Simpson intervals 256 through 16,384 and report the
  inherited all-component `1e-7` convergence, finiteness and determinism;
- reconstruct onset points, switches, certified tie enclosures and partitions;
- capture the warning class, exact message, active piece, inherited quadrature
  parameters, returned estimate/error, bounded full-output diagnostics and stack
  location without suppressing the warning;
- use the independently audited continuity oracle around relevant boundaries;
- compare only current piecewise adaptive, onset-only unsplit adaptive, direct
  65,536-interval Simpson, and inherited switch-split Simpson at nominal 32,768
  and 65,536 resolutions.

Report defender, switch, tie, enclosure and piece counts; normalized minimum,
median and maximum piece widths; adjacent-float pieces; pairwise method
differences; and whether the problematic piece is associated with a switch,
onset or tie enclosure. Detailed geometry and traces remain ignored.

Do not change tolerances, methods, partitions, fields or warning policy. A new
defect or failure after execution begins is preserved and stops without repair
or rerun.

## Access, implementation and tests

No other empirical state, target, outcome, model, coefficient, option share,
partial Session 14R scientific summary, provider product, protected/reserved or
withheld data, pose, xT or progression material is authorized.

Add a new strict byte-gate helper, synthetic regression tests and a separate
runner exposing only `preflight`, `diagnose` and `publication-check`. Historical
modules remain unchanged. The runner requires committed protocol and code,
frozen input hashes, a clean tree, an exclusive ignored marker and no prior
output. It records one access attempt and prevents automatic rerun.

Before governed execution, tests cover exact byte equivalence and every required
rejection, deterministic serialization, warning capture, partition diagnostics,
ordinal restriction, failure closure and absence of prohibited routes. Commit
the tested implementation before reading ordinal 1.

## Outputs and decision

Publish under `outputs/continuous_occlusion_warning_diagnosis_resumed/`:

- `equivalence_repair.json`
- `failure_authority.json`
- `partition_summary.json`
- `warning_diagnostics.json`
- `method_comparison.json`
- `qc.json`
- `manifest.json`

Choose exactly one warning classification: A verifier-only warning with healthy
production estimator; B overly strict or fragile piecewise verifier; C partition
or tie-enclosure defect; D production estimator also affected; E field or
maximum-representation defect; F multiple independent issues; G unresolved.
Separately choose readiness 1 bounded verifier-contract repair, 2 small
implementation repair, 3 production/representation numerical revision, or 4
more evidence.

Close and hash evidence before interpretation. Preserve three commits: protocol;
tested repair; closed outputs/report and append-only research log. Run focused,
relevant and full tests, compilation, schema/hash, privacy, links, history,
staged and diff checks; push, await CI, and verify synchronized heads and the
unchanged tag. Recommend exactly one separately governed next action and do not
execute it.
