# Phase 14ah — empirical canonical-switch owner diagnosis

**Status:** frozen prospective authority  
**Date:** 2026-09-13  
**Starting commit:** `dcbada1334af9408bdb08a5c7721fb8b4c26c801`

## Question and scope

Session 14ah asks what topology caused `switch_owner_semantics_changed` on the
single already-exposed Session 14R6 location, and whether that topology is valid
under the unchanged constant-width field. It separately repairs prospective
failure publication so bounded `numerical_stage` diagnostics can coexist with
unchanged lifecycle events. It performs no scientific comparison.

Only zero-based prepared state ordinal 2, receiver ordinal 8 and candidate
`constant_width` are authorized. Exact geometry, roots, bits, individual field
values, owner sequences and traceback remain ignored. Public records contain
neutral ordinals, sanitized classifications, counts, equality flags and hashes.
No other receiver, the two completed-state summaries, targets, outcomes, models,
shares, protected or withheld data, pose, xT or progression may be opened.

## Bound authority

- R6 protocol SHA-256: `6d3eb647091c8562836592469d1cbf765c2b164bfb6a506962bec08985899a80`.
- R6 runner SHA-256: `01b06d766cf2bcb1488447ea3ed8bf6fb7cecdb211e278b2d66a6d860b584d25`.
- R6 manifest SHA-256: `15fb0f626bf591d95b20060feed0620169327f97f642e9c7eaa8420224e95e27`.
- R6 compact failure authority SHA-256: `5413afab0ec6ec1a3295468028c767fe4a72d7461d8c822b9ab75936562aa469`.
- Prepared population SHA-256: `15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0`.
- Canonical population SHA-256: `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
- R6 journal SHA-256: `3f210d54065ab716ab07a6dfe78772189495832be424c0953857217930a9c9a7`.
- R6 launch-failure SHA-256: `3687db657a4689d13554ea240e826bee06092aff56318926e128d5df5481b0e6`.

R6 remains D/readiness 3. Its retained journal and launcher failure establish
the access and exception history. Its normal failure publisher did not close:
exposure replay rejected `numerical_stage`, the emergency path repeated that
replay, and the committed compact manifest does not satisfy the R6 runner's
normal publication schema. Session 14ah does not retroactively validate R6.

## Frozen diagnosis

The unchanged detector evaluates owners at probes no farther than `1e-7` and
one quarter of adjacent partition spacing. The unchanged canonical certifier
begins with witnesses one `1/65536` grid cell from the raw root and expands if
needed. The failing invariant is exact tuple equality between the owners at the
certifier witnesses and the detector's stored `owners_before` and
`owners_after`; mismatch raises `switch_owner_semantics_changed`. Different
probe locations are a hypothesis, not a diagnosis.

The diagnostic will reproduce the unchanged failure and record privately the
solver bracket, Brent root and bits, residual, crossing pairs, detector probes,
certification witnesses, attempted enclosure, analytical onsets and tie
boundaries. A minimal neighborhood contains each disputed root or canonical
candidate and its first two predecessor and successor floats, deduplicated by
bits. At each point it records individual values, maximum and the inherited
absolute `1e-12` block-high owners. No broad empirical grid or second edge is
permitted. Unreturned canonical records are `uncertified`.

Production health is limited to the unchanged joint-Simpson ladder, finiteness,
bounded-residual routing and existing maximum checks. Independent maximum
integration is unavailable if unchanged certification cannot produce valid
partitions. Continuity uses the existing analytical and independent scalar
oracle authority; slopes alone do not prove continuity.

Primary diagnoses are: A valid topology/current invariant too narrow; B
canonicalization defect; C tie or multiway representation defect; D onset and
switch coincidence defect; E owner-certification implementation bug; F
production numerical defect; G multiple issues; H unresolved. Readiness is 1
bounded owner-contract repair, 2 small implementation repair, 3 representation
or numerical redesign, or 4 more evidence.

## Prospective publication adapter

Before empirical access, a new versioned adapter will validate the complete
hash-chained journal. It accepts `numerical_stage` only while a matching field
call is active, with string state/edge/candidate, a known stage, and a mapping
detail whose optional `pieces`, `bounded` and `quadrature` values are nonnegative
integers and consistent when all are present. Diagnostics never alter lifecycle
or access counters. All other events retain the unchanged exposure semantics.

Missing or invalid stage, wrong type or context, forbidden extra payload keys,
unknown events, and lifecycle/access mismatches fail. Normal publication binds
the actual journal, lifecycle snapshot, QC, evidence and manifest. An independent
emergency writer records the original and publication exceptions without first
requiring journal replay. This is prospective compatibility only.

## Execution and stop rules

The runner exposes only `preflight`, `diagnose` and `publication-check`. Protocol
and tested-tooling commits must precede the one diagnosis. Access attempts and
successful materialization are written durably under an exclusive marker. The
prepared line is compared byte-for-byte with the exact current selective
reconstruction before geometry is used. Any ambiguity, failure mismatch,
additional defect or post-access exception is retained and closes the phase
without repair, rerun or another edge.

Evidence is hash-closed before interpretation. A post-diagnostic synthetic
topology description may be recorded, but no numerical execution or switch
repair follows exposure. The claim ledger and all historical artifacts remain
unchanged. Exactly one later governed action is recommended from the observed
diagnosis.
