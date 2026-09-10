# Phase 06b protocol: tracking Git/LFS integrity review

**Status:** FROZEN FOR METADATA-ONLY REVIEW

**Starting authority:** `045d24ab014a2962d9da046bf0b2efc3eb805664`

**SkillCorner source:** `02a396ffd09b283c9f092fdedeff11da6d535b66`

## Question and boundaries

Determine whether Session 6's `reserved_01` tracking failure arose from a
provenance-record defect, Git/LFS representation mismatch, local pinned-repository
mismatch, upstream source-state mismatch, or ambiguous payload identity. End with
one classification: A unique intended payload recoverable; B provenance bug
recoverable with bounded repair; C source-state mismatch requiring a new pin and
protocol; or D ambiguous payload identity.

This review does not authorize tracking-payload download or parsing, reserved
population construction, fitting, scoring, passage inspection, source revision
changes, or changes to scientific definitions. Session 6 remains closed as
primary D and secondary 4. Its artifacts and access ledger are immutable.

## Frozen evidence scope

The failed source is stable alias `reserved_01`, path
`data/matches/1874553/1874553_tracking_extrapolated.jsonl`. The sole comparator is
stable alias `development_01`, path
`data/matches/1886347/1886347_tracking_extrapolated.jsonl`. No other match or
provider product may be requested.

Existing evidence may be projected from Session 1 manifests and archived code,
Session 2/6a provenance outputs, the frozen Session 6 verifier, and the ignored
Session 6 access ledger. Do not open the locally acquired reserved metadata or
Dynamic Events files. Search only documented locations for a pre-existing
SkillCorner source checkout; do not create, fetch, checkout, smudge, or pull one.

New upstream access is limited to GitHub API metadata for the pinned commit,
commit tree, exact path entries, Git blob envelopes, bounded Git LFS pointer
bytes, Contents API metadata, and `.gitattributes`. Never follow `download_url`,
media, raw tracking, LFS batch/download, or tracking-preview endpoints. Reject
redirects, substituted revisions, unexpected object types, unexpected paths,
oversized JSON responses, and decoded pointer content over 1 KiB.

Only the three LFS pointer fields may be decoded: version line, SHA-256 OID, and
declared payload size. No tracking JSONL value may enter memory, logs, errors, or
artifacts. Record every request immediately in a new ignored append-only ledger.

## Identity model and diagnostics

Represent independently:

1. pinned commit, tree, path, object type, and Git blob OID;
2. Git tree/blob pointer byte size;
3. Git blob envelope size and decoded pointer byte count;
4. Contents API reported size;
5. LFS payload SHA-256 OID and declared payload byte size.

For every identity claim record its source artifact, field origin, claimed
values, and evidence status: `contemporaneous`, `reconstructed`, `unavailable`,
or `not_evaluated`. Filenames alone do not establish equivalence. Pointer identity
establishes an intended payload identity but not downloaded-payload integrity.

Reproduce the frozen Session 6 comparison while reporting expected and observed
hash and size checks separately. Determine whether the Contents API exposes
pointer size or payload size at this pinned path. Compare the same semantics for
`development_01` using recorded identities before any permitted upstream query.
Do not characterize reconstructed values as values retained by Session 6.

## Commands and chronology

The separate standard-library runner exposes:

- `preflight`: verify starting authority, closed-artifact integrity, exact source
  and path allowlists, ignored storage, and absence of prohibited imports;
- `review`: project existing records, perform bounded metadata-only requests,
  classify the evidence, and write compact outputs;
- `publication-check`: validate schemas, hashes, aliases, provenance labels, and
  absence of paths, payload content, football values, or scientific outputs.

Commit this protocol before implementing the audit. Commit the tested audit
implementation before `review`. Commit the reviewed result package separately;
do not amend or squash these checkpoints.

## Synthetic requirements

Test ordinary blobs; distinct pointer/payload sizes; correct pointer SHA/OID;
pointer SHA mismatch; pointer-size mismatch; LFS OID mismatch; synthetic payload-
size mismatch; materialized working-tree bytes with unchanged pointer identity;
wrong revision/path association; and malformed pointers. Also test match/product,
path, symlink, redirect, response-size, and publication firewalls.

Static tests must prove that the review runner has no tracking-payload endpoint,
tracking parser, population builder, model fitter, ranking, or scoring import or
call path. Run focused and full active tests, compilation, authority and output
hash checks, staged review, and `git diff --check`.

## Outputs and decision rule

Create only:

- `docs/session_06b_tracking_integrity_review.md`;
- `outputs/tracking_integrity_review/identity_comparison.json`;
- `outputs/tracking_integrity_review/verifier_diagnostics.json`;
- `outputs/tracking_integrity_review/manifest.json`;
- bounded append-only additions to `docs/research_log.md`.

Detailed request records and local paths remain ignored. Public outputs contain
stable aliases, bounded identity metadata, hashes, and verification states only.
The report maps all 39 requested items to evidence or an explicit unavailable
status and records the manifest's external SHA-256.

Choose B when the pinned path has one valid pointer and payload identity and the
failure is fully explained by repairable provenance/verifier semantics. Choose A
only if no such defect exists. Choose C only when the current pin cannot support
the intended identity. Choose D when multiple plausible identities remain or
provenance cannot select one.

For A or B, draft a prospective repair plan without implementing it. Name the
defect, future code and protocol changes, invariants, tests, preserved invalid
history, and the exact authorization needed for renewed acquisition, structural
preparation, and one scoring run. Stop after classification and recommendation.
