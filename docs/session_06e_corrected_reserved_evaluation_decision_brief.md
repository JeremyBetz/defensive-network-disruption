# Session 6e — Corrected protected evaluation decision brief

## Decision

**Primary: A — M1 INCREMENTAL SIGNAL REPLICATES.** The frozen M1 model improves target-receiver MRR over M0 in all ten prospectively reserved matches. Match-macro MRR increases by **0.091670004**, from 0.487333389 to 0.579003393. The paired median is 0.091815536; gains range from 0.062348615 to 0.118545766. Hit@1 and Hit@3 also improve in every match, with macro gains 0.105717845 and 0.109783483. The magnitude and agreement across matches and secondary metrics support replication descriptively; no significance or practical-effect threshold was introduced.

**Secondary: 1 — M2 INCREMENT REPLICATES, with a smaller and metric-dependent increment.** M2 increases MRR over M1 in all ten matches, reaching 0.585853527. Macro gain is **0.006850134** and paired median 0.006682388; gains range from 0.002033925 to 0.011936449. Hit@1 improves in nine matches and decreases in one, with macro gain 0.011272220. Hit@3 is split five positive/five negative, with macro gain 0.002235794. Thus the fixed attenuation feature adds consistent reciprocal-rank information; this does not establish uniform top-three retrieval improvement, a practically meaningful threshold, or accessibility validity.

The official LFS transport succeeded with normal TLS. All thirty products verified, all ten matches passed the unchanged input contract, and exactly one protected scoring execution completed. There was no retry, refit, scientific amendment, post-access implementation change, or corrective scoring run.

## Population and results

8,177 raw pass attempts produced **8,169 evaluation-eligible and 8,169 fit-eligible observations**, recorded separately. Two attempts had missing targets; six had an untracked carrier. All other exclusion categories are zero. No retained target-outside observations remain. Each eligible choice set has ten candidates and eleven valid defenders; these are observed structural counts, not admission rules.

Targets are present in 8,175/8,177 raw attempts; two are missing, zero are self-targeting/unresolved. Current-state target validity is assessable and valid for 8,169 attempts; six have a not-assessable invalid state. Target presence is not treated as completeness of independent intended-receiver ground truth.

| Model | Match-macro MRR | Hit@1 | Hit@3 |
| --- | ---: | ---: | ---: |
| M0 | 0.487333389 | 0.258110726 | 0.636738692 |
| M1 | 0.579003393 | 0.363828571 | 0.746522175 |
| M2 | 0.585853527 | 0.375100791 | 0.748757969 |

| Alias | Evaluation / fit | M1−M0 MRR | Hit@1 / Hit@3 direction | M2−M1 MRR | Hit@1 / Hit@3 direction |
| --- | ---: | ---: | :---: | ---: | :---: |
| reserved_01 | 835 / 835 | +0.118545766 | + / + | +0.003997244 | + / − |
| reserved_02 | 996 / 996 | +0.090376586 | + / + | +0.008665216 | + / − |
| reserved_03 | 814 / 814 | +0.077476990 | + / + | +0.011936449 | + / − |
| reserved_04 | 765 / 765 | +0.093254487 | + / + | +0.002033925 | − / − |
| reserved_05 | 659 / 659 | +0.072767180 | + / + | +0.006609341 | + / − |
| reserved_06 | 844 / 844 | +0.104102253 | + / + | +0.006755435 | + / + |
| reserved_07 | 751 / 751 | +0.062348615 | + / + | +0.008995942 | + / + |
| reserved_08 | 847 / 847 | +0.090294878 | + / + | +0.008715635 | + / + |
| reserved_09 | 835 / 835 | +0.096569718 | + / + | +0.005440072 | + / + |
| reserved_10 | 823 / 823 | +0.110963567 | + / + | +0.005352080 | + / + |

M1−M0 paired mean: 0.09167000388684854; median: 0.09181553634394413; signs: **10 positive, 0 negative, 0 zero**. M2−M1 paired mean: 0.00685013393383479; median: 0.006682387971717607; signs: **10 positive, 0 negative, 0 zero**. The last-bit difference between the M2 paired mean and difference of macro means is ordinary floating-point summation order; both governed quantities are preserved exactly in the generated aggregate file. No rounding tolerance or result bytes were changed.

All three models have zero tied-target blocks in this population. The frozen expected-credit tie policy still applies. Metric denominators, fit counts and target-outside zero counts match the committed structural authority for every model and alias.

## Interpretation and reservation

In the ten prospectively reserved matches, the frozen model containing two transparent defensive-geometry features ranked the provider target receiver better than the defender-free attacking-geometry baseline. This replicated the incremental defensive-geometry signal observed in the leave-one-match-out development comparison. The prospectively fixed summed multi-defender attenuation feature provided additional receiver-ranking information beyond the minimum-distance representation, with the secondary-metric qualifications above.

