# Session 14h — Failure localization and diagnostic preservation

## Result

**LOCALIZED — EXACT TYPEERROR SOURCE ESTABLISHED.** The single governed
reproduction followed the unchanged Session 14g engineering fixture order and
reproduced the historical exception at check 6, `multiway_plateau`, during
baseline signature construction. Five completed checks were flushed and
preserved before the exception.

The exact failing operation is the `sorted(...)` call that constructs tie
records in `mapped_signature()` at
`geometry/verification_repair.py:294`. Its generated records contain a first
sort field produced by `boundary(x.start)`. For the active envelope, that field
is `None` for an endpoint tie interval and a tuple for another interval. Python
cannot order those unlike types and raises:

> `TypeError: '<' not supported between instances of 'tuple' and 'NoneType'`

This is **B — TYPE NORMALIZATION / CONTAINER DEFECT**. It is a signature-record
ordering defect in verification machinery, not evidence against any occlusion
field, union, maximum, or Session 13 geometry.

## Twenty-seven-item handoff

1. **Starting HEAD:** `661f1beaac7eea9d47500747ddd9f2f36b3e8ed5`.
2. **Ending HEAD:** recorded after the closure commit and push in the delivery
   handoff; this report avoids a self-referential commit identifier.
3. **Protocol:** [Phase 14h](protocols/phase_14h_failure_localization.md), commit
   `41056a54c45a9c268bc82e6875df3b8e74e73ccb`, SHA-256
   `435cdd2f026b2e41b48607d1a8f82797ea948d626fff0003a94fe47d1c3c8841`.
4. **Diagnostic-preservation changes:** a separate observer records active
   fixture, stage, substage, function and bounded type/shape information; it
   flushes completed fixture rows and captures full and sanitized tracebacks.
5. **Fixture order:** `constant`, `crossing`, `three_constants`,
   `rounded_plateau`, `exact_plateau`, `multiway_plateau`, exactly matching the
   Session 14g dictionary insertion order.
6. **Governed reproduction:** one execution after protocol and implementation
   commits; it stopped at the first exception and did not retry.
7. **TypeError reproduced:** yes.
8. **Active fixture:** check 6, `multiway_plateau`.
9. **Active stage:** `signature_construction`; substage
   `baseline_signature`.
10. **Exception class:** `TypeError`.
11. **Sanitized message:** `TypeError: '<' not supported between instances of
    'tuple' and 'NoneType'`. The public summary retains the exception message
    without the class prefix.
12. **Failing operation:** `mapped_signature()` in
    `src/defensive_network_disruption/geometry/verification_repair.py`, line
    294, while sorting mapped tie-interval records.
13. **Traceback preservation:** the full traceback with local paths is ignored;
    the [public summary](../outputs/continuous_occlusion_failure_localization/failure_summary.json)
    retains repository-relative frames and a sanitized traceback.
14. **Completed checks:** five of six.
15. **Completed rows:** all five prior rows are preserved in
    [engineering_progress.csv](../outputs/continuous_occlusion_failure_localization/engineering_progress.csv):
    constant, crossing, three constants, rounded plateau and exact plateau.
16. **Observed input:** a non-scalar `VerifiedEnvelope`. Within the failing
    generated sort records, one mapped start boundary is `None` and another is
    a tuple.
17. **Expected contract:** every mapped tie record must have a deterministic,
    permutation-stable ordering key whose fields are mutually comparable while
    retaining endpoint absence explicitly.
18. **Defect classification:** B — type normalization/container defect.
19. **Minimal repair recommendation:** change only `mapped_signature()` so it
    builds its existing tie records unchanged, then sorts them with an explicit
    key that maps absent start/end boundaries to deterministic endpoint
    positions and compares uniform scalar/tuple fields. Do not replace `None` in
    the returned record or change ownership semantics. Add a regression using
    the unchanged multiway plateau with simultaneous endpoint and interior tie
    intervals, checking the full mapped signature under every defender
    permutation.
20. **Historical numerical evidence:** unaffected. The failure occurs in
    verification-signature ordering after envelope construction; no field,
    integral, reference or tolerance value is changed by localization. A future
    repair still requires new synthetic production-wiring acceptance because
    Session 14g did not complete it.
21. **Session classification:** LOCALIZED — EXACT TYPEERROR SOURCE ESTABLISHED.
22. **Acceptance work:** the 108-case sweep, 366 references and 399 acceptance
    permutations were not rerun; QC records zero for each.
23. **Data/model access:** no empirical geometry, provider product, target,
    model, utility, option share, protected/withheld/pose, xT or progression
    material was accessed.
24. **Claim ledger:** unchanged. Accessibility remains **PROXY ONLY** and
    suppression **NOT SUPPORTABLE**.
25. **Checks:** 15 focused tests passed; 93 relevant Session 14-series tests
    passed; the full suite ran 382 tests, with 379 passed and three retained
    skips. Compilation and range-level diff checks passed. Software tests do not
    override the governed LOCALIZED result.
26. **Commits/push:** protocol `41056a5`, diagnostic implementation `f464d60`,
    and a separate closure commit. Push and synchronization are reported after
    remote verification.
27. **Exactly one recommendation:** separately govern the bounded
    `mapped_signature()` ordering repair described in item 19, followed by one
    synthetic production-wiring acceptance execution. Do not resume Session
    14R before that acceptance succeeds.

## Diagnostic evidence

The observer preserved bounded structural context before each operation. It did
not dump arrays or envelope records. The active input summary reports only
`python_type=VerifiedEnvelope` and `is_scalar=false`. The traceback itself
establishes the mixed `tuple`/`NoneType` comparison inside the tie-record sort;
source inspection identifies `boundary(x.start)` as the only first-position
expression returning exactly those two types.

The completed public rows report these permutation counts and partition counts:

| Fixture | Permutations checked | Partitions |
| --- | ---: | ---: |
| constant | 1 | 2 |
| crossing | 2 | 3 |
| three_constants | 6 | 2 |
| rounded_plateau | 2 | 6 |
| exact_plateau | 2 | 6 |

No row exists for `multiway_plateau` because signature construction failed
before its completion. Partial progress does not imply readiness.

The diagnostic tests injected failures at fixture evaluation, switch detection,
combined enclosure/partition validation, signature construction, permutation
detection and progress persistence. They verified a synthetic `TypeError`,
traceback sanitization, durable prior rows, exclusive markers, false readiness,
strict package validation and no-rerun behavior. A pre-governed test of the
unchanged path also encountered the same sixth-fixture exception. Under the
protocol, that observation was treated as preparatory evidence; the governed
reproduction above established the cause.

Post-localization validation did not rerun the governed command. Focused tests:
15 run and passed, zero skipped. Relevant Session 14-series tests: 93 run and
passed, zero skipped. Full active suite: 382 run, 379 passed and three retained
scaffold skips. Source, script and test compilation passed. Output schemas,
hashes, LF CSV, publication/privacy guards, documentation links, historical
authority, append-only log preservation, staged contents and full-range diff
checks passed before the closure commit. Final CI is reported after push.

## Closure and boundaries

The [manifest](../outputs/continuous_occlusion_failure_localization/manifest.json)
SHA-256 is
`60e34c1ff4994eb56c97f4ca98c105cb890541c38cda4d10a5fc25ab49786a8a`.
It binds the diagnostic contract, progress, failure summary and QC. The full
traceback, progress ledger, access ledger and execution markers remain ignored.

Session 14g remains historically INVALID. Sessions 14e and 14f remain
unchanged. Session 14h does not repair the defect, rerun Session 14g acceptance,
or authorize Session 14R.
