# Phase 14ap — Terminal subdivision and error-evidence review

Date: 2026-09-14. Planning: ON; Turbo: OFF; Model: Sol Medium.
Starting authority: `fba26be949b7cbe3ded168222b3a9f8e9ccbddfb`.
Local, tracking and live GitHub heads were clean and synchronized before
mutation. Preserve annotated `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question and boundary

Review only Session 14ao's retained terminal subdivision and error records to
determine what they establish about convergence, why the warning occurred, and
what exact evidence remains missing. This phase performs no field evaluation,
quadrature, geometry reconstruction, tolerance change, subdivision-limit
change, warning suppression, alternative integration or scientific analysis.
It opens no empirical row or edge. Session 14ao remains H/readiness 4 and is not
rewritten, repaired or rerun.

Use a standard-library-only internal reviewer and an isolated runner exposing
only `preflight`, `review` and `publication-check`. The runner must not import
NumPy, SciPy's numerical modules, a geometry module, a field evaluator or an
integration function. Reading the installed SciPy source text for warning
semantics is documentary inspection, not numerical execution.

## Retained authority

The Session 14ao public manifest SHA-256 is
`367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3`.
Its private-index SHA-256 is
`23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955`.
The exact allowlisted projection contains 68 indexed records and its canonical
`{filename: sha256}` mapping has SHA-256
`66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a`.
It consists only of:

- `000001_reference.json` and `000003_onsets.json`;
- levels `000022`, `000042`, `000062`, `000082`, `000102`, `000122`;
- comparisons `000023`, `000043`, `000063`, `000083`, `000103`, `000123`;
- the nine `_piece.json` records immediately preceding each level, beginning
  `000005` and ending `000121`, for 54 piece records total.

The reviewer must reconstruct this filename set from the frozen sequence,
compare it exactly with the selected private-index entries, recompute the
canonical mapping digest, and hash-check every record before decoding it. It
must reject missing, additional, changed, nonfinite or malformed evidence.
`000002_selected_geometry.json`, all `_piece_started.json` records, the journal,
attempt marker, synthetic controls, and every other historical/private product
are outside the review projection and must not be opened.

The locked SciPy source is
`.venv/lib/python3.13/site-packages/scipy/integrate/_quadpack_py.py`, version
1.18.1, SHA-256
`c59e4133f23ef272e488204c217caf36a38b5921fe0ffeeb2a8f1b804f5ba0d9`.
The lock SHA-256 is
`c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c`.
Locate the installed source through standard-library package metadata, require
the version and source hash, and match the retained warning text to the local
documented termination explanation. Do not import or call quadrature.

Documentary bindings:

- `AGENTS.md`: `269f22fa10845e267b4cd4dc02cca48ed94ea42db0fca594e7e67409122b0501`
- `docs/research_governance.md`: `c5c37b6e8f4dcf6799570c15fdb351dfeeb76847e2d74bc23371c1b0af8150a2`
- `docs/research_log.md`: `f018aafc265eae1ed813dfddbb9be2cf81d7f2ad3fb7269de58b6d1a8b39bb6e`
- Phase 14ao protocol: `1bc295129b7306ea2d900213356441b50894ebcc353299f8a46e3ba9d3a4513b`
- Session 14ao report: `85a8f83a4f1b4b041cff47cbda431fb703e2637130cbc6f43493b4849bac9d39`
- Session 14ao numerical helper: `8a5035e939ee0c4aeb122c9130122b2c47363626fb58e9d6c7ad39524a6394b4`
- Session 14ao runner: `335e59a16b2e5f95ef1581a857dc04e72a84be95257e1723dfe618fd7af67c9f`

## Read-only reductions

Validate initialized terminal arrays using `last`: their lengths must equal
`last`, endpoints must be ordered inside the piece, estimates and errors must
be finite, and `neval` must equal callback count and retained trace length.
Never inspect uninitialized storage.

For every level retain exact values privately and publish only availability,
counts, exact-equality flags, gate flags, behavior labels and evidence hashes.
Compute adjacent estimate/error differences from retained values only. The
warning-level aggregate estimate was historically unavailable because 14ao
sets incomplete-level totals to null. If all nine returned piece estimates are
present, privately compute `math.fsum` and label it
`reviewer_derived_piece_return_sum`; never relabel it a historical level result.

Verify trace identity by direct ordered equality of every retained `(t,value)`
pair, per-piece trace hashes, ordered piece-hash sequences, terminal arrays and
level hashes. A matching level hash alone is insufficient. Report exactly which
layers match.

Reconstruct only the retained terminal partition representation. Calculate
active interval counts, subdivision operations, width summaries, error ranking,
cumulative top-one/top-three shares, sanitized dominant interval ordinals and
exact onset-endpoint adjacency using the retained onset record. Do not infer a
switch, geometry, rejected-panel history, intermediate global estimate, local
tolerance acceptance or unrecorded refinement. State whether retained errors
shrink, plateau, oscillate or inflate, and separately whether estimates stabilize.

The warning interpretation must distinguish:

1. stability of returned estimates;
2. behavior of reported error estimates;
3. certification under the warning-free and retained-reference agreement rules.

The integrator's reported roundoff condition is evidence about its termination
decision, not independent proof of the true numerical error or field behavior.

## Prospective decision rules

Use existing comparison authority `G = 1e-10`. Apply classifications in this
order:

1. **G — invalid/evidence-integrity failure** for any source, hash, schema,
   chronology, finiteness or execution failure.
2. **E — multiple identified mechanisms** only for two independently supported
   mechanisms; two descriptions of one warning are not independent.
3. **D — estimate itself not converged** when retained adjacent estimates drift
   beyond `G` or the warning-level returned-component sum is inconsistent with
   the completed plateau beyond `G`.
4. **C — roundoff/subdivision limitation identified** when exact retained
   termination metadata maps to the locked implementation's roundoff or work
   limitation and the retained arrays support that bounded statement.
5. **B — terminal error remains above contract despite stable estimate** when
   estimates are stable but a retained terminal error or agreement condition
   remains outside its frozen condition and no more specific mechanism is
   established.
6. **A — stable estimate; certification failure only** only when retained
   independent authority establishes accuracy within the existing gate and the
   remaining failure is certification alone.
7. **F — retained evidence insufficient** otherwise.

Readiness: A -> 1; B/C -> 2 unless the retained evidence independently proves
the method needs revision, then 3; D/E -> 3; G -> 4. F -> 2 only when one bounded
evidence item can resolve the ambiguity and is available under separate
authority, otherwise 4.

If evidence is insufficient, select exactly one next item from the first unmet
entry in this order: warning-level returned component; initialized warning-level
local-error vector or termination metadata; one independently bounded reference
for the sanitized terminal interval responsible for the unresolved discrepancy;
one unchanged-method next-level record that demonstrably performs additional
work. Recommend it but do not acquire it.

## Persistence, outputs and closure

Use a create-once marker, atomic files and an independently writable failure
record. Store exact values and all derived exact quantities in ignored `local/`
evidence with a hash-bound private index. Public outputs contain no exact
single-edge estimate, error, difference, width, coordinate, trace or warning-piece
value.

Create exactly seven public artifacts under
`outputs/continuous_occlusion_terminal_error_review/`:

- `level_summary.csv`
- `terminal_subdivision_summary.json`
- `error_contribution_summary.csv`
- `warning_semantics.json`
- `missing_evidence.json`
- `qc.json`
- `manifest.json`

Freeze complete, partial and invalid schemas in tested code. Publication checking
must validate actual stored evidence, recompute all hashes and classification,
and never regenerate or substitute missing outputs. A partial or invalid package
cannot claim A/B/C readiness.

Before the governed review, test complete/partial retained histories, unavailable
warning estimates, exact/hash-only trace cases, changed nodes/values/topology,
error trends, malformed arrays, nonfinite data, warning-source mismatch,
classification rejection, privacy, evidence changes, marker collision and
failure closure. Run focused and relevant tests, compilation and the full suite.
These are synthetic validation only and do not create review evidence.

Execute one retained-evidence review after committing tested tooling. Preserve
unexpected failure without repair or rerun. Close evidence before classification,
write `docs/session_14ap_terminal_error_evidence_review.md`, append one research-log
entry, and make exactly three commits: protocol; tested tooling; closed evidence.
Push, require green Python 3.11, Python 3.13 and distribution CI, verify clean
synchronized heads and the unchanged release, recommend exactly one bounded next
action, and stop.