Vendor target labels remain useful with **Tier B limitations**. Accessibility remains **PROXY ONLY**; suppression remains **NOT SUPPORTABLE**. This is an offline extrapolated-tracking benchmark. Past frame selection does not prove provider processing was causal or available in real time. Results are receiver-selection evidence, not pass success, tactical value, calibrated availability, or the best pass. Generalization concerns these ten reserved matches, not automatically unseen teams, leagues or providers.

Prospectively reserved from this project stage forward. Session 1 schema inventory mechanically over-read post-header bytes into process memory, but no evidence indicates value-level content was surfaced, persisted, or used analytically.

Exact membership and the withheld-ID firewall are frozen in [Phase 6e](protocols/phase_06e_official_lfs_transport_and_reserved_evaluation.md). Public results use stable aliases; the identity mapping remains ignored. No withheld file or protected passage was opened.

## Transport, integrity and chronology

The historical records remain distinct and byte-identical: Session 6 D/4 — INVALID (Git/LFS verification semantics); Session 6b B — bounded verifier repair; Session 6c D/4 — INVALID (TLS hostname failure before tracking bytes); Session 6d B — official LFS protocol is the secure path. Session 6e replaces transport and orchestration only. It neither rewrites those failures nor claims a git-lfs binary was installed or tested.

The pinned source is `02a396ffd09b283c9f092fdedeff11da6d535b66`, tree `44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`. Bounded Git metadata/pointer requests matched the prior identity-only authority. Twenty ordinary Git blobs and ten LFS payloads independently passed actual hash/byte-count checks. The tracking payload total is **907,710,720 bytes**. Per-alias expected and actual SHA-256/size are in the committed population summary.

Each LFS batch request contained one frozen OID/size; each action passed the fixed HTTPS-origin, public-DNS, header and normal-TLS checks. No historical media URL, redirects, TLS weakening, credential forwarding, alternative source pin, or automatic resume was used. The access ledger records 62 started operations: 12 source-metadata/pointer requests, ten batch requests, thirty product downloads, and ten projected-match inspections. All completed; no retry, refresh or failure was recorded. Detailed URLs and action credentials were never logged. All thirty products were verified before the first projected match inspection.

| Checkpoint | Commit |
| --- | --- |
| Starting clean live-remote checkpoint | `aecdb860f6a3b354c4eb9631aff54b694fefe88f` |
| Prospective protocol | `d8112ad1e44a183e3c27c58b118b5c34662a6be4` |
| Tested implementation before upstream inspection | `016db704b624a24dac20e22676a4a0e6d0b288f2` |
| Transport/source authority before acquisition | `1693f8f7c5a261954e99de4375b840850971bf4f` |
| Structural population authority before scoring | `0da14cff08e43d7175da3e289cf5b8f8c4faf35d` |
| Reviewed result package | The commit introducing this brief; resolve with `git log --diff-filter=A -1 --format=%H -- docs/session_06e_corrected_reserved_evaluation_decision_brief.md`. |

The final result commit is pushed after review; live remote equality and clean local status are checked in the final handoff. This enclosing-commit reference avoids a self-referential commit hash.

## Reproducibility and evidence map

