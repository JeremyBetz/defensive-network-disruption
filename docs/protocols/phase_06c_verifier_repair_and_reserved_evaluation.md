# Phase 06c protocol: verifier repair and corrected reserved evaluation

**Status:** FROZEN FOR ONE CORRECTED EXECUTION

**Starting authority:** `5d2a4f94d88ff479834ead4ef05ed50b051c62f3`

**SkillCorner source:** `02a396ffd09b283c9f092fdedeff11da6d535b66`

## Historical authority and question

Session 6 remains closed as **D / 4 — EXECUTION INVALID**. It failed before a
tracking payload was downloaded or parsed because its verifier compared the
decoded 133-byte Git LFS pointer for `reserved_01` with the Contents API's
90,729,279-byte payload-size value. Session 6b remains closed as **B — PROVENANCE
BUG RECOVERABLE WITH BOUNDED REPAIR**: the pinned pointer uniquely identified the
intended payload, but did not establish downloaded-payload integrity.

Session 6c asks the two unchanged protected questions, in order: whether frozen
M1 improves receiver ranking over M0, and whether frozen M2 improves it over M1.
This protocol authorizes only a bounded verifier repair, renewed acquisition,
structural population preparation, and one corrected scoring execution. Closed
Session 2/3/4/5/6a/6/6b files and results remain immutable.

The development set, models, preprocessing, pass and label semantics, timing,
coordinates, candidates, defenders, exclusion waterfall, metrics, ties, and
aggregation are unchanged. Rebuilding the development population, refitting,
development-performance calculation, passage inspection, pose, orientation,
network features, and new scientific choices are prohibited.

## Partitions and access

Reserved provider IDs are exactly `1874553`, `1927964`, `1959846`, `1986691`,
`1996436`, `2006363`, `2007448`, `2007721`, `2010085`, and `2016236`, assigned
`reserved_01` through `reserved_10` in ascending order. Match `1953632` remains
withheld and unopened. The reservation qualification is:

> Prospectively reserved from this project stage forward. Session 1 schema inventory mechanically over-read post-header bytes into process memory, but no evidence indicates value-level content was surfaced, persisted, or used analytically.

The nine development IDs remain `1886347`, `1899585`, `1925299`, `1996435`,
`2006229`, `2011166`, `2013725`, `2015213`, and `2017461`. Development access is
limited to Git/object/pointer metadata and hashing already-present ignored
tracking payloads without parsing them.

For every reserved match, only metadata, Dynamic Events, and extrapolated
tracking are authorized. Reject every other match and product before a request
or file open. Store new opaque products under ignored `data/session_06c/` and
detailed identities, receipts, population, ledger, and execution state under
ignored `outputs/reserved_evaluation_v2/local/`. Use a new append-only ledger;
do not alter historical downloads or ledgers.

## Corrected source verification

Implement the repair in a versioned Session 6c helper and runner. Do not edit the
historical Session 6 or 6b implementations. Commands are `preflight`,
`verify-sources`, `acquire-reserved`, `prepare-reserved`, `score`, and
`publication-check`; none crosses a required commit boundary automatically.

For every authorized path verify the pinned commit, actual Git tree entry, exact
path, blob type, Git OID, and tree byte size. Decode the Git blob envelope and
require its OID, size, computed Git hash, and decoded length to match the tree.
For tracking, bound pointer bytes to 1 KiB and require exactly these semantic
lines: the Git LFS v1 version, `oid sha256:` plus 64 lowercase hexadecimal
characters, and `size` plus a nonnegative decimal integer. LF or CRLF and trailing
whitespace-only lines are allowed; other content is not. Contents API size is
diagnostic only and is never the pointer-blob size authority.

Before parsing a downloaded tracking payload, require its actual SHA-256 and byte
count to equal the pointer OID and declared payload size. Verify ordinary
metadata/event bytes against their Git object identity and size before projected
parsing. Reject path traversal, symlinks, redirects, revisions or paths that
change, unexpected object types, unapproved hosts, and oversized responses.

## Frozen transport retry policy

Each individual acquisition request permits an initial attempt plus at most two
retries, only for a timeout, connection reset or dropped connection, explicit
interrupted-stream transport error, or HTTP 500, 502, 503, or 504. Wait one second
before retry one and two seconds before retry two.

Every attempt requests the identical endpoint, pin, path, and expected identity;
receives its own ledger entry with attempt and failure category; and writes to a
fresh temporary file. Discard incomplete bytes before restarting and never
resume or combine streams. A verified earlier product does not disable retries
for a later product.

