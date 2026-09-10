# Session 06b tracking Git/LFS integrity review

**Classification:** **B — PROVENANCE BUG RECOVERABLE WITH BOUNDED REPAIR**

Session 6 failed because its verifier compared the GitHub Contents API `size`
for an LFS-managed path with the decoded Git pointer's byte length. At the pinned
revision, Contents reports the payload size (`90,729,279` bytes for
`reserved_01`), while the Git tree and blob envelope correctly report a 133-byte
pointer. The decoded pointer's Git OID is exactly the expected OID. Its single LFS
OID and declared size exactly match the contemporaneous Session 1 record.

The same relationship appears for `development_01`: Contents reports the
`89,280,839`-byte payload size while the pointer is 133 bytes. Its payload was
already verified independently in Session 2. This establishes a verifier-wide
metadata-semantics defect for the two tested tracking paths, rather than a source
revision, path, object, pointer, or payload-identity disagreement.

No tracking payload was requested or parsed in Session 6b. Pointer identity
establishes the uniquely intended payload, but does not newly verify the reserved
payload bytes. Session 6 remains historically valid as a stopped **D / 4 —
EXECUTION INVALID** run under its frozen verifier.

## Identity comparison

| Identity | `reserved_01` | `development_01` |
| --- | ---: | ---: |
| Git pointer blob OID | `7439f0ba7da6bc03625258b98fe84a5bf770b72e` | `6c1d01ae3bafa28cf94e4b7a581fb3779effe4bd` |
| Git tree/blob pointer size | 133 bytes | 133 bytes |
| Blob-envelope size | 133 bytes | 133 bytes |
| Contents API size | 90,729,279 bytes | 89,280,839 bytes |
| LFS payload SHA-256 | `ea97f58f8eaad925feaeacc6395ec24860dd80027af8a89450276adebd29d265` | `3577e2803da95390f8b2f85d47829eb55fbbfee6211c94adc65db0dc78e46b41` |
| LFS declared payload size | 90,729,279 bytes | 89,280,839 bytes |
| Frozen hash check | pass | pass |
| Frozen size check | fail | fail |

The pinned commit resolves to tree
`44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`, matching Session 1. Both paths
resolve to the recorded pointer OIDs. The repository `.gitattributes` rule applies
Git LFS filtering to both paths. There is no documented local SkillCorner source
checkout, and none of the three bounded candidate locations exists. Local smudge
or materialization therefore did not affect the API-only Session 6 code path.

## Evidence map: 39 requested items

1. **Starting HEAD:** `045d24ab014a2962d9da046bf0b2efc3eb805664`, clean and synchronized.
2. **Ending HEAD:** the pushed result commit containing this report; its exact OID
   is reported with the final execution handoff because a commit cannot contain
   its own identity.
3. **Protocol:** `docs/protocols/phase_06b_tracking_integrity_review.md`, SHA-256
   `c665a9ab073c78761056c7f5a514d860758bdf060b70d4b661b305ba970660b5`,
   committed as `bdae204fd294493f83b2bff075dcff533a56291b`.
4. **Failed alias/path:** `reserved_01`,
   `data/matches/1874553/1874553_tracking_extrapolated.jsonl`.
5. **Pinned revision:** `02a396ffd09b283c9f092fdedeff11da6d535b66`.
6. **Expected Git blob SHA:** `7439f0ba7da6bc03625258b98fe84a5bf770b72e` from the Session 1 tree record.
7. **Observed Git blob SHA:** `7439f0ba7da6bc03625258b98fe84a5bf770b72e` from reconstructed pinned metadata
   and decoded pointer bytes.
8. **Expected size in the failed Session 6 expression:** 90,729,279 bytes from
   Contents API metadata.
9. **Observed decoded Git blob size:** 133 bytes.
10. **Actual pointer identity:** Git blob
    `7439f0ba7da6bc03625258b98fe84a5bf770b72e`, 133 bytes, valid three-line LFS
    pointer.
11. **LFS OID:** `ea97f58f8eaad925feaeacc6395ec24860dd80027af8a89450276adebd29d265`.
12. **LFS declared payload size:** 90,729,279 bytes.
13. **Exact failed check:** `len(decoded_git_blob) != contents_metadata.size`;
    the hash half of the combined condition passes.
14. **Pointer/payload conflation:** yes. Contents payload size was treated as
    pointer-blob size.