| Requirement | Evidence / disposition |
| --- | --- |
| Historical preservation and exact starting checkpoint | Starting live remote verified; production `verify_history` compares all historical tracked bytes, allowing only append-only research-log entries. Historical protocols, source helpers, populations and results unchanged. |
| Frozen source and exact partition | Phase 6e allowlist, committed transport authority, source commit/tree and alias-bound product identities; withheld access false. |
| Protocol before implementation/access | Commit chronology above. No amendments or squashing. |
| Separate commands and namespaces | `scripts/session_06e_reserved.py`; `preflight`, `verify-sources`, `acquire-reserved`, `prepare-reserved`, `score`, `publication-check`; independent commit gates. |
| Official batch request, object matching, bounded response | `data/session6e_transport.py` and focused exact-request/cardinality/OID/size/duplicate-key/transfer tests; 64 KiB response cap. |
| HTTPS, public origin, TLS, redirects, headers and secret redaction | Focused origin/userinfo/port/private-DNS/header/TLS/redirect tests; live acquisitions passed; no git-lfs installation or new dependency. |
| Pointer versus payload identity | Frozen corrected verifier reused; 133-byte/90,729,279-byte regression retained; per-product identities and separate actual payload verification recorded. Contents size is not pointer authority. |
| Transport retry/expiry policy | Synthetic allowed-failure, exhaustion, immutable-request, fresh-file, partial-byte disposal, no-retry and expiry-refresh tests. Live retries and refreshes: zero. |
| Unsafe paths/products/partitions/symlinks | Production source/destination guards and focused rejection fixtures. API credentials scoped to API origin; public batch/raw products receive none. |
| Final-model authority and environment | Original model SHA below; original features/means/scales/coefficients/QC hash-bound. Python 3.13.15, NumPy 2.5.3, SciPy 1.18.1 and original lock/platform unchanged. No empirical fitting. |
| Thirty files before parsing | Verified receipts and ledger; 20 ordinary blobs + 10 tracking payloads. No development population regeneration or development performance calculation. |
| Restricted projection and unchanged input contract | Historical Session 6 reader reused; synthetic sentinel projection, identity/fallback/conflict, interval/direction and timing tests in active suite. No unsupported reserved case occurred. |
| Candidate independence and fixed scientific rules | Frozen helper reuse; independent active finite teammate/opponent sets, goalkeepers/backward options retained, no new cutoff/offside repair; features and h=5 unchanged. |
| Decision-time and numerical qualifications | Latest same-period strictly prior frame at most 100 ms old, integer-microsecond timing; 100 ms is a prospective cadence-based draft, not timing truth. Segment 1e-9 m is implementation tolerance only. |
| Raw attempts, target usability and all exclusions | `population_summary.json`: 8,177 raw, 2 missing targets, 6 untracked carriers, all other exclusions zero; overlapping QC and explicit target numerators/denominators retained. |
| Independent evaluation/fit eligibility and target-outside handling | 8,169 / 8,169 separately recorded; zero outside cases; no equality rule generalized to future data. |
| Candidate/defender validity and population hashes | Per-match/combined structural counts and hashes; ten nonempty groups; population authority committed before scoring. |
| Single scoring and concurrency boundary | Exclusive persistent execution marker; synthetic repeat/concurrency rejection; one live score command. Preparation has no scoring route; score has no provider acquisition, fitting or preprocessing-estimation call. |
| Frozen metrics and identical populations | Three match CSVs, QC and aggregate; expected block-high 1e-12 ties, zero-credit handling, within-match means and equal ten-match macro aggregation unchanged. |
| Primary hierarchy and evidence | M1−M0 evaluated first: A; ten paired MRR values above and exact CSV; mean/median/signs and Hit@1/3 agreement reported. |
| Secondary hierarchy and evidence | M2−M1 independently classified 1; smaller increment, Hit@3 disagreement explicitly retained. No new metric, significance test, bootstrap, confidence interval or effect threshold. |
| Atomic outputs, schema/cross-file validation and closure | Generated bytes written atomically; denominator, alias, finite metric, paired/aggregate and output hashes validated before closed marker/performance display. No manual result edits or second score. |
| Failure preservation | Acquisition, preparation and scoring-validation failure paths rehearsed synthetically before access. No live failure. Failure-only report fields are not applicable to this valid execution. |
| Publication boundary | Only protocols/code/tests and aggregate/hash/alias results published. Raw products, projected/detail rows, timestamps, coordinates, player/event identities, alias map, receipts, access/execution records remain ignored. No per-attempt scores/rankings published. |
| Full verification | Focused 24 passed / 0 skipped. Full active suite 157 passed / 3 existing scaffold skips (160 total), before and after execution. Compilation, history/environment, output schema/hash, publication and diff checks passed; staged artifacts reviewed before commit. |
| Closure, push and stop | Separate reviewed result commit follows all gates; final remote synchronization checked after push. Exactly one future direction below; no follow-on execution. |

All visible requested outcomes and inherited publication/closure rules are mapped above. The truncated attachment supplied no authoritative exact final report-item count; none is invented.

## Governed hashes

| Artifact | SHA-256 |
| --- | --- |
| Closed manifest | `eb7f44be01ae8de3d997d727f26e52d702f6df64217d72a8bef98c336ead5bb1` |
| Transport authority | `543ad3938526003f4c75150188f3e86f366b8a12d7a3c33d95242b16244d2f79` |
| Population summary | `eb0eb5aa97bb22a1f4f31cdd5cc96a98d4145d5931deaea9132e9bf90e368d7b` |
| Ignored canonical reserved population | `85090ae5a7da4d0d9c275e37a199150855b669d38be7d060ecd6f8855fe85b99` |
| Final development models, unchanged | `0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65` |
| Aggregate metrics | `97ff79b2d6b8a2a3ee5b7d675fc8767e40bccd9a4b1c6778488dfaae532be907` |
| QC | `b1b518f9ae61019308ef56388f44308c882d17144e5c8cf06535357090ae7c96` |
| Ignored access ledger | `12e4faaada16fbe7e76439f3647cc91534b947a4787f41d7d735aa05067c9d51` |

The [manifest](../outputs/reserved_evaluation_v3/manifest.json) binds exact protocol/implementation/environment, final-model, transport/population authority, receipts, ledger and metric-output hashes. Its own hash is recorded here, not recursively inside itself. Full-precision results are in the [aggregate](../outputs/reserved_evaluation_v3/aggregate_metrics.json), [primary pairs](../outputs/reserved_evaluation_v3/m1_m0_paired.csv), and [secondary pairs](../outputs/reserved_evaluation_v3/m2_m1_paired.csv).

## One next direction, not executed

Recommend a **separately governed development-only construct-validity and practitioner diagnostic review of the frozen M0/M1/M2 ladder**, retaining M2's smaller, metric-dependent contribution. Session 6e stops here: no protected-passage inspection, tuning, orientation, reachability, network/GNN work, new model or Session 7 execution.
