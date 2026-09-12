# Session 14af — Empirical-capable lifecycle and publication authority

## Decision

**A — EMPIRICAL-CAPABLE LIFECYCLE / PUBLICATION AUTHORITY ESTABLISHED**

**Readiness 1 — ready for a fresh, separately governed empirical retry**

Session 14af was synthetic orchestration and publication work. It opened zero
real empirical states and zero real empirical edges. It changed no field,
integration rule, numerical reference, model, scientific output, claim,
dependency, or released API. The closed evidence is bound by the
[manifest](../outputs/session14_empirical_lifecycle_publication/manifest.json),
SHA-256 `089d60c3536517b91502620a5a02902204967ee1d340d974c5dd02adcad01be4`.

## Historical qualification and repair

Session 14ae remains historically A/readiness 1 and is unchanged. The narrower
prospective qualification is: **Session 14ae established a valid synthetic
lifecycle model and zero-access pre-empirical accounting behavior, but did not
fully establish empirical-capable cross-file publication validation or
partial-progress preservation under unexpected nonzero-access failure.**

Three gaps were confirmed by static inspection. Its cross-file audit summarized
some expected rejections as fixed strings; its validator required state/edge
access to equal `0/0`; and its unexpected-failure record used generic zero-access
values rather than the live lifecycle and access state. Session 14af adds a new
internal adapter around the unchanged 14ae lifecycle.

Processing progress and access history now have separate authority. Successful
transitions are retained in a private hash-chained journal, which is authoritative
for whether state and edge opens occurred. Public access counts are derived from
that journal and checked against the lifecycle snapshot. A failure handler
captures the pre-failure snapshot, applies failure to the actual active context,
captures the terminal snapshot, and preserves a private traceback. A package
cannot hide prior access by resetting every public count because validation
replays the private journal.

Publication validation uses explicit `pre_access`, `empirical_partial`,
`empirical_failure`, and `empirical_success` contexts. It recomputes lifecycle
and journal hashes and compares actual status, counters, access, active context,
and failure stage across QC, manifest, evidence, and report-facing views.

## Requested handoff

1. **Starting HEAD:** `010bc8876c2abad227ff969c8e2655d96a3f397e`.
2. **Ending HEAD:** the closure commit is reported in the final execution handoff.
3. **Protocol:** [Phase 14af](protocols/phase_14af_empirical_capable_lifecycle_publication.md), commit `9f8409c`, SHA-256 `9600345e2c158faa19530b40ddb7c1e9070120247b3bb35c71592d1209e6a126`.
4. **Session 14ae qualification:** exactly the bounded statement above; its A/readiness 1 record remains historical.
5. **Fixed-string evidence gap:** confirmed and replaced by ten actual validator invocations.
6. **Zero-access limitation:** removed from the new general validator; `0/0` remains mandatory only for `pre_access`.
7. **Unexpected-failure gap:** repaired by retaining live pre-failure and terminal snapshots, access, context, and traceback.
8. **Validation modes:** four explicit contexts distinguish pre-access, incomplete, failed, and successful empirical packages.
9. **Lifecycle/access contract:** processing retains the 14ae state and edge lifecycle; access is separate append-only history.
10. **Failure handler:** derives active state/edge and counters from the authoritative object rather than loop counters or exception location.
11. **Canonical hashes:** each view binds the recomputed lifecycle SHA-256 and private journal SHA-256.
12. **Governed injections:** all 10 were executed against the real cross-file validator.
13. **Invalid results:** 10/10 rejected: lifecycle hash, access, completion, active state, active edge, status, failure stage, manifest success, pre-access nonzero access, and access reset.
14. **Pre-access control:** accepted with one discovered/prepared state, zero evaluation/completion, and `0/0` opens.
15. **Empirical partial-failure control:** accepted with 3 prepared states, 2 evaluation starts, 1 completed state, 4/3 edge starts/completions, and synthetic access `2/4`.
16. **Empirical success control:** accepted with 2 completed states, 4 completed edges, and synthetic access `2/4`.
17. **Access reset:** rejected as `journal_view_mismatch` even after all public counts and the public lifecycle digest were rewritten consistently.
18. **Active context:** failures before a state, during a state, during an edge, and between completed and next edges retained the appropriate state/edge presence.
19. **Partial progress:** the unexpected failure retained 1 completed state and 3 completed edges.
20. **Traceback:** preserved privately and bound publicly by SHA-256; public artifacts expose no traceback or local path.
21. **R4 compatibility:** the actual fail-closed launcher reached its authorization sentinel, then validated a synthetic nonzero-access partial failure.
22. **Real states opened:** `0`.
23. **Real edges opened:** `0`.
24. **Classification:** A — empirical-capable lifecycle / publication authority established.
25. **Readiness:** 1.
26. **Historical 14ae:** protocol, implementation, report, manifest, and results remained byte-identical.
27. **Numerical/scientific authority:** unchanged.
28. **Empirical data:** not accessed.
29. **Session 14R scientific output:** not inspected.
30. **Tests:** 13 focused passed; 39 additional Session 14ae/14ad/R3 tests passed (52 combined); full suite 581 run, 578 passed, 3 retained skips.
31. **Python 3.11 CI:** required after the closure push and reported in the final execution handoff.
32. **Python 3.13 CI:** required after the closure push and reported in the final execution handoff.
33. **Distribution CI:** required after the closure push and reported in the final execution handoff.
34. **Commits/push:** protocol `9f8409c`; tested implementation `c8f0474`; closure commit and push are reported after completion.
35. **Recommendation:** separately govern a fresh Session 14R empirical representation retry using the empirical-capable lifecycle/publication authority.

## Validation and limits

The focused and full suites, relevant historical tests, compilation, strict
schemas, hashes, publication scan, history hashes, and whitespace checks passed
before closure. The previous Session 14ae test result is recorded accurately as
568 run, 565 passed, and 3 skipped; the current expanded suite is 581 run, 578
passed, and 3 skipped.

This work establishes orchestration and evidence integrity. It provides no
evidence for a continuous field, cover shadow, accessibility, suppression,
attribution, or value. Session 14R remains paused.
