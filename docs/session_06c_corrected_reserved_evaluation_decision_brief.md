# Session 06c corrected reserved evaluation decision brief

**Decision:** **D — INVALID** for the primary M1-versus-M0 question and
**4 — INVALID** for the secondary M2-versus-M1 question.

Session 6c corrected and froze the Git/LFS identity verifier, but the protected
evaluation did not reach tracking acquisition, parsing, population construction,
or scoring. `reserved_01` metadata and Dynamic Events passed their pinned Git
object checks. Opening the authorized tracking media endpoint then failed TLS
hostname verification before response or payload bytes were received. This is
not one of the prospectively permitted retry cases, so it was attempted once and
the execution stopped. No scientific or verifier change was made after access.

## Source authority

The corrected source chain verified pinned commit
`02a396ffd09b283c9f092fdedeff11da6d535b66` and tree
`44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`. All nine development tracking
identities and their already-present payload hashes passed without parsing. The
ten reserved tracking identities frozen before acquisition were:

| Alias | Git pointer OID | Expected LFS SHA-256 | Bytes |
| --- | --- | --- | ---: |
| reserved_01 | `7439f0ba7da6bc03625258b98fe84a5bf770b72e` | `ea97f58f8eaad925feaeacc6395ec24860dd80027af8a89450276adebd29d265` | 90,729,279 |
| reserved_02 | `fa22f7fbca40a66d046b675e59b2c6ba0db19af6` | `858c7a756ca3d33017f864775af5999d2c0f364e58ab60ae040c8b9ebab17827` | 91,049,828 |
| reserved_03 | `13664e719ca355c2ab5e14899fe1c3dbefb007a7` | `5ba2d87f6fd1ba3138301b369bd9266be69416a2d799a3fba5b5ec8a52e1284b` | 87,710,167 |
| reserved_04 | `4402bd9c59300005a9674882c5735299e55dc2f5` | `630e946950fe459f5e48872b01a36e6dfc319cf9027e7b98156150bb6e2c30f6` | 88,531,597 |
| reserved_05 | `78b70bcba5d4dbf375bc43dd7188ef0da1a666b2` | `fab9d331e06f3042c83ac17798901b49bb259c99a8f3b319cd0146263cde65e7` | 88,945,845 |
| reserved_06 | `5880f8f797b3353814fa8e6af91e3554a945fefc` | `61dfdbd83f8e654127b249b8503f062338c14ec0c9e65404bcf70fb7c1346bd4` | 90,591,887 |
| reserved_07 | `8b0d91430bed0fe3217e8f0a9525ee744fb2d906` | `12d00d6e4257218812df6e4c4263c49387ba0313a83ff8d826c4416828f9c798` | 90,025,383 |
| reserved_08 | `2ef15e0a762e293cd16084202da60dbd7a71803e` | `fea913b8d4cbde8d85c6bdf5f1a4b3fd203b78227e976a171c8ab0946705d378` | 92,872,706 |
| reserved_09 | `cbc77fbf800b88f1f49974c49d62d5c0acc53a95` | `04562d9754b2977c80430535e9b5733426bc4ce910db56fe7a3760876211ac5a` | 92,516,156 |
| reserved_10 | `c68f711f9c32d42aadfccd8e9a416b8a82e5fd0e` | `d78555f9dfd7d1ce9de38066d3c98e6d54417c6d45d73b1f1ce7e26f07263d8f` | 94,737,872 |

These values establish intended identities only. Zero reserved tracking payloads
were downloaded or integrity-verified.

## Evidence map: 67 requested report items

