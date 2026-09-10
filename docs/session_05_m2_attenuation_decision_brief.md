# Session 05 decision brief: M2 multi-defender attenuation

## Decision

**A — DISTRIBUTED STATIC DEFENSE ADDS INCREMENTAL INFORMATION.**

In the nine leave-one-match-out development comparisons, adding a continuous
multi-defender segment-attenuation feature provided incremental receiver-ranking
information beyond M1's nearest-defender minima.

This is consistent development evidence from one prospectively frozen feature.
It has no declared practical-effect threshold and is not protected or external
validation. Accessibility remains **PROXY ONLY**. Suppression remains
**NOT SUPPORTABLE**.

## Required execution record

1. **Starting / ending HEAD:** start
   `746357d0c358062df49ec6641a9ac20c7eba97fc`; scored execution HEAD
   `01331646a3ed5d056de4cef7f09601eea5453a19`; the final package is the
   results commit containing this brief.
2. **Protocol:** `docs/protocols/phase_05_m2_multi_defender_attenuation.md`,
   SHA-256 `d539f233e18a20be95c5fa0dceb06a17f931d54c7b951236456979b24ca6504c`,
   committed prospectively as `d4fd5da`.
3. **Implementation:** frozen before scoring as `0133164`; runner SHA-256
   `14c5e7e3584dd6ecfe78947a7a9c5995d5f878c1e32438d6f3744904ed53b473`.
4. **Formula:** `A = sum_j exp(-d_j / 5.0)`, where each `d_j` is distance
   to the finite carrier-receiver segment.
5. **Scale and rationale:** `h = 5.0 m`, a transparent prospective local
   geometric decay scale; it is not a tactical cutoff or interception radius.
6. **Library reuse:** bounded review found no exact dependency-light primitive.
   DataBallPy is a conceptual summed-influence comparator; Floodlight,
   mplsoccer, and UnravelSports do not implement the frozen finite-segment sum.
   The tiny primitive was implemented locally with the existing projection,
   `math.exp`, numeric distance sorting, and `math.fsum`.
7. **Synthetic invariants:** exact 0/5/10 m contributions, linear
   multiplicity, Session 4 one-versus-three separation, monotonicity,
   bit-identical permutation invariance, degenerate-segment behavior, extreme
   finite distance, nonfinite rejection, and empty-defender rejection passed.
8. **Population identity:** Session 3 population SHA-256
   `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`
   was verified before parsing and again before execution.
9. **Benchmark attempts:** 7,227 evaluation-eligible and fit-eligible attempts.
10. **Development matches:** the same nine allowlisted matches, represented
    publicly only as `development_01` through `development_09`.
11. **Folds:** nine leave-one-match-out folds; each fit used the other eight
    matches and evaluated the identical held-out population for M1 and M2.
12. **M1 match-macro MRR:** `0.5677850077704323`.
13. **M2 match-macro MRR:** `0.5726246145826912`.
14. **M2−M1 MRR:** `+0.004839606812258923`.
15. **Nine paired MRR differences:** development 01 `+0.00846560846560851`;
    02 `+0.01189584448011427`; 03 `+0.005127467653728068`; 04
    `+0.001975982335161386`; 05 `+0.00462962962962965`; 06
    `+0.007494889847830977`; 07 `+0.002111381201695406`; 08
    `+0.0016424462609749835`; 09 `+0.00021321143558705735`.
16. **Mean paired MRR difference:** `+0.004839606812258923`.
17. **Median paired MRR difference:** `+0.00462962962962965`.
18. **MRR direction counts:** 9 positive, 0 negative, 0 tied.
19. **M1 Hit@1:** `0.35464033099272835`.
20. **M2 Hit@1:** `0.3610016864769666`.
21. **Hit@1 difference:** `+0.006361355484238274`; seven matches positive,
    none negative, two tied.
22. **M1 Hit@3:** `0.7273112108986005`.
23. **M2 Hit@3:** `0.7317703656806165`.
24. **Hit@3 difference:** `+0.004459154782015973`; seven matches positive,
    one negative, one tied. The single negative fold was development 07 at
    `-0.0013089005235601414`.
