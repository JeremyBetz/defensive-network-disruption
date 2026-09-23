# Phase 14R9AC-CI2 — Checkpoint CI attempt-binding repair

Planning: ON  
Turbo: OFF  
Model: Astra Medium

## Prospective authority

Start from clean synchronized `34e44aab799075f52bfe2ea346db87139f3b8a5b`.
Preserve release `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
R9AC remains unexecuted. R9M v1 binds runs and jobs but cannot encode an
attempt. Run 35878553378 attempt 1 was cancelled; attempt 2 succeeded.
Cancellation actor/cause is not established by actor metadata.

No empirical access, terminal authority decoding, bound invocation, operational
R9AC receipt or execution marker is authorized. No numerical/scientific change.
Preserve historical v1 implementation, receipts and behavior byte-for-byte.

## Version 2 contract

New internal immutable expectation and verified-authority objects use
schema_version 2 and authority_id checkpoint_ci_authority_v2. Canonical JSON
has sorted keys, compact separators, ASCII escaping, finite numbers and one
newline. Hash complete bytes externally; provenance_sha256 hashes the complete
object without that field. Bind repository, exact commit, numeric workflow ID,
name/path/source hash, run ID, positive attempt, exact required job names and IDs,
completed-success statuses, UTC timestamps, protocol/runner/lockfile hashes,
capture environment, and canonical authenticated source metadata hashes.

Capture selects the explicit REST attempt endpoint and paginated attempt jobs;
every job must match run, attempt, commit and repository URL context. Reject
missing/extra/duplicate jobs, mixed attempts, unsuccessful/nonexistent attempts,
wrong workflow/repository/commit and invalid timestamps. Capture metadata and
receipt with create-once synchronized writes; interrupted capture is preserved
and cannot be overwritten. No inference from latest run state.

Offline verification checks strict schemas, canonical bytes/provenance, complete
source consistency, immutable independently supplied run/attempt selection and
expected content hash, and implementation bindings. It never contacts GitHub.
Historical v1 remains on its unchanged path and cannot satisfy a v2 gate.

The new capture command requires explicit run, attempt, checkpoint, protocol and
runner. Resolve all bound source bytes from that checkpoint's Git objects.
R9AC preflight and persisted-publication receipt validation require v2 through
one helper. Execution requires current HEAD; publication requires the recorded
execution checkpoint. Freeze selection alongside the receipt with its hash.
Do not change numerical behavior or the three R9AC commands.

## Acceptance and delivery

After implementation CI passes all three required jobs, capture exactly one
CI2-only validation receipt for checkpoint 34e44aab799075f52bfe2ea346db87139f3b8a5b,
run 35878553378, attempt 2. Required IDs: distribution 107278457488,
test (3.11) 107278457283, test (3.13) 107278457058. Validate offline and prove
that it cannot authorize the newer repair HEAD. Never place it in R9AC's
operational namespace. Future execution needs fresh exact-checkpoint authority.

Before capture test correct selection, cancelled/nonexistent attempts, mixed IDs,
wrong bindings, missing/tampered attempt, unsuccessful jobs, timestamps,
pagination, interrupted/duplicate writes, canonical/provenance/source tampering,
v1 preservation, both R9AC gates, stale authority, and offline/access tripwires.
Run focused/R9M/R9AC, full and actual tracked-checkout suites, compilation,
hash/schema/privacy/link/history/staged/diff checks. Report run/pass/skip counts.

Unexpected acceptance/integrity failure stops acceptance without recapture.
Preserve failures separately and do not expand into numerical work.

Exactly six sanitized files in outputs/continuous_occlusion_checkpoint_attempt_binding_repair:
repair_contract.json, receipt_regression.json, negative_controls.csv,
historical_preservation.json, qc.json, manifest.json. Private source/receipt/test
evidence is indexed by hash. Publication checking is read-only with no recapture.
Report maps all 15 handoff items; append one bounded research-log entry.

Three commits: research: freeze checkpoint attempt-binding repair;
fix: bind checkpoint CI authority to workflow attempt;
research: close checkpoint attempt-binding repair. Push implementation and require
green distribution/test (3.11)/test (3.13) before capture; require final green CI,
clean synchronized heads and unchanged tag after closure.

A/readiness 1 requires complete repair, both receipt paths, compatibility,
negative controls, authenticated capture, zero access and green delivery.
B/2 is partial repair; C/3 is historical compatibility broken; D/4 is invalid or
blocked. If A/1 recommend exactly: resume R9AC at v2 checkpoint-receipt capture
and frozen preflight, then execute the single terminal-cell bound if all gates
pass. Do not execute that recommendation here.