Never retry an identity or hash mismatch, declared-size mismatch, cleanly
completed truncated response, redirect or substitution, unsupported schema, or
parse/input-contract failure. Never redownload an already verified product
automatically. Exhausted transport retries preserve verified products and
failure metadata, discard incomplete bytes, and stop Session 6c.

## Prospective checkpoints

Before upstream inspection, commit this protocol and then the tested repair.
`verify-sources` must apply the corrected contract to all nine development
tracking identities and establish object/pointer identities for all authorized
reserved products. Any ambiguity stops before acquisition.

Commit `outputs/reserved_evaluation_v2/repair_authority.json` before reserved
payload acquisition. It binds the protocol, verifier, tests, environment lock,
source revision, development compatibility, exact reserved paths, Git pointer
OIDs, LFS payload OIDs, declared sizes, ordinary-product identities, closed
historical authorities, and unchanged final-development-model artifact.

After that commit, acquire and integrity-check all thirty reserved products in
ascending match order. Source verification and structural preparation constitute
protected-value exposure. Any newly discovered implementation or input-contract
problem stops this execution and is not repaired in place.

Only after all products pass integrity checks may projected parsing begin. Use
the strict frozen Session 6 input contract. Unsupported identity/schema/clock or
interval cases stop. Established observation cases retain the six-category
waterfall without repair or new exclusions. Preparation cannot calculate
utilities, rankings, or metrics.

Publish aggregate structural counts, separate evaluation/fit eligibility,
target completeness and outside-set reasons, candidates, defenders, QC, and
per-match/combined population hashes in
`outputs/reserved_evaluation_v2/population_summary.json`. Require all ten aliases,
no withheld/development substitution, and a nonempty evaluation population in
each match. Commit this authority before scoring; population rules then cannot
change.

## Models, scoring, and results

Reuse, without refitting, the final development model artifact whose SHA-256 is
`0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`.
Verify its original protocol and implementation authority, M0/M1/M2 feature
orders, preprocessing, coefficients, fit QC, environment, and population link.
New Session 6c infrastructure hashes are separate. Any invalid authority stops.

Scoring requires clean committed checkpoints, unchanged hashes, ten nonempty
groups, absent Session 6c results, and an atomically created Session 6c execution
marker. It cannot acquire, parse provider products, fit, or estimate
preprocessing. Apply frozen models once to identical observations.

Use descending utility, the absolute `1e-12` block-high tie rule, expected MRR and
Hit@1/3 credits, and zero credit for retained target-outside cases. Average within
match and equally across ten matches. Report M1-minus-M0 first and M2-minus-M1
second, including ten differences, mean, median, sign counts, and secondary
metric agreement. No significance test, bootstrap, extra metric, threshold,
tuning, alternate model, or rerun is authorized.

Write the requested metric CSVs, paired CSVs, `aggregate_metrics.json`, `qc.json`,
and `manifest.json` atomically under `outputs/reserved_evaluation_v2/`. Validate
and hash the closed package before performance is displayed or interpreted. Keep
raw rows, identities, paths, coordinates, timestamps, candidates, and per-attempt
outputs ignored and publish only stable aliases and non-reconstructive aggregates.

## Regression, validation, and stop rule

Before acquisition, test all eighteen specified Git/LFS cases. The frozen Session
6 verifier must reproduce the 133/90,729,279 failure while the corrected verifier
accepts it. Test the exact retry categories, waits, identity stability, fresh
temporary files, disposal, ledger records, and exhaustion. Also test access and
projection firewalls, strict input handling, timing, candidates, feature nesting,
final-model authority, metrics/ties, command separation, concurrency, schemas,
and a synthetic end-to-end rehearsal.

After scoring, run focused and full active tests, compilation, schema and hash
checks, publication and changed-artifact guards, staged inspection, and
`git diff --check`. Reverify all historical authorities. Maintain separate
protocol, implementation/tests, repair-authority, population-authority, and
reviewed-result commits; do not amend or squash.

Classify primary replication as A/B/C/D and secondary replication as 1/2/3/4
using descriptive paired evidence without post-hoc cutoffs. Vendor targets retain
Tier B limitations, accessibility remains **PROXY ONLY**, suppression remains
**NOT SUPPORTABLE**, and extrapolated tracking supports only an offline benchmark.

If a defect appears after protected metrics are exposed, preserve the result and
stop without patching or rescoring. The final brief maps all 67 requested items
to evidence or explicit unavailability. Recommend one separately governed later
direction based on the primary result, but do not execute it. Stop after Session
6c without passage review, orientation, network/GNN work, M3, or new provider
work.