25. **Attenuation coefficient signs:** negative in all nine folds, zero positive
    and zero tied; values ranged from `-0.2916858364422624` to
    `-0.22863147337243078`. This is model behavior, not causal attribution.
26. **Identifiability and convergence:** every M2 fold had rank 6/6, conclusive
    no-complete/no-quasi-separation results, successful optimization, and maximum
    absolute gradient at most `1.234577692364562e-07`, below the `1e-6` gate.
27. **Strict nesting:** every M2 raw matrix contained byte-identical M1 columns;
    shared training means, scales, and standardized columns were exactly equal.
28. **Same evaluation population:** confirmed; both models scored the same 7,227
    held-out observations with the same labels, candidates, ties, and folds.
29. **Classification:** A, based descriptively on 9/9 positive paired MRR folds,
    positive mean/median, positive aggregate Hit@1/3, and passed QC. This does
    not establish a practically meaningful effect size.
30. **Allowed wording:** “In the nine leave-one-match-out development
    comparisons, adding a continuous multi-defender segment-attenuation feature
    provided incremental receiver-ranking information beyond M1's
    nearest-defender minima.”
31. **Accessibility:** PROXY ONLY.
32. **Suppression:** NOT SUPPORTABLE.
33. **Scale tuning:** none; `h = 5.0 m` was committed before performance.
34. **Alternate M2:** none was constructed, fitted, or evaluated.
35. **Reserved values:** none opened.
36. **Pose:** no pose or skeletal data opened.
37. **Velocity/reachability:** neither used.
38. **Network features:** none used.
39. **Scored passages:** none inspected.
40. **Outputs:** compact M1/M2 match metrics, paired comparison, aggregate
    metrics, QC, and manifest under `outputs/receiver_ranking_m2/`; detailed
    preparation, parameters, and execution state remain ignored.
41. **Output hashes:** aggregate
    `27335311d05ee455ba0844fd84a28a093c18d2ac34a14b35009eeddec9781d89`;
    M1 metrics `f8a76aa640f7c59b04911898b0a98d1c95e4a8d9fb0f52e5e55ddd4fb46dbcb3`;
    M2 metrics `f1fb7774f7ac5d8e4e5ccf5c6305d5dc9c025fd805c18c6368bb325612d45fe4`;
    paired comparison `2e4286665142318a98112cab82deae136819b70bcb8092ef2c47d9108b260fdd`;
    QC `8ab5dff7519a0d608157b46f6ddeca688cfe3e16249fdea8772bf07e2e6bf3ac`;
    manifest `c90a8a69f5bfda1440a820d3a0b387e156925b17474cc7b9b9764ff2b1701edd`.
42. **Tests:** six focused Session 5 tests and the full active project suite
    passed before scoring; final results-package verification is recorded below.
43. **Publication checks:** output schemas, aliases, hashes, private-path guard,
    provider-identifier guard, and compact publication check passed.
44. **Commit/push:** protocol and implementation commits preceded execution;
    the reviewed result-package commit and synchronized push are the final
    closure actions for this brief.
45. **Final git status:** required to be clean with `HEAD == origin/main` after
    the result-package push.
46. **Recommended next direction:** freeze the edge-level M0/M1/M2 ladder and
    write a separate protected-evaluation protocol for the ten reserved matches.
    Do not access those matches until that protocol is committed.

## Interpretation

The attenuation extension made a small, directionally consistent improvement in
development LOMO. MRR improved in every match, while both secondary aggregate
metrics improved and only one Hit@3 fold moved slightly downward. The negative
attenuation coefficient in every fold is coherent with greater summed proximity
reducing conditional receiver utility after controlling for M1, but it does not
turn the feature into an accessibility probability or a causal suppression
measure.

The edge-level ladder is mature enough to freeze. The next scientific action is
protected evaluation under a new protocol, not another development model.
