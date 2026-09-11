# Phase 14w — Failure-state evidence and authorized-edge routing repair

Status: **FROZEN BEFORE IMPLEMENTATION OR AUTHORIZED-EDGE ACCESS**
Date: 2026-09-11

Session 14w begins from synchronized `348ccdea71df1fc06df04440ef457f2a87daf849`; `v0.1.0` remains at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. Session 14v remains historically F/4 and immutable.

This phase repairs only three defects: routing evidence was not persisted before a count assertion; failure publication required success-complete outputs; and generic failure QC recorded zero access after one authorized state and edge had opened. It then reruns exactly prepared row ordinal 1, `constant_width`, receiver ordinal 7 once. No other state, edge, target, outcome, model, share, provider product, protected/withheld data, pose, xT, progression, or Session 14R partial output is authorized.

The micro-interval contract is unchanged: `0 <= O_max(t) <= 1`, global residual budget `1e-12`, and for `N` positive structural pieces a piece is bounded exactly when its realized float64 width is at most `1e-12/N`. Its contribution is `[0,width]`; every other piece uses inherited adaptive quadrature. Structural partitions, fields, detection, certification, Simpson, tolerances, and references do not change. No eligible-piece count is assumed.

Before any acceptance assertion, persist private per-piece ordinal, endpoints, width, threshold, routing, eligibility and boundary associations, plus a public non-reconstructive summary containing structural/positive/bounded/quadrature counts, threshold, eligible widths and stably summed residual bounds. Routing passes only when every piece follows the frozen inequality, all structural pieces remain represented, residual upper bound is at most `1e-12`, and repeat routing is identical.

Failure publication is a first-class `status: failure` schema. It permits unavailable success artifacts and retains stage, exception, marker state, partial routing evidence and actual access counters. Counters advance from access records: pre-access `0/0`, state-open `1/0`, edge-open `1/1`; unauthorized further access blocks and is recorded. Failure after routing must preserve routing evidence and `1/1` accounting.

Before edge access, tests cover zero/one/multiple/all eligible pieces, equality and adjacent-float threshold cases, structural/work counts, access transitions, unauthorized access, and failures before routing, after persisted routing, during quadrature, comparison and closure. The original Session 14v tests and frozen 108 cases, 366 references and 399 permutations must pass with unchanged joint Simpson values and partitions.

The edge must pass exact historical byte equivalence and reproduce 12 pieces, one switch, zero tie intervals and the known `3.3306690738754696e-15` onset-adjacent width. Observed routing is governed by the rule. Persist evidence before verifying warnings, 2,048-interval deterministic joint Simpson, interval-aware maximum agreement and the residual budget. A failure is preserved without repair or rerun.

Publish the nine named artifacts under `outputs/continuous_occlusion_routing_repair/`, with explicit success/failure schemas, strict hashes and privacy guards. Classify A–F and readiness 1–4 prospectively; readiness 1 requires A. Preserve protocol, tested implementation and closure commits, append the research log, push, verify CI and synchronized heads, and stop. A/1 recommends only a separately governed fresh Session 14R retry; otherwise recommend one bounded blocker-specific action.