15. **Session 1 origin:** recursive Git-tree entry supplied pointer OID and
    133-byte size; Git-blob pointer parsing supplied LFS OID and declared size.
16. **Session 1 provenance correctness:** correct for the failed path and fixed
    comparator; every reconstructed pinned identity agrees.
17. **Local pinned repository integrity:** unavailable because no documented
    source checkout exists. No checkout was created or inferred.
18. **Upstream pinned-revision integrity:** verified for commit, tree, both exact
    path/OID associations, pointer blobs, pointer declarations, and LFS rule.
19. **Smudge/materialization:** did not cause the failure; Session 6 used GitHub
    API responses and never read a source working-tree tracking file.
20. **Issue scope:** verifier-wide for the two prespecified tracking paths, not
    specific to `reserved_01`.
21. **Synthetic reproduction:** all ten required Git/LFS cases passed. The exact
    failure is reproduced by a correct pointer hash plus Contents payload size.
22. **Classification:** **B — PROVENANCE BUG RECOVERABLE WITH BOUNDED REPAIR**.
23. **Rationale:** the intended payload is unique and all conflicts reduce to one
    incorrect size-semantic comparison; neither data nor scientific choice is
    ambiguous.
24. **Unique recoverability:** yes at the identity level. Reserved payload-byte
    integrity remains unverified until a separately authorized acquisition.
25. **Source revision change:** none required or recommended.
26. **Scientific-rule change:** none required or authorized.
27. **Future repair files:** prospectively update only
    `src/defensive_network_disruption/data/session6_source.py`, its Session 6
    source tests, and a new rerun protocol/runner authority. Do not edit closed
    Session 6 artifacts.
28. **Required repair invariant:** verify pointer OID and pointer byte length
    against Git tree/blob metadata; verify LFS payload SHA-256 and length against
    pointer fields after authorized download; record Contents size separately and
    never use it as pointer size.
29. **Tests before rerun:** the ten Session 6b synthetic cases plus captured
    metadata fixtures for both aliases, path/revision firewalls, pointer/payload
    separation, payload hash/size verification, redirects, and one-run state.
30. **Protocol amendment:** do not amend the historical Session 6 protocol. A new
    prospective rerun protocol must supersede it and freeze the corrected
    invariant before acquisition.
31. **Invalid Session 6 preservation:** confirmed. Its D/4 decision, partial
    downloads, access ledger, code, and reports remain unchanged.
32. **Future authorization:** explicitly authorize the new verification code,
    acquisition into a new ignored root and ledger, structural preparation, a
    committed population checkpoint, and one protected scoring execution.
33. **Files created/changed:** Phase 6b protocol, metadata-only helper, runner,
    tests, three compact output JSON files, this report, and one append-only log
    entry. The post-review code change only narrowed a publication regex and did
    not rerun source access or classification.
34. **Tests/results:** focused 17/17 passed; full active suite 96 passed with 3
    planned skips; compilation, authority checks, output hashes, publication
    checks, and diff checks passed.
35. **Reserved tracking values:** none downloaded or parsed.
36. **Reserved population:** none prepared.
37. **Models:** none fitted or scored.
38. **Passages:** none inspected.
39. **Commit/push/status and next step:** protocol `bdae204`, audit implementation
    `cbb9564`, and the result package are committed and pushed; the final handoff
    records the exact synchronized head. Next, prepare one separately authorized
    rerun protocol implementing the bounded verification repair.

## Prospective repair recommendation

Retain the frozen Session 6 implementation and its invalid result. In a separate
protocol, create a successor acquisition helper that receives the tree-recorded
pointer OID and pointer size as its Git authority. Fetch the pinned blob, require
its computed OID and byte length to match those values, parse exactly one bounded
LFS pointer, and treat Contents API size as informational payload metadata only.
After a newly authorized payload download, require its SHA-256 and byte count to
match the pointer before parsing.

Use a new ignored acquisition root and access ledger so the failed attempt remains
auditable. Freeze and commit the repair and captured metadata regression tests,
then require explicit authorization for renewed acquisition, structural reserved
preparation, its population checkpoint, and one protected score. Session 6b does
not grant that authority.

The compact manifest SHA-256 is
`14e67c1ff8454c9a1e77b8f7bfd2efb799a3e5fe5fe14ea070bd4438a98b5c06`.