1. **Starting HEAD:** `5d2a4f94d88ff479834ead4ef05ed50b051c62f3`.
2. **Ending HEAD:** recorded after the reviewed closure commit below.
3. **Protocol:** `docs/protocols/phase_06c_verifier_repair_and_reserved_evaluation.md`; SHA-256 `8f74ea7566358519b30f010fd0f770e70d15d735dc41e1da4077ca435de7893f`; commit `7f910d21420d39de90e515c01ab2f94275020e83`.
4. **Repair:** `session6c_source.py`, runner, and tests have SHA-256 values `18755779187f27975d4e9d67735d525e78ca3fc5b85bd3cfd495d13b45a21bd9`, `2dffb71b053c68cc0e9309bf387d2256524d8130374b001212f31914fd308cfd`, and `bda03bbb6311d4404091757041d1de63b28c348582c3030c3f6ede63f0029625`; commits `ae7c6c0` and pre-access direct-run correction `db2fc27`.
5. **Historical defect:** decoded pointer length was compared with Contents API payload-size semantics.
6. **Historical regression:** the frozen verifier rejects 133 versus 90,729,279 bytes; the repaired verifier accepts the distinct pointer and payload identities.
7. **New semantics:** commit/tree/path/blob and pointer identity are verified separately from downloaded-payload SHA/size; Contents size is diagnostic only.
8. **Development compatibility:** nine of nine pointer identities and nine of nine existing payload SHA/size checks passed without parsing.
9. **Pinned revision:** `02a396ffd09b283c9f092fdedeff11da6d535b66`.
10. **Reserved membership:** exactly `1874553`, `1927964`, `1959846`, `1986691`, `1996436`, `2006363`, `2007448`, `2007721`, `2010085`, and `2016236`.
11. **Reservation qualification:** Prospectively reserved from this project stage forward. Session 1 schema inventory mechanically over-read post-header bytes into process memory, but no evidence indicates value-level content was surfaced, persisted, or used analytically.
12. **Withheld match:** `1953632` remained unopened.
13. **Pointer identities:** all ten are listed in the source-authority table above.
14. **Expected payload identities:** all ten SHA-256 values and declared sizes are listed above.
15. **Actual tracking SHA/size:** unavailable because no tracking response bytes were received.
16. **Tracking payloads verified:** 0 of 10.
17. **Acquisition failure:** TLS certificate hostname mismatch for the authorized media host on `reserved_01` tracking attempt 1; no retry was authorized for this category.
18. **Reserved raw attempts:** unavailable; no parsing occurred.
19. **Evaluation eligibility:** unavailable.
20. **Exclusion waterfall:** unavailable.
21. **Target completeness:** unavailable.
22. **Target outside:** unavailable.
23. **Candidate summary:** unavailable.
24. **Population hash:** unavailable; no population exists.
25. **Population-freeze commit:** unavailable because preparation was not reached.
26. **M0 authority:** unchanged final-model artifact verified at SHA-256 `0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`.
27. **M1 authority:** verified in the same unchanged artifact.
28. **M2 authority:** verified in the same unchanged artifact.
29. **Reserved fitting:** none.
30. **M0 MRR:** unavailable.
31. **M1 MRR:** unavailable.
32. **M1−M0:** unavailable.
33. **Primary paired differences:** unavailable.
34. **Primary paired mean:** unavailable.
35. **Primary paired median:** unavailable.
36. **Primary signs:** unavailable.
37. **M0/M1 Hit@1:** unavailable.
38. **M1−M0 Hit@1:** unavailable.
39. **M0/M1 Hit@3:** unavailable.
40. **M1−M0 Hit@3:** unavailable.
41. **Primary classification:** **D — INVALID**.
42. **M2 MRR:** unavailable.
43. **M2−M1:** unavailable.
44. **Secondary paired differences:** unavailable.
45. **Secondary paired mean:** unavailable.
46. **Secondary paired median:** unavailable.
47. **Secondary signs:** unavailable.
48. **M2 Hit@1 difference:** unavailable.
49. **M2 Hit@3 difference:** unavailable.
50. **Secondary classification:** **4 — INVALID**.
51. **M1 development-signal replication:** not evaluated.
52. **M2 development-increment replication:** not evaluated.
53. **Allowed interpretation:** no protected ranking claim is supportable; this execution establishes only source identities and two verified ordinary products.
54. **Accessibility:** **PROXY ONLY**.
55. **Suppression:** **NOT SUPPORTABLE**.
56. **Post-access tuning:** none.
57. **Pose/orientation:** none.
58. **Network/GNN:** none.
59. **Passage inspection:** none.
60. **Public outputs:** repair authority `644d33b4eafcfb7029f83b91c4347ecd5cb2cbfdff8f44b44d2bcffb81d07f8e`; QC `48f32a614854178542f53f66bb0f8a25d48922d92e7b28864260dcc0781e1678`; manifest SHA-256 `4671b2490feda41ee79a7e15c185b3e93983afc3f68e376a11841bea52086136`.
61. **Tests:** 114 active tests passed and 3 planned scaffold tests skipped; compilation and focused Session 6c tests passed.
62. **Publication/change review:** JSON schemas, recorded hashes, sensitive-field search, historical-artifact checks, staged review, and `git diff --check` passed. Metric and population artifacts are explicitly absent rather than fabricated.
63. **Session 6:** preserved as D / 4 invalid.
64. **Session 6b:** preserved as B recoverable.
65. **Commit/push:** recorded after the reviewed closure commit and synchronization.
66. **Final Git status:** recorded after synchronization.
67. **Exact next direction:** a separately authorized, bounded transport-endpoint and TLS-identity review of the pinned LFS delivery path. It must resolve the hostname-certificate failure without acquiring or parsing football data before any new protected-execution protocol is proposed.

## Closure

The two verified ordinary products, source authority, receipts, and access ledger
remain ignored and preserved. The ledger SHA-256 is
`809aae47bc9d04bcdcd17415815bb09ae5d39afc44c6be6b887399638fe9575d`.
No execution marker, population, metric CSV, paired comparison, or aggregate
metric exists. Session 6c stops here.
